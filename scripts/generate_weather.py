import datetime
import json
import urllib.request

from glass import THEMES, background_defs, tile_css

# Home base — Kolkata, since that's the IST anchor used elsewhere.
LAT, LON = 22.5726, 88.3639
WIDTH, HEIGHT = 460, 170

WEATHER_CODES = {
    0: "clear sky", 1: "mostly clear", 2: "partly cloudy", 3: "overcast",
    45: "fog", 48: "fog", 51: "light drizzle", 61: "light rain",
    63: "rain", 65: "heavy rain", 80: "rain showers", 95: "thunderstorm",
}


def fetch_weather():
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={LAT}&longitude={LON}"
        "&current=temperature_2m,weather_code"
        "&daily=sunrise,sunset&timezone=Asia%2FKolkata"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())


def golden_hour_line(sunset_str):
    ist = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
    sunset = datetime.datetime.fromisoformat(sunset_str).replace(tzinfo=ist)
    golden_start = sunset - datetime.timedelta(minutes=45)
    now = datetime.datetime.now(ist)

    if now < golden_start:
        delta = golden_start - now
        hrs, rem = divmod(int(delta.total_seconds()), 3600)
        mins = rem // 60
        return f"golden hour in {hrs}h {mins}m"
    if golden_start <= now <= sunset:
        return "golden hour now"
    return "past sunset"


def build_svg(theme_name, temp, condition, golden_line):
    t = THEMES[theme_name]
    html = f"""
    <div xmlns="http://www.w3.org/1999/xhtml" class="wrap">
      <style>
        {tile_css(theme_name)}
        .wrap {{ width: {WIDTH}px; height: {HEIGHT}px; padding: 16px; }}
        .tile {{ width: 100%; height: 100%; }}
        .temp {{ font-size: 30px; font-weight: 600; }}
        .cond {{ font-size: 13px; color: {t['muted']}; margin-top: 2px; }}
        .golden {{ margin-top: 12px; font-size: 12px; color: {t['accent']}; }}
      </style>
      <div class="tile">
        <div class="label">Kolkata right now</div>
        <div class="temp">{temp:.0f}&#176;C</div>
        <div class="cond">{condition}</div>
        <div class="golden">{golden_line}</div>
      </div>
    </div>
    """
    bg = background_defs(theme_name, WIDTH, HEIGHT, seed=4)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">
  {bg}
  <foreignObject x="0" y="0" width="{WIDTH}" height="{HEIGHT}">
    {html}
  </foreignObject>
</svg>
"""


def main():
    try:
        data = fetch_weather()
        temp = data["current"]["temperature_2m"]
        code = data["current"]["weather_code"]
        condition = WEATHER_CODES.get(code, "—")
        sunset = data["daily"]["sunset"][0]
        golden_line = golden_hour_line(sunset)
    except Exception as e:
        print(f"weather fetch failed ({e}), using placeholder")
        temp, condition, golden_line = 0.0, "—", "—"

    for theme_name in ("dark", "light"):
        svg = build_svg(theme_name, temp, condition, golden_line)
        out = f"weather-{theme_name}.svg"
        with open(out, "w") as f:
            f.write(svg)
        print(f"Wrote {out}")


if __name__ == "__main__":
    main()
