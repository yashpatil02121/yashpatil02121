"""Self-hosted SVG cards for the profile README (no third-party card services).

Pure rendering: every function takes plain data and writes one SVG into assets/.
scripts/update_readme.py fetches the data and calls build_all(); running this file
directly only rebuilds the static cards (section headers, contents, connect).
"""
import math
from datetime import date, timedelta
from html import escape as _esc
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

BG, PANEL, BORDER = "#0d1117", "#161b22", "#30363d"
PURPLE, VIOLET, PINK, CYAN, GREEN, YELLOW = "#A855F7", "#7C3AED", "#EC4899", "#22D3EE", "#3FB950", "#E3B341"
TEXT, MUTED = "#E6EDF3", "#8B949E"
MONO = "Consolas, 'SF Mono', Menlo, 'DejaVu Sans Mono', monospace"
SANS = "'Segoe UI', Ubuntu, -apple-system, Helvetica, Arial, sans-serif"
HEAT = ["#161b22", "#3b1f63", "#6d28d9", "#9333ea", "#c084fc"]

# (anchor, title, shell command shown on the right of the header)
SECTIONS = [
    ("about", "About Me", "whoami"),
    ("building", "Building Now", "./now --building"),
    ("activity", "Live Activity", "tail -f activity.log"),
    ("stack", "Tech Stack", "ls ~/stack"),
    ("journey", "Journey", "git log --journey"),
    ("stats", "GitHub Stats", "gh api /users/me"),
    ("setup", "Setup", "cat ~/.setup"),
    ("connect", "Connect", "ping yash"),
]

CONNECT = [
    ("linkedin", "LinkedIn", "in/yash-patil-6655b5215", "#0A66C2", "in"),
    ("website", "Website", "patilyash.tech", PURPLE, "◆"),
    ("leetcode", "LeetCode", "u/yashpatil2121", "#FFA116", "{}"),
    ("hackerrank", "HackerRank", "patilyash02121", "#2EC866", "H"),
    ("guestbook-sign", "Sign the guestbook", "leave a note · takes 10 seconds", PINK, "✎"),
    ("guestbook-read", "Read the guestbook", "see who stopped by", CYAN, "☰"),
]


def esc(s):
    return _esc(str(s), quote=True)


def clip(s, n):
    s = " ".join(str(s or "").split())
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


def wrap(s, width, lines=2):
    words, out, cur = str(s or "").split(), [], ""
    for w in words:
        if len(cur) + len(w) + (1 if cur else 0) > width:
            out.append(cur)
            cur = w
            if len(out) == lines:
                break
        else:
            cur = f"{cur} {w}" if cur else w
    else:
        out.append(cur)
    out = [l for l in out if l][:lines]
    if len(out) == lines and " ".join(out) != " ".join(words):
        out[-1] = clip(out[-1] + " …", width)
    return out


def write(name, w, h, body, css="", defs=""):
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" font-family="{SANS}">'
        f"<defs>{GRAD}{defs}</defs><style>{css}</style>{body}</svg>"
    )
    path = ASSETS / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg, encoding="utf-8", newline="\n")


GRAD = (
    f'<linearGradient id="brand" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="{PINK}"/>'
    f'<stop offset=".5" stop-color="{PURPLE}"/><stop offset="1" stop-color="{CYAN}"/></linearGradient>'
)
FADE_UP = (
    "@keyframes up{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}"
    ".up{opacity:0;animation:up .7s cubic-bezier(.2,.7,.2,1) forwards}"
)


def frame(w, h, title=None, sub=None):
    out = (
        f'<rect x=".5" y=".5" width="{w-1}" height="{h-1}" rx="12" fill="{BG}" stroke="{BORDER}"/>'
        f'<rect x="1" y="1" width="{w-2}" height="3" rx="1.5" fill="url(#brand)" opacity=".9"/>'
    )
    if title:
        out += f'<text x="24" y="38" fill="{TEXT}" font-size="16" font-weight="700">{esc(title)}</text>'
    if sub:
        out += f'<text x="{w-24}" y="38" fill="{MUTED}" font-size="12" font-family="{MONO}" text-anchor="end">{esc(sub)}</text>'
    return out


def ago(d, today):
    days = (today - d).days
    if days <= 0:
        return "today"
    if days == 1:
        return "yesterday"
    if days < 30:
        return f"{days}d ago"
    if days < 365:
        return f"{days // 30}mo ago"
    return f"{days // 365}y ago"


