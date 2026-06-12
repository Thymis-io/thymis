"""Generates the module icon set (light + dark variants) from a single source.

Each icon is a 100x100 line-art glyph. Two placeholders keep the variants in sync:
  {S} -> theme stroke color  (light #1a1a1a / dark #e5e5e5)
  {A} -> theme accent color  (the webpage blue: light #2563eb / dark #4f8cff)

Run from this directory:  python _generate_module_icons.py
"""

import pathlib

STROKE_LIGHT = "#1a1a1a"
STROKE_DARK = "#e5e5e5"
ACCENT_LIGHT = "#2563eb"  # --ds-accent (light theme)
ACCENT_DARK = "#4f8cff"  # --ds-accent (dark theme)

# Per-icon fit as (scale, center_x, center_y): each icon's content is scaled so its
# longest dimension fills the same target box (80 of 100) and is centered. The base
# stroke width (7) is divided by this scale so the rendered stroke stays uniform
# across icons. Auto-measured from each icon's getBBox(); re-measure if a glyph's
# geometry changes. NOTE: a plain transform is used (NOT vector-effect:
# non-scaling-stroke, which breaks when the SVG is rendered via <img>).
BASE_STROKE = 7.0
FITS: dict[str, tuple[float, float, float]] = {
    "CoreDevice": (1.4286, 50, 50),
    "Containers": (1.5385, 50, 50),
    "Display": (1.3333, 50, 52),
    "Networking": (1.4134, 50, 56.7343),
    "Localization": (1.2500, 50, 50),
    "Security": (1.4286, 50, 54),
    "Files": (1.2500, 55, 50),
    "Bash": (1.1765, 50, 50),
    "Python": (1.0204, 50, 50),
    "CustomCoding": (1.2500, 50, 50),
}

