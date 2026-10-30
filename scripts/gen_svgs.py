"""Generates the animated SVGs for the GitHub profile README.

All animation is CSS inside the SVG (works when GitHub serves it through <img>).
Usage: python scripts/gen_svgs.py [out_dir]   (default: assets)
scripts/update_readme.py calls terminal() with live GitHub data.
"""
import sys
from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path("assets")

BG, PANEL, BORDER = "#0d1117", "#161b22", "#30363d"
PURPLE, VIOLET, PINK, CYAN, GREEN, YELLOW = "#A855F7", "#7C3AED", "#EC4899", "#22D3EE", "#3FB950", "#E3B341"
TEXT, MUTED = "#E6EDF3", "#8B949E"
MONO = "Consolas, 'SF Mono', Menlo, 'DejaVu Sans Mono', 'Courier New', monospace"
SANS = "'Segoe UI', Ubuntu, -apple-system, Helvetica, Arial, sans-serif"
CW = 8.4  # forced monospace advance (via textLength) so typing covers line up everywhere


class Anim:
    """Builds per-element looping keyframes on one shared cycle."""

    def __init__(self, cycle):
        self.cycle, self.css, self.n = cycle, [], 0

    def pct(self, t):
        return f"{min(max(t / self.cycle * 100, 0), 100):.3f}%"

    def _name(self):
        self.n += 1
        return f"k{self.n}"

    def appear(self, start, fade=0.25, end=None):
        """Class that is hidden until `start`, then visible until `end` (default: cycle end)."""
        name = self._name()
        end = end if end is not None else self.cycle - 0.4
        self.css.append(
            f"@keyframes {name}{{0%,{self.pct(start)}{{opacity:0}}"
            f"{self.pct(start + fade)},{self.pct(end)}{{opacity:1}}"
            f"{self.pct(end + 0.3)},100%{{opacity:0}}}}"
            f".{name}{{opacity:0;animation:{name} {self.cycle}s linear infinite}}"
        )
        return name

    def type(self, start, chars, per_char=0.06):
        """Class for a cover rect / cursor that slides right in `chars` steps."""
        name = self._name()
        dur = chars * per_char
        dist = chars * CW
        self.css.append(
            f"@keyframes {name}{{0%,{self.pct(start)}{{transform:translateX(0);animation-timing-function:steps({chars},end)}}"
            f"{self.pct(start + dur)},100%{{transform:translateX({dist:.1f}px)}}}}"
            f".{name}{{animation:{name} {self.cycle}s linear infinite}}"
        )
        return name, start + dur

    def style(self, extra=""):
        return f"<style>{''.join(self.css)}{extra}</style>"


def mono_text(x, y, spans, size=14, cls="", weight=None):
    """spans: list of (text, color). Each span gets an exact width so columns align."""
    out, cx = [], x
    for txt, color in spans:
        if not txt:
            continue
        w = len(txt) * CW
        fw = f' font-weight="{weight}"' if weight else ""
        out.append(
            f'<text x="{cx:.1f}" y="{y}" fill="{color}" font-size="{size}"{fw} '
            f'textLength="{w:.1f}" lengthAdjust="spacingAndGlyphs" xml:space="preserve">{escape(txt)}</text>'
        )
        cx += w
    c = f' class="{cls}"' if cls else ""
    return f"<g{c}>{''.join(out)}</g>"


def window(w, h, title):
    return (
        f'<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="12" fill="{BG}" stroke="{BORDER}"/>'
        f'<path d="M1 13 a12 12 0 0 1 12 -12 h{w-26} a12 12 0 0 1 12 12 v25 h-{w-2} z" fill="{PANEL}"/>'
        f'<line x1="1" y1="38" x2="{w-1}" y2="38" stroke="{BORDER}"/>'
        f'<circle cx="22" cy="20" r="6" fill="#FF5F57"/><circle cx="42" cy="20" r="6" fill="#FEBC2E"/>'
        f'<circle cx="62" cy="20" r="6" fill="#28C840"/>'
        f'<text x="{w/2}" y="24.5" fill="{MUTED}" font-size="13" text-anchor="middle" font-family="{SANS}">{escape(title)}</text>'
    )


