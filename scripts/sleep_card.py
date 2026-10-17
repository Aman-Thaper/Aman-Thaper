"""Night Patrol: logs a night of sleep and redraws assets/sleep.svg.

  python scripts/sleep_card.py --hours 6.5            # log last night
  python scripts/sleep_card.py --hours 7 --date 2026-10-17
  python scripts/sleep_card.py                        # just redraw

Keeps the last 7 nights in data/sleep.json. Each night is a strand of silk
with a spider hanging off the end: the longer the strand, the more you slept.
"""
import argparse
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from spider import spider, RED, BLUE

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "sleep.json"
CARD = ROOT / "assets" / "sleep.svg"
BADGE = ROOT / "data" / "sleep-badge.json"
IST = timezone(timedelta(hours=5, minutes=30))
FONT = "'Segoe UI', 'Helvetica Neue', Helvetica, Arial, sans-serif"
MONO = "'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace"
GOAL = 8.0


def load():
    if DATA.exists():
        return json.loads(DATA.read_text()).get("nights", [])
    return []


def save(nights):
    DATA.parent.mkdir(exist_ok=True)
    DATA.write_text(json.dumps({"nights": nights}, indent=2) + "\n")


def log(nights, hours, day):
    if not 0 <= hours <= 16:
        raise SystemExit(f"hours must be between 0 and 16, got {hours}")
    nights = [n for n in nights if n["date"] != day]
    nights.append({"date": day, "hours": round(hours, 2)})
    nights.sort(key=lambda n: n["date"])
    return nights[-7:]


def verdict(h):
    if h < 4.5:
        return "running on web fluid and caffeine", RED
    if h < 6:
        return "spider-sense: fuzzy. do not deploy.", RED
    if h < 7.5:
        return "mostly functional. bugs beware.", "#f2cc60"
    return "fully recharged. city is safe.", BLUE


def fmt(h):
    hh, mm = int(h), round((h - int(h)) * 60)
    if mm == 60:
        hh, mm = hh + 1, 0
    return f"{hh}h {mm:02d}m"


def card(nights):
    W, H = 900, 300
    head = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Night Patrol sleep tracker">
<defs>
  <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#0b1020"/><stop offset="1" stop-color="#1a0b16"/></linearGradient>
  <clipPath id="c"><rect width="{W}" height="{H}" rx="16"/></clipPath>
</defs>
<g clip-path="url(#c)">
<rect width="{W}" height="{H}" fill="url(#bg)"/>
<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="16" fill="none" stroke="#30363d"/>
<text x="32" y="46" font-family="{MONO}" font-size="13" letter-spacing="4" fill="#8b949e">NIGHT PATROL</text>
<circle cx="196" cy="41" r="4" fill="{RED}"><animate attributeName="opacity" values="1;.2;1" dur="1.6s" repeatCount="indefinite"/></circle>
<text x="207" y="46" font-family="{MONO}" font-size="11" fill="{RED}">LIVE</text>
'''
    if not nights:
        body = f'''<text x="32" y="130" font-family="{FONT}" font-size="40" font-weight="800" fill="#e6edf3">no nights logged yet</text>
<text x="32" y="170" font-family="{MONO}" font-size="15" fill="#8b949e">the web is waiting for the first report from my phone.</text>
<line x1="640" y1="0" x2="640" y2="150" stroke="#e6edf3" stroke-opacity=".6"/>
<g transform="translate(640 162) rotate(90)">{spider(scuttle=1.8, scale=1.3)}</g>'''
        return head + body + "</g></svg>"

    last = nights[-1]["hours"]
    avg = sum(n["hours"] for n in nights) / len(nights)
    debt = sum(max(0.0, GOAL - n["hours"]) for n in nights)
    text, color = verdict(last)

    left = f'''<text x="32" y="80" font-family="{MONO}" font-size="12" letter-spacing="3" fill="#8b949e">LAST NIGHT</text>
