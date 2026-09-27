import datetime
import json
import os
import urllib.request
from xml.sax.saxutils import escape

import yaml

from glass import THEMES, background_defs, tile_css
from portfolio import get_portfolio

USERNAME = os.environ.get("GITHUB_USERNAME", "AdityaSeth777")
TOKEN = os.environ.get("GITHUB_TOKEN")
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

WIDTH, HEIGHT = 900, 340


def api(path):
    req = urllib.request.Request(f"https://api.github.com{path}")
    req.add_header("Accept", "application/vnd.github+json")
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())


def fetch_github_stats():
    user = api(f"/users/{USERNAME}")
    repos = []
    page = 1
    while True:
        batch = api(f"/users/{USERNAME}/repos?per_page=100&page={page}&type=owner")
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1

    stars = sum(r.get("stargazers_count", 0) for r in repos)
    created = datetime.datetime.strptime(
        user["created_at"], "%Y-%m-%dT%H:%M:%SZ"
    ).replace(tzinfo=datetime.timezone.utc)
    days_old = (datetime.datetime.now(datetime.timezone.utc) - created).days

    return {
        "followers": user.get("followers", 0),
        "public_repos": user.get("public_repos", len(repos)),
        "stars": stars,
        "days_old": days_old,
    }


def load_skills():
    path = os.path.join(DATA_DIR, "skills.yml")
    with open(path) as f:
        doc = yaml.safe_load(f)
    return doc["categories"]


def local_time_str():
    ist = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
    now = datetime.datetime.now(ist)
    return now.strftime("%H:%M"), now.strftime("%a, %d %b")


def build_svg(theme_name, stats, portfolio, skill_categories):
    t = THEMES[theme_name]
    time_str, date_str = local_time_str()

    # rotate which 3 skill categories get featured based on the day of year,
    # so the tile stays fresh across regenerations without needing new data.
    day_index = datetime.date.today().timetuple().tm_yday
    start = day_index % len(skill_categories)
    featured = (skill_categories * 2)[start:start + 3]

    pills = "".join(
        f'<span class="pill">{escape(cat["name"])}</span>' for cat in featured
    )
    role = escape(portfolio["role"])

    html = f"""
    <div xmlns="http://www.w3.org/1999/xhtml" class="wrap">
      <style>
        {tile_css(theme_name)}
        .wrap {{ width: {WIDTH}px; height: {HEIGHT}px; padding: 18px; }}
        .grid {{
          display: grid;
          grid-template-columns: 1.7fr 1fr 1fr;
          grid-template-rows: 1fr 1fr;
          gap: 12px;
          width: 100%;
          height: 100%;
        }}
        .identity {{ grid-row: span 2; justify-content: center; }}
        .name {{ font-size: 27px; font-weight: 600; letter-spacing: -0.01em; display: flex; align-items: center; gap: 8px; }}
        .role {{ margin-top: 6px; font-size: 13px; color: {t['muted']}; line-height: 1.5; max-width: 34ch; }}
        .focus-row {{ margin-top: 14px; display: flex; gap: 8px; flex-wrap: wrap; }}
        .now .sub {{ font-size: 11.5px; color: {t['muted']}; margin-top: 2px; }}
      </style>
      <div class="grid">
        <div class="tile identity">
          <div class="name"><span class="safelight"></span> Aditya Seth</div>
          <div class="role">{role}</div>
          <div class="focus-row">{pills}</div>
        </div>
        <div class="tile since">
          <div class="label">on github for</div>
          <div class="value accent">{stats['days_old']:,} days</div>
        </div>
        <div class="tile signal">
          <div class="label">followers &#183; stars</div>
          <div class="value accent2">{stats['followers']} &#183; {stats['stars']}</div>
        </div>
        <div class="tile repos">
          <div class="label">public repos</div>
          <div class="value accent">{stats['public_repos']}</div>
        </div>
        <div class="tile now">
          <div class="label">Kolkata / IST</div>
          <div class="value">{time_str}</div>
          <div class="sub">{date_str}</div>
        </div>
      </div>
    </div>
    """

    bg = background_defs(theme_name, WIDTH, HEIGHT, seed=1)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">
  {bg}
  <foreignObject x="0" y="0" width="{WIDTH}" height="{HEIGHT}">
    {html}
  </foreignObject>
</svg>
"""


def main():
    try:
        stats = fetch_github_stats()
    except Exception as e:
        print(f"GitHub API fetch failed ({e}), using placeholder stats")
        stats = {"followers": 0, "public_repos": 0, "stars": 0, "days_old": 0}

    portfolio = get_portfolio()
    skill_categories = load_skills()

    for theme_name in ("dark", "light"):
        svg = build_svg(theme_name, stats, portfolio, skill_categories)
        out = f"bento-{theme_name}.svg"
        with open(out, "w") as f:
            f.write(svg)
        print(f"Wrote {out}")


if __name__ == "__main__":
    main()
