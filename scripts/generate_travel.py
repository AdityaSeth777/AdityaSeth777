import math
import os
from xml.sax.saxutils import escape

import yaml

from glass import THEMES, background_defs, tile_css, MONO_STACK

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "trips.yml")
WIDTH, HEIGHT = 460, 340
MAP_W, MAP_H = 420, 180


def load_trips():
    with open(DATA_PATH) as f:
        doc = yaml.safe_load(f) or {}
    return doc.get("trips") or []


def haversine_km(a, b):
    r = 6371
    lat1, lon1, lat2, lon2 = map(math.radians, [a["lat"], a["lon"], b["lat"], b["lon"]])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def project(lat, lon):
    """Plain equirectangular projection into the map viewport — a stylized
    flight-path plot, not a literal landmass map (no world-map asset data)."""
    x = (lon + 180) / 360 * MAP_W
    y = (90 - lat) / 180 * MAP_H
    return x, y


def build_svg(theme_name, trips, total_km):
    t = THEMES[theme_name]

    if not trips:
        body = f"""
        <div class="tile placeholder">
          <div class="label">flight log</div>
          <div class="value">No trips logged yet</div>
          <div class="sub">Add entries to data/trips.yml to plot them here.</div>
        </div>
        """
    else:
        points = [project(tr["lat"], tr["lon"]) for tr in trips]
        dots = ""
        for (x, y), tr in zip(points, trips):
            dots += (
                f'<circle cx="{x}" cy="{y}" r="4" fill="{t["accent"]}" />'
                f'<text x="{x+7}" y="{y+4}" font-size="9" fill="{t["muted"]}" '
                f"font-family='{MONO_STACK}'>{escape(tr.get('city',''))}</text>"
            )
        paths = ""
        for (x1, y1), (x2, y2) in zip(points, points[1:]):
            mx, my = (x1 + x2) / 2, min(y1, y2) - 24
            paths += (
                f'<path d="M {x1} {y1} Q {mx} {my} {x2} {y2}" '
                f'fill="none" stroke="{t["accent2"]}" stroke-width="1.4" '
                f'stroke-dasharray="3 3" opacity="0.8"/>'
            )
        body = f"""
        <div class="tile map-tile">
          <div class="label">flight log &#8212; {len(trips)} trips</div>
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {MAP_W} {MAP_H}" width="{MAP_W}" height="{MAP_H}" style="margin-top:8px;">
            {paths}
            {dots}
          </svg>
          <div class="odometer">
            <span class="label">distance traveled</span>
            <div class="value accent">{total_km:,.0f} km</div>
          </div>
        </div>
        """

    html = f"""
    <div xmlns="http://www.w3.org/1999/xhtml" class="wrap">
      <style>
        {tile_css(theme_name)}
        .wrap {{ width: {WIDTH}px; height: {HEIGHT}px; padding: 18px; }}
        .tile {{ width: 100%; height: 100%; }}
        .map-tile {{ align-items: flex-start; }}
        .odometer {{ margin-top: 10px; }}
        .placeholder .value {{ font-size: 18px; font-weight: 600; margin-top: 6px; }}
        .placeholder .sub {{ font-size: 12px; color: {t['muted']}; margin-top: 6px; }}
      </style>
      {body}
    </div>
    """
    bg = background_defs(theme_name, WIDTH, HEIGHT, seed=6)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">
  {bg}
  <foreignObject x="0" y="0" width="{WIDTH}" height="{HEIGHT}">
    {html}
  </foreignObject>
</svg>
"""


def main():
    trips = load_trips()
    total_km = sum(haversine_km(a, b) for a, b in zip(trips, trips[1:]))

    for theme_name in ("dark", "light"):
        svg = build_svg(theme_name, trips, total_km)
        out = f"travel-{theme_name}.svg"
        with open(out, "w") as f:
            f.write(svg)
        print(f"Wrote {out} ({len(trips)} trips, {total_km:.0f} km)")


if __name__ == "__main__":
    main()