def typed_line(a, x, y, prompt, cmd, start, bg):
    """A prompt plus a command that types itself, with a moving block cursor."""
    p_w = len(prompt) * CW
    cover, done = a.type(start, len(cmd) + 1)
    vis = a.appear(start - 0.3, fade=0.1)
    cur_vis = a.appear(start - 0.3, fade=0.05, end=done + 0.35)
    cx = x + p_w
    svg = (
        f'<g class="{vis}">'
        + mono_text(x, y, [("yash", GREEN), ("@", MUTED), ("dev", CYAN), (":", MUTED), ("~", PURPLE), ("$ ", MUTED)])
        + mono_text(cx, y, [(cmd, TEXT)])
        + f'<rect class="{cover}" x="{cx:.1f}" y="{y-15}" width="{(len(cmd)+2)*CW:.1f}" height="21" fill="{bg}"/>'
        + "</g>"
        + f'<g class="{cur_vis}"><rect class="{cover}" x="{cx:.1f}" y="{y-14}" width="{CW:.1f}" height="18" fill="{PURPLE}"/></g>'
    )
    return svg, done


# ─────────────────────────────── terminal.svg ───────────────────────────────
DEFAULT_NOW = [
    ("feature-planner", "Claude Code plugin · plans features before you build"),
    ("search-auditor", "e-commerce search-relevance testing harness"),
    ("draftly", "rich-text document workspace with sharing"),
]


def terminal(now=DEFAULT_NOW, status="Building something cool..."):
    """`now`: up to 3 (repo, tagline) rows; `status`: the neofetch Status value."""
    W, H, CYCLE = 860, 520, 18
    tbg = "#0b0f17"
    a = Anim(CYCLE)
    body = []
    x0 = 28
    line1, t = typed_line(a, x0, 72, "yash@dev:~$ ", "neofetch", 0.6, tbg)
    body.append(line1)

    # pixel-art "YP" logo: rects instead of box-drawing glyphs, which render differently per font
    art = [
        "X...X.XXXX.",
        "X...X.X...X",
        ".X.X..X...X",
        "..X...XXXX.",
        "..X...X....",
        "..X...X....",
        "..X...X....",
    ]
    show = t + 0.4
    px, ax, ay = 16, x0 + 14, 112
    body.append(f'<g class="{a.appear(show, 0.5)}">')
    for r, row in enumerate(art):
        for c, ch in enumerate(row):
            if ch == "X":
                body.append(f'<rect x="{ax + c*px}" y="{ay + r*px}" width="{px-3}" height="{px-3}" rx="2" fill="url(#art)"/>')
    body.append(
        f'<text x="{ax + len(art[0])*px/2 - 1.5}" y="{ay + len(art)*px + 34}" fill="{MUTED}" font-size="12" text-anchor="middle" '
        f'font-family="{MONO}" letter-spacing="3">YASH.DEV</text>'
    )
    body.append("</g>")

    ix = 250
    info = [
        [("yash", PURPLE), ("@", MUTED), ("github", PURPLE)],
        [("─" * 30, BORDER)],
        [("Name      ", CYAN), ("Yash Sanjay Patil", TEXT)],
        [("Role      ", CYAN), ("Full-Stack Developer", TEXT)],
        [("Company   ", CYAN), ("Smarter Codes", TEXT)],
        [("Location  ", CYAN), ("Navi Mumbai, India", TEXT)],
        [("Shell     ", CYAN), ("TypeScript · Python", TEXT)],
        [("Frontend  ", CYAN), ("React · Next.js · Nuxt.js", TEXT)],
        [("Backend   ", CYAN), ("Django · FastAPI · Node.js", TEXT)],
        [("AI        ", CYAN), ("LLMs · NLP · Claude Code plugins", TEXT)],
        [("Focus     ", CYAN), ("AI + Developer Tools", TEXT)],
        [("Status    ", CYAN), ("● ", GREEN), (status[:58], GREEN)],
    ]
    for i, spans in enumerate(info):
        cls = a.appear(show + 0.1 + i * 0.11, 0.2)
        body.append(f'<g font-family="{MONO}">' + mono_text(ix, 104 + i * 22, spans, cls=cls, weight="600" if i == 0 else None) + "</g>")
    palette = [BG, "#FF5F57", GREEN, YELLOW, "#58A6FF", PURPLE, CYAN, TEXT]
    pc = a.appear(show + 0.1 + len(info) * 0.11, 0.3)
    body.append(f'<g class="{pc}">' + "".join(
        f'<rect x="{ix + i*30}" y="{104 + len(info)*22 - 8}" width="28" height="16" rx="2" fill="{c}" stroke="{BORDER}"/>'
        for i, c in enumerate(palette)) + "</g>")

    line2, t2 = typed_line(a, x0, 410, "yash@dev:~$ ", "./now --top 3", show + 2.6, tbg)
    body.append(f'<g font-family="{MONO}">{line2}</g>')
    now = [(n[:17].ljust(19), d[:53]) for n, d in now[:3]]
    for i, (name, desc) in enumerate(now):
        cls = a.appear(t2 + 0.35 + i * 0.25, 0.2)
        body.append(f'<g font-family="{MONO}">' + mono_text(x0 + 16, 436 + i * 22, [("▸ ", PINK), (name, PURPLE), (desc, MUTED)], cls=cls) + "</g>")

    end_t = t2 + 0.35 + len(now) * 0.25 + 0.4
    fin = a.appear(end_t, 0.1)
    p_w = len("yash@dev:~$ ") * CW
    body.append(
        f'<g class="{fin}" font-family="{MONO}">'
        + mono_text(x0, 506, [("yash", GREEN), ("@", MUTED), ("dev", CYAN), (":", MUTED), ("~", PURPLE), ("$ ", MUTED)])
        + f'<rect class="blink" x="{x0 + p_w:.1f}" y="492" width="{CW:.1f}" height="18" fill="{PURPLE}"/></g>'
    )

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H + 10}" viewBox="0 0 {W} {H + 10}" font-family="{MONO}">'
        f'<defs><linearGradient id="art" gradientUnits="userSpaceOnUse" x1="40" y1="110" x2="220" y2="230">'
        f'<stop offset="0" stop-color="{PINK}"/><stop offset=".5" stop-color="{PURPLE}"/><stop offset="1" stop-color="{CYAN}"/></linearGradient></defs>'
        + a.style("@keyframes bl{0%,49%{opacity:1}50%,100%{opacity:0}}.blink{animation:bl 1s step-end infinite}")
        + window(W, H + 10, "yash@dev: ~ — zsh").replace(f'fill="{BG}"', f'fill="{tbg}"', 1)
        + "".join(body)
        + "</svg>"
    )
    (OUT / "terminal.svg").write_text(svg, encoding="utf-8")