# Each value is the inner SVG markup using the {S} / {A} placeholders.
ICONS: dict[str, str] = {
    # Device (CoreDevice): a microchip / SBC with a blue core.
    "CoreDevice": """
    <g fill="none" stroke="{S}" stroke-width="{SW}" stroke-linecap="round" stroke-linejoin="round">
      <rect x="32" y="32" width="36" height="36" rx="4" />
      <line x1="40" y1="32" x2="40" y2="22" />
      <line x1="50" y1="32" x2="50" y2="22" />
      <line x1="60" y1="32" x2="60" y2="22" />
      <line x1="40" y1="68" x2="40" y2="78" />
      <line x1="50" y1="68" x2="50" y2="78" />
      <line x1="60" y1="68" x2="60" y2="78" />
      <line x1="32" y1="40" x2="22" y2="40" />
      <line x1="32" y1="50" x2="22" y2="50" />
      <line x1="32" y1="60" x2="22" y2="60" />
      <line x1="68" y1="40" x2="78" y2="40" />
      <line x1="68" y1="50" x2="78" y2="50" />
      <line x1="68" y1="60" x2="78" y2="60" />
    </g>
    <rect x="43" y="43" width="14" height="14" rx="2" fill="{A}" />
    """,
    # OCI Containers: a 2x2 grid of boxes, one highlighted blue.
    "Containers": """
    <g fill="none" stroke="{S}" stroke-width="{SW}" stroke-linecap="round" stroke-linejoin="round">
      <rect x="24" y="24" width="22" height="22" rx="3" />
      <rect x="24" y="54" width="22" height="22" rx="3" />
      <rect x="54" y="54" width="22" height="22" rx="3" />
    </g>
    <rect x="54" y="24" width="22" height="22" rx="3" fill="{A}" />
    """,
    # Kiosk (Display): a monitor on a stand with a blue content bar.
    "Display": """
    <g fill="none" stroke="{S}" stroke-width="{SW}" stroke-linecap="round" stroke-linejoin="round">
      <rect x="20" y="26" width="60" height="40" rx="5" />
      <line x1="50" y1="66" x2="50" y2="76" />
      <line x1="36" y1="78" x2="64" y2="78" />
    </g>
    <line x1="31" y1="38" x2="55" y2="38" stroke="{A}" stroke-width="{SW}" stroke-linecap="round" />
    """,
    # Networking: a WiFi signal with a blue source dot.
    "Networking": """
    <g fill="none" stroke="{S}" stroke-width="{SW}" stroke-linecap="round" stroke-linejoin="round">
      <path d="M21.7 45.7 A40 40 0 0 1 78.3 45.7" />
      <path d="M30.2 54.2 A28 28 0 0 1 69.8 54.2" />
      <path d="M38.7 62.7 A16 16 0 0 1 61.3 62.7" />
    </g>
    <circle cx="50" cy="74" r="5.5" fill="{A}" />
    """,
    # Localization & Time: a clock face with hands.
    "Localization": """
    <g fill="none" stroke="{S}" stroke-width="{SW}" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="50" cy="50" r="32" />
      <polyline points="50,50 50,30" />
      <polyline points="50,50 65,58" />
    </g>
    """,
    # Security & Access: a padlock with a blue keyhole.
    "Security": """
    <g fill="none" stroke="{S}" stroke-width="{SW}" stroke-linecap="round" stroke-linejoin="round">
      <path d="M36 48 V40 a14 14 0 0 1 28 0 V48" />
      <rect x="26" y="48" width="48" height="34" rx="7" />
    </g>
    <circle cx="50" cy="62" r="5" fill="{A}" />
    <line x1="50" y1="65" x2="50" y2="73" stroke="{S}" stroke-width="{SW}" stroke-linecap="round" />
    """,
    # Files: a document with a folded corner and text lines.
    "Files": """
    <g fill="none" stroke="{S}" stroke-width="{SW}" stroke-linecap="round" stroke-linejoin="round">
      <path d="M32 18 H60 L78 36 V82 H32 Z" />
      <polyline points="60,18 60,36 78,36" />
      <line x1="42" y1="54" x2="66" y2="54" />
      <line x1="42" y1="66" x2="66" y2="66" />
    </g>
    """,
    # Bash: a terminal window with a prompt chevron and a blue cursor.
    "Bash": """
    <g fill="none" stroke="{S}" stroke-width="{SW}" stroke-linecap="round" stroke-linejoin="round">
      <rect x="16" y="24" width="68" height="52" rx="8" />
      <polyline points="30,44 40,52 30,60" />
    </g>
    <line x1="48" y1="61" x2="62" y2="61" stroke="{A}" stroke-width="{SW}" stroke-linecap="round" />
    """,
    # Python: the Python logo outline (svgrepo), themed light/dark with blue eyes.
    "Python": """
    <g transform="translate(8 8) scale(5.6)" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M4.5 4V1.5C4.5 0.947715 4.94772 0.5 5.5 0.5H9.5C10.0523 0.5 10.5 0.947715 10.5 1.5V6.5C10.5 7.05228 10.0523 7.5 9.5 7.5H5.5C4.94772 7.5 4.5 7.94772 4.5 8.5V13.5C4.5 14.0523 4.94772 14.5 5.5 14.5H9.5C10.0523 14.5 10.5 14.0523 10.5 13.5V11M8 4.5H1.5C0.947715 4.5 0.5 4.94772 0.5 5.5V10.5C0.5 11.0523 0.947715 11.5 1.5 11.5H4.5M7 10.5H13.5C14.0523 10.5 14.5 10.0523 14.5 9.5V4.5C14.5 3.94772 14.0523 3.5 13.5 3.5H10.5"
            stroke="{S}" stroke-width="1.25" />
      <path d="M6 2.5H7M8 12.5H9" stroke="{A}" stroke-width="1.1" />
    </g>
    """,
    # Custom Nix (CustomCoding): code angle-brackets with a blue slash.
    "CustomCoding": """
    <g fill="none" stroke="{S}" stroke-width="{SW}" stroke-linecap="round" stroke-linejoin="round">
      <polyline points="34,34 18,50 34,66" />
      <polyline points="66,34 82,50 66,66" />
    </g>
    <line x1="58" y1="30" x2="42" y2="70" stroke="{A}" stroke-width="{SW}" stroke-linecap="round" />
    """,
}

SVG_TEMPLATE = (
    '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'
    '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" '
    'viewBox="0 0 100 100" fill="none">\n'
    '<g transform="{fit}">{inner}\n</g>\n</svg>\n'
)


def main():
    here = pathlib.Path(__file__).parent
    for name, inner in ICONS.items():
        scale, cx, cy = FITS.get(name, (1.0, 50, 50))
        # scale the geometry around its center to fill the target box
        fit = f"translate(50 50) scale({scale:g}) translate({-cx:g} {-cy:g})"
        # counter-scale the stroke so it renders at the same width for every icon
        sw = f"{BASE_STROKE / scale:.3f}"
        for suffix, stroke, accent in (
            (".svg", STROKE_LIGHT, ACCENT_LIGHT),
            ("_dark.svg", STROKE_DARK, ACCENT_DARK),
        ):
            body = inner.format(S=stroke, A=accent, SW=sw).rstrip()
            content = SVG_TEMPLATE.format(inner=body, fit=fit)
            (here / f"{name}{suffix}").write_text(content, encoding="utf-8")
            print(f"wrote {name}{suffix}")


if __name__ == "__main__":
    main()
