"""Render the profile cards as static SVGs.

Everything the README shows is generated here and committed to the repo, so the
images are served straight from GitHub instead of a third-party renderer that
can rate-limit or disappear. Standard library only -- no install step in CI.

Each card is emitted twice, light and dark, and the README picks between them
with <picture>. That is the same pattern the contribution snake already uses.
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from collections import Counter
from datetime import date, timedelta

USER = os.environ.get("PROFILE_USER", "Aman-Thaper")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUT = "assets"

# Palette. `accent` is the violet the rest of the profile is built around.
THEMES = {
    "light": {
        "bg": "#ffffff", "border": "#d0d7de", "title": "#7c3aed",
        "label": "#57606a", "value": "#1f2328", "accent": "#7c3aed",
        "muted": "#8c959f",
    },
    "dark": {
        "bg": "#0d1117", "border": "#30363d", "title": "#8b5cf6",
        "label": "#8b949e", "value": "#e6edf3", "accent": "#8b5cf6",
        "muted": "#6e7681",
    },
}

# Brand colours for the languages this profile actually surfaces; anything else
# falls back to a neutral so an unmapped language still renders.
LANG_COLORS = {
    "Python": "#3572A5", "JavaScript": "#f1e05a", "TypeScript": "#3178c6",
    "Java": "#b07219", "C": "#555555", "HTML": "#e34c26", "CSS": "#563d7c",
    "Shell": "#89e051", "Dockerfile": "#384d54", "Makefile": "#427819",
    "Jupyter Notebook": "#DA5B0B", "C++": "#f34b7d", "Go": "#00ADD8",
    "Rust": "#dea584", "Ruby": "#701516", "PHP": "#4F5D95",
}
FALLBACK_LANG_COLOR = "#8b949e"


def api(path: str):
    """GET a JSON endpoint, returning None rather than raising on failure."""
    req = urllib.request.Request(
        f"https://api.github.com{path}",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": f"{USER}-profile-cards",
            **({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}),
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.load(resp)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        print(f"warning: GET {path} failed: {exc}", file=sys.stderr)
        return None


def esc(text) -> str:
    return (
        str(text)
        .replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def human(n: int) -> str:
    return f"{n/1000:.1f}k".replace(".0k", "k") if n >= 1000 else str(n)


def collect():
    """Pull the public numbers behind both cards."""
    user = api(f"/users/{USER}") or {}

    repos, page = [], 1
    while page <= 5:
        batch = api(f"/users/{USER}/repos?per_page=100&page={page}&type=owner")
        if not batch:
            break
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1

    owned = [r for r in repos if not r.get("fork")]
    stars = sum(r.get("stargazers_count", 0) for r in owned)
    forks = sum(r.get("forks_count", 0) for r in owned)

    # Language totals are byte counts, so a big repo counts more than a stub.
    langs: Counter[str] = Counter()
    for repo in owned:
        data = api(f"/repos/{USER}/{repo['name']}/languages")
        if data:
            langs.update(data)

    return {
        "name": user.get("name") or USER,
        "repos": len(owned),
        "followers": user.get("followers", 0),
        "stars": stars,
        "forks": forks,
        "contrib": contributions(),
        "langs": langs,
    }


def contributions():
    """Total contributions in the last year plus the current streak.

    Read off the public contribution calendar -- the same page the graph on the
    profile renders from -- so it needs no token and no extra scope. Returns
    None if the markup ever changes shape.
    """
    today = date.today()
    url = (
        f"https://github.com/users/{USER}/contributions"
        f"?from={today - timedelta(days=365)}&to={today}"
    )
    req = urllib.request.Request(url, headers={"User-Agent": f"{USER}-profile-cards"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            html = resp.read().decode("utf-8", "replace")
    except (urllib.error.URLError, TimeoutError) as exc:
        print(f"warning: contribution calendar unavailable: {exc}", file=sys.stderr)
        return None

    cells = re.findall(r'data-date="(\d{4}-\d{2}-\d{2})"[^>]*data-level="(\d+)"', html)
    if not cells:
        cells = [(d, lvl) for d, lvl in re.findall(
            r'data-level="(\d+)"[^>]*data-date="(\d{4}-\d{2}-\d{2})"', html)]
    counts = re.findall(r'data-count="(\d+)"', html)
    if not counts and not cells:
        print("warning: unrecognised calendar markup", file=sys.stderr)
        return None

    total = sum(int(c) for c in counts) if counts else None

    # Walk backwards from today. Today being empty does not break a streak yet;
    # any earlier empty day does.
    streak = 0
    if cells:
        by_date = {d: int(lvl) for d, lvl in cells}
        for i in range(0, 400):
            day = (today - timedelta(days=i)).isoformat()
            if day not in by_date:
                break
            if by_date[day] > 0:
                streak += 1
            elif i > 0:
                break
    return {"total": total, "streak": streak}


def shell(width: int, height: int, theme: dict, title: str) -> list[str]:
    """The rounded card frame and heading shared by both cards."""
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{esc(title)}">',
        "<style>"
        ".t{font:600 16px 'Segoe UI',Ubuntu,Sans-Serif}"
        ".l{font:400 13px 'Segoe UI',Ubuntu,Sans-Serif}"
        ".v{font:600 13px 'Segoe UI',Ubuntu,Sans-Serif}"
        ".s{font:400 11px 'Segoe UI',Ubuntu,Sans-Serif}"
        ".p{font:600 12px 'Segoe UI',Ubuntu,Sans-Serif}"
        "</style>",
        f'<rect x="0.5" y="0.5" width="{width-1}" height="{height-1}" rx="10" '
        f'fill="{theme["bg"]}" stroke="{theme["border"]}"/>',
        f'<text class="t" x="25" y="33" fill="{theme["title"]}">{esc(title)}</text>',
    ]


def stats_card(data: dict, theme: dict) -> str:
    # Stars and forks only earn a row once they are non-zero -- a card
    # advertising "0" reads worse than one that simply doesn't mention it.
    rows = [("Public repositories", human(data["repos"]))]
    if data.get("followers") is not None:
        rows.append(("Followers", human(data["followers"])))
    if data["stars"]:
        rows.insert(0, ("Total stars earned", human(data["stars"])))
    if data["forks"]:
        rows.insert(1 if data["stars"] else 0, ("Total forks", human(data["forks"])))
    contrib = data.get("contrib") or {}
    if contrib.get("total") is not None:
        rows.append(("Contributions (last year)", human(contrib["total"])))
    if contrib.get("streak"):
        rows.append(("Current streak", f"{contrib['streak']} days"))

    height = 70 + len(rows) * 27
    parts = shell(440, height, theme, f"{data['name']} — GitHub")
    parts.append(
        f'<line x1="25" y1="45" x2="415" y2="45" stroke="{theme["border"]}"/>'
    )
    for i, (label, value) in enumerate(rows):
        y = 70 + i * 27
        parts.append(
            f'<text class="l" x="25" y="{y}" fill="{theme["label"]}">{esc(label)}</text>'
        )
        parts.append(
            f'<text class="v" x="415" y="{y}" text-anchor="end" '
            f'fill="{theme["value"]}">{esc(value)}</text>'
        )
    parts.append("</svg>")
    return "\n".join(parts)


def languages_card(langs: Counter, theme: dict) -> str:
    top = langs.most_common(6)
    total = sum(langs.values())
    width, height = 440, 200
    parts = shell(width, height, theme, "Most used languages")

    if not top or total == 0:
        parts.append(
            f'<text class="l" x="25" y="70" fill="{theme["muted"]}">No language data yet</text>'
        )
        parts.append("</svg>")
        return "\n".join(parts)

    # Stacked bar. Clip it so the segments inherit the rounded ends.
    bar_x, bar_y, bar_w, bar_h = 25, 58, width - 50, 10
    parts.append(
        f'<clipPath id="bar"><rect x="{bar_x}" y="{bar_y}" width="{bar_w}" '
        f'height="{bar_h}" rx="5"/></clipPath>'
        f'<g clip-path="url(#bar)">'
    )
    offset = 0.0
    for name, count in top:
        seg = bar_w * count / total
        parts.append(
            f'<rect x="{bar_x + offset:.2f}" y="{bar_y}" width="{seg:.2f}" '
            f'height="{bar_h}" fill="{LANG_COLORS.get(name, FALLBACK_LANG_COLOR)}"/>'
        )
        offset += seg
    parts.append("</g>")

    # Legend, two columns.
    for i, (name, count) in enumerate(top):
        col, row = i % 2, i // 2
        x = 25 + col * 205
        y = 100 + row * 26
        pct = 100 * count / total
        parts.append(
            f'<circle cx="{x + 5}" cy="{y - 4}" r="5" '
            f'fill="{LANG_COLORS.get(name, FALLBACK_LANG_COLOR)}"/>'
        )
        parts.append(
            f'<text class="l" x="{x + 18}" y="{y}" fill="{theme["value"]}">{esc(name)}</text>'
        )
        parts.append(
            f'<text class="s" x="{x + 180}" y="{y}" text-anchor="end" '
            f'fill="{theme["muted"]}">{pct:.1f}%</text>'
        )
    parts.append("</svg>")
    return "\n".join(parts)


# The stack, rendered as pills rather than pulled from a badge service so it
# cannot go blank. Colours are each project's own brand colour.
TECH = [
    ("Languages", [
        ("Python", "#3776AB"), ("JavaScript", "#F7DF1E"), ("TypeScript", "#3178C6"),
        ("Java", "#ED8B00"), ("C", "#00599C"),
    ]),
    ("Frontend", [
        ("React", "#61DAFB"), ("Next.js", "#111111"), ("Tailwind CSS", "#06B6D4"),
        ("HTML5", "#E34F26"), ("CSS3", "#1572B6"),
    ]),
    ("Backend & data", [
        ("FastAPI", "#009688"), ("Node.js", "#339933"), ("Express", "#4b5563"),
        ("SQLAlchemy", "#D71F00"), ("MongoDB", "#47A248"), ("MySQL", "#4479A1"),
    ]),
    ("AI & tooling", [
        ("OpenAI", "#412991"), ("TensorFlow", "#FF6F00"), ("OpenCV", "#5C3EE8"),
        ("Docker", "#2496ED"), ("Git", "#F05032"), ("GitHub Actions", "#2088FF"),
    ]),
]


def ink(hex_color: str) -> str:
    """Black or white label, whichever stays legible on the pill."""
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    return "#000000" if (0.299 * r + 0.587 * g + 0.114 * b) > 150 else "#ffffff"


def tech_card(theme: dict) -> str:
    width, pad, gap = 860, 25, 7
    rows, y = [], 76

    for group, items in TECH:
        rows.append(("label", group, y))
        y += 22
        x = pad
        for name, colour in items:
            # Segoe UI at 12px semibold averages a shade under 7px per glyph.
            w = int(len(name) * 6.9) + 26
            if x + w > width - pad:
                x, y = pad, y + 32
            rows.append(("pill", (name, colour, x, y, w), None))
            x += w + gap
        y += 42

    height = y - 10
    parts = shell(width, height, theme, "Tech I build with")
    parts.append(f'<line x1="{pad}" y1="45" x2="{width-pad}" y2="45" stroke="{theme["border"]}"/>')

    for kind, payload, ry in rows:
        if kind == "label":
            parts.append(
                f'<text class="s" x="{pad}" y="{ry}" fill="{theme["muted"]}" '
                f'letter-spacing="0.6">{esc(payload.upper())}</text>'
            )
        else:
            name, colour, x, y_, w = payload
            parts.append(
                f'<rect x="{x}" y="{y_}" width="{w}" height="24" rx="12" fill="{colour}" '
                f'stroke="{theme["border"]}" stroke-width="0.5"/>'
            )
            parts.append(
                f'<text class="p" x="{x + w/2:.1f}" y="{y_ + 16}" text-anchor="middle" '
                f'fill="{ink(colour)}">{esc(name)}</text>'
            )
    parts.append("</svg>")
    return "\n".join(parts)


def main() -> int:
    data = collect()
    if not data["repos"] and not data["followers"]:
        print("error: GitHub returned no profile data; refusing to write empty cards",
              file=sys.stderr)
        return 1

    os.makedirs(OUT, exist_ok=True)
    for suffix, theme in THEMES.items():
        tag = "" if suffix == "light" else "-dark"
        for stem, svg in (
            ("stats", stats_card(data, theme)),
            ("languages", languages_card(data["langs"], theme)),
            ("tech", tech_card(theme)),
        ):
            path = os.path.join(OUT, f"{stem}{tag}.svg")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(svg)
            print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
