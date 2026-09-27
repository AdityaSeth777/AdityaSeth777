import json
import os
from xml.sax.saxutils import escape

from glass import THEMES, background_defs, tile_css, MONO_STACK

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "guestbook.json")
WIDTH, HEIGHT = 460, 240
MAX_STAMPS = 12


def load_entries():
    with open(DATA_PATH) as f:
        return json.load(f)


def build_svg(theme_name, entries):
    t = THEMES[theme_name]

    if not entries:
        body = f"""
        <div class="tile placeholder">
          <div class="label">passport</div>
          <div class="value">No stamps yet</div>
          <div class="sub">Open an issue labeled "guestbook" to stamp it.</div>
        </div>
        """
    else:
        recent = entries[-MAX_STAMPS:]
        stamps = ""
        for i, entry in enumerate(recent):
            angle = (i * 37) % 25 - 12
            x = 20 + (i % 4) * 100
            y = 40 + (i // 4) * 60
            stamps += f"""
            <div class="stamp" style="left:{x}px; top:{y}px; transform: rotate({angle}deg);">
              <div class="ring"></div>
              <span class="stamp-user">{escape(entry.get('user',''))}</span>
              <span class="stamp-date">{escape(entry.get('date',''))}</span>
            </div>
            """
        body = f"""
        <div class="tile passport-tile">
          <div class="label">passport &#8212; {len(entries)} stamps total</div>
          <div class="stamps-area">{stamps}</div>
        </div>
        """

    html = f"""
    <div xmlns="http://www.w3.org/1999/xhtml" class="wrap">
      <style>
        {tile_css(theme_name)}
        .wrap {{ width: {WIDTH}px; height: {HEIGHT}px; padding: 18px; }}
        .tile {{ width: 100%; height: 100%; align-items: flex-start; }}
        .stamps-area {{ position: relative; width: 100%; height: 100%; margin-top: 8px; }}
        .stamp {{ position: absolute; text-align: center; }}
        .ring {{
          width: 46px; height: 46px; border-radius: 50%;
          border: 2px solid {t['safelight']};
          opacity: 0.75;
          margin: 0 auto;
        }}
        .stamp-user {{
          display: block; font-family: {MONO_STACK}; font-size: 9px;
          color: {t['safelight']}; margin-top: -32px;
        }}
        .stamp-date {{
          display: block; font-family: {MONO_STACK}; font-size: 8px;
          color: {t['muted']}; margin-top: 30px;
        }}
        .placeholder .value {{ font-size: 18px; font-weight: 600; margin-top: 6px; }}
        .placeholder .sub {{ font-size: 12px; color: {t['muted']}; margin-top: 6px; }}
      </style>
      {body}
    </div>
    """
    bg = background_defs(theme_name, WIDTH, HEIGHT, seed=7)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">
  {bg}
  <foreignObject x="0" y="0" width="{WIDTH}" height="{HEIGHT}">
    {html}
  </foreignObject>
</svg>
"""


def main():
    entries = load_entries()
    for theme_name in ("dark", "light"):
        svg = build_svg(theme_name, entries)
        out = f"guestbook-{theme_name}.svg"
        with open(out, "w") as f:
            f.write(svg)
        print(f"Wrote {out} ({len(entries)} entries)")


if __name__ == "__main__":
    main()