<text x="30" y="140" font-family="{FONT}" font-size="58" font-weight="900" fill="#e6edf3">{fmt(last)}</text>
<text x="32" y="172" font-family="{MONO}" font-size="14" fill="{color}">&gt; {text}</text>
<text x="32" y="222" font-family="{MONO}" font-size="12" letter-spacing="2" fill="#8b949e">7-NIGHT AVG</text>
<text x="32" y="250" font-family="{FONT}" font-size="24" font-weight="800" fill="#e6edf3">{fmt(avg)}</text>
<text x="190" y="222" font-family="{MONO}" font-size="12" letter-spacing="2" fill="#8b949e">SLEEP DEBT</text>
<text x="190" y="250" font-family="{FONT}" font-size="24" font-weight="800" fill="{RED if debt > 5 else '#e6edf3'}">{fmt(debt)}</text>
<line x1="380" y1="30" x2="380" y2="{H-30}" stroke="#30363d"/>'''

    # the silk strand everyone hangs from
    x0, x1, top, max_len = 420, 870, 34, 170
    strands = [f'<path d="M{x0-10},{top} Q{(x0+x1)/2},{top+10} {x1+10},{top}" fill="none" stroke="#e6edf3" stroke-opacity=".35"/>']
    gap = (x1 - x0) / 7
    goal_y = top + GOAL / 10 * max_len
    strands.append(f'<line x1="{x0-10}" y1="{goal_y:.0f}" x2="{x1+10}" y2="{goal_y:.0f}" stroke="{BLUE}" stroke-opacity=".35" stroke-dasharray="3 5"/>'
                   f'<text x="{x1+6}" y="{goal_y-6:.0f}" text-anchor="end" font-family="{MONO}" font-size="10" fill="{BLUE}" fill-opacity=".8">goal {GOAL:g}h</text>')
    pad = [None] * (7 - len(nights)) + nights
    for i, n in enumerate(pad):
        x = x0 + gap * (i + 0.5)
        sag = 10 * (1 - ((x - (x0 + x1) / 2) / ((x1 - x0) / 2)) ** 2)
        anchor = top + sag * 0.5
        if n is None:
            strands.append(f'<circle cx="{x:.0f}" cy="{anchor:.0f}" r="2" fill="#30363d"/>')
            continue
        h = n["hours"]
        length = max(18, min(h, 10) / 10 * max_len)
        _, col = verdict(h)
        day = datetime.strptime(n["date"], "%Y-%m-%d").strftime("%a")
        is_last = i == len(pad) - 1
        bob = 3 if not is_last else 6
        strands.append(
            f'<g><animateTransform attributeName="transform" type="translate" values="0 0;0 {bob};0 0" '
            f'dur="{2.6 + i*0.3:.1f}s" repeatCount="indefinite"/>'
            f'<line x1="{x:.0f}" y1="{anchor:.0f}" x2="{x:.0f}" y2="{anchor+length:.0f}" stroke="{col}" stroke-width="{2 if is_last else 1.3}"/>'
            f'<g transform="translate({x:.0f} {anchor+length+12:.0f}) rotate(90)">{spider(scuttle=1.4 + i*0.15, scale=0.62)}</g>'
            f'<text x="{x+9:.0f}" y="{anchor+length-4:.0f}" font-family="{MONO}" font-size="11" fill="#e6edf3">{h:.1f}</text></g>')
        strands.append(f'<text x="{x:.0f}" y="{H-24}" text-anchor="middle" font-family="{MONO}" font-size="12" '
                       f'fill="{"#e6edf3" if is_last else "#8b949e"}">{day}</text>')
    stamp = datetime.now(IST).strftime("%d %b, %H:%M IST")
    foot = f'<text x="{W-32}" y="46" text-anchor="end" font-family="{MONO}" font-size="11" fill="#6e7681">updated {stamp}</text>'
    return head + left + "".join(strands) + foot + "</g></svg>"


def badge(nights):
    if not nights:
        return {"schemaVersion": 1, "label": "last night", "message": "no data", "color": "lightgrey"}
    h = nights[-1]["hours"]
    color = "e62429" if h < 6 else ("f2cc60" if h < 7.5 else "1b3a8c")
    return {"schemaVersion": 1, "label": "last night", "message": fmt(h), "color": color}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--hours", type=float)
    p.add_argument("--date", help="YYYY-MM-DD; defaults to today in IST")
    a = p.parse_args()
    nights = load()
    if a.hours is not None:
        day = a.date or datetime.now(IST).date().isoformat()
        date.fromisoformat(day)  # validates the format
        nights = log(nights, a.hours, day)
        save(nights)
    CARD.parent.mkdir(exist_ok=True)
    CARD.write_text(card(nights))
    BADGE.write_text(json.dumps(badge(nights)) + "\n")
    print(f"{len(nights)} night(s) on file -> {CARD.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
