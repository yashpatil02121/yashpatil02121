"""Refreshes the live parts of the profile README from the GitHub API.

- assets/terminal.svg: `./now --top 3` lists the 3 most recently pushed repos,
  and the neofetch Status line shows the latest push.
- README.md: rewrites the blocks between <!-- ACTIVITY:START/END --> (recent public
  activity) and <!-- GUESTBOOK:START/END --> (latest signers), plus the repo count badge.
- assets/stats, assets/projects, assets/sections, assets/connect: self-hosted cards
  drawn by scripts/build_cards.py from GraphQL data (needs GITHUB_TOKEN).

Runs in .github/workflows/update-readme.yml. Locally: python scripts/update_readme.py
(set GITHUB_TOKEN to avoid the 60 requests/hour anonymous limit).
"""
import html
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import build_cards  # noqa: E402
import gen_svgs  # noqa: E402

USER = os.environ.get("GITHUB_USER", "yashpatil02121")
TOKEN = os.environ.get("GITHUB_TOKEN")
IST = timezone(timedelta(hours=5, minutes=30))
MAX_ACTIVITY = 6

# Taglines for repos whose GitHub description is empty or too long for the terminal.
TAGLINES = json.loads((ROOT / "scripts" / "taglines.json").read_text(encoding="utf-8"))
FEATURED = json.loads((ROOT / "scripts" / "featured.json").read_text(encoding="utf-8"))["projects"]


