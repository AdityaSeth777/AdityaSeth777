"""Shared 'light table & loupe' glass theme used by every generated SVG tile.

Real CSS backdrop-filter is unreliable inside an SVG loaded via <img> (the
technique every tile here uses to get real HTML/CSS into a GitHub README).
So instead of live blur we bake the blur into the SVG itself with an
<feGaussianBlur> filter applied to a background layer, then lay a
translucent "glass" tile on top of it. That renders identically in every
browser because it's just an SVG filter, not a live compositing effect.
"""

THEMES = {
    "dark": {
        "bg": "#0E1116",
        "blobs": ["#E8A04A", "#2F6F73", "#3B3F6B"],
        "glass_fill": "rgba(255,244,230,0.06)",
        "glass_border": "rgba(255,236,210,0.14)",
        "highlight": "rgba(255,255,255,0.18)",
        "shadow": "rgba(0,0,0,0.45)",
        "text": "#EDE6DA",
        "muted": "#9A958C",
        "accent": "#E8A04A",
        "accent2": "#6FB7C9",
        "safelight": "#D7263D",
    },
    "light": {
        "bg": "#F4EDE3",
        "blobs": ["#F2A65A", "#E76F51", "#8AB6C1"],
        "glass_fill": "rgba(255,255,255,0.45)",
        "glass_border": "rgba(255,255,255,0.7)",
        "highlight": "rgba(255,255,255,0.6)",
        "shadow": "rgba(120,72,30,0.18)",
        "text": "#1E1A16",
        "muted": "#7A7168",
        "accent": "#E76F51",
        "accent2": "#3E8C97",
        "safelight": "#D7263D",
    },
}

FONT_STACK = (
    '-apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif'
)
MONO_STACK = '"SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace'


def background_defs(theme_name, width, height, seed=0):
    """SVG <defs> with baked-in blur blobs + film grain, reused as the page bg."""
    t = THEMES[theme_name]
    blobs = t["blobs"]
    positions = [
        (width * 0.15, height * 0.2),
        (width * 0.75, height * 0.3),
        (width * 0.45, height * 0.8),
    ]
    circles = "".join(
        f'<circle cx="{x}" cy="{y}" r="{width*0.28}" fill="{color}" opacity="0.32"/>'
        for (x, y), color in zip(positions, blobs)
    )
    return f"""
  <defs>
    <filter id="bake-blur-{theme_name}" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="46"/>
    </filter>
    <filter id="grain-{theme_name}">
      <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves="2" seed="{seed}" result="noise"/>
      <feColorMatrix in="noise" type="saturate" values="0"/>
      <feComponentTransfer><feFuncA type="linear" slope="0.06"/></feComponentTransfer>
      <feComposite operator="over" in2="SourceGraphic"/>
    </filter>
    <clipPath id="page-clip-{theme_name}">
      <rect x="0" y="0" width="{width}" height="{height}" rx="20"/>
    </clipPath>
  </defs>
  <g clip-path="url(#page-clip-{theme_name})">
    <rect x="0" y="0" width="{width}" height="{height}" fill="{t['bg']}"/>
    <g filter="url(#bake-blur-{theme_name})">{circles}</g>
    <rect x="0" y="0" width="{width}" height="{height}" filter="url(#grain-{theme_name})" opacity="0.5"/>
  </g>
"""


def tile_css(theme_name):
    t = THEMES[theme_name]
    return f"""
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    .tile {{
      background: {t['glass_fill']};
      border: 1px solid {t['glass_border']};
      border-radius: 16px;
      box-shadow: 0 12px 32px {t['shadow']}, inset 0 1px 0 {t['highlight']};
      padding: 14px 18px;
      display: flex;
      flex-direction: column;
      justify-content: center;
      overflow: hidden;
      color: {t['text']};
      font-family: {FONT_STACK};
    }}
    .label {{
      font-family: {MONO_STACK};
      font-size: 11px;
      color: {t['muted']};
    }}
    .value {{ font-size: 22px; font-weight: 600; margin-top: 4px; }}
    .value.accent {{ color: {t['accent']}; }}
    .value.accent2 {{ color: {t['accent2']}; }}
    .pill {{
      font-family: {MONO_STACK};
      font-size: 11px;
      color: {t['accent2']};
      background: color-mix(in srgb, {t['accent2']} 16%, transparent);
      border: 1px solid color-mix(in srgb, {t['accent2']} 40%, transparent);
      border-radius: 999px;
      padding: 3px 10px;
    }}
    .safelight {{
      width: 8px; height: 8px; border-radius: 50%;
      background: {t['safelight']};
      box-shadow: 0 0 8px {t['safelight']};
      display: inline-block;
    }}
"""
