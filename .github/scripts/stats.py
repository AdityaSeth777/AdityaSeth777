#!/usr/bin/env python3
"""Generate stats.svg from the GitHub GraphQL API.

Replaces lowlighter/metrics' overview card, which reported 0 stargazers,
0 forks and 0 releases for an account that has 163, 37 and 8. Its run log
showed the fetch succeeding, so the aggregation itself dropped the values.
That project has had no real commit since December 2023.

Layout deliberately mirrors the card this replaces, down to the octicons,
which are lifted from the original output into octicons.json.

Totals cover every repository the account owns: forks and private repos
included, so the token needs the repo scope.
"""
import base64
import datetime as dt
import json
import os
import pathlib
import time
import urllib.error
import urllib.request

API = "https://api.github.com/graphql"
USER = os.environ.get("STATS_USER", "AdityaSeth777")
TOKEN = os.environ["GITHUB_TOKEN"]
OUT = os.environ.get("STATS_OUT", "stats.svg")
ICONS = json.loads((pathlib.Path(__file__).parent / "octicons.json").read_text())

QUERY = """
query($login:String!, $cursor:String) {
  user(login:$login) {
    name login avatarUrl createdAt
    followers { totalCount }
    packages { totalCount }
    sponsorshipsAsMaintainer { totalCount }
    repositoriesContributedTo(includeUserRepositories:true) { totalCount }
    contributionsCollection {
      contributionCalendar {
        weeks { contributionDays { contributionCount color date } }
      }
    }
    repositories(first:50, after:$cursor, ownerAffiliations:OWNER) {
      totalCount
      pageInfo { hasNextPage endCursor }
      nodes {
        stargazerCount forkCount diskUsage
        releases { totalCount }
        watchers { totalCount }
        licenseInfo { spdxId }
      }
    }
  }
}
"""


def call(cursor=None, attempts=5):
    """GitHub's GraphQL endpoint returns intermittent 502s on this query,
    so retry with backoff rather than failing the daily run."""
    body = json.dumps({"query": QUERY, "variables": {"login": USER, "cursor": cursor}})
    for attempt in range(1, attempts + 1):
        req = urllib.request.Request(
            API, data=body.encode(),
            headers={"Authorization": f"bearer {TOKEN}",
                     "Content-Type": "application/json",
                     "User-Agent": "profile-stats-card"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                payload = json.load(r)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as err:
            if attempt == attempts:
                raise
            print(f"attempt {attempt} failed ({err}), retrying")
            time.sleep(2 ** attempt)
            continue
        if "errors" in payload:
            raise SystemExit(f"GraphQL errors: {payload['errors']}")
        return payload["data"]["user"]


def collect():
    stars = forks = releases = watchers = disk = 0
    licenses = {}
    cursor, user = None, None
    while True:
        user = call(cursor)
        repos = user["repositories"]
        for n in repos["nodes"]:
            stars += n["stargazerCount"]
            forks += n["forkCount"]
            releases += n["releases"]["totalCount"]
            watchers += n["watchers"]["totalCount"]
            disk += n.get("diskUsage") or 0
            spdx = (n.get("licenseInfo") or {}).get("spdxId")
            if spdx:
                licenses[spdx] = licenses.get(spdx, 0) + 1
        if not repos["pageInfo"]["hasNextPage"]:
            break
        cursor = repos["pageInfo"]["endCursor"]

    days = [d for w in user["contributionsCollection"]["contributionCalendar"]["weeks"]
            for d in w["contributionDays"]]
    joined = dt.datetime.fromisoformat(user["createdAt"].replace("Z", "+00:00"))
    years = int((dt.datetime.now(dt.timezone.utc) - joined).days / 365.25)

    return {
        "name": user["name"] or user["login"],
        "avatar": user["avatarUrl"],
        "years": years,
        "followers": user["followers"]["totalCount"],
        "contributed": user["repositoriesContributedTo"]["totalCount"],
        "repos": user["repositories"]["totalCount"],
        "license": max(licenses, key=licenses.get) if licenses else None,
        "releases": releases,
        "packages": user["packages"]["totalCount"],
        "disk": disk,
        "sponsors": user["sponsorshipsAsMaintainer"]["totalCount"],
        "stars": stars,
        "forks": forks,
        "watchers": watchers,
        "calendar": days[-14:],
    }


def avatar_b64(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "profile-stats-card"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return base64.b64encode(r.read()).decode()
    except Exception as err:          # the card is still useful without a face on it
        print(f"avatar fetch failed ({err}), rendering without it")
        return None


def human_size(kb):
    mb = kb / 1024
    return f"{mb/1024:.2f} GB" if mb >= 1024 else f"{mb:.1f} MB"


def esc(t):
    return str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


W, H = 540, 222
BLUE, GREY, BG = "#58a6ff", "#8b949e", "#131316"


def row(x, y, icon, text, cls="v"):
    return (f'<g transform="translate({x},{y})">'
            f'<svg viewBox="0 0 16 16" width="15" height="15" y="-11" fill="{GREY}">{ICONS[icon]}</svg>'
            f'<text x="23" class="{cls}">{esc(text)}</text></g>')


def render(d):
    av = avatar_b64(d["avatar"])
    head = (f'<image x="30" y="22" width="26" height="26" clip-path="circle(13px at 13px 13px)" '
            f'href="data:image/png;base64,{av}"/>' if av else "")
    name_x = 64 if av else 30

    cal = "".join(
        f'<rect x="{295 + i * 16}" y="34" width="12" height="12" rx="2.5" '
        f'fill="{day["color"] if day["contributionCount"] else "#2a2a31"}"/>'
        for i, day in enumerate(d["calendar"]))

    left = [
        row(30, 80, "clock", f"Joined GitHub {d['years']} years ago"),
        row(30, 102, "people", f"Followed by {d['followers']:,} users"),
        row(30, 142, "repo", f"{d['repos']:,} Repositories", "h"),
        row(30, 164, "law", f"{d['license']} preference" if d["license"] else "No license preference"),
        row(30, 186, "tag", f"{d['releases']:,} Releases"),
        row(30, 208, "package", f"{d['packages']:,} Packages"),
    ]
    right = [
        row(295, 74, "contributed", f"Contributed to {d['contributed']:,} repositories"),
        row(295, 142, "star", f"{d['stars']:,} Stargazers", "h"),
        row(295, 164, "fork", f"{d['forks']:,} Forkers"),
        row(295, 186, "eye", f"{d['watchers']:,} Watchers"),
        row(295, 208, "database", f"{human_size(d['disk'])} used"),
    ]
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="GitHub statistics for {esc(d['name'])}">
<title>GitHub statistics for {esc(d['name'])}</title>
<style>
 .n{{font:700 20px -apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,sans-serif;fill:{BLUE}}}
 .h{{font:600 15px -apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,sans-serif;fill:{BLUE}}}
 .v{{font:400 14px -apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,sans-serif;fill:#c9d1d9}}
</style>
<rect width="{W}" height="{H}" rx="12" fill="{BG}"/>
{head}<text x="{name_x}" y="44" class="n">{esc(d['name'])}</text>
{cal}
{''.join(left)}{''.join(right)}
</svg>
"""


if __name__ == "__main__":
    data = collect()
    pathlib.Path(OUT).write_text(render(data))
    print(json.dumps({k: v for k, v in data.items()
                      if k not in ("calendar", "avatar")}, indent=2))
