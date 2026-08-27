"""One-time helper: turn a Spotify app's credentials into a refresh token.

Run this on your own machine, not in CI:

    python .github/scripts/spotify_auth.py

It opens a browser for you to approve, catches the redirect on a local port,
and prints the refresh token to paste into the repository secrets. The token
does not expire on its own, so this is a one-time step.

Before running, create an app at https://developer.spotify.com/dashboard and
add exactly this redirect URI to it:

    http://127.0.0.1:8888/callback

Spotify accepts plain http only for the loopback literal 127.0.0.1 -- not for
"localhost" -- so the address has to match character for character.
"""

from __future__ import annotations

import base64
import getpass
import http.server
import json
import secrets
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request
import webbrowser

PORT = 8888
REDIRECT = f"http://127.0.0.1:{PORT}/callback"
SCOPES = "user-read-currently-playing user-read-recently-played"

result: dict[str, str] = {}


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        result.update({k: v[0] for k, v in params.items()})
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        ok = "code" in params
        self.wfile.write(
            b"<h2>All set - you can close this tab.</h2>" if ok
            else b"<h2>Authorization failed. Check the terminal.</h2>"
        )

    def log_message(self, *args):  # keep the console clean
        pass


def main() -> int:
    client_id = input("Spotify client ID: ").strip()
    client_secret = getpass.getpass("Spotify client secret (hidden): ").strip()
    if not client_id or not client_secret:
        print("Both values are required.", file=sys.stderr)
        return 1

    state = secrets.token_urlsafe(16)
    auth_url = "https://accounts.spotify.com/authorize?" + urllib.parse.urlencode({
        "client_id": client_id,
        "response_type": "code",
        "redirect_uri": REDIRECT,
        "scope": SCOPES,
        "state": state,
    })

    server = http.server.HTTPServer(("127.0.0.1", PORT), Handler)
    threading.Thread(target=server.handle_request, daemon=True).start()

    print(f"\nOpening your browser. If nothing happens, visit:\n\n{auth_url}\n")
    try:
        webbrowser.open(auth_url)
    except webbrowser.Error:
        pass

    print("Waiting for the redirect...")
    for _ in range(300):
        if result:
            break
        threading.Event().wait(1)
    server.server_close()

    if "error" in result:
        print(f"Spotify returned an error: {result['error']}", file=sys.stderr)
        return 1
    if result.get("state") != state:
        print("State mismatch -- aborting rather than trusting the response.",
              file=sys.stderr)
        return 1
    code = result.get("code")
    if not code:
        print("No authorization code came back. Did the redirect URI match?",
              file=sys.stderr)
        return 1

    body = urllib.parse.urlencode({
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT,
    }).encode()
    basic = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    req = urllib.request.Request(
        "https://accounts.spotify.com/api/token", data=body,
        headers={"Authorization": f"Basic {basic}",
                 "Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.load(resp)
    except urllib.error.HTTPError as exc:
        print(f"Token exchange failed ({exc.code}): "
              f"{exc.read().decode('utf-8', 'replace')[:300]}", file=sys.stderr)
        return 1

    refresh = payload.get("refresh_token")
    if not refresh:
        print("No refresh token in the response.", file=sys.stderr)
        return 1

    print("\nDone. Add these three repository secrets under")
    print("Settings -> Secrets and variables -> Actions:\n")
    print(f"  SPOTIFY_CLIENT_ID      {client_id}")
    print("  SPOTIFY_CLIENT_SECRET  (the secret you just entered)")
    print(f"  SPOTIFY_REFRESH_TOKEN  {refresh}\n")
    print("Treat the refresh token like a password -- anyone holding it can")
    print("read your listening history.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