# ───────────────────────────── static cards ─────────────────────────────
def section_headers():
    css = (
        "@keyframes sweep{0%{transform:translateX(-160px)}100%{transform:translateX(900px)}}"
        ".sw{animation:sweep 4.5s cubic-bezier(.6,0,.4,1) infinite}"
        "@keyframes bl{0%,49%{opacity:1}50%,100%{opacity:0}}.cur{animation:bl 1.1s step-end infinite}"
    )
    for i, (key, title, cmd) in enumerate(SECTIONS, 1):
        w, h = 860, 66
        body = (
            f'<text x="2" y="44" font-family="{MONO}" font-size="36" font-weight="700" fill="url(#brand)">{i:02d}</text>'
            f'<text x="70" y="42" fill="{TEXT}" font-size="24" font-weight="700">{esc(title)}</text>'
            f'<text x="{w-14}" y="40" fill="{MUTED}" font-size="13" font-family="{MONO}" text-anchor="end">'
            f'<tspan fill="{GREEN}">$</tspan> {esc(cmd)}</text>'
            f'<rect class="cur" x="{w-10}" y="28" width="7" height="15" fill="{PURPLE}"/>'
            f'<rect x="0" y="{h-6}" width="{w}" height="1" fill="{BORDER}"/>'
            f'<rect x="0" y="{h-7}" width="{w}" height="3" rx="1.5" fill="url(#brand)" opacity=".35"/>'
            f'<g clip-path="url(#cl)"><rect class="sw" x="0" y="{h-8}" width="160" height="5" fill="url(#glint)"/></g>'
        )
        defs = (
            f'<clipPath id="cl"><rect x="0" y="{h-8}" width="{w}" height="5"/></clipPath>'
            f'<linearGradient id="glint"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
            f'<stop offset=".5" stop-color="#fff" stop-opacity=".9"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
        )
        write(f"sections/{key}.svg", w, h, body, css, defs)

        tw, th = 270, 58
        toc = (
            f'<rect x=".5" y=".5" width="{tw-1}" height="{th-1}" rx="10" fill="{PANEL}" stroke="{BORDER}"/>'
            f'<rect x="1" y="10" width="3" height="{th-20}" rx="1.5" fill="url(#brand)"/>'
            f'<text x="18" y="36" font-family="{MONO}" font-size="18" font-weight="700" fill="url(#brand)">{i:02d}</text>'
            f'<text x="56" y="35" fill="{TEXT}" font-size="15" font-weight="600">{esc(title)}</text>'
            f'<text x="{tw-18}" y="35" fill="{MUTED}" font-size="15" text-anchor="end">→</text>'
        )
        write(f"sections/toc-{key}.svg", tw, th, toc)


def connect_cards():
    css = "@keyframes glow{0%,100%{opacity:.25}50%{opacity:.6}}.gl{animation:glow 3s ease-in-out infinite}"
    for key, title, handle, color, glyph in CONNECT:
        w, h = 425, 78
        body = (
            f'<rect x=".5" y=".5" width="{w-1}" height="{h-1}" rx="12" fill="{PANEL}" stroke="{BORDER}"/>'
            f'<circle class="gl" cx="44" cy="39" r="24" fill="{color}"/>'
            f'<circle cx="44" cy="39" r="19" fill="{BG}" stroke="{color}" stroke-width="2"/>'
            f'<text x="44" y="45" fill="{color}" font-size="16" font-weight="800" text-anchor="middle">{esc(glyph)}</text>'
            f'<text x="84" y="35" fill="{TEXT}" font-size="16" font-weight="700">{esc(title)}</text>'
            f'<text x="84" y="56" fill="{MUTED}" font-size="12.5" font-family="{MONO}">{esc(handle)}</text>'
            f'<text x="{w-24}" y="45" fill="{color}" font-size="18" text-anchor="end">↗</text>'
        )
        write(f"connect/{key}.svg", w, h, body, css)


# ───────────────────────────── dynamic cards ─────────────────────────────
def streaks(days):
    """days: list of (date, count) sorted ascending. Returns (current, longest, longest_end)."""
    longest = run = 0
    longest_end = None
    for d, c in days:
        run = run + 1 if c > 0 else 0
        if run > longest:
            longest, longest_end = run, d
    current = 0
    for i, (d, c) in enumerate(reversed(days)):
        if c > 0:
            current += 1
        elif i == 0:
            continue  # today with no commits yet doesn't break the streak
        else:
            break
    return current, longest, longest_end