def api(path):
    req = urllib.request.Request(f"https://api.github.com{path}", headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": f"{USER}-profile-readme",
        **({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}),
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def gql(query, **variables):
    req = urllib.request.Request("https://api.github.com/graphql", method="POST",
                                 data=json.dumps({"query": query, "variables": variables}).encode(),
                                 headers={"Authorization": f"Bearer {TOKEN}", "User-Agent": f"{USER}-profile-readme"})
    with urllib.request.urlopen(req, timeout=60) as r:
        out = json.load(r)
    if out.get("errors"):
        raise RuntimeError(out["errors"])
    return out["data"]


REPO_FIELDS = """name description url homepageUrl stargazerCount pushedAt isPrivate isFork isArchived
  primaryLanguage { name color }
  languages(first: 8, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name color } } }
  releases(first: 3, orderBy: {field: CREATED_AT, direction: DESC}) { nodes { name tagName publishedAt description isPrerelease isDraft } }"""


def card_data(today):
    """Everything build_cards.build_all needs. Private repos are always filtered out."""
    now = datetime.now(timezone.utc)
    base = gql(f"""query($u: String!, $since: DateTime!) {{ user(login: $u) {{
        createdAt followers {{ totalCount }}
        repositories(ownerAffiliations: OWNER, privacy: PUBLIC, isFork: false, first: 100,
                     orderBy: {{field: PUSHED_AT, direction: DESC}}) {{ totalCount nodes {{ {REPO_FIELDS} }} }}
        year: contributionsCollection {{ contributionYears }}
        month: contributionsCollection(from: $since) {{
          commitContributionsByRepository(maxRepositories: 25) {{
            repository {{ name description isPrivate primaryLanguage {{ name color }} }} contributions {{ totalCount }} }} }}
    }} }}""", u=USER, since=(now - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ"))["user"]

    years = sorted(base["year"]["contributionYears"])
    aliases = " ".join(
        f'y{y}: contributionsCollection(from: "{y}-01-01T00:00:00Z", to: "{y}-12-31T23:59:59Z") '
        "{ totalCommitContributions totalPullRequestContributions "
        "contributionCalendar { totalContributions weeks { contributionDays { date contributionCount } } } }" for y in years)
    cal = gql(f"query($u: String!) {{ user(login: $u) {{ {aliases} }} }}", u=USER)["user"]
    by_year = {}
    for y in years:
        days = [(datetime.strptime(d["date"], "%Y-%m-%d").date(), d["contributionCount"])
                for w in cal[f"y{y}"]["contributionCalendar"]["weeks"] for d in w["contributionDays"]]
        by_year[y] = sorted(d for d in days if d[0].year == y)
    all_days = sorted(d for days in by_year.values() for d in days if d[0] <= today)
    totals = {k: sum(cal[f"y{y}"][k] for y in years) for k in ("totalCommitContributions", "totalPullRequestContributions")}
    totals["contributions"] = sum(cal[f"y{y}"]["contributionCalendar"]["totalContributions"] for y in years)

    repos = [r for r in base["repositories"]["nodes"] if not r["isPrivate"] and not r["isArchived"] and r["name"] != USER]
    by_name = {r["name"]: r for r in repos}
    langs = {}
    for r in repos:
        for e in r["languages"]["edges"]:
            n = e["node"]["name"]
            if n in ("Jupyter Notebook", "HTML", "CSS", "SCSS"):
                continue  # notebooks and markup swamp the byte counts
            size, color = langs.get(n, (0, e["node"]["color"] or "#8B949E"))
            langs[n] = (size + e["size"], color)

    def tag(name, desc):
        return TAGLINES.get(name) or desc or "work in progress"

    focus = [{
        "name": c["repository"]["name"], "commits": c["contributions"]["totalCount"],
        "tagline": tag(c["repository"]["name"], c["repository"]["description"]),
        "language": (c["repository"]["primaryLanguage"] or {}).get("name"),
        "color": (c["repository"]["primaryLanguage"] or {}).get("color") or "#8B949E",
    } for c in base["month"]["commitContributionsByRepository"]
        if not c["repository"]["isPrivate"] and c["repository"]["name"] != USER]

    releases = sorted(({
        "repo": r["name"], "tag": rel["tagName"], "name": rel["name"] or rel["tagName"],
        "notes": rel["description"], "date": when(rel["publishedAt"]).date(),
    } for r in repos for rel in r["releases"]["nodes"]
        if rel["publishedAt"] and not rel["isDraft"] and not rel["isPrerelease"]), key=lambda x: x["date"], reverse=True)

    projects = []
    for f in FEATURED:
        r = by_name.get(f["name"])
        if f.get("private"):
            projects.append({**f, "pushed": None})
            continue
        if not r:
            print(f"featured repo {f['name']} not found or not public, skipped")
            continue
        lang = r["primaryLanguage"] or {}
        projects.append({
            "name": r["name"], "tagline": f.get("tagline") or tag(r["name"], r["description"]),
            "language": lang.get("name"), "color": lang.get("color"), "stars": r["stargazerCount"],
            "pushed": when(r["pushedAt"]).date(), "live": bool(f.get("live") or r["homepageUrl"]),
        })

    return {
        "stats": {
            "contributions": totals["contributions"],
            "commits": totals["totalCommitContributions"],
            "prs": totals["totalPullRequestContributions"],
            "repos": base["repositories"]["totalCount"],
            "stars": sum(r["stargazerCount"] for r in repos),
            "followers": base["followers"]["totalCount"],
            "since": when(base["createdAt"]).year,
            "days": all_days,
            "languages": [(n, s, c) for n, (s, c) in sorted(langs.items(), key=lambda kv: -kv[1][0])],
        },
        "years": by_year,
        "focus": focus,
        "releases": releases,
        "projects": projects,
    }


def guestbook_block():
    """Latest guestbook signers (avatars only: visitor messages stay on the issues)."""
    try:
        issues = api(f"/repos/{USER}/{USER}/issues?labels=guestbook&state=all&per_page=12")
    except Exception as e:
        print(f"guestbook skipped: {e}")
        issues = []
    seen, people = set(), []
    for i in issues:
        login = i["user"]["login"]
        if login not in seen and i["user"]["type"] == "User":
            seen.add(login)
            people.append(f'<a href="{html.escape(i["html_url"])}"><img src="https://github.com/{html.escape(login)}.png?size=64" '
                          f'width="40" height="40" alt="{html.escape(login)}" title="{html.escape(login)}"/></a>')
    inner = (" ".join(people[:10]) + "<br/><sub>latest signatures</sub>") if people else \
        "<sub>No signatures yet. Be the first! ✍️</sub>"
    return "\n".join(["<!-- GUESTBOOK:START -->", '<p align="center">', inner, "</p>", "<!-- GUESTBOOK:END -->"])


def when(iso):
    return datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(IST)


def tagline(repo):
    if repo["name"] in TAGLINES:
        return TAGLINES[repo["name"]]
    if repo.get("description"):
        return repo["description"]
    return f"{repo['language']} project" if repo.get("language") else "fresh repo"


def clip(text, limit=72):
    """First line of `text`, shortened and HTML-escaped."""
    text = text.strip().splitlines()[0] if text.strip() else ""
    text = text if len(text) <= limit else text[: limit - 1].rstrip() + "…"
    return html.escape(text)


def link(url, label):
    return f'<a href="{html.escape(url)}">{label}</a>'


def repo_link(full):
    name = full.split("/", 1)[1] if full.startswith(USER + "/") else full
    return link(f"https://github.com/{full}", html.escape(name))


def activity_lines(events):
    """Turns public events into at most MAX_ACTIVITY markdown bullet lines."""
    lines, seen_push = [], set()
    commit_cache = {}
    for e in events:
        if len(lines) >= MAX_ACTIVITY:
            break
        kind, repo, p = e["type"], e["repo"]["name"], e.get("payload", {})
        if repo == f"{USER}/{USER}":
            continue  # the profile repo's own bot commits are noise
        day = when(e["created_at"]).strftime("%b %d")
        line = None
        if kind == "PushEvent":
            if (repo, day) in seen_push:
                continue
            seen_push.add((repo, day))
            msg = ""
            head = p.get("head")
            if head:
                if head not in commit_cache:
                    try:
                        commit_cache[head] = api(f"/repos/{repo}/commits/{head}")["commit"]["message"]
                    except Exception:
                        commit_cache[head] = ""
                msg = clip(commit_cache[head])
            line = f"📦 Pushed to {repo_link(repo)}" + (f" — <code>{msg}</code>" if msg else "")
        elif kind == "CreateEvent" and p.get("ref_type") == "repository":
            line = f"🆕 Created {repo_link(repo)}"
        elif kind == "PublicEvent":
            line = f"🌍 Open-sourced {repo_link(repo)}"
        elif kind == "PullRequestEvent" and p.get("action") in ("opened", "closed"):
            pr = p["pull_request"]
            if p["action"] == "closed" and not pr.get("merged"):
                continue
            verb = "🎉 Merged" if p["action"] == "closed" else "🔀 Opened"
            line = f"{verb} PR {link(pr['html_url'], '#' + str(pr['number']))} in {repo_link(repo)} — {clip(pr.get('title') or '', 60)}"
        elif kind == "IssuesEvent" and p.get("action") == "opened":
            iss = p["issue"]
            line = f"🐛 Opened issue {link(iss['html_url'], '#' + str(iss['number']))} in {repo_link(repo)}"
        elif kind == "ReleaseEvent" and p.get("action") == "published":
            rel = p["release"]
            line = f"🚀 Released {link(rel['html_url'], clip(rel.get('tag_name') or '', 30))} of {repo_link(repo)}"
        elif kind == "WatchEvent":
            line = f"⭐ Starred {repo_link(repo)}"
        elif kind == "ForkEvent":
            line = f"🍴 Forked {repo_link(repo)}"
        if line:
            lines.append(f"<sub><code>{day}</code></sub> &nbsp;{line}")
    return lines


def main():
    repos = [r for r in api(f"/users/{USER}/repos?per_page=100&type=owner&sort=pushed")
             if not r["fork"] and not r["archived"] and r["name"] != USER]
    repos.sort(key=lambda r: r["pushed_at"], reverse=True)
    profile = api(f"/users/{USER}")
    events = api(f"/users/{USER}/events/public?per_page=100")
    events.sort(key=lambda e: e["created_at"], reverse=True)

    latest = repos[0]
    now = [(r["name"], tagline(r)) for r in repos[:3]]
    status = f"last push {when(latest['pushed_at']).strftime('%b %d')} → {latest['name']}"
    gen_svgs.OUT = ROOT / "assets"
    gen_svgs.terminal(now=now, status=status)

    lines = activity_lines(events) or ["<sub>Quiet week — probably deep in a private repo. 🤫</sub>"]
    langs = sorted({r["language"] for r in repos if r.get("language")})
    stars = sum(r["stargazers_count"] for r in repos)
    refreshed = datetime.now(IST).strftime("%d %b %Y")
    block = "\n".join([
        "<!-- ACTIVITY:START -->",
        "<!-- This block is rewritten automatically by scripts/update_readme.py -->",
        "",
        "<table>",
        "<tr>",
        "<td width=\"62%\" valign=\"top\">",
        "<b>⚡ Recent activity</b><br/><br/>",
        *[f"{l}<br/>" for l in lines],
        "</td>",
        "<td width=\"38%\" valign=\"top\">",
        "<b>🔥 Most recently pushed</b>",
        "<ol>",
        *[f"<li>{link(r['html_url'], html.escape(r['name']))}<br/><sub>{clip(tagline(r), 56)}</sub></li>" for r in repos[:3]],
        "</ol>",
        f"<sub>📁 {profile['public_repos']} public repos · 🧬 {len(langs)} languages · ⭐ {stars} stars</sub>",
        "</td>",
        "</tr>",
        "</table>",
        "",
        f"<p align=\"right\"><sub>🤖 auto-refreshed {refreshed} by "
        f"<a href=\"scripts/update_readme.py\">update_readme.py</a></sub></p>",
        "",
        "<!-- ACTIVITY:END -->",
    ])

    if TOKEN:
        today = datetime.now(IST).date()
        build_cards.build_all(card_data(today), today)
    else:
        print("no GITHUB_TOKEN: skipped the GraphQL cards")

    readme_path = ROOT / "README.md"
    readme = readme_path.read_text(encoding="utf-8")
    new, n = re.subn(r"<!-- ACTIVITY:START -->.*?<!-- ACTIVITY:END -->", lambda _: block, readme, flags=re.S)
    if n != 1:
        sys.exit("README.md needs exactly one ACTIVITY:START/END block")
    if "<!-- GUESTBOOK:START -->" in new:
        new = re.sub(r"<!-- GUESTBOOK:START -->.*?<!-- GUESTBOOK:END -->", lambda _: guestbook_block(), new, flags=re.S)
    new = re.sub(r"badge/repos-\d+-", f"badge/repos-{profile['public_repos']}-", new)
    readme_path.write_text(new, encoding="utf-8", newline="\n")
    print(f"now: {[n for n, _ in now]} | {len(lines)} activity lines | status: {status}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
