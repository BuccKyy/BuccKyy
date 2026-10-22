#!/usr/bin/env python3
"""Generate the colourful animated README panels (banners, pilot, experience,
systems, mission "episode posters", CTA and contact buttons) on top of cropped
key-visual photos.

Type sizes are chosen so text stays readable when the 1000px-wide SVG is scaled
down to a phone (~0.36x): secondary text >= 20 units, body text >= 28.

Source JPEGs live in tools/src/ (gitignored); crops are compressed and embedded
as data URIs because SVGs shown via <img> cannot load external files.
Run: python3 tools/panels_gen.py
"""
import base64
import io
import pathlib
import random

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
A = ROOT / "assets"
SRC = ROOT / "tools/src"


def _subset_font():
    """Embed only the glyphs the panels use; the full face was ~16 KB base64 per SVG."""
    from fontTools import subset
    from fontTools.ttLib import TTFont
    opts = subset.Options()
    opts.layout_features = ["kern"]
    font = TTFont(ROOT / "tools/fonts/BarlowCondensed-Medium.ttf")
    sub = subset.Subsetter(opts)
    sub.populate(unicodes=list(range(0x20, 0x7F)) + [0xB1, 0xB7, 0x2022, 0x2014, 0x25B8])
    sub.subset(font)
    buf = io.BytesIO()
    font.save(buf)
    return base64.b64encode(buf.getvalue()).decode()


FONT = _subset_font()

ACC = {"sunset": "#FFD56A", "neon": "#7FE7FF", "dawn": "#FFD56A", "ocean": "#FF9A5C", "fire": "#7FE7FF", "aurora": "#FFD56A"}
TINT = {"sunset": "#7A2BA8", "neon": "#5B2BD8", "dawn": "#B03AA0", "ocean": "#1F6FD0", "fire": "#9A1F6A", "aurora": "#1F6FD0"}

_cache = {}


