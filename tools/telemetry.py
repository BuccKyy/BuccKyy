#!/usr/bin/env python3
"""Render assets/telemetry.svg for the BuccKyy profile from the GitHub GraphQL API.

Local:   GITHUB_TOKEN=$(gh auth token) python tools/telemetry.py
Action:  GITHUB_TOKEN is provided by the workflow.

Every glyph is converted to a path, so the SVG has no font dependency at render
time. Only ASCII is used, which keeps the committed subset fonts tiny.
"""
from __future__ import annotations

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
    return payload["data"]["user"]


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

    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="BuccKyy telemetry: {total} contributions, {stars} stars, {repos["totalCount"]} public repositories, {followers} followers.">']
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
        (f"{stars:02d}", "STARS EARNED", f"ACROSS {repos['totalCount']} REPOS"),
        (f"{repos['totalCount']:02d}", "PUBLIC REPOS", "DEPLOYED"),
        (f"{followers:02d}", "FOLLOWERS", "LINKED"),
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

    # activity heatmap (53 weeks x 7 days), GitHub-calendar style
    s.append(f'<rect x="520" y="186" width="1" height="94" fill="{STEEL}" opacity="0.35"/>')
    s.append(text("ACTIVITY // LAST 12 MONTHS", 548, 196, 7.8, face=MONO, fill=PERI, tracking=1.6))
    s.append(text("DAILY CONTRIBUTIONS", 548, 207, 6.2, face=MONO, fill=DIM, tracking=1.0))
    cell, gap = 5.0, 1.45
    grid = weeks[-53:]
    x0, y0 = 548, 218
    buckets = [
        (0, "#1E0B33"),
        (2, "#4A1A66"),
        (5, "#B8337A"),
        (9, CYAN),
        (10**9, CYAN_HOT),
    ]
    for wi, week in enumerate(grid):
        for di, day in enumerate(week["contributionDays"]):
            value = day["contributionCount"]
            fill = next(color for limit, color in buckets if value <= limit)
            opacity = 1.0 if value else 0.85
            s.append(
                f'<rect x="{x0 + wi * (cell + gap):.2f}" y="{y0 + di * (cell + gap):.2f}" '
                f'width="{cell}" height="{cell}" fill="{fill}" opacity="{opacity}"/>'
            )
    # legend
    lx = 900
    s.append(text("LESS", lx, 196, 5.4, face=MONO, fill=DIM, tracking=0.8))
    for i, (_, color) in enumerate(buckets):
        s.append(f'<rect x="{lx + 26 + i * 8.4}" y="{191.6}" width="5" height="5" fill="{color}"/>')
    s.append(text("MORE", lx + 26 + 5 * 8.4 + 4, 196, 5.4, face=MONO, fill=DIM, tracking=0.8))
    s.append(text(f"STREAK {current_streak:02d}D", 548, 280, 7.2, face=MONO, fill=PERI, tracking=1.2))
    s.append(text(f"BEST {best_streak:02d}D", 640, 280, 7.2, face=MONO, fill=DIM, tracking=1.2))
    s.append(text(f"PEAK {peak:02d}/WK", 732, 280, 7.2, face=MONO, fill=DIM, tracking=1.2))
    s.append(text("SIGNAL // VERIFIED", 970, 280, 6.2, face=MONO, fill=STEEL, tracking=1.1, anchor="end"))

    # footer micro
    s.append(f'<rect x="30" y="288" width="1" height="0" fill="none"/>')
    s.append(text("MS-01 / TELEMETRY", 30, 289, 5.8, face=MONO, fill=STEEL, tracking=1.4))
    s.append(text("SELF-HOSTED SVG / NO THIRD-PARTY CARD", 970, 289, 5.8, face=MONO, fill=STEEL, tracking=1.2, anchor="end"))
    s.append(frame(W, H))
    s.append("</svg>")
    return "\n".join(s)


def main() -> None:
    user = fetch()
    svg = render(user)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(svg)
    print(f"wrote {OUT} ({len(svg):,} bytes)")


if __name__ == "__main__":
    main()
