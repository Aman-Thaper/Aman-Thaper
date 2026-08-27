"""Render the Spotify card as a committed SVG.

Talks to the Spotify Web API with a long-lived refresh token, then writes
assets/spotify.svg (and the dark variant) so the README serves the card from
this repo. Nothing is fetched when someone views the profile.

Album art is inlined as a data URI on purpose: an SVG displayed through an
<img> tag cannot load external resources, so a remote href would render empty.

Needs three repo secrets -- SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET and
SPOTIFY_REFRESH_TOKEN. Without them the script leaves the existing card in
place rather than overwriting it with an error state.
"""

from __future__ import annotations

import base64
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

OUT = "assets"
TOKEN_URL = "https://accounts.spotify.com/api/token"
API = "https://api.spotify.com/v1"

THEMES = {
    "light": {"bg": "#ffffff", "border": "#d0d7de", "text": "#1f2328",
              "muted": "#57606a", "track": "#e6e6e6"},
    "dark": {"bg": "#0d1117", "border": "#30363d", "text": "#e6edf3",
             "muted": "#8b949e", "track": "#2d333b"},
}
GREEN = "#1DB954"

W, H = 440, 128
ART = 96


def esc(text) -> str:
    return (str(text).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def clip(text: str, limit: int) -> str:
    text = str(text)
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def configured() -> bool:
    return all(os.environ.get(k) for k in
               ("SPOTIFY_CLIENT_ID", "SPOTIFY_CLIENT_SECRET", "SPOTIFY_REFRESH_TOKEN"))


def access_token() -> str | None:
    cid = os.environ.get("SPOTIFY_CLIENT_ID", "")
    secret = os.environ.get("SPOTIFY_CLIENT_SECRET", "")
    refresh = os.environ.get("SPOTIFY_REFRESH_TOKEN", "")
    if not (cid and secret and refresh):
        return None

    body = urllib.parse.urlencode(
        {"grant_type": "refresh_token", "refresh_token": refresh}
    ).encode()
    basic = base64.b64encode(f"{cid}:{secret}".encode()).decode()
    req = urllib.request.Request(
        TOKEN_URL, data=body,
        headers={"Authorization": f"Basic {basic}",
                 "Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.load(resp).get("access_token")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:200]
        print(f"token refresh failed ({exc.code}): {detail}", file=sys.stderr)
    except (urllib.error.URLError, TimeoutError) as exc:
        print(f"token refresh failed: {exc}", file=sys.stderr)
    return None


def get(path: str, token: str):
    req = urllib.request.Request(
        f"{API}{path}", headers={"Authorization": f"Bearer {token}"}
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            if resp.status == 204:  # nothing currently playing
                return None
            return json.load(resp)
    except urllib.error.HTTPError as exc:
        print(f"GET {path} -> {exc.code}", file=sys.stderr)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        print(f"GET {path} failed: {exc}", file=sys.stderr)
    return None


def current_track(token: str):
    """Whatever is playing now, else the most recent play."""
    now = get("/me/player/currently-playing", token)
    if now and now.get("item"):
        item = now["item"]
        return {
            "live": bool(now.get("is_playing")),
            "name": item.get("name", "Unknown"),
            "artists": ", ".join(a["name"] for a in item.get("artists", [])),
            "url": item.get("external_urls", {}).get("spotify", ""),
            "art": (item.get("album", {}).get("images") or [{}])[-1].get("url"),
            "progress": now.get("progress_ms") or 0,
            "duration": item.get("duration_ms") or 0,
        }

    recent = get("/me/player/recently-played?limit=1", token)
    items = (recent or {}).get("items") or []
    if not items:
        return None
    item = items[0]["track"]
    return {
        "live": False,
        "name": item.get("name", "Unknown"),
        "artists": ", ".join(a["name"] for a in item.get("artists", [])),
        "url": item.get("external_urls", {}).get("spotify", ""),
        "art": (item.get("album", {}).get("images") or [{}])[-1].get("url"),
        "progress": 0,
        "duration": item.get("duration_ms") or 0,
    }


def art_data_uri(url: str | None) -> str | None:
    if not url:
        return None
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            raw = resp.read()
            mime = resp.headers.get("Content-Type", "image/jpeg").split(";")[0]
    except (urllib.error.URLError, TimeoutError) as exc:
        print(f"album art fetch failed: {exc}", file=sys.stderr)
        return None
    return f"data:{mime};base64," + base64.b64encode(raw).decode()


def render(track: dict | None, theme: dict) -> str:
    tx = 16 + ART + 18  # text column starts right of the album art
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}" role="img" aria-label="Spotify">',
        "<style>"
        ".lbl{font:600 10px 'Segoe UI',Ubuntu,Sans-Serif;letter-spacing:1.3px}"
        ".ttl{font:600 15px 'Segoe UI',Ubuntu,Sans-Serif}"
        ".art{font:400 13px 'Segoe UI',Ubuntu,Sans-Serif}"
        "</style>",
        f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="10" '
        f'fill="{theme["bg"]}" stroke="{theme["border"]}"/>',
        f'<clipPath id="a"><rect x="16" y="16" width="{ART}" height="{ART}" rx="6"/></clipPath>',
    ]

    if track is None:
        parts += [
            f'<rect x="16" y="16" width="{ART}" height="{ART}" rx="6" fill="{theme["track"]}"/>',
            f'<circle cx="64" cy="64" r="17" fill="none" stroke="{theme["muted"]}" stroke-width="2"/>',
            f'<circle cx="64" cy="64" r="4" fill="{theme["muted"]}"/>',
            f'<text class="lbl" x="{tx}" y="52" fill="{GREEN}">SPOTIFY</text>',
            f'<text class="ttl" x="{tx}" y="76" fill="{theme["text"]}">Nothing playing</text>',
        ]
        parts.append("</svg>")
        return "\n".join(parts)

    art = art_data_uri(track.get("art"))
    if art:
        parts.append(
            f'<image x="16" y="16" width="{ART}" height="{ART}" href="{art}" '
            f'clip-path="url(#a)" preserveAspectRatio="xMidYMid slice"/>'
        )
    else:
        parts.append(
            f'<rect x="16" y="16" width="{ART}" height="{ART}" rx="6" fill="{theme["track"]}"/>'
        )

    label = "NOW PLAYING" if track["live"] else "LAST PLAYED"
    parts.append(f'<text class="lbl" x="{tx}" y="42" fill="{GREEN}">{label}</text>')
    # Three animated bars stand in for a playing indicator. Their resting height
    # is non-zero, so a renderer that ignores SMIL still shows the bars.
    if track["live"]:
        for i, (bx, dur) in enumerate(((0, "0.9s"), (5, "1.25s"), (10, "1.05s"))):
            parts.append(
                f'<rect x="{W - 36 + bx}" y="34" width="3" height="10" rx="1.5" fill="{GREEN}">'
                f'<animate attributeName="height" values="4;12;4" dur="{dur}" '
                f'repeatCount="indefinite"/>'
                f'<animate attributeName="y" values="40;32;40" dur="{dur}" '
                f'repeatCount="indefinite"/></rect>'
            )
    parts.append(
        f'<text class="ttl" x="{tx}" y="66" fill="{theme["text"]}">'
        f'{esc(clip(track["name"], 30))}</text>'
    )
    parts.append(
        f'<text class="art" x="{tx}" y="87" fill="{theme["muted"]}">'
        f'{esc(clip(track["artists"], 34))}</text>'
    )

    # Progress bar, only meaningful while something is actually playing.
    if track["live"] and track["duration"]:
        bw = W - tx - 20
        pct = max(0.0, min(1.0, track["progress"] / track["duration"]))
        parts.append(
            f'<rect x="{tx}" y="102" width="{bw}" height="4" rx="2" fill="{theme["track"]}"/>'
        )
        parts.append(
            f'<rect x="{tx}" y="102" width="{bw * pct:.1f}" height="4" rx="2" fill="{GREEN}"/>'
        )
    parts.append("</svg>")
    return "\n".join(parts)


def write(track, label: str) -> int:
    os.makedirs(OUT, exist_ok=True)
    for suffix, theme in THEMES.items():
        tag = "" if suffix == "light" else "-dark"
        path = os.path.join(OUT, f"spotify{tag}.svg")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(render(track, theme))
        print(f"wrote {path}")
    print(label)
    return 0


def main() -> int:
    if not configured():
        # Never set up. Publish the neutral card so the README has something
        # to show rather than a broken image.
        print("spotify credentials not set; publishing the placeholder card",
              file=sys.stderr)
        return write(None, "placeholder card written")

    token = access_token()
    if token is None:
        # Configured, but the refresh failed. Keeping the last good card beats
        # replacing it with an error state.
        print("token refresh failed; leaving the existing card in place",
              file=sys.stderr)
        return 0

    track = current_track(token)
    if track:
        state = "now playing" if track["live"] else "last played"
        return write(track, f"{state}: {track['name']} — {track['artists']}")
    return write(None, "no recent listening data")


if __name__ == "__main__":
    raise SystemExit(main())
