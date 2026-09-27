import json
import os
import urllib.request
from xml.sax.saxutils import escape

from glass import THEMES, background_defs, tile_css, MONO_STACK

USERNAME = os.environ.get("GITHUB_USERNAME", "AdityaSeth777")
TOKEN = os.environ.get("GITHUB_TOKEN")
WIDTH, HEIGHT = 460, 240

# RGB-ish channel colors so the bars read like a camera histogram
CHANNEL_COLORS = ["#E76F51", "#6FB7C9", "#F2A65A", "#8AB6C1", "#D7263D", "#9A958C"]


def api(path):
    req = urllib.request.Request(f"https://api.github.com{path}")
    req.add_header("Accept", "application/vnd.github+json")
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())


def fetch_language_counts():
    repos = []
    page = 1
    while True:
        batch = api(f"/users/{USERNAME}/repos?per_page=100&page={page}&type=owner")
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1

    counts = {}
    for r in repos:
        lang = r.get("language")
        if lang:
            counts[lang] = counts.get(lang, 0) + 1
    return sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[:6]


def build_svg(theme_name, languages):
    t = THEMES[theme_name]
    max_count = max((c for _, c in languages), default=1)

    bars = ""
    y = 0
    bar_height = 24
    gap = 10
    for i, (lang, count) in enumerate(languages):
        width_pct = round((count / max_count) * 100, 1)
        color = CHANNEL_COLORS[i % len(CHANNEL_COLORS)]
        bars += f"""
        <div class="bar-row">
          <span class="bar-label">{escape(lang)}</span>
          <div class="bar-track">
            <div class="bar-fill" style="width: {width_pct}%; background: {color};"></div>
          </div>
        </div>
        """

    html = f"""
    <div xmlns="http://www.w3.org/1999/xhtml" class="wrap">
      <style>
        {tile_css(theme_name)}
        .wrap {{ width: {WIDTH}px; height: {HEIGHT}px; padding: 16px 20px; }}
        .tile {{ width: 100%; height: 100%; }}
        .bar-row {{ display: flex; align-items: center; gap: 8px; margin-bottom: 9px; }}
        .bar-label {{
          font-family: {MONO_STACK}; font-size: 11px; color: {t['muted']};
          width: 78px; flex-shrink: 0; text-align: right;
        }}
        .bar-track {{ flex: 1; height: 10px; background: rgba(128,128,128,0.15); border-radius: 4px; overflow: hidden; }}
        .bar-fill {{ height: 100%; border-radius: 4px; }}
      </style>
      <div class="tile">
        <div class="label">language mix &#8212; by repo count</div>
        <div style="margin-top: 12px;">{bars}</div>
      </div>
    </div>
    """
    bg = background_defs(theme_name, WIDTH, HEIGHT, seed=5)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">
  {bg}
  <foreignObject x="0" y="0" width="{WIDTH}" height="{HEIGHT}">
    {html}
  </foreignObject>
</svg>
"""


def main():
    try:
        languages = fetch_language_counts()
    except Exception as e:
        print(f"language fetch failed ({e}), using placeholder")
        languages = [("—", 1)]

    for theme_name in ("dark", "light"):
        svg = build_svg(theme_name, languages)
        out = f"histogram-{theme_name}.svg"
        with open(out, "w") as f:
            f.write(svg)
        print(f"Wrote {out}")


if __name__ == "__main__":
    main()
