import json
import os
from xml.sax.saxutils import escape

from glass import THEMES, background_defs, tile_css, MONO_STACK

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "votes.json")
WIDTH, HEIGHT = 460, 240


def load_votes():
    with open(DATA_PATH) as f:
        return json.load(f)


def build_svg(theme_name, votes):
    t = THEMES[theme_name]

    if not votes:
        body = f"""
        <div class="tile placeholder">
          <div class="label">next destination &#8212; vote board</div>
          <div class="value">No votes yet</div>
          <div class="sub">Open an issue titled "vote: &lt;city&gt;" labeled "vote" to cast one.</div>
        </div>
        """
    else:
        ranked = sorted(votes.items(), key=lambda kv: kv[1], reverse=True)[:5]
        total = sum(v for _, v in ranked) or 1
        rows = ""
        for city, count in ranked:
            pct = round((count / total) * 100, 1)
            flaps = "".join(
                f'<span class="flap">{escape(ch)}</span>' for ch in city.upper()[:14]
            )
            rows += f"""
            <div class="flap-row">
              <div class="flap-board">{flaps}</div>
              <div class="flap-track"><div class="flap-fill" style="width:{pct}%;"></div></div>
              <span class="flap-count">{count}</span>
            </div>
            """
        body = f"""
        <div class="tile poll-tile">
          <div class="label">next destination &#8212; vote board</div>
          <div style="margin-top:10px;">{rows}</div>
        </div>
        """

    html = f"""
    <div xmlns="http://www.w3.org/1999/xhtml" class="wrap">
      <style>
        {tile_css(theme_name)}
        .wrap {{ width: {WIDTH}px; height: {HEIGHT}px; padding: 18px; }}
        .tile {{ width: 100%; height: 100%; align-items: flex-start; }}
        .flap-row {{ display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }}
        .flap-board {{ display: flex; gap: 2px; }}
        .flap {{
          font-family: {MONO_STACK}; font-size: 11px; font-weight: 700;
          background: rgba(0,0,0,0.35);
          color: {t['text']};
          border-radius: 3px;
          padding: 3px 4px;
          min-width: 8px;
          text-align: center;
        }}
        .flap-track {{ flex: 1; height: 8px; background: rgba(128,128,128,0.15); border-radius: 4px; overflow: hidden; }}
        .flap-fill {{ height: 100%; background: {t['accent']}; }}
        .flap-count {{ font-family: {MONO_STACK}; font-size: 11px; color: {t['muted']}; width: 20px; text-align: right; }}
        .placeholder .value {{ font-size: 18px; font-weight: 600; margin-top: 6px; }}
        .placeholder .sub {{ font-size: 12px; color: {t['muted']}; margin-top: 6px; max-width: 32ch; }}
      </style>
      {body}
    </div>
    """
    bg = background_defs(theme_name, WIDTH, HEIGHT, seed=8)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">
  {bg}
  <foreignObject x="0" y="0" width="{WIDTH}" height="{HEIGHT}">
    {html}
  </foreignObject>
</svg>
"""


def main():
    votes = load_votes()
    for theme_name in ("dark", "light"):
        svg = build_svg(theme_name, votes)
        out = f"poll-{theme_name}.svg"
        with open(out, "w") as f:
            f.write(svg)
        print(f"Wrote {out} ({len(votes)} options)")


if __name__ == "__main__":
    main()