def stats_card(s, today):
    """s: dict with contributions, commits, prs, issues, repos, stars, followers, days, languages."""
    w, h = 860, 290
    current, longest, _ = streaks(s["days"])
    tiles = [
        ("Contributions", s["contributions"], "last 12 months", PURPLE),
        ("Commits", s["commits"], "last 12 months", PINK),
        ("Pull requests", s["prs"], "last 12 months", CYAN),
        ("Own repos", s["repos"], f"public · since {s['since']}", GREEN),
        ("Stars earned", s["stars"], "across my repos", YELLOW),
        ("Followers", s["followers"], "and counting", "#58A6FF"),
    ]
    body = [frame(w, h, "GitHub at a glance", f"refreshed {today:%d %b %Y}")]
    css = [FADE_UP, "@keyframes ring{from{stroke-dashoffset:var(--c)}}"
           ".rg{animation:ring 1.6s cubic-bezier(.2,.7,.2,1) .3s both}"
           "@keyframes grow{from{transform:scaleX(0)}}.gr{transform-origin:left;animation:grow 1.2s cubic-bezier(.2,.7,.2,1) both}"]
    for i, (label, val, sub, col) in enumerate(tiles):
        x, y = 24 + (i % 3) * 132, 62 + (i // 3) * 104
        body.append(
            f'<g class="up" style="animation-delay:{.08 * i:.2f}s">'
            f'<rect x="{x}" y="{y}" width="120" height="92" rx="10" fill="{PANEL}" stroke="{BORDER}"/>'
            f'<rect x="{x}" y="{y + 14}" width="3" height="20" rx="1.5" fill="{col}"/>'
            f'<text x="{x + 14}" y="{y + 29}" fill="{MUTED}" font-size="11.5">{esc(label)}</text>'
            f'<text x="{x + 14}" y="{y + 62}" fill="{TEXT}" font-size="28" font-weight="800">{val:,}</text>'
            f'<text x="{x + 14}" y="{y + 80}" fill="{MUTED}" font-size="10" font-family="{MONO}">{esc(sub)}</text></g>'
        )
    # streak ring
    cx, cy, r = 506, 164, 58
    circ = 2 * math.pi * r
    frac = min(current / max(longest, 1), 1) if longest else 0
    body.append(
        f'<g class="up" style="animation-delay:.4s">'
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{PANEL}" stroke-width="10"/>'
        f'<circle class="rg" cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="url(#brand)" stroke-width="10" stroke-linecap="round" '
        f'stroke-dasharray="{circ:.1f}" stroke-dashoffset="{circ * (1 - frac):.1f}" style="--c:{circ:.1f}" transform="rotate(-90 {cx} {cy})"/>'
        f'<text x="{cx}" y="{cy + 4}" fill="{TEXT}" font-size="34" font-weight="800" text-anchor="middle">{current}</text>'
        f'<text x="{cx}" y="{cy + 24}" fill="{MUTED}" font-size="11" text-anchor="middle">day streak</text>'
        f'<text x="{cx}" y="{cy - r - 20}" fill="{PINK}" font-size="12" font-weight="700" text-anchor="middle">🔥 current streak</text>'
        f'<text x="{cx}" y="{cy + r + 30}" fill="{MUTED}" font-size="12" text-anchor="middle">longest: '
        f'<tspan fill="{TEXT}" font-weight="700">{longest} days</tspan></text></g>'
    )
    # languages
    lx, ly, lw = 610, 72, 226
    langs = s["languages"][:6]
    total = sum(v for _, v, _ in langs) or 1
    body.append(f'<text x="{lx}" y="{ly}" fill="{TEXT}" font-size="13" font-weight="700">Top languages</text>')
    body.append(f'<clipPath id="bar"><rect x="{lx}" y="{ly + 14}" width="{lw}" height="10" rx="5"/></clipPath><g clip-path="url(#bar)" class="gr">')
    bx = lx
    for name, v, color in langs:
        bw = lw * v / total
        body.append(f'<rect x="{bx:.1f}" y="{ly + 14}" width="{bw + .5:.1f}" height="10" fill="{color}"/>')
        bx += bw
    body.append("</g>")
    for i, (name, v, color) in enumerate(langs):
        y = ly + 50 + i * 26
        body.append(
            f'<g class="up" style="animation-delay:{.5 + .07 * i:.2f}s"><circle cx="{lx + 5}" cy="{y - 4}" r="5" fill="{color}"/>'
            f'<text x="{lx + 18}" y="{y}" fill="{TEXT}" font-size="12.5">{esc(name)}</text>'
            f'<text x="{lx + lw}" y="{y}" fill="{MUTED}" font-size="12" font-family="{MONO}" text-anchor="end">{100 * v / total:.1f}%</text></g>'
        )
    write("stats/overview.svg", w, h, "".join(body), "".join(css))


def heatmap(year, days, today):
    """days: list of (date, count) for one calendar year."""
    w, h = 860, 196
    cell, gap = 12, 3
    counts = sorted(c for _, c in days if c > 0)
    q = [counts[int(len(counts) * f)] if counts else 1 for f in (.25, .5, .75)]

    def level(c):
        return 0 if c == 0 else 1 + sum(c > t for t in q)

    total = sum(c for _, c in days)
    active = sum(1 for _, c in days if c > 0)
    months = {}
    for d, c in days:
        months[d.month] = months.get(d.month, 0) + c
    best = max(months, key=months.get) if total else None
    _, longest, _ = streaks(days)
    big = max(days, key=lambda dc: dc[1]) if days else None

    start = date(year, 1, 1)
    offset = (start.weekday() + 1) % 7  # GitHub weeks start on Sunday
    x0, y0 = 50, 64
    body = [frame(w, h, f"{year}", None)]
    stats = f"{total:,} contributions · {active} active days · longest streak {longest}d"
    if best:
        stats += f" · best month {date(year, best, 1):%b}"
    body.append(f'<text x="{w - 24}" y="38" fill="{MUTED}" font-size="12" text-anchor="end">{esc(stats)}</text>')
    for i, lab in enumerate(["Mon", "Wed", "Fri"]):
        body.append(f'<text x="{x0 - 10}" y="{y0 + (1 + 2 * i) * (cell + gap) + 10}" fill="{MUTED}" font-size="10" text-anchor="end">{lab}</text>')
    seen_month = set()
    css = ["@keyframes pop{from{opacity:0;transform:scale(.4)}to{opacity:1;transform:none}}"
           ".c{transform-box:fill-box;transform-origin:center;animation:pop .45s ease-out both}"]
    by_date = dict(days)
    d = start
    while d.year == year:
        idx = (d - start).days + offset
        col, row = idx // 7, idx % 7
        x, y = x0 + col * (cell + gap), y0 + row * (cell + gap)
        if d.day == 1 and d.month not in seen_month:
            seen_month.add(d.month)
            body.append(f'<text x="{x}" y="{y0 - 8}" fill="{MUTED}" font-size="10">{d:%b}</text>')
        if d <= today:
            c = by_date.get(d, 0)
            mark = f' stroke="{YELLOW}" stroke-width="1.5"' if big and d == big[0] and big[1] > 0 else ""
            body.append(
                f'<rect class="c" style="animation-delay:{col * .018:.3f}s" x="{x}" y="{y}" width="{cell}" height="{cell}" rx="2.5" '
                f'fill="{HEAT[level(c)]}"{mark}><title>{d:%d %b}: {c}</title></rect>'
            )
        d += timedelta(days=1)
    ly = h - 20
    body.append(f'<text x="{w - 150}" y="{ly + 9}" fill="{MUTED}" font-size="10" text-anchor="end">less</text>')
    for i, col in enumerate(HEAT):
        body.append(f'<rect x="{w - 144 + i * 15}" y="{ly}" width="11" height="11" rx="2" fill="{col}"/>')
    body.append(f'<text x="{w - 64}" y="{ly + 9}" fill="{MUTED}" font-size="10">more</text>')
    if big and big[1] > 0:
        body.append(
            f'<rect x="{x0}" y="{ly}" width="11" height="11" rx="2" fill="none" stroke="{YELLOW}" stroke-width="1.5"/>'
            f'<text x="{x0 + 18}" y="{ly + 9}" fill="{MUTED}" font-size="10">biggest day: {big[0]:%d %b} · {big[1]} contributions</text>'
        )
    write(f"stats/heatmap-{year}.svg", w, h, "".join(body), "".join(css))


def focus_card(rows, today):
    """rows: list of dicts name, tagline, commits, color, language, pushed (date)."""
    rows = rows[:5]
    w, h = 860, 64 + max(len(rows), 1) * 58 + 10
    body = [frame(w, h, "Current focus", "most commits · last 30 days")]
    css = [FADE_UP, "@keyframes grow{from{transform:scaleX(0)}}.gr{transform-origin:left;transform-box:fill-box;animation:grow 1.1s cubic-bezier(.2,.7,.2,1) both}"]
    top = max((r["commits"] for r in rows), default=1)
    if not rows:
        body.append(f'<text x="24" y="90" fill="{MUTED}" font-size="13">Quiet month in public — the work is happening in private repos.</text>')
    for i, r in enumerate(rows):
        y = 62 + i * 58
        bw = 230 * r["commits"] / top
        body.append(
            f'<g class="up" style="animation-delay:{.1 * i:.1f}s">'
            f'<rect x="16" y="{y}" width="{w - 32}" height="50" rx="9" fill="{PANEL}"/>'
            f'<text x="34" y="{y + 22}" fill="{TEXT}" font-size="14.5" font-weight="700">{esc(r["name"])}</text>'
            f'<text x="34" y="{y + 40}" fill="{MUTED}" font-size="12">{esc(clip(r["tagline"], 58))}</text>'
            f'<circle cx="470" cy="{y + 25}" r="5" fill="{r["color"]}"/>'
            f'<text x="481" y="{y + 29}" fill="{MUTED}" font-size="11.5">{esc(r["language"] or "—")}</text>'
            f'<rect x="570" y="{y + 19}" width="230" height="12" rx="6" fill="{BG}"/>'
            f'<rect class="gr" style="animation-delay:{.15 + .1 * i:.2f}s" x="570" y="{y + 19}" width="{max(bw, 6):.1f}" height="12" rx="6" fill="url(#brand)"/>'
            f'<text x="{w - 30}" y="{y + 30}" fill="{TEXT}" font-size="13" font-weight="700" font-family="{MONO}" text-anchor="end">{r["commits"]}</text>'
            "</g>"
        )
    write("stats/focus.svg", w, h, "".join(body), "".join(css))


def releases_card(rels, today):
    """rels: newest-first list of dicts repo, tag, name, date, notes."""
    w = 860
    if not rels:
        h = 110
        body = [frame(w, h, "Latest releases"),
                f'<text x="24" y="80" fill="{MUTED}" font-size="13">No public releases yet — soon.</text>']
        write("stats/releases.svg", w, h, "".join(body))
        return
    head, rest = rels[0], rels[1:6]
    lines = [l.strip() for l in (head["notes"] or "").splitlines() if l.strip() and not l.strip().startswith("#")]
    bullets = [l.lstrip("-*+ ").strip() for l in lines if l[:2] in ("- ", "* ", "+ ")]
    notes = [n.replace("**", "").replace("`", "") for n in (bullets or lines)][:3]
    h = 214
    body = [frame(w, h, "Latest releases", f"{len(rels)} recent")]
    css = [FADE_UP, "@keyframes ping{0%{r:6;opacity:.8}100%{r:16;opacity:0}}.pg{animation:ping 1.8s ease-out infinite}"]
    body.append(
        f'<g class="up"><rect x="16" y="56" width="420" height="140" rx="10" fill="{PANEL}" stroke="{BORDER}"/>'
        f'<rect x="32" y="72" width="{len(head["tag"]) * 8.5 + 22:.0f}" height="24" rx="12" fill="{GREEN}" fill-opacity=".15" stroke="{GREEN}" stroke-opacity=".6"/>'
        f'<text x="43" y="89" fill="{GREEN}" font-size="12.5" font-weight="700" font-family="{MONO}">{esc(head["tag"])}</text>'
        f'<text x="{len(head["tag"]) * 8.5 + 66:.0f}" y="89" fill="{TEXT}" font-size="15" font-weight="700">{esc(head["repo"])}</text>'
        f'<text x="420" y="89" fill="{MUTED}" font-size="11.5" text-anchor="end">{esc(ago(head["date"], today))}</text>'
    )
    for i, n in enumerate(notes or [clip(head["name"], 60)]):
        body.append(f'<text x="34" y="{122 + i * 22}" fill="{MUTED}" font-size="12.5"><tspan fill="{PURPLE}">▸ </tspan>{esc(clip(n, 60))}</text>')
    body.append("</g>")
    # timeline of older releases
    tx = 470
    body.append(f'<line x1="{tx}" y1="70" x2="{tx}" y2="{70 + max(len(rest) - 1, 0) * 30}" stroke="{BORDER}" stroke-width="2"/>')
    body.append(f'<circle class="pg" cx="{tx}" cy="70" r="6" fill="{GREEN}"/>' if rest else "")
    for i, r in enumerate(rest):
        y = 70 + i * 30
        body.append(
            f'<g class="up" style="animation-delay:{.15 + .1 * i:.2f}s"><circle cx="{tx}" cy="{y}" r="5" fill="{BG}" stroke="{PURPLE}" stroke-width="2"/>'
            f'<text x="{tx + 18}" y="{y + 4}" fill="{TEXT}" font-size="12.5" font-family="{MONO}" font-weight="700">{esc(clip(r["tag"], 12))}</text>'
            f'<text x="{tx + 118}" y="{y + 4}" fill="{MUTED}" font-size="12.5">{esc(clip(r["repo"], 26))}</text>'
            f'<text x="{w - 28}" y="{y + 4}" fill="{MUTED}" font-size="11.5" text-anchor="end">{r["date"]:%d %b %Y}</text></g>'
        )
    write("stats/releases.svg", w, h, "".join(body), "".join(css))


def project_card(p, today):
    """p: dict name, tagline, language, color, stars, pushed (date|None), live (bool), private (bool)."""
    w, h = 425, 158
    body = [
        f'<rect x=".5" y=".5" width="{w-1}" height="{h-1}" rx="12" fill="{PANEL}" stroke="{BORDER}"/>',
        f'<rect x="1" y="1" width="{w-2}" height="3" rx="1.5" fill="url(#brand)" opacity=".8"/>',
        f'<text x="22" y="40" fill="{TEXT}" font-size="17" font-weight="700">{esc(clip(p["name"], 30))}</text>',
    ]
    badge, bcol = ("🔒 private", MUTED) if p.get("private") else (("● live", GREEN) if p.get("live") else ("repo", PURPLE))
    bw = len(badge) * 7 + 18
    body.append(
        f'<rect x="{w - 20 - bw}" y="22" width="{bw}" height="24" rx="12" fill="{bcol}" fill-opacity=".12" stroke="{bcol}" stroke-opacity=".5"/>'
        f'<text x="{w - 20 - bw / 2}" y="38.5" fill="{bcol}" font-size="11.5" font-weight="600" text-anchor="middle">{esc(badge)}</text>'
    )
    for i, line in enumerate(wrap(p["tagline"], 54, 2)):
        body.append(f'<text x="22" y="{70 + i * 20}" fill="{MUTED}" font-size="13">{esc(line)}</text>')
    fy = h - 24
    meta = f'<circle cx="27" cy="{fy - 4}" r="5" fill="{p.get("color") or MUTED}"/>' \
           f'<text x="38" y="{fy}" fill="{MUTED}" font-size="12">{esc(p.get("language") or "—")}</text>'
    if not p.get("private"):
        meta += f'<text x="150" y="{fy}" fill="{MUTED}" font-size="12">★ {p.get("stars", 0)}</text>'
    if p.get("pushed"):
        meta += f'<text x="{w - 22}" y="{fy}" fill="{MUTED}" font-size="12" text-anchor="end">updated {esc(ago(p["pushed"], today))}</text>'
    body.append(meta)
    write(f"projects/{p['name']}.svg", w, h, "".join(body))


def splitter():
    css = "@keyframes mv{0%{transform:translateX(-200px)}100%{transform:translateX(1060px)}}.mv{animation:mv 6s linear infinite}"
    body = (
        f'<rect x="0" y="9" width="860" height="1" fill="{BORDER}"/>'
        f'<rect class="mv" x="0" y="8" width="200" height="3" rx="1.5" fill="url(#brand)"/>'
        f'<circle cx="430" cy="9.5" r="4" fill="{BG}" stroke="{PURPLE}" stroke-width="2"/>'
    )
    write("sections/splitter.svg", 860, 20, body, css)


def build_static():
    splitter()
    section_headers()
    connect_cards()


def build_all(data, today):
    build_static()
    stats_card(data["stats"], today)
    for year, days in data["years"].items():
        heatmap(year, days, today)
    focus_card(data["focus"], today)
    releases_card(data["releases"], today)
    for p in data["projects"]:
        project_card(p, today)


if __name__ == "__main__":
    build_static()
    print("static cards rebuilt")
