import os
from xml.sax.saxutils import escape

from glass import THEMES, background_defs, MONO_STACK

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "now.md")
WIDTH, HEIGHT = 460, 240


def load_fields():
    fields = {}
    with open(DATA_PATH) as f:
        for line in f:
            line = line.strip()
            if not line or ":" not in line:
                continue
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip()
    return fields


def build_svg(theme_name, fields):
    t = THEMES[theme_name]
    lines = [
        ("$ whoami", "aditya-seth"),
        ("$ cat focus.txt", fields.get("focus", "—")),
        ("$ cat reading.txt", fields.get("reading", "—")),
        ("$ cat last_trip.txt", fields.get("last_trip", "—")),
    ]

    rows = ""
    delay = 0
    for prompt, value in lines:
        rows += f"""
        <div class="row" style="animation-delay: {delay}s;">
          <span class="prompt">{escape(prompt)}</span>
          <span class="out">{escape(value)}</span>
        </div>
        """
        delay += 1.1

    html = f"""
    <div xmlns="http://www.w3.org/1999/xhtml" class="wrap">
      <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        .wrap {{
          width: {WIDTH}px; height: {HEIGHT}px;
          background: {THEMES[theme_name]['glass_fill']};
          border: 1px solid {t['glass_border']};
          border-radius: 16px;
          box-shadow: 0 12px 32px {t['shadow']}, inset 0 1px 0 {t['highlight']};
          padding: 16px 20px;
          font-family: {MONO_STACK};
          font-size: 12.5px;
          color: {t['text']};
          overflow: hidden;
        }}
        .row {{
          opacity: 0;
          animation: reveal 0.01s linear forwards;
          margin-bottom: 10px;
          line-height: 1.45;
        }}
        @keyframes reveal {{ to {{ opacity: 1; }} }}
        .prompt {{ color: {t['accent2']}; display: block; }}
        .out {{ color: {t['text']}; display: block; margin-top: 2px; }}
        .cursor {{
          display: inline-block; width: 7px; height: 14px;
          background: {t['accent']};
          animation: blink 1s steps(1) infinite;
          margin-left: 4px; vertical-align: text-bottom;
        }}
        @keyframes blink {{ 50% {{ opacity: 0; }} }}
      </style>
      <div class="term">
        {rows}
        <span class="cursor"></span>
      </div>
    </div>
    """

    bg = background_defs(theme_name, WIDTH, HEIGHT, seed=3)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">
  {bg}
  <foreignObject x="0" y="0" width="{WIDTH}" height="{HEIGHT}">
    {html}
  </foreignObject>
</svg>
"""


def main():
    fields = load_fields()
    for theme_name in ("dark", "light"):
        svg = build_svg(theme_name, fields)
        out = f"now-{theme_name}.svg"
        with open(out, "w") as f:
            f.write(svg)
        print(f"Wrote {out}")


if __name__ == "__main__":
    main()
