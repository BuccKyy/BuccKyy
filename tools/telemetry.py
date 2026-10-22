#!/usr/bin/env python3
"""Render assets/telemetry.svg for the BuccKyy profile from the GitHub GraphQL API.

Local:   GITHUB_TOKEN=$(gh auth token) python tools/telemetry.py
Action:  GITHUB_TOKEN is provided by the workflow.

Every glyph is converted to a path, so the SVG has no font dependency at render
time. Only ASCII is used, which keeps the committed subset fonts tiny.
"""
from __future__ import annotations

import base64
import pathlib
import json
import os
import sys
import urllib.request
from datetime import date, datetime, timezone

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(ROOT, "tools", "fonts")

VOID = "#12061F"
NAVY = "#1A0830"
STEEL = "#8A3A8F"
MIST = "#EAEAEA"
DIM = "#C9A4E8"
PERI = "#FF9A5C"
CYAN = "#FFB347"
CYAN_HOT = "#7FE7FF"
GOLD = "#C8A44D"

LOGIN = os.environ.get("GITHUB_LOGIN", "BuccKyy")
OUT = os.path.join(ROOT, "assets", "telemetry.svg")

QUERY = """
query($login: String!) {
  user(login: $login) {
    followers { totalCount }
    repositories(first: 100, ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC) {
      totalCount
      nodes { stargazerCount primaryLanguage { name } }
    }
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""


class Face:
    def __init__(self, filename: str) -> None:
        font = TTFont(os.path.join(FONTS, filename))
        self.scale = 1.0 / font["head"].unitsPerEm
        self.glyphs = font.getGlyphSet()
        self.cmap = font.getBestCmap()


BAR_LIGHT = Face("BarlowCondensed-Light.ttf")
BAR_REG = Face("BarlowCondensed-Regular.ttf")
BAR_MED = Face("BarlowCondensed-Medium.ttf")
MONO = Face("IBMPlexMono-Regular.ttf")


def measure(string: str, size: float, tracking: float, face: Face) -> float:
    width = 0.0
    for ch in string:
        name = face.cmap.get(ord(ch))
        if name:
            width += face.glyphs[name].width * face.scale * size
        width += tracking
    return width - tracking if string else 0.0


def text(string: str, x: float, y: float, size: float, *, face: Face = BAR_REG,
         fill: str = MIST, tracking: float = 0.0, opacity: float = 1.0,
         anchor: str = "start") -> str:
    if face is MONO:
        size *= 1.3  # mono labels were too small once the SVG is scaled to column width
    if anchor == "middle":
        x -= measure(string, size, tracking, face) / 2
    elif anchor == "end":
        x -= measure(string, size, tracking, face)
    cursor = x
    parts = []
    for ch in string:
        name = face.cmap.get(ord(ch))
        if not name:
            cursor += size * 0.5 + tracking
            continue
        glyph = face.glyphs[name]
        pen = SVGPathPen(face.glyphs)
        glyph.draw(pen)
        d = pen.getCommands()
        if d:
            parts.append(
                f'<path d="{d}" transform="translate({cursor:.2f} {y:.2f}) '
                f'scale({size * face.scale:.5f} {(-size * face.scale):.5f})"/>'
            )
        cursor += glyph.width * face.scale * size + tracking
    if not parts:
        return ""
    return f'<g fill="{fill}" opacity="{opacity}">' + "".join(parts) + "</g>"


def fetch() -> dict:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        sys.exit("GITHUB_TOKEN is required (try: GITHUB_TOKEN=$(gh auth token))")
    body = json.dumps({"query": QUERY, "variables": {"login": LOGIN}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={
            "Authorization": f"bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "BuccKyy-profile-telemetry",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        payload = json.loads(response.read())
    if "errors" in payload:
        sys.exit(f"GraphQL error: {payload['errors']}")
    user = payload["data"]["user"]
    # "Make profile private" makes the API report zero contributions, so keep
    # the last real calendar and reuse it instead of drawing an empty heatmap.
    cache = pathlib.Path(__file__).parent / "calendar_cache.json"
    cal = user["contributionsCollection"]["contributionCalendar"]
    if cal["totalContributions"] > 0:
        cache.write_text(json.dumps(cal))
    elif cache.exists():
        user["contributionsCollection"]["contributionCalendar"] = json.loads(cache.read_text())
    return user


def streaks(days: list[dict]) -> tuple[int, int]:
    days = sorted(days, key=lambda d: d["date"])
    current = 0
    index = len(days) - 1
    today = datetime.now(timezone.utc).date().isoformat()
    if index >= 0 and days[index]["contributionCount"] == 0 and days[index]["date"] == today:
        index -= 1
    while index >= 0 and days[index]["contributionCount"] > 0:
        current += 1
        index -= 1
    best = run = 0
    for day in days:
        if day["contributionCount"] > 0:
            run += 1
            best = max(best, run)
        else:
            run = 0
    return current, best


def languages(nodes: list[dict]) -> list[tuple[str, int]]:
    counts: dict[str, int] = {}
    for node in nodes:
        lang = (node.get("primaryLanguage") or {}).get("name")
        if lang:
            counts[lang] = counts.get(lang, 0) + 1
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    top = ranked[:4]
    other = sum(value for _, value in ranked[4:])
    total = sum(counts.values()) or 1
    rows = [(name.upper().replace("JUPYTER NOTEBOOK", "JUPYTER"), value) for name, value in top]
    if other:
        rows.append(("OTHER", other))
    return [(name, round(value * 100 / total)) for name, value in rows]


def frame(w: int, h: int) -> str:
    inset = 14
    length = 16
    stroke = f'stroke="{PERI}" stroke-opacity="0.4" stroke-width="1"'
    return (
        f'<g fill="none" {stroke}>'
        f'<path d="M{inset} {inset + length} L{inset} {inset} L{inset + length} {inset}"/>'
        f'<path d="M{w - inset - length} {inset} L{w - inset} {inset} L{w - inset} {inset + length}"/>'
        f'<path d="M{inset} {h - inset - length} L{inset} {h - inset} L{inset + length} {h - inset}"/>'
        f'<path d="M{w - inset - length} {h - inset} L{w - inset} {h - inset} L{w - inset} {h - inset - length}"/>'
        f"</g>"
    )


def render(user: dict) -> str:
    W, H = 1000, 300
    repos = user["repositories"]
    nodes = repos["nodes"]
    stars = sum(node["stargazerCount"] for node in nodes)
    followers = user["followers"]["totalCount"]
    total = user["contributionsCollection"]["contributionCalendar"]["totalContributions"]
    weeks = user["contributionsCollection"]["contributionCalendar"]["weeks"]
    days = [day for week in weeks for day in week["contributionDays"]]
    current_streak, best_streak = streaks(days)
    rows = languages(nodes)
    now = datetime.now(timezone.utc).strftime("%Y.%m.%d // %H:%M UTC")
    spark = weeks[-26:]
    peak = max((sum(d["contributionCount"] for d in w["contributionDays"]) for w in spark), default=1) or 1

    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="BuccKyy stats: {total} public contributions, {repos["totalCount"]} public repositories, 2 awards, 5 client verticals at MaxflowAI.">']
    s.append("<defs>")
    s.append(
        f'<linearGradient id="bar" x1="0" y1="0" x2="1" y2="0">'
        f'<stop offset="0" stop-color="{PERI}"/><stop offset="1" stop-color="{CYAN}"/></linearGradient>'
    )
    s.append(
        f'<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">'
        f'<stop offset="0" stop-color="#12061F"/><stop offset="0.6" stop-color="{VOID}"/>'
        f'<stop offset="1" stop-color="#12061F"/></linearGradient>'
    )
    s.append(
        f'<pattern id="scan" width="4" height="4" patternUnits="userSpaceOnUse">'
        f'<rect width="4" height="1" fill="{MIST}" opacity="0.035"/></pattern>'
    )
    s.append("</defs>")
    s.append(f'<rect width="{W}" height="{H}" fill="url(#bg)"/>')
    bg = base64.b64encode((pathlib.Path(__file__).parent / "telemetry_bg.jpg").read_bytes()).decode()
    s.append(f'<image href="data:image/jpeg;base64,{bg}" width="{W}" height="{H}" preserveAspectRatio="xMidYMid slice" opacity="0.55"/>')
    s.append(f'<rect width="{W}" height="{H}" fill="#12061F" opacity="0.58"/>')
    s.append(f'<rect width="{W}" height="{H}" fill="url(#scan)"/>')
    s.append(f'<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" fill="none" stroke="{STEEL}" stroke-opacity="0.5"/>')

    # header
    s.append(text("_COMBAT RECORD", 30, 42, 26, face=BAR_REG, fill=MIST, tracking=2.4))
    s.append(text(f"SYNCED // {now}", W - 30, 34, 7.4, face=MONO, fill=DIM, tracking=1.2, anchor="end"))
    s.append(text("SOURCE // GITHUB GRAPHQL API", W - 30, 47, 6.6, face=MONO, fill=DIM, tracking=1.2, anchor="end"))
    s.append(f'<rect x="30" y="56" width="{W - 60}" height="1" fill="{STEEL}" opacity="0.55"/>')
    s.append(f'<rect x="30" y="56" width="120" height="1" fill="{PERI}" opacity="0.8"/>')

    # headline metrics
    metrics = [
        (f"{total:02d}", "PUBLIC CONTRIBUTIONS", "LAST 12 MONTHS"),
        (f"{repos['totalCount']:02d}", "PUBLIC REPOS", "SHIPPED"),
        ("02", "AWARDS", "HACKATHON + BME 2025"),
        ("05", "CLIENT VERTICALS", "AT MAXFLOWAI"),
    ]
    xs = [30, 272, 514, 756]
    for i, (value, label, sub) in enumerate(metrics):
        x = xs[i]
        s.append(text(value, x, 126, 52, face=BAR_LIGHT, fill=MIST, tracking=1.5))
        s.append(text(label, x + 2, 144, 7.8, face=MONO, fill=PERI, tracking=1.6))
        s.append(text(sub, x + 2, 156, 6.6, face=MONO, fill=DIM, tracking=1.2))
        if i:
            s.append(f'<rect x="{x - 22}" y="88" width="1" height="66" fill="{STEEL}" opacity="0.45"/>')

    s.append(f'<rect x="30" y="176" width="{W - 60}" height="1" fill="{STEEL}" opacity="0.32"/>')

    # loadout bars
    s.append(text("LOADOUT DISTRIBUTION", 30, 196, 7.8, face=MONO, fill=PERI, tracking=1.6))
    s.append(text("BY PRIMARY LANGUAGE / PUBLIC REPOS", 30, 207, 6.2, face=MONO, fill=DIM, tracking=1.0))
    bar_x, bar_max = 132, 296
    y = 220
    for name, pct in rows:
        s.append(text(name, 30, y + 6.4, 7.6, face=MONO, fill=MIST, tracking=1.0, opacity=0.9))
        s.append(f'<rect x="{bar_x}" y="{y}" width="{bar_max}" height="7" fill="{STEEL}" opacity="0.28"/>')
        s.append(
            f'<rect x="{bar_x}" y="{y}" width="{bar_max * pct / 100:.1f}" height="7" fill="url(#bar)" opacity="0.92"/>'
        )
        s.append(text(f"{pct:02d}%", bar_x + bar_max + 12, y + 6.4, 7.2, face=MONO, fill=PERI, tracking=0.8))
        y += 14

    # recognition (replaces the small heatmap; the full-width one lives in heatmap.svg)
    s.append(f'<rect x="520" y="186" width="1" height="94" fill="{STEEL}" opacity="0.35"/>')
    s.append(text("RECOGNITION", 548, 196, 7.8, face=MONO, fill=PERI, tracking=1.6))
    rows_r = [("VPBANK TECHNOLOGY HACKATHON 2025", "SENIOR TRACK"),
              ("BIOMEDICAL ENGINEERING INNOVATION 2025", "TEAM LEAD // IOT BP MONITORING"),
              ("B.ENG ELECTRONICS & TELECOM // VNU-HCM", "GPA 3.4 / 4.0")]
    ry = 216
    for head, sub in rows_r:
        s.append(text(head, 548, ry, 12, face=BAR_REG, fill=MIST, tracking=1.2))
        s.append(text(sub, 548, ry + 12, 6.2, face=MONO, fill=DIM, tracking=1.0))
        ry += 27
    s.append(text(f"STREAK {current_streak:02d}D", 30, 289, 5.4, face=MONO, fill=STEEL, tracking=1.2))

    # footer micro
    s.append(f'<rect x="30" y="288" width="1" height="0" fill="none"/>')
    s.append(text("MS-01 / TELEMETRY", 30, 289, 5.8, face=MONO, fill=STEEL, tracking=1.4))
    s.append(text("SELF-HOSTED SVG / NO THIRD-PARTY CARD", 970, 289, 5.8, face=MONO, fill=STEEL, tracking=1.2, anchor="end"))
    s.append(frame(W, H))
    s.append("</svg>")
    return "\n".join(s)


HEAT_OUT = os.path.join(ROOT, "assets", "heatmap.svg")
HEAT_COLORS = ["#2A1247", "#6A2C8F", "#E2447A", "#FF8A3D", "#FFD56A"]


def render_heatmap(user: dict) -> str:
    """Full-width 53-week contribution heatmap in the profile palette."""
    W, H = 1000, 236
    cal = user["contributionsCollection"]["contributionCalendar"]
    weeks = cal["weeks"][-53:]
    days = [d for w in weeks for d in w["contributionDays"]]
    peak_day = max(days, key=lambda d: d["contributionCount"], default=None)
    top = max((d["contributionCount"] for d in days), default=1) or 1
    cell, pitch, x0, y0 = 15, 17.6, 54, 70

    def level(n: int) -> int:
        if n == 0:
            return 0
        q = n / top
        return 1 if q <= .25 else 2 if q <= .5 else 3 if q <= .75 else 4

    bg = base64.b64encode((pathlib.Path(__file__).parent / "telemetry_bg.jpg").read_bytes()).decode()
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" '
         f'aria-label="Contribution heatmap: {cal["totalContributions"]} public contributions in the last year.">',
         "<style>@keyframes pop{from{opacity:0;transform:scale(.2)}to{opacity:1;transform:scale(1)}}"
         "@keyframes ring{0%,100%{opacity:.25}50%{opacity:1}}"
         "@keyframes sweep{from{transform:translateX(-120px)}to{transform:translateX(1100px)}}"
         ".c{transform-box:fill-box;transform-origin:center;animation:pop .5s ease-out both}"
         ".r{animation:ring 1.6s ease-in-out infinite}.sw{animation:sweep 6s linear infinite}"
         "@media (prefers-reduced-motion:reduce){*{animation:none!important}}</style>",
         '<defs><clipPath id="f"><rect width="1000" height="236" rx="6"/></clipPath>'
         '<linearGradient id="sg" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#FFD56A" stop-opacity=".35"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient></defs>',
         f'<g clip-path="url(#f)"><rect width="{W}" height="{H}" fill="#12061F"/>',
         f'<image href="data:image/jpeg;base64,{bg}" width="{W}" height="{H}" preserveAspectRatio="xMidYMid slice" opacity="0.5"/>',
         f'<rect width="{W}" height="{H}" fill="#12061F" opacity="0.6"/>',
         f'<rect class="sw" y="0" width="120" height="{H}" fill="url(#sg)"/></g>']
    s.append(text("_YEAR IN FLIGHT", 30, 44, 28, face=BAR_REG, fill=MIST, tracking=2.6))
    s.append(text(f"{cal['totalContributions']} PUBLIC CONTRIBUTIONS // LAST 12 MONTHS", W - 30, 40, 8, face=MONO, fill=PERI, tracking=1.4, anchor="end"))
    last_month = None
    for wi, week in enumerate(weeks):
        first = week["contributionDays"][0]["date"]
        month = first[5:7]
        if month != last_month and wi < len(weeks) - 2:
            names = ["", "JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]
            s.append(text(names[int(month)], x0 + wi * pitch, 62, 7, face=MONO, fill=DIM, tracking=1.2))
            last_month = month
        for di, day in enumerate(week["contributionDays"]):
            n = day["contributionCount"]
            x, y = x0 + wi * pitch, y0 + di * pitch
            op = 1.0 if n else 0.8
            s.append(f'<rect class="c" x="{x:.1f}" y="{y:.1f}" width="{cell}" height="{cell}" rx="3" fill="{HEAT_COLORS[level(n)]}" opacity="{op}" style="animation-delay:{wi * 0.03:.2f}s"/>')
            if peak_day and day["date"] == peak_day["date"] and n:
                s.append(f'<rect class="r" x="{x - 2:.1f}" y="{y - 2:.1f}" width="{cell + 4}" height="{cell + 4}" rx="5" fill="none" stroke="#FFD56A" stroke-width="1.6"/>')
    for di, label in ((1, "MON"), (3, "WED"), (5, "FRI")):
        s.append(text(label, 30, y0 + di * pitch + 11, 6.4, face=MONO, fill=DIM, tracking=1.0))
    s.append(text("LESS", W - 214, 222, 6.4, face=MONO, fill=DIM, tracking=1.0))
    for i, color in enumerate(HEAT_COLORS):
        s.append(f'<rect x="{W - 180 + i * 20}" y="213" width="14" height="14" rx="3" fill="{color}"/>')
    s.append(text("MORE", W - 72, 222, 6.4, face=MONO, fill=DIM, tracking=1.0))
    s.append(text("RING = PEAK DAY // REGENERATED DAILY BY GITHUB ACTIONS", 54, 222, 6.4, face=MONO, fill=STEEL, tracking=1.2))
    s.append(frame(W, H))
    s.append("</svg>")
    return "\n".join(s)


def main() -> None:
    user = fetch()
    svg = render(user)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(svg)
    print(f"wrote {OUT} ({len(svg):,} bytes)")
    heat = render_heatmap(user)
    with open(HEAT_OUT, "w", encoding="utf-8") as fh:
        fh.write(heat)
    print(f"wrote {HEAT_OUT} ({len(heat):,} bytes)")


if __name__ == "__main__":
    main()