# ──────────────────────────────── editor.svg ────────────────────────────────
def editor():
    W, H, CYCLE = 860, 600, 20
    ebg = "#1a1b26"
    KW, TY, STR, CMT, PROP, PUN, FN = PINK, CYAN, "#9ECE6A", "#565F89", "#C0CAF5", "#89DDFF", "#7AA2F7"
    code = [
        [("// yash.ts — who I am, compiled to TypeScript", CMT)],
        [],
        [("interface ", KW), ("Developer", TY), (" {", PUN)],
        [("  name", PROP), (": ", PUN), ("string", TY), (";", PUN)],
        [("  role", PROP), (": ", PUN), ("string", TY), (";", PUN)],
        [("  stack", PROP), (": ", PUN), ("string", TY), ("[];", PUN)],
        [("  mission", PROP), (": ", PUN), ("string", TY), (";", PUN)],
        [("}", PUN)],
        [],
        [("export const ", KW), ("yash", FN), (": ", PUN), ("Developer", TY), (" = {", PUN)],
        [("  name", PROP), (": ", PUN), ('"Yash Sanjay Patil"', STR), (",", PUN)],
        [("  role", PROP), (": ", PUN), ('"Full-Stack Developer @ Smarter Codes"', STR), (",", PUN)],
        [("  stack", PROP), (": ", PUN), ("[", PUN), ('"TypeScript"', STR), (", ", PUN), ('"Python"', STR), (", ", PUN),
         ('"React"', STR), (", ", PUN), ('"Django"', STR), (", ", PUN), ('"FastAPI"', STR), ("],", PUN)],
        [("  mission", PROP), (": ", PUN), ('"Build tools that make developers\' lives easier"', STR), (",", PUN)],
        [("};", PUN)],
    ]
    a = Anim(CYCLE)
    body = []
    gx, cx, top, lh = 66, 112, 98, 22
    t = 0.5
    for i, spans in enumerate(code):
        y = top + i * lh
        n = sum(len(s) for s, _ in spans)
        vis = a.appear(t - 0.05, 0.05)
        body.append(f'<text class="{vis}" x="{gx + 30}" y="{y}" fill="{MUTED}" font-size="13" text-anchor="end">{i + 1}</text>')
        if n:
            cover, done = a.type(t, n + 1, per_char=0.028)
            body.append(
                f'<g class="{vis}">' + mono_text(cx, y, spans)
                + f'<rect class="{cover}" x="{cx}" y="{y - 15}" width="{(n + 2) * CW:.1f}" height="21" fill="{ebg}"/></g>'
            )
            cur = a.appear(t - 0.05, 0.02, end=done + 0.05)
            body.append(f'<g class="{cur}"><rect class="{cover}" x="{cx}" y="{y - 14}" width="2" height="18" fill="{PURPLE}"/></g>')
            t = done + 0.12
        else:
            t += 0.15
    code_end = t

    # integrated terminal panel
    py = top + len(code) * lh + 8
    body.append(
        f'<line x1="48" y1="{py}" x2="{W - 1}" y2="{py}" stroke="{BORDER}"/>'
        f'<text x="{cx - 40}" y="{py + 22}" fill="{TEXT}" font-size="11" font-family="{SANS}" letter-spacing="1">TERMINAL</text>'
        f'<line x1="{cx - 40}" y1="{py + 28}" x2="{cx + 22}" y2="{py + 28}" stroke="{PURPLE}" stroke-width="2"/>'
        f'<text x="{cx + 40}" y="{py + 22}" fill="{MUTED}" font-size="11" font-family="{SANS}" letter-spacing="1">PROBLEMS</text>'
        f'<text x="{cx + 128}" y="{py + 22}" fill="{MUTED}" font-size="11" font-family="{SANS}" letter-spacing="1">OUTPUT</text>'
    )
    run, rdone = a.type(code_end + 0.5, 11, per_char=0.06)
    rv = a.appear(code_end + 0.4, 0.1)
    ry = py + 54
    body.append(
        f'<g class="{rv}">' + mono_text(cx - 40, ry, [("$ ", GREEN)]) + mono_text(cx - 40 + 2 * CW, ry, [("pnpm build", TEXT)])
        + f'<rect class="{run}" x="{cx - 40 + 2 * CW:.1f}" y="{ry - 15}" width="{12 * CW:.1f}" height="21" fill="{ebg}"/></g>'
    )
    out = [
        [("✓ ", GREEN), ("yash.ts compiled successfully — 0 errors, 0 warnings", TEXT)],
        [("▶ ", PURPLE), ("ready to ship ideas to production", MUTED)],
    ]
    for i, spans in enumerate(out):
        cls = a.appear(rdone + 0.4 + i * 0.35, 0.2)
        body.append(mono_text(cx - 40, ry + 24 + i * 22, spans, cls=cls))

    # status bar
    sy = H - 26
    body.append(
        f'<path d="M1 {sy} h{W - 2} v13 a12 12 0 0 1 -12 12 h-{W - 26} a12 12 0 0 1 -12 -12 z" fill="{VIOLET}"/>'
        f'<g font-family="{SANS}" font-size="12" fill="#fff" xml:space="preserve">'
        f'<text x="16" y="{sy + 17}">⎇ main</text><text x="90" y="{sy + 17}">✓ 0 problems</text>'
        f'<text x="{W - 16}" y="{sy + 17}" text-anchor="end">Ln 15, Col 3    UTF-8    TypeScript    ♥ Prettier</text></g>'
    )

    # activity bar + tabs
    act = (
        f'<rect x="1" y="38" width="47" height="{sy - 38}" fill="{PANEL}"/>'
        f'<line x1="48" y1="38" x2="48" y2="{sy}" stroke="{BORDER}"/>'
        f'<rect x="1" y="50" width="2" height="26" fill="{PURPLE}"/>'
        f'<g fill="none" stroke="{TEXT}" stroke-width="1.6" stroke-linejoin="round">'
        f'<path d="M16 54 h10 l6 6 v14 h-16 z"/></g>'
        f'<g fill="none" stroke="{MUTED}" stroke-width="1.6"><circle cx="23" cy="106" r="6"/><path d="M27.5 110.5 L33 116"/>'
        f'<circle cx="19" cy="146" r="2.5"/><circle cx="19" cy="162" r="2.5"/><circle cx="29" cy="152" r="2.5"/>'
        f'<path d="M19 148.5 v11 M19 152 h7.5"/>'
        f'<rect x="15" y="190" width="7" height="7"/><rect x="25" y="190" width="7" height="7"/><rect x="15" y="200" width="7" height="7"/>'
        f'<rect x="25" y="200" width="7" height="7" transform="rotate(20 28.5 203.5)"/></g>'
    )
    tabs = (
        f'<rect x="48" y="39" width="{W - 49}" height="34" fill="{PANEL}"/>'
        f'<rect x="48" y="39" width="124" height="34" fill="{ebg}"/>'
        f'<line x1="48" y1="39.5" x2="172" y2="39.5" stroke="{PURPLE}" stroke-width="2"/>'
        f'<text x="62" y="61" fill="#3178C6" font-size="11" font-weight="700" font-family="{SANS}">TS</text>'
        f'<text x="82" y="61" fill="{TEXT}" font-size="13" font-family="{SANS}">yash.ts</text>'
        f'<text x="152" y="61" fill="{MUTED}" font-size="13" font-family="{SANS}">×</text>'
        f'<text x="190" y="61" fill="{YELLOW}" font-size="11" font-weight="700" font-family="{SANS}">{{}}</text>'
        f'<text x="208" y="61" fill="{MUTED}" font-size="13" font-family="{SANS}">skills.json</text>'
        f'<text x="300" y="61" fill="{CYAN}" font-size="11" font-weight="700" font-family="{SANS}">M↓</text>'
        f'<text x="322" y="61" fill="{MUTED}" font-size="13" font-family="{SANS}">README.md</text>'
        f'<line x1="48" y1="73" x2="{W - 1}" y2="73" stroke="{BORDER}"/>'
    )

    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{MONO}">'
        + a.style()
        + window(W, H, "yash.ts — portfolio — Visual Studio Code").replace(f'fill="{BG}"', f'fill="{ebg}"', 1)
        + act + tabs + "".join(body)
        + "</svg>"
    )
    (OUT / "editor.svg").write_text(svg, encoding="utf-8")


