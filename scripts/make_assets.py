"""Generates the animated header and the crawling-spider dividers.

Run once (or whenever you tweak something):  python scripts/make_assets.py
"""
import math
import random
from pathlib import Path

from spider import spider, RED

OUT = Path(__file__).resolve().parent.parent / "assets"
OUT.mkdir(exist_ok=True)
FONT = "'Segoe UI', 'Helvetica Neue', Helvetica, Arial, sans-serif"
MONO = "'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace"


def web(cx, cy, a0, a1, spokes, rings, step, opacity=0.22):
    """A corner web: straight spokes plus sagging rings between them."""
    angs = [math.radians(a0 + (a1 - a0) * i / (spokes - 1)) for i in range(spokes)]
    out = []
    reach = rings * step + 20
    for a in angs:
        out.append(f'<line x1="{cx}" y1="{cy}" x2="{cx + reach*math.cos(a):.1f}" '
                   f'y2="{cy + reach*math.sin(a):.1f}"/>')
    for r in range(1, rings + 1):
        rad = r * step
        d = f"M{cx + rad*math.cos(angs[0]):.1f},{cy + rad*math.sin(angs[0]):.1f}"
        for a, b in zip(angs, angs[1:]):
            mid = (a + b) / 2
            sag = rad * 0.86
            d += (f" Q{cx + sag*math.cos(mid):.1f},{cy + sag*math.sin(mid):.1f} "
                  f"{cx + rad*math.cos(b):.1f},{cy + rad*math.sin(b):.1f}")
        out.append(f'<path d="{d}" fill="none"/>')
    return (f'<g stroke="#e6edf3" stroke-opacity="{opacity}" stroke-width="1.1">'
            + "".join(out) + "</g>")


def skyline(w, h, rng):
    parts, x = [], -10
    while x < w:
        bw = rng.randint(38, 92)
        bh = rng.randint(50, 132)
        top = h - bh
        parts.append(f'<rect x="{x}" y="{top}" width="{bw}" height="{bh}" fill="#060810"/>')
        if rng.random() < 0.25:  # antenna
            parts.append(f'<rect x="{x + bw//2 - 1}" y="{top - 18}" width="2" height="18" fill="#060810"/>')
            parts.append(f'<circle cx="{x + bw//2}" cy="{top - 20}" r="2.4" fill="{RED}">'
                         f'<animate attributeName="opacity" values="1;0.15;1" dur="{rng.uniform(1.2, 2.4):.1f}s" '
                         f'repeatCount="indefinite"/></circle>')
        for wy in range(top + 10, h - 8, 14):
            for wx in range(x + 7, x + bw - 8, 11):
                if rng.random() < 0.28:
                    win = f'<rect x="{wx}" y="{wy}" width="5" height="7" fill="#ffd27a" opacity="0.75"'
                    if rng.random() < 0.18:
                        dur = rng.uniform(3, 9)
                        win += (f'><animate attributeName="opacity" values="0.75;0.05;0.75" '
                                f'dur="{dur:.1f}s" begin="{rng.uniform(0, 5):.1f}s" repeatCount="indefinite"/></rect>')
                    else:
                        win += "/>"
                    parts.append(win)
        x += bw + rng.randint(0, 6)
    return "".join(parts)


def stars(w, h, rng, n=60):
    out = []
    for _ in range(n):
        x, y, r = rng.uniform(0, w), rng.uniform(0, h * 0.55), rng.uniform(0.5, 1.5)
        s = f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.1f}" fill="#fff" opacity="0.7"'
        if rng.random() < 0.4:
            s += (f'><animate attributeName="opacity" values="0.8;0.1;0.8" dur="{rng.uniform(2, 5):.1f}s" '
                  f'begin="{rng.uniform(0, 4):.1f}s" repeatCount="indefinite"/></circle>')
        else:
            s += "/>"
        out.append(s)
    return "".join(out)


def header():
    W, H = 1200, 360
    rng = random.Random(7)
    sub = "your friendly neighborhood developer"
    sub_w = 470
    hang = (
        # thread + spider, bobbing up and down and swinging a little
        f'<g><animateTransform attributeName="transform" type="rotate" values="-5 1015 0;5 1015 0;-5 1015 0" '
        f'dur="5s" repeatCount="indefinite"/>'
        f'<g><animateTransform attributeName="transform" type="translate" values="0 0;0 60;0 25;0 80;0 0" '
        f'dur="9s" repeatCount="indefinite" calcMode="spline" keySplines=".4 0 .6 1;.4 0 .6 1;.4 0 .6 1;.4 0 .6 1"/>'
        f'<line x1="1015" y1="-200" x2="1015" y2="88" stroke="#e6edf3" stroke-opacity="0.7" stroke-width="1.2"/>'
        f'<g transform="translate(1015 100) rotate(90)">{spider(scuttle=1.6, scale=1.25)}</g>'
        f'</g></g>'
    )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Aman Thaper — your friendly neighborhood developer">
