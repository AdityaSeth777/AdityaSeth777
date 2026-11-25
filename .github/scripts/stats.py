#!/usr/bin/env python3
"""Generate stats.svg from the GitHub GraphQL API.

Written to replace lowlighter/metrics' overview card, which reported 0
stargazers, 0 forks and 0 releases for an account that has 163, 33 and 8.
That project has had no real commit since December 2023.

Totals cover all non-fork repositories owned by the account, private
included, so the token needs the repo scope.
"""
import json
import os
import time
import urllib.error
import urllib.request

API = "https://api.github.com/graphql"
USER = os.environ.get("STATS_USER", "AdityaSeth777")
TOKEN = os.environ["GITHUB_TOKEN"]
OUT = os.environ.get("STATS_OUT", "stats.svg")

QUERY = """
query($login:String!, $cursor:String) {
  user(login:$login) {
    name
    followers { totalCount }
    following { totalCount }
    repositoriesContributedTo(includeUserRepositories:true) { totalCount }
    pullRequests(states:MERGED) { totalCount }
    issues { totalCount }
    repositories(first:50, after:$cursor, ownerAffiliations:OWNER,
                 isFork:false) {
      totalCount
      pageInfo { hasNextPage endCursor }
      nodes {
        stargazerCount
        forkCount
        releases { totalCount }
        watchers { totalCount }
        primaryLanguage { name }
      }
    }
  }
}
"""


def call(cursor=None, attempts=5):
    """GitHub's GraphQL endpoint returns intermittent 502s on heavier queries,
    so retry with backoff rather than failing the daily run."""
    body = json.dumps({"query": QUERY, "variables": {"login": USER, "cursor": cursor}})
    for attempt in range(1, attempts + 1):
        req = urllib.request.Request(
            API,
            data=body.encode(),
            headers={
                "Authorization": f"bearer {TOKEN}",
                "Content-Type": "application/json",
                "User-Agent": "profile-stats-card",
            },
        )
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
    stars = forks = releases = watchers = 0
    langs = {}
    cursor, user = None, None
    while True:
        user = call(cursor)
        repos = user["repositories"]
        for n in repos["nodes"]:
            stars += n["stargazerCount"]
            forks += n["forkCount"]
            releases += n["releases"]["totalCount"]
            watchers += n["watchers"]["totalCount"]
            lang = (n.get("primaryLanguage") or {}).get("name")
            if lang:
                langs[lang] = langs.get(lang, 0) + 1
        if not repos["pageInfo"]["hasNextPage"]:
            break
        cursor = repos["pageInfo"]["endCursor"]
    return {
        "name": user["name"] or USER,
        "repos": user["repositories"]["totalCount"],
        "stars": stars,
        "forks": forks,
        "releases": releases,
        "watchers": watchers,
        "followers": user["followers"]["totalCount"],
        "contributed": user["repositoriesContributedTo"]["totalCount"],
        "merged_prs": user["pullRequests"]["totalCount"],
        "top_langs": sorted(langs.items(), key=lambda kv: -kv[1])[:5],
    }


def esc(t):
    return (str(t).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def human(n):
    return f"{n:,}"


ACCENT = "#53B14F"
W, H = 840, 290


def render(d):
    tiles = [
        ("Stars earned", d["stars"]),
        ("Forks", d["forks"]),
        ("Releases", d["releases"]),
        ("Watchers", d["watchers"]),
        ("Repositories", d["repos"]),
        ("Followers", d["followers"]),
        ("Merged PRs", d["merged_prs"]),
        ("Contributed to", d["contributed"]),
    ]
    cols, pad, gap = 4, 30, 14
    tw = (W - 2 * pad - (cols - 1) * gap) / cols
    th = 74
    cells = []
    for i, (label, value) in enumerate(tiles):
        x = pad + (i % cols) * (tw + gap)
        y = 92 + (i // cols) * (th + gap)
        cells.append(
            f'<g><rect x="{x:.1f}" y="{y}" width="{tw:.1f}" height="{th}" rx="11" '
            f'fill="#1a1a1f" stroke="#2a2a31"/>'
            f'<text x="{x + 16:.1f}" y="{y + 32}" class="num">{human(value)}</text>'
            f'<text x="{x + 16:.1f}" y="{y + 55}" class="lbl">{esc(label)}</text></g>'
        )
    langs = "  ·  ".join(f"{esc(n)}" for n, _ in d["top_langs"])
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="GitHub statistics">
<title>GitHub statistics for {esc(d['name'])}</title>
<style>
  .t{{font:700 22px -apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,sans-serif;fill:#fff}}
  .s{{font:400 13px ui-monospace,Menlo,monospace;fill:#70707a}}
  .num{{font:700 26px ui-monospace,Menlo,monospace;fill:{ACCENT}}}
  .lbl{{font:400 12px -apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,sans-serif;fill:#8a8a93}}
</style>
<rect width="{W}" height="{H}" rx="14" fill="#131316"/>
<text x="30" y="44" class="t">GitHub statistics</text>
<text x="30" y="68" class="s">all owned repositories, private included  ·  {esc(langs)}</text>
{''.join(cells)}
</svg>
"""


if __name__ == "__main__":
    data = collect()
    with open(OUT, "w") as fh:
        fh.write(render(data))
    print(json.dumps({k: v for k, v in data.items() if k != "top_langs"}, indent=2))