# ─────────────────────────────── timeline.svg ───────────────────────────────
def timeline():
    entries = [
        ("2022", "Hello, World", "C, DSA, Java & Python fundamentals", "First ML project: car price prediction"),
        ("2023", "Into the Data", "Data science, NLP, deep learning, Power BI", "B.E. project: smarter school-bus routing"),
        ("2024", "Applied AI", "Android botnet detection with ML", "Llama-2 blog generator · first dev job"),
        ("2025", "Shipping Products", "Django · FastAPI · Next.js · Node.js", "xmlToJson · Tags2Braces · DomSearch"),
        ("2026", "AI Developer Tools", "Claude Code plugins & search-quality tooling", "feature-planner · draftly · search-auditor"),
    ]
    W, step, top = 860, 108, 40
    H = top + len(entries) * step + 70
    CYCLE = 16
    a = Anim(CYCLE)
    cx = W / 2
    line_len = len(entries) * step + 10
    body = []
    draw = "draw"
    css_extra = (
        f"@keyframes {draw}{{0%{{stroke-dashoffset:{line_len}}}25%,97%{{stroke-dashoffset:0}}100%{{stroke-dashoffset:{line_len}}}}}"
        f".{draw}{{stroke-dasharray:{line_len};stroke-dashoffset:{line_len};animation:{draw} {CYCLE}s ease-out infinite}}"
        "@keyframes pulse{0%{r:7;opacity:.7}100%{r:20;opacity:0}}.pulse{animation:pulse 1.8s ease-out infinite}"
        "@keyframes bl{0%,49%{opacity:1}50%,100%{opacity:0}}.blink{animation:bl 1.1s step-end infinite}"
    )
    body.append(f'<line x1="{cx}" y1="{top}" x2="{cx}" y2="{top + line_len}" stroke="{BORDER}" stroke-width="3"/>')
    body.append(f'<line class="{draw}" x1="{cx}" y1="{top}" x2="{cx}" y2="{top + line_len}" stroke="url(#tl)" stroke-width="3" stroke-linecap="round"/>')
    for i, (year, title, l1, l2) in enumerate(entries):
        y = top + 50 + i * step
        t = 0.5 + i * 0.75
        vis = a.appear(t, 0.45)
        left = i % 2 == 0
        cw_, ch = 360, 84
        x = cx - 34 - cw_ if left else cx + 34
        tx = x + 20
        conn = (cx - 34, cx - 8) if left else (cx + 8, cx + 34)
        body.append(
            f'<g class="{vis}">'
            f'<circle class="pulse" cx="{cx}" cy="{y}" r="7" fill="{PURPLE}"/>'
            f'<circle cx="{cx}" cy="{y}" r="8" fill="{BG}" stroke="{PURPLE}" stroke-width="3"/>'
            f'<circle cx="{cx}" cy="{y}" r="3" fill="{PINK}"/>'
            f'<line x1="{conn[0]}" y1="{y}" x2="{conn[1]}" y2="{y}" stroke="{PURPLE}" stroke-width="2" stroke-dasharray="3 3"/>'
            f'<rect x="{x}" y="{y - ch/2}" width="{cw_}" height="{ch}" rx="10" fill="{PANEL}" stroke="{BORDER}"/>'
            f'<rect x="{x}" y="{y - ch/2}" width="4" height="{ch}" rx="2" fill="url(#tl)"/>'
            f'<text x="{tx}" y="{y - 14}" font-family="{MONO}" font-size="14" font-weight="700" fill="{PURPLE}">{year}</text>'
            f'<text x="{tx + 50}" y="{y - 14}" font-family="{SANS}" font-size="15" font-weight="700" fill="{TEXT}">{escape(title)}</text>'
            f'<text x="{tx}" y="{y + 9}" font-family="{SANS}" font-size="12.5" fill="{MUTED}">{escape(l1)}</text>'
            f'<text x="{tx}" y="{y + 28}" font-family="{SANS}" font-size="12.5" fill="{CYAN}">{escape(l2)}</text>'
            "</g>"
        )
    fy = top + line_len + 22
    fv = a.appear(0.5 + len(entries) * 0.75, 0.4)
    body.append(
        f'<g class="{fv}"><text x="{cx}" y="{fy}" text-anchor="middle" font-family="{MONO}" font-size="13" fill="{MUTED}">'
        f'next: <tspan fill="{PURPLE}">loading</tspan><tspan class="blink" fill="{PURPLE}">_</tspan></text></g>'
    )
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
        f'<defs><linearGradient id="tl" gradientUnits="userSpaceOnUse" x1="0" y1="{top}" x2="0" y2="{top + line_len}"><stop offset="0" stop-color="{PINK}"/>'
        f'<stop offset=".5" stop-color="{PURPLE}"/><stop offset="1" stop-color="{CYAN}"/></linearGradient></defs>'
        + a.style(css_extra)
        + f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="12" fill="{BG}" stroke="{BORDER}"/>'
        + "".join(body) + "</svg>"
    )
    (OUT / "timeline.svg").write_text(svg, encoding="utf-8")


