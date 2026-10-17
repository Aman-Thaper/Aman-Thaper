"""Shared spider drawing used by every SVG in this profile.

The spider is drawn top-down, facing +x, centred on the origin.
Its legs scuttle in two alternating sets so it looks like it's walking.
"""

BODY = "#0d1117"
RED = "#ff3b3f"
BLUE = "#3b82f6"

# (attach, knee, foot) for the upper side; the lower side is mirrored.
_LEGS = [
    ((5, -3), (14, -12), (25, -14)),
    ((3, -4), (8, -15), (14, -24)),
    ((0, -4), (-4, -15), (-9, -23)),
    ((-3, -3), (-12, -11), (-21, -17)),
]


def _leg(a, k, f, flip):
    s = -1 if flip else 1
    return (f'<path d="M{a[0]},{a[1]*s} Q{k[0]},{k[1]*s - 2*s} {f[0]},{f[1]*s}" '
            f'fill="none" stroke="{RED}" stroke-width="2" stroke-linecap="round"/>')


def spider(scuttle=0.32, scale=1.0, still=False):
    """Return an SVG <g> for one spider. `scuttle` is the leg cycle in seconds."""
    set_a, set_b = [], []
    for i, (a, k, f) in enumerate(_LEGS):
        (set_a if i % 2 == 0 else set_b).append(_leg(a, k, f, False))
        (set_b if i % 2 == 0 else set_a).append(_leg(a, k, f, True))

    def animated(paths, phase):
        if still:
            return f'<g>{"".join(paths)}</g>'
        vals = "0;9;0;-9;0" if phase == 0 else "0;-9;0;9;0"
        return (f'<g>{"".join(paths)}<animateTransform attributeName="transform" type="rotate" '
                f'values="{vals}" dur="{scuttle}s" repeatCount="indefinite"/></g>')

    body = (
        f'<ellipse cx="-10" cy="0" rx="11" ry="8.5" fill="{BODY}" stroke="{RED}" stroke-width="1.6"/>'
        f'<path d="M-15,0 L-10,-3.5 L-5,0 L-10,3.5 Z" fill="{RED}"/>'
        f'<circle cx="-16" cy="0" r="1.4" fill="{BLUE}"/>'
        f'<circle cx="-4" cy="0" r="1.4" fill="{BLUE}"/>'
        f'<ellipse cx="3.5" cy="0" rx="7" ry="6" fill="{BODY}" stroke="{RED}" stroke-width="1.6"/>'
        f'<circle cx="8" cy="-2.2" r="1.5" fill="#fff"/>'
        f'<circle cx="8" cy="2.2" r="1.5" fill="#fff"/>'
        f'<path d="M10,-1.5 l3,-1 M10,1.5 l3,1" stroke="{RED}" stroke-width="1.4" stroke-linecap="round"/>'
    )
    return (f'<g transform="scale({scale})">{animated(set_a, 0)}{animated(set_b, 1)}{body}</g>')