<defs>
  <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#04060d"/><stop offset=".55" stop-color="#0c1430"/><stop offset="1" stop-color="#2a0d1c"/>
  </linearGradient>
  <linearGradient id="title" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#ff3b3f"/><stop offset=".5" stop-color="#ffffff"/><stop offset="1" stop-color="#3b82f6"/>
    <animateTransform attributeName="gradientTransform" type="translate" values="-0.4 0;0.4 0;-0.4 0" dur="8s" repeatCount="indefinite"/>
  </linearGradient>
  <radialGradient id="moonGlow"><stop offset="0" stop-color="#fff6d5" stop-opacity=".55"/><stop offset="1" stop-color="#fff6d5" stop-opacity="0"/></radialGradient>
  <filter id="glow" x="-20%" y="-50%" width="140%" height="200%"><feGaussianBlur stdDeviation="6" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
  <clipPath id="typing"><rect x="{600 - sub_w/2}" y="160" width="0" height="40">
    <animate attributeName="width" values="0;{sub_w};{sub_w};0" keyTimes="0;.35;.85;1" dur="7s" repeatCount="indefinite"/>
  </rect></clipPath>
  <clipPath id="frame"><rect width="{W}" height="{H}" rx="18"/></clipPath>
</defs>
<g clip-path="url(#frame)">
  <rect width="{W}" height="{H}" fill="url(#sky)"/>
  {stars(W, H, rng)}
  <circle cx="1105" cy="70" r="110" fill="url(#moonGlow)"/>
  <circle cx="1105" cy="70" r="38" fill="#f6efd9"/>
  <circle cx="1093" cy="60" r="7" fill="#e3d9bd"/><circle cx="1117" cy="82" r="5" fill="#e3d9bd"/>
  {web(0, 0, 0, 90, 9, 7, 42)}
  {web(W, H, 180, 270, 7, 4, 38, 0.12)}
  {skyline(W, H, rng)}
  <text x="600" y="132" text-anchor="middle" font-family="{FONT}" font-size="78" font-weight="900" letter-spacing="6" fill="url(#title)" filter="url(#glow)">AMAN THAPER</text>
  <g clip-path="url(#typing)">
    <text x="600" y="186" text-anchor="middle" font-family="{MONO}" font-size="22" fill="#c9d1d9">{sub}</text>
  </g>
  <text x="600" y="218" text-anchor="middle" font-family="{MONO}" font-size="14" fill="#8b949e" letter-spacing="3">// web-slinging code since forever</text>
  {hang}
</g>
</svg>'''


def crawler(reverse=False, dur=16):
    """A thin divider strip with a spider wandering along a strand of silk."""
    W, H = 1200, 70
    path = ("M60,35 C260,5 420,62 600,35 S940,8 1140,35 "
            "C1185,45 1170,62 1110,58 C900,62 760,48 600,52 S260,64 90,56 C40,52 30,40 60,35 Z")
    if reverse:
        path = ("M1140,35 C940,5 780,62 600,35 S260,8 60,35 "
                "C15,45 30,62 90,58 C300,62 440,48 600,52 S940,64 1110,56 C1160,52 1170,40 1140,35 Z")
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="a spider wandering along a strand of web">
<defs><linearGradient id="strand" x1="0" x2="1">
  <stop offset="0" stop-color="#ff3b3f" stop-opacity="0"/><stop offset=".2" stop-color="#ff3b3f" stop-opacity=".55"/>
  <stop offset=".8" stop-color="#3b82f6" stop-opacity=".55"/><stop offset="1" stop-color="#3b82f6" stop-opacity="0"/>
</linearGradient></defs>
<path d="{path}" fill="none" stroke="url(#strand)" stroke-width="1.2" stroke-dasharray="2 6"/>
<g>
  <animateMotion dur="{dur}s" repeatCount="indefinite" rotate="auto" path="{path}"
    keyPoints="0;0.18;0.22;0.5;0.55;0.8;1" keyTimes="0;0.2;0.3;0.55;0.65;0.88;1" calcMode="linear"/>
  {spider(scuttle=0.28)}
</g>
</svg>'''


if __name__ == "__main__":
    (OUT / "header.svg").write_text(header())
    (OUT / "crawler.svg").write_text(crawler())
    (OUT / "crawler-reverse.svg").write_text(crawler(reverse=True, dur=19))
    print("wrote", ", ".join(p.name for p in sorted(OUT.glob("*.svg"))))