# ───────────────────────────────── hero.svg ─────────────────────────────────
def hero():
    W, H = 860, 300
    css = (
        "@keyframes drift1{0%,100%{transform:translate(0,0)}50%{transform:translate(60px,30px)}}"
        "@keyframes drift2{0%,100%{transform:translate(0,0)}50%{transform:translate(-70px,-20px)}}"
        ".o1{animation:drift1 9s ease-in-out infinite}.o2{animation:drift2 11s ease-in-out infinite}"
        "@keyframes ping{0%{r:5;opacity:.8}100%{r:13;opacity:0}}.ping{animation:ping 1.6s ease-out infinite}"
        "@keyframes up{0%{opacity:0;transform:translateY(14px)}100%{opacity:1;transform:translateY(0)}}"
        ".u1,.u2,.u3,.u4{opacity:0;animation:up .9s cubic-bezier(.2,.7,.2,1) forwards}"
        ".u1{animation-delay:.1s}.u2{animation-delay:.35s}.u3{animation-delay:.7s}.u4{animation-delay:1s}"
        "@keyframes scan{0%{transform:translateY(-40px)}100%{transform:translateY(340px)}}.scan{animation:scan 6s linear infinite}"
    )
    grid = "".join(f'<line x1="{x}" y1="0" x2="{x}" y2="{H}"/>' for x in range(0, W + 1, 40)) + "".join(
        f'<line x1="0" y1="{y}" x2="{W}" y2="{y}"/>' for y in range(0, H + 1, 40))
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">'
        "<defs>"
        f'<linearGradient id="name" x1="0" y1="0" x2="1" y2="0" spreadMethod="repeat">'
        f'<stop offset="0" stop-color="{PINK}"/><stop offset=".33" stop-color="{PURPLE}"/><stop offset=".66" stop-color="{CYAN}"/><stop offset="1" stop-color="{PINK}"/>'
        f'<animateTransform attributeName="gradientTransform" type="translate" values="-1 0;0 0" dur="5s" repeatCount="indefinite"/>'
        f'</linearGradient>'
        f'<radialGradient id="g1"><stop offset="0" stop-color="{PURPLE}" stop-opacity=".55"/><stop offset="1" stop-color="{PURPLE}" stop-opacity="0"/></radialGradient>'
        f'<radialGradient id="g2"><stop offset="0" stop-color="{CYAN}" stop-opacity=".35"/><stop offset="1" stop-color="{CYAN}" stop-opacity="0"/></radialGradient>'
        f'<linearGradient id="sc" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{PURPLE}" stop-opacity="0"/><stop offset="1" stop-color="{PURPLE}" stop-opacity=".18"/></linearGradient>'
        f'<clipPath id="c"><rect x="1" y="1" width="{W-2}" height="{H-2}" rx="14"/></clipPath>'
        "</defs>"
        f"<style>{css}</style>"
        f'<g clip-path="url(#c)">'
        f'<rect width="{W}" height="{H}" fill="{BG}"/>'
        f'<circle class="o1" cx="170" cy="70" r="230" fill="url(#g1)"/>'
        f'<circle class="o2" cx="720" cy="250" r="220" fill="url(#g2)"/>'
        f'<g stroke="{PURPLE}" stroke-opacity=".09">{grid}</g>'
        f'<rect class="scan" x="0" y="0" width="{W}" height="40" fill="url(#sc)"/>'
        "</g>"
        f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="14" fill="none" stroke="{BORDER}"/>'
        # availability pill
        f'<g class="u1"><rect x="{W/2 - 112}" y="36" width="224" height="30" rx="15" fill="{GREEN}" fill-opacity=".1" stroke="{GREEN}" stroke-opacity=".5"/>'
        f'<circle class="ping" cx="{W/2 - 90}" cy="51" r="5" fill="{GREEN}"/><circle cx="{W/2 - 90}" cy="51" r="4.5" fill="{GREEN}"/>'
        f'<text x="{W/2 + 8}" y="56" text-anchor="middle" font-family="{SANS}" font-size="13.5" font-weight="600" fill="{GREEN}">Available for collaboration</text></g>'
        # name
        f'<g class="u2"><text x="{W/2}" y="142" text-anchor="middle" font-family="{SANS}" font-size="78" font-weight="800" letter-spacing="2" fill="url(#name)">YASH<tspan fill="{TEXT}">.</tspan>DEV</text></g>'
        f'<g class="u3"><text x="{W/2}" y="180" text-anchor="middle" font-family="{MONO}" font-size="14" letter-spacing="6" fill="{PURPLE}">FULL STACK  +  AI</text></g>'
        f'<g class="u4"><text x="{W/2}" y="225" text-anchor="middle" font-family="{SANS}" font-size="24" font-weight="700" fill="{TEXT}">Building things that make developers’ lives easier.</text>'
        f'<text x="{W/2}" y="260" text-anchor="middle" font-family="{MONO}" font-size="14" fill="{MUTED}">'
        f'Code <tspan fill="{PURPLE}">·</tspan> Systems <tspan fill="{PURPLE}">·</tspan> AI <tspan fill="{PURPLE}">·</tspan> Open Source</text></g>'
        "</svg>"
    )
    (OUT / "hero.svg").write_text(svg, encoding="utf-8")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        OUT = Path(sys.argv[1])
    OUT.mkdir(parents=True, exist_ok=True)
    hero()
    terminal()
    editor()
    timeline()
    print("wrote", *sorted(p.name for p in OUT.glob("*.svg")))
