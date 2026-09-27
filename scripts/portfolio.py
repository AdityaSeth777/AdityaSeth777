import re
import urllib.request

PORTFOLIO_URL = "https://adityaseth.in"


def fetch_portfolio():
    """Scrape adityaseth.in for skill categories and the current headline.

    The site is a server-rendered Bootstrap page (skills sit in
    <h5 class="mb-0">Category</h5><p class="mt-3">description</p> pairs),
    so a plain fetch + regex is enough — no JS execution needed.
    """
    req = urllib.request.Request(PORTFOLIO_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        html = resp.read().decode("utf-8", errors="ignore")

    title_match = re.search(r"<title>([^<]*)</title>", html)
    title = title_match.group(1).strip() if title_match else ""
    # "Aditya Seth - Software Engineer, Cloud Architect & AI Researcher"
    role = title.split("-", 1)[1].strip() if "-" in title else title

    pairs = re.findall(
        r'<h5 class="mb-0">(.*?)</h5>.*?<p class="mt-3">(.*?)</p>', html, re.S
    )
    skills = []
    for heading, desc in pairs:
        heading = _clean(heading)
        desc = _clean(desc)
        skills.append({"category": heading, "summary": desc})

    return {"role": role, "skills": skills}


def _clean(text):
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("&amp;", "&").replace("&#9733;", "*")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def fallback_portfolio():
    return {
        "role": "Software Engineer, Cloud Architect & AI Researcher",
        "skills": [
            {"category": "AI / ML Engineering", "summary": "GenAI, RAG pipelines, PyTorch"},
            {"category": "Cloud Architecture", "summary": "GCP, Azure, Oracle Cloud"},
        ],
    }


def get_portfolio():
    try:
        data = fetch_portfolio()
        if data["skills"]:
            return data
    except Exception:
        pass
    return fallback_portfolio()
