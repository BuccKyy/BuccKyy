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
    """Compact stats panel: big numbers, labels that stay readable on a phone."""
    W, H = 1000, 330
    repos = user["repositories"]
    cal = user["contributionsCollection"]["contributionCalendar"]
    now = datetime.now(timezone.utc).strftime("%Y.%m.%d")
    bg = base64.b64encode((pathlib.Path(__file__).parent / "telemetry_bg.jpg").read_bytes()).decode()
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" '
         f'aria-label="Stats: {cal["totalContributions"]} public contributions in the last 12 months, {repos["totalCount"]} original public repositories, 2 awards, 5 client verticals at MaxflowAI.">',
         f'<defs><clipPath id="f"><rect width="{W}" height="{H}" rx="6"/></clipPath></defs>',
         f'<g clip-path="url(#f)"><rect width="{W}" height="{H}" fill="#12061F"/>',
         f'<image href="data:image/jpeg;base64,{bg}" width="{W}" height="{H}" preserveAspectRatio="xMidYMid slice" opacity="0.55"/>',
         f'<rect width="{W}" height="{H}" fill="#12061F" opacity="0.62"/></g>']
    s.append(text("_STATS", 30, 62, 46, face=BAR_REG, fill=MIST, tracking=3))
    s.append(text(f"SYNCED {now}", W - 30, 54, 12.5, face=MONO, fill=PERI, tracking=1.4, anchor="end"))
    s.append(f'<rect x="30" y="80" width="{W - 60}" height="1" fill="{STEEL}" opacity="0.6"/>')
    s.append(f'<rect x="30" y="80" width="160" height="2" fill="{PERI}"/>')
    metrics = [
        (f"{cal['totalContributions']:02d}", "CONTRIBUTIONS", "LAST 12 MONTHS"),
        (f"{repos['totalCount']:02d}", "ORIGINAL REPOS", "EXCL. FORKS"),
        ("02", "AWARDS", "HACKATHON + BME"),
        ("05", "CLIENT VERTICALS", "AT MAXFLOWAI"),
    ]
    xs = [30, 275, 520, 765]
    for i, (value, label, sub) in enumerate(metrics):
        x = xs[i]
        s.append(text(value, x, 168, 84, face=BAR_LIGHT, fill=MIST, tracking=1.5))
        s.append(text(label, x + 2, 202, 16, face=MONO, fill=PERI, tracking=1.0))
        s.append(text(sub, x + 2, 230, 13, face=MONO, fill=MIST, tracking=0.6, opacity=0.8))
        if i:
            s.append(f'<rect x="{x - 18}" y="104" width="1" height="130" fill="{STEEL}" opacity="0.55"/>')
    s.append(f'<rect x="30" y="248" width="{W - 60}" height="1" fill="{STEEL}" opacity="0.45"/>')
    s.append(text("NOW", 30, 282, 16, face=MONO, fill=PERI, tracking=1.4))
    s.append(text("Building multi-agent workflows at MaxflowAI", 130, 282, 26, face=BAR_REG, fill=MIST, tracking=1.2))
    s.append(text("TOOLS", 30, 312, 16, face=MONO, fill=PERI, tracking=1.4))
    s.append(text("Claude Code · Python · Playwright · TensorFlow / PyTorch", 130, 312, 26, face=BAR_REG, fill=MIST, tracking=1.2))
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