def photo(key, x0f, y0f, wf, w, h, q=55, scale=0.8):
    """Crop a region of tools/src/<key>.jpg to w x h and return a data URI."""
    if key not in _cache:
        _cache[key] = Image.open(SRC / f"{key}.jpg").convert("RGB")
    im = _cache[key]
    W, H = im.size
    cw = wf * W
    ch = cw * h / w
    x0, y0 = x0f * W, min(y0f * H, H - ch)
    box = tuple(int(v) for v in (x0, y0, x0 + cw, y0 + ch))
    out = im.crop(box).resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    buf = io.BytesIO()
    out.save(buf, "JPEG", quality=q, optimize=True, progressive=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def wrap(w, h, body, defs="", css="", label=""):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{label}">
<style>
@font-face{{font-family:BC;src:url(data:font/ttf;base64,{FONT})}}
text{{font-family:BC,'Arial Narrow',sans-serif}}
@keyframes tw{{0%,100%{{opacity:.15}}50%{{opacity:1}}}}
@keyframes shine{{from{{transform:translateX(-260px)}}to{{transform:translateX({w + 260}px)}}}}
@keyframes bl{{0%,100%{{opacity:1}}50%{{opacity:.35}}}}
@keyframes spin{{to{{transform:rotate(360deg)}}}}
@keyframes rise{{0%{{transform:translateY(0);opacity:0}}20%{{opacity:.9}}100%{{transform:translateY(-90px);opacity:0}}}}
@keyframes kb{{from{{transform:scale(1.0)}}to{{transform:scale(1.09)}}}}
@keyframes flash{{0%,100%{{opacity:0}}50%{{opacity:.16}}}}
.tw{{animation:tw 3s ease-in-out infinite}}
.shine{{animation:shine 5.5s linear infinite}}
.bl{{animation:bl 1.4s ease-in-out infinite}}
.rise{{animation:rise 5s linear infinite}}
.kb{{transform-origin:50% 50%;animation:kb 12s ease-in-out infinite alternate}}
.flash{{animation:flash 6s ease-in-out infinite}}
{css}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}
</style>
<defs>{defs}</defs>
{body}
</svg>"""


def bgimg(uri, w, h):
    return (f'<g clip-path="url(#cp)"><image class="kb" href="{uri}" xlink:href="{uri}" width="{w}" height="{h}" preserveAspectRatio="xMidYMid slice"/></g>')


def common_defs(w, h, rx, tint, acc):
    return (f'<clipPath id="cp"><rect width="{w}" height="{h}" rx="{rx}"/></clipPath>'
            f'<linearGradient id="ov" x1="0" x2="1"><stop offset="0" stop-color="#0B0414" stop-opacity=".78"/><stop offset=".6" stop-color="#0B0414" stop-opacity=".3"/><stop offset="1" stop-color="#0B0414" stop-opacity=".05"/></linearGradient>'
            f'<linearGradient id="tn" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{tint}" stop-opacity=".42"/><stop offset="1" stop-color="{acc}" stop-opacity=".18"/></linearGradient>'
            '<linearGradient id="sh" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".5" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
            f'<linearGradient id="tt" x1="0" x2="1"><stop offset="0" stop-color="#fff"/><stop offset="1" stop-color="{acc}"/></linearGradient>'
            f'<linearGradient id="ln" x1="0" x2="1"><stop offset="0" stop-color="{acc}" stop-opacity="0"/><stop offset=".5" stop-color="{acc}"/><stop offset="1" stop-color="{acc}" stop-opacity="0"/></linearGradient>')


def stars(w, h, n, seed, color="#fff"):
    rnd = random.Random(seed)
    return "".join(
        f'<circle class="tw" cx="{rnd.randint(4, w - 4)}" cy="{rnd.randint(4, int(h * .7))}" r="{rnd.choice([1, 1.3, 1.8])}" fill="{color}" style="animation-delay:{rnd.random() * 3:.2f}s"/>'
        for _ in range(n))


def embers(w, h, n, seed, color):
    rnd = random.Random(seed)
    return "".join(
        f'<circle class="rise" cx="{rnd.randint(10, w - 10)}" cy="{h - rnd.randint(4, 30)}" r="{rnd.choice([1.4, 2, 2.6])}" fill="{color}" style="animation-delay:{rnd.random() * 5:.2f}s"/>'
        for _ in range(n))


def brackets(w, h, c="#fff", o=.85, m=10, s=14):
    return (f'<path d="M{m} {m + s}V{m}H{m + s}M{w - m - s} {m}H{w - m}V{m + s}M{w - m} {h - m - s}V{h - m}H{w - m - s}'
            f'M{m + s} {h - m}H{m}V{h - m - s}" fill="none" stroke="{c}" stroke-width="1.6" opacity="{o}"/>')


def frame(w, h, rx, pal, uri, seed, extra=""):
    acc, tint = ACC[pal], TINT[pal]
    return (f'{bgimg(uri, w, h)}<rect width="{w}" height="{h}" rx="{rx}" fill="url(#tn)"/>'
            f'<rect width="{w}" height="{h}" rx="{rx}" fill="url(#ov)"/>'
            f'{stars(w, h, 16, seed)}{embers(w, h, 8, seed, acc)}'
            f'<rect class="shine" width="100" height="{h}" fill="url(#sh)" opacity=".22"/>'
            f'<rect class="flash" width="{w}" height="{h}" rx="{rx}" fill="#fff"/>{extra}')


def T(x, y, size, txt, fill="#fff", ls=0, anchor="start", sw=1.1, op=1):
    """Text with a dark outline so it stays legible over the artwork."""
    return (f'<text x="{x}" y="{y}" font-size="{size}" letter-spacing="{ls}" text-anchor="{anchor}" fill="{fill}" opacity="{op}" '
            f'stroke="#12061F" stroke-width="{sw}" paint-order="stroke">{txt}</text>')


# ---------------------------------------------------------------- banners
BANNERS = [
    ("sec-01-pilot.svg", "_PILOT", "01 // ABOUT ME", "sunset", ("kv4", .05, .02, .9), 11),
    ("sec-06-experience.svg", "_EXPERIENCE", "02 // EXPERIENCE", "aurora", ("kv4", .0, .60, 1.0), 61),
    ("sec-02-systems.svg", "_SYSTEMS", "03 // SKILLS", "neon", ("kv2", .0, .10, 1.0), 23),
    ("sec-03-missions.svg", "_MISSIONS", "04 // PROJECTS", "dawn", ("kv4", .0, .27, 1.0), 37),
    ("sec-04-telemetry.svg", "_RECORD", "05 // STATS + TIMELINE", "ocean", ("kv2", .0, .38, 1.0), 41),
    ("sec-05-comms.svg", "_COMMS", "06 // CONTACT", "fire", ("kv4", .0, .45, 1.0), 53),
]


def banners():
    w, h = 1000, 130
    for name, title, tag, pal, (k, x, y, wf), seed in BANNERS:
        acc = ACC[pal]
        body = (frame(w, h, 6, pal, photo(k, x, y, wf, w, h), seed) +
                f'<text x="28" y="86" font-size="66" letter-spacing="7" fill="url(#tt)" stroke="#12061F" stroke-width="1.2" paint-order="stroke">{title}</text>' +
                T(w - 28, 42, 24, tag, ls=4, anchor="end") +
                f'<rect x="0" y="{h - 3}" width="{w}" height="3" fill="url(#ln)"/>' + brackets(w, h, acc, .85, 8, 12))
        (A / name).write_text(wrap(w, h, body, common_defs(w, h, 6, TINT[pal], acc), label=title))


# ---------------------------------------------------------------- pilot
def pilot():
    w, h = 1000, 360
    pal = "neon"
    rows = [("CALLSIGN", "BuccKyy  //  Tran Trung Duc", "#FFD56A"), ("ROLE", "AI Engineer @ MaxflowAI", "#FF7AA8"),
            ("BASE", "Ho Chi Minh City, Vietnam  ·  UTC+7", "#7FE7FF"),
            ("SEEKING", "AI / agent engineer roles, fully remote", "#C9A4FF"),
            ("WORKS", "Async-first remote teams, worldwide", "#8BE8A8"),
            ("FOCUS", "LLM agents  ·  applied deep learning  ·  edge AI", "#FF9A5C")]
    t = ""
    for i, (k, v, c) in enumerate(rows):
        y = 64 + i * 52
        t += (f'<rect x="28" y="{y - 30}" width="158" height="40" rx="4" fill="{c}"/>'
              f'<text x="107" y="{y - 1}" font-size="22" letter-spacing="3" text-anchor="middle" fill="#1A0830">{k}</text>' +
              T(204, y, 31, v, ls=1))
    cx, cy = 890, h // 2
    rings = "".join(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#7FE7FF" stroke-opacity="{o}"/>' for r, o in ((24, .6), (52, .5), (80, .4)))
    blips = "".join(f'<circle class="bl" cx="{x}" cy="{y}" r="5" fill="{c}" style="animation-delay:{d}s"/>' for x, y, c, d in
                    ((cx + 28, cy - 50, "#FFD56A", 0), (cx - 40, cy + 30, "#FF5C9A", .5), (cx + 50, cy + 36, "#7FE7FF", 1)))
    radar = (f'<circle cx="{cx}" cy="{cy}" r="84" fill="#0B0414" fill-opacity=".55"/>{rings}'
             f'<line x1="{cx - 84}" y1="{cy}" x2="{cx + 84}" y2="{cy}" stroke="#7FE7FF" stroke-opacity=".4"/><line x1="{cx}" y1="{cy - 84}" x2="{cx}" y2="{cy + 84}" stroke="#7FE7FF" stroke-opacity=".4"/>'
             f'<g style="transform-origin:{cx}px {cy}px;animation:spin 4s linear infinite"><path d="M{cx} {cy} L{cx} {cy - 84} A84 84 0 0 1 {cx + 58} {cy - 61}Z" fill="url(#sw)"/></g>' + blips)
    uri = photo("kv4", .0, .02, 1.0, w, h)
    body = (frame(w, h, 6, pal, uri, 5) + t + radar + brackets(w, h, "#FF9A5C", .9, 8, 16) +
            f'<rect x="0" y="{h - 3}" width="{w}" height="3" fill="url(#ln)"/>')
    defs = common_defs(w, h, 6, TINT[pal], ACC[pal]) + '<linearGradient id="sw" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#7FE7FF" stop-opacity=".75"/><stop offset="1" stop-color="#7FE7FF" stop-opacity="0"/></linearGradient>'
    (A / "panel-pilot.svg").write_text(wrap(w, h, body, defs, label="Pilot data: BuccKyy, Tran Trung Duc, AI Engineer at MaxflowAI, Ho Chi Minh City, UTC+7. Seeking AI and agent engineer roles, fully remote. Works with async-first remote teams worldwide. Focus: LLM agents, applied deep learning, edge AI."))


# ---------------------------------------------------------------- experience
EXPERIENCE = [
    ("01", "AI Engineer / Agent Builder", "MaxflowAI  ·  Ho Chi Minh City", "2026 - NOW", "sunset", ("kv4", .0, .02, 1.0),
     ["Multi-agent systems for 5 client verticals",
      "Python + JSON orchestration, CRM / SMS / SMTP, Playwright QA"],
     "Built multi-agent systems for real clients across event ops, B2B sales automation, inventory logistics, email pipelines and HR, using Python and JSON orchestration, event triggers, scheduled jobs, CRM / SMS / SMTP connectors and Playwright QA scripts."),
    ("02", "AI Engineer Intern", "ITR VN  ·  Ho Chi Minh City", "NOV 2024 - JAN 2025", "neon", ("kv2", .0, .05, 1.0),
     ["PPG2BP-Net: SBP MAE 9.76, DBP MAE 5.25 mmHg",
      "NumPy pipeline ~40% faster; STM32 + MAX30102 prototype"],
     "Implemented PPG2BP-Net for cuffless blood pressure (SBP MAE 9.76 ± 8.99 mmHg, DBP MAE 5.25 ± 5.26 mmHg), built MIMIC-III data pipelines, cut processing latency about 40% with NumPy vectorisation, and built an STM32 + MAX30102 Bluetooth prototype."),
    ("03", "Product Reviewer / QA Collaborator", "SNOW Vietnam  ·  Ho Chi Minh City", "APR - OCT 2025", "fire", ("kv4", .0, .33, 1.0),
     ["Reviewed AI AR filters and computer-vision effects",
      "Found low-light and occlusion failures for the CV team"],
     "Reviewed AI-generated AR filters and computer-vision effects, found low-light and occlusion failures, and documented defect patterns for the CV research team."),
]


def experience():
    w, h = 1000, 210
    for n, role, org, dates, pal, (k, x, y, wf), bullets, alt in EXPERIENCE:
        acc = ACC[pal]
        dw = 30 + len(dates) * 12
        body = (frame(w, h, 6, pal, photo(k, x, y, wf, w, h, q=55), int(n) * 19) +
                T(26, 56, 48, role, ls=1.2, sw=1.3) +
                T(26, 94, 26, org.upper(), fill=acc, ls=3) +
                f'<rect x="{w - dw - 24}" y="22" width="{dw}" height="36" rx="18" fill="{acc}"/>'
                f'<text x="{w - 24 - dw / 2}" y="48" font-size="22" letter-spacing="2" text-anchor="middle" fill="#1A0830">{dates}</text>' +
                T(26, 146, 31, "▸ " + bullets[0]) + T(26, 188, 31, "▸ " + bullets[1]) + brackets(w, h, acc, .9, 7, 12))
        (A / f"panel-exp-{n}.svg").write_text(wrap(w, h, body, common_defs(w, h, 6, TINT[pal], acc), label=f"{role} at {org}. {alt}"))


def awards():
    w, h = 1000, 300
    items = [("AWARD  ·  2025", "VPBank Technology Hackathon  ·  Senior Track", "#FFD56A"),
             ("AWARD  ·  2025", "Biomedical Eng. Innovation  ·  Team Lead, IoT BP monitor", "#7FE7FF"),
             ("EDUCATION  ·  2021 - 2025", "B.Eng. Electronics &amp; Telecom  ·  VNU-HCM  ·  GPA 3.4", "#FF7AA8")]
    rows = ""
    for i, (tag, line, c) in enumerate(items):
        y0 = 18 + i * 92
        rows += T(28, y0 + 34, 22, tag, fill=c, ls=4) + T(28, y0 + 76, 38, line, ls=0.5)
        if i:
            rows += f'<rect x="28" y="{y0 - 6}" width="{w - 56}" height="1" fill="#fff" opacity=".3"/>'
    body = frame(w, h, 6, "dawn", photo("kv4", .0, .48, 1.0, w, h, q=50), 71) + rows + brackets(w, h, "#FFD56A", .9, 7, 12)
    (A / "panel-awards.svg").write_text(wrap(w, h, body, common_defs(w, h, 6, TINT["dawn"], "#FFD56A"),
                                              label="Awards and education: VPBank Technology Hackathon 2025 Senior Track; Biomedical Engineering Innovation Competition 2025 Team Lead; B.Eng. Electronics and Telecommunication, VNU-HCM, GPA 3.4"))


# ---------------------------------------------------------------- systems (no self-rated percentages)
SYSTEMS = [
    ("01", "LLM + AGENTS", ["Claude", "OpenAI", "LangChain", "RAG", "n8n"], "sunset", ("kv4", .1, .30, .9)),
    ("02", "ML + SIGNALS", ["PyTorch", "TensorFlow", "scikit-learn", "NumPy", "Pandas"], "neon", ("kv2", .0, .25, 1.0)),
    ("03", "EDGE + SHIP", ["Python", "TypeScript", "C", "Kotlin", "STM32"], "aurora", ("kv3", .0, .35, 1.0)),
]


def systems():
    w, h = 1000, 170
    for n, title, items, pal, (k, x, y, wf) in SYSTEMS:
        acc = ACC[pal]
        chips, cx = "", 28
        for it in items:
            cw = 34 + len(it) * 12.5
            chips += (f'<rect x="{cx}" y="104" width="{cw:.0f}" height="44" rx="22" fill="#0B0414" fill-opacity=".62" stroke="{acc}" stroke-width="1.5"/>'
                      f'<text x="{cx + cw / 2:.0f}" y="134" font-size="26" text-anchor="middle" fill="#fff">{it}</text>')
            cx += cw + 12
        body = (frame(w, h, 6, pal, photo(k, x, y, wf, w, h), int(n) * 11) +
                T(28, 38, 22, f"SYSTEM {n}", fill=acc, ls=5) + T(28, 84, 50, title, ls=2, sw=1.3) + chips + brackets(w, h, acc, .9, 7, 12))
        (A / f"panel-sys-{n}.svg").write_text(wrap(w, h, body, common_defs(w, h, 6, TINT[pal], acc), label=f"System {n}: {title}: " + ", ".join(items)))


# ---------------------------------------------------------------- missions
MISSIONS = [
    ("01", "agent-reliability-kit", "Tool-call validation, retry, fallback", "PYTHON · TESTED", "sunset", ("kv4", .0, .02, .75)),
    ("02", "payment-approval-agent-n8n", "AI-assisted internal payment approvals", "N8N · OPENAI", "neon", ("kv2", .0, .05, .9)),
    ("03", "ai-news-agent-n8n", "27 sources, LLM scoring, Telegram alerts", "N8N · GROQ", "dawn", ("kv4", .25, .30, .7)),
    ("04", "prompt-master-for-codex", "Turns rough requests into scoped tasks", "PYTHON · CODEX", "fire", ("kv4", .3, .14, .7)),
    ("05", "Deep-PPG-Research-Core", "Research framework for PPG blood pressure", "PYTHON · PYTORCH", "ocean", ("kv2", .1, .30, .8)),
    ("06", "Cuffless-BP-IoT-System", "Real-time cuffless BP on STM32 + Android", "C · EDGE AI", "aurora", ("kv3", .0, .20, 1.0)),
]


def missions():
    w, h = 492, 220
    for n, title, brief, stack, pal, (k, x, y, wf) in MISSIONS:
        acc = ACC[pal]
        sw = 28 + len(stack) * 12
        body = (frame(w, h, 6, pal, photo(k, x, y, wf, w, h), int(n) * 17) +
                f'<text x="{w - 10}" y="{h - 14}" font-size="170" text-anchor="end" fill="#fff" opacity=".16">{n}</text>' +
                T(20, 36, 20, f"MISSION {n}", fill=acc, ls=5) + T(20, 86, 36 if len(title) > 24 else 38, title, ls=0.3, sw=1.2) + T(20, 122, 24, brief) +
                f'<rect x="20" y="146" width="{sw}" height="40" rx="20" fill="{acc}"/>'
                f'<text x="{20 + sw / 2}" y="173" font-size="21" letter-spacing="2" text-anchor="middle" fill="#1A0830">{stack}</text>' + brackets(w, h, acc, .9, 7, 12))
        (A / f"panel-ms-{n}.svg").write_text(wrap(w, h, body, common_defs(w, h, 6, TINT[pal], acc), label=f"Mission {n}: {title}. {brief}"))


def timeline():
    w, h = 1000, 440
    y0, y1 = 2021.0, 2027.0
    X = lambda yr: 40 + (yr - y0) / (y1 - y0) * 920
    rows = [("", "B.Eng. Electronics &amp; Telecom", 2021.5, 2025.5, "#FF7AA8"),
            ("ITR VN", "AI Engineer Intern", 2024.83, 2025.08, "#7FE7FF"),
            ("SNOW Vietnam", "Product Reviewer / QA", 2025.25, 2025.83, "#C9A4FF"),
            ("MaxflowAI", "AI Engineer / Agent Builder", 2026.0, 2026.8, "#FFD56A")]
    body = ""
    for yr in range(2021, 2027):
        x = X(yr)
        body += f'<rect x="{x:.0f}" y="84" width="1" height="236" fill="#fff" opacity=".18"/>' + T(x + 6, 78, 22, str(yr), fill="#fff", op=.9, sw=.8)
    for i, (tag, label, a, b, c) in enumerate(rows):
        y = 100 + i * 56
        xa, xb = X(a), X(b)
        body += f'<rect x="{xa:.0f}" y="{y}" width="{max(xb - xa, 10):.0f}" height="40" rx="8" fill="{c}"/>'
        inside = xb - xa > 420
        if inside:
            body += f'<text x="{xa + 16:.0f}" y="{y + 29}" font-size="26" fill="#1A0830">{label}</text>'
        else:
            lx, anchor = (xb + 14, "start") if xb < 640 else (xa - 14, "end")
            body += T(f"{lx:.0f}", y + 29, 26, f"{tag}: {label}", anchor=anchor)
    mx = X(2026.8)
    body += f'<circle class="bl" cx="{mx + 4:.0f}" cy="{100 + 3 * 56 + 20}" r="9" fill="#FFD56A"/>'
    ay = 100 + 4 * 56 + 8
    ax = X(2025.5)
    body += f'<path d="M{ax:.0f} {ay} l16 20 l-16 20 l-16 -20z" fill="#FFD56A"/>' + T(f"{ax - 26:.0f}", ay + 29, 26, "2025 awards: VPBank Hackathon, BME Innovation", anchor="end")
    body += T(28, h - 26, 28, "Most client work lives in private repositories.", fill="#FFE9A8", ls=0.5)
    body = (frame(w, h, 6, "ocean", photo("kv2", .0, .55, 1.0, w, h, q=50), 83) +
            T(28, 52, 44, "_TIMELINE", ls=4, sw=1.3) + T(w - 28, 48, 22, "2021 - NOW", fill="#FF9A5C", ls=4, anchor="end") + body + brackets(w, h, "#FF9A5C", .9, 8, 14))
    (A / "panel-timeline.svg").write_text(wrap(w, h, body, common_defs(w, h, 6, TINT["ocean"], "#FF9A5C"),
                                               label="Timeline 2021 to now: B.Eng. Electronics and Telecom 2021-2025; ITR VN intern Nov 2024 to Jan 2025; SNOW Vietnam Apr to Oct 2025; MaxflowAI from 2026; 2025 awards. Most client work lives in private repositories."))


# ---------------------------------------------------------------- comms (2 x 2)
COMMS = [("GITHUB", "BuccKyy", "sunset", ("kv4", .5, .05, .5)), ("LINKEDIN", "tranductrung-ai", "ocean", ("kv2", .2, .2, .6)),
         ("WEBSITE", "bucckyy.github.io", "neon", ("kv2", .1, .05, .7)), ("EMAIL", "trantrungduc313@gmail.com", "fire", ("kv4", .1, .55, .6))]


def comms():
    w, h = 496, 120
    for k, v, pal, (ik, x, y, wf) in COMMS:
        acc = ACC[pal]
        body = (frame(w, h, 8, pal, photo(ik, x, y, wf, w, h), len(k) * 13) +
                T(20, 38, 22, k, fill=acc, ls=5) + T(20, 88, 40 if len(v) < 20 else 34, v, sw=1.2) +
                f'<circle class="bl" cx="{w - 18}" cy="20" r="5" fill="{acc}"/>' + brackets(w, h, acc, .9, 6, 10))
        (A / f"panel-link-{k.lower()}.svg").write_text(wrap(w, h, body, common_defs(w, h, 8, TINT[pal], acc), label=f"{k}: {v}"))


# ---------------------------------------------------------------- CTA buttons
def ctas():
    specs = [("cta-portfolio.svg", 1000, 110, "LAUNCH", "ENTER PORTFOLIO", "sunset", ("kv4", .0, .05, 1.0), 66, 24),
             ("cta-repos.svg", 332, 110, "ARCHIVE", "REPOSITORIES", "neon", ("kv2", .1, .1, .8), 40, 19),
             ("cta-cv.svg", 332, 110, "RESUME // PDF", "DOWNLOAD CV", "dawn", ("kv4", .3, .25, .7), 40, 19),
             ("cta-contact.svg", 332, 110, "OPEN CHANNEL", "CONTACT", "fire", ("kv4", .2, .5, .7), 40, 19)]
    for name, w, h, tag, title, pal, (k, x, y, wf), fs, ts in specs:
        acc = ACC[pal]
        body = (frame(w, h, 8, pal, photo(k, x, y, wf, w, h, q=62), len(name)) +
                T(24, 38, ts, tag, fill=acc, ls=5) + T(24, h - 22, fs, title, ls=6 if w > 400 else 2, sw=1.3) +
                f'<path d="M{w - 54} {h // 2 - 14}l22 14-22 14" fill="none" stroke="{acc}" stroke-width="4"/>'
                f'<circle class="bl" cx="{w - 18}" cy="18" r="5" fill="{acc}"/>' + brackets(w, h, acc, .95, 6, 12))
        (A / name).write_text(wrap(w, h, body, common_defs(w, h, 8, TINT[pal], acc), label=title))


if __name__ == "__main__":
    banners()
    pilot()
    experience()
    awards()
    timeline()
    systems()
    missions()
    comms()
    ctas()
    sizes = {p.name: p.stat().st_size // 1024 for p in sorted(A.glob("*.svg"))}
    print(sizes)
