"""Refreshes the live parts of the profile README from the GitHub API.

- assets/terminal.svg: `./now --top 3` lists the 3 most recently pushed repos,
  and the neofetch Status line shows the latest push.
- README.md: rewrites the block between <!-- ACTIVITY:START --> and <!-- ACTIVITY:END -->
  with recent public activity, plus the public repo count badge.

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
import gen_svgs  # noqa: E402

USER = os.environ.get("GITHUB_USER", "yashpatil02121")
TOKEN = os.environ.get("GITHUB_TOKEN")
IST = timezone(timedelta(hours=5, minutes=30))
MAX_ACTIVITY = 6

# Taglines for repos whose GitHub description is empty or too long for the terminal.
TAGLINES = json.loads((ROOT / "scripts" / "taglines.json").read_text(encoding="utf-8"))


def api(path):
    req = urllib.request.Request(f"https://api.github.com{path}", headers={
        "Accept": "application/vnd.github+json",
        "User-Agent": f"{USER}-profile-readme",
        **({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}),
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


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

    readme_path = ROOT / "README.md"
    readme = readme_path.read_text(encoding="utf-8")
    new, n = re.subn(r"<!-- ACTIVITY:START -->.*?<!-- ACTIVITY:END -->", lambda _: block, readme, flags=re.S)
    if n != 1:
        sys.exit("README.md needs exactly one ACTIVITY:START/END block")
    new = re.sub(r"badge/repos-\d+-", f"badge/repos-{profile['public_repos']}-", new)
    readme_path.write_text(new, encoding="utf-8", newline="\n")
    print(f"now: {[n for n, _ in now]} | {len(lines)} activity lines | status: {status}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
