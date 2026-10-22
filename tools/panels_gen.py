#!/usr/bin/env python3
"""Generate the colourful animated README panels (banners, pilot, systems,
mission "episode posters", comms buttons) on top of cropped key-visual photos.

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
FONT = base64.b64encode((ROOT / "tools/fonts/BarlowCondensed-Medium.ttf").read_bytes()).decode()

ACC = {"sunset": "#FFD56A", "neon": "#7FE7FF", "dawn": "#FFD56A", "ocean": "#FF9A5C", "fire": "#7FE7FF", "aurora": "#FFD56A"}
TINT = {"sunset": "#7A2BA8", "neon": "#5B2BD8", "dawn": "#B03AA0", "ocean": "#1F6FD0", "fire": "#9A1F6A", "aurora": "#1F6FD0"}

_cache = {}


def photo(key, x0f, y0f, wf, w, h, q=72, scale=1.0):
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
@keyframes grow{{from{{transform:scaleX(0)}}to{{transform:scaleX(1)}}}}
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
            f'<linearGradient id="ov" x1="0" x2="1"><stop offset="0" stop-color="#0B0414" stop-opacity=".78"/><stop offset=".55" stop-color="#0B0414" stop-opacity=".25"/><stop offset="1" stop-color="#0B0414" stop-opacity="0"/></linearGradient>'
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


# ---------------------------------------------------------------- banners
BANNERS = [
    ("sec-01-pilot.svg", "_PILOT", "01 // ABOUT ME", "sunset", ("kv4", .05, .02, .9), 11),
    ("sec-06-experience.svg", "_EXPERIENCE", "02 // EXPERIENCE", "aurora", ("kv4", .0, .60, 1.0), 61),
    ("sec-02-systems.svg", "_SYSTEMS", "03 // SKILLS", "neon", ("kv2", .0, .10, 1.0), 23),
    ("sec-03-missions.svg", "_MISSIONS", "04 // PROJECTS", "dawn", ("kv4", .0, .27, 1.0), 37),
    ("sec-04-telemetry.svg", "_TELEMETRY", "05 // STATS", "ocean", ("kv2", .0, .38, 1.0), 41),
    ("sec-05-comms.svg", "_COMMS", "06 // CONTACT", "fire", ("kv4", .0, .45, 1.0), 53),
]


def banners():
    w, h = 1000, 130
    for name, title, tag, pal, (k, x, y, wf), seed in BANNERS:
        acc = ACC[pal]
        uri = photo(k, x, y, wf, w, h, scale=1.0)
        body = (frame(w, h, 6, pal, uri, seed) +
                f'<text x="28" y="82" font-size="62" letter-spacing="7" fill="url(#tt)" stroke="#12061F" stroke-width="1.2" paint-order="stroke">{title}</text>'
                f'<text x="972" y="34" font-size="15" letter-spacing="5" text-anchor="end" fill="#fff" stroke="#12061F" stroke-width=".8" paint-order="stroke">{tag}</text>'
                f'<rect x="0" y="{h - 3}" width="{w}" height="3" fill="url(#ln)"/>' + brackets(w, h, acc, .85, 8, 12))
        (A / name).write_text(wrap(w, h, body, common_defs(w, h, 6, TINT[pal], acc), label=title))


# ---------------------------------------------------------------- pilot
def pilot():
    w, h = 1000, 250
    pal = "neon"
    rows = [("CALLSIGN", "BuccKyy  //  Tran Trung Duc", "#FFD56A"), ("ROLE", "AI Engineer @ MaxflowAI", "#FF7AA8"),
            ("BASE", "Ho Chi Minh City, Vietnam  ·  UTC+7", "#7FE7FF"), ("CHANNEL", "Open to remote AI engineering roles", "#C9A4FF"),
            ("FOCUS", "LLM agents  ·  applied deep learning  ·  edge AI", "#FF9A5C")]
    t = ""
    for i, (k, v, c) in enumerate(rows):
        y = 52 + i * 38
        t += (f'<rect x="30" y="{y - 20}" width="104" height="26" rx="3" fill="{c}"/>'
              f'<text x="82" y="{y - 2}" font-size="15" letter-spacing="3" text-anchor="middle" fill="#1A0830">{k}</text>'
              f'<text x="150" y="{y - 1}" font-size="24" letter-spacing="1.5" fill="#fff" stroke="#12061F" stroke-width=".8" paint-order="stroke">{v}</text>')
    rings = "".join(f'<circle cx="868" cy="125" r="{r}" fill="none" stroke="#7FE7FF" stroke-opacity="{o}"/>' for r, o in ((26, .6), (58, .5), (90, .4)))
    blips = "".join(f'<circle class="bl" cx="{x}" cy="{y}" r="4.5" fill="{c}" style="animation-delay:{d}s"/>' for x, y, c, d in
                    ((896, 80, "#FFD56A", 0), (833, 152, "#FF5C9A", .5), (920, 162, "#7FE7FF", 1)))
    radar = (f'<circle cx="868" cy="125" r="94" fill="#0B0414" fill-opacity=".55"/>{rings}'
             '<line x1="770" y1="125" x2="966" y2="125" stroke="#7FE7FF" stroke-opacity=".4"/><line x1="868" y1="25" x2="868" y2="225" stroke="#7FE7FF" stroke-opacity=".4"/>'
             '<g style="transform-origin:868px 125px;animation:spin 4s linear infinite"><path d="M868 125 L868 31 A94 94 0 0 1 935 59Z" fill="url(#sw)"/></g>' + blips)
    uri = photo("kv4", .0, .02, 1.0, w, h)
    body = (frame(w, h, 6, pal, uri, 5) + t + radar + brackets(w, h, "#FF9A5C", .9, 8, 16) +
            f'<rect x="0" y="{h - 3}" width="{w}" height="3" fill="url(#ln)"/>')
    defs = common_defs(w, h, 6, TINT[pal], ACC[pal]) + '<linearGradient id="sw" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#7FE7FF" stop-opacity=".75"/><stop offset="1" stop-color="#7FE7FF" stop-opacity="0"/></linearGradient>'
    (A / "panel-pilot.svg").write_text(wrap(w, h, body, defs, label="Pilot data"))


# ---------------------------------------------------------------- systems
SYSTEMS = [
    ("01", "LLM + AGENTS", ["Claude", "OpenAI", "LangChain", "RAG", "n8n"], 94, "ACTIVE", "sunset", ("kv4", .1, .30, .75)),
    ("02", "ML + SIGNALS", ["PyTorch", "TensorFlow", "scikit-learn", "NumPy", "Pandas"], 88, "ACTIVE", "neon", ("kv2", .1, .20, .8)),
    ("03", "EDGE + SHIP", ["Python", "TypeScript", "C", "Kotlin", "STM32"], 82, "ON-DEVICE", "aurora", ("kv3", .0, .35, 1.0)),
]


def systems():
    w, h = 326, 230
    for n, title, items, lvl, state, pal, (k, x, y, wf) in SYSTEMS:
        acc = ACC[pal]
        chips, cx, cy = "", 20, 104
        for it in items:
            cw = 16 + len(it) * 9
            if cx + cw > w - 14:
                cx, cy = 20, cy + 30
            chips += (f'<rect x="{cx}" y="{cy}" width="{cw}" height="23" rx="11.5" fill="#0B0414" fill-opacity=".6" stroke="{acc}"/>'
                      f'<text x="{cx + cw / 2}" y="{cy + 17}" font-size="15" text-anchor="middle" fill="#fff">{it}</text>')
            cx += cw + 8
        bw = int((w - 40) * lvl / 100)
        body = (frame(w, h, 6, pal, photo(k, x, y, wf, w, h), int(n) * 11) +
                f'<text x="20" y="38" font-size="14" letter-spacing="5" fill="{acc}" stroke="#12061F" stroke-width=".7" paint-order="stroke">SYSTEM {n}</text>'
                f'<text x="20" y="78" font-size="36" letter-spacing="2" fill="#fff" stroke="#12061F" stroke-width="1" paint-order="stroke">{title}</text>' + chips +
                f'<rect x="20" y="{h - 40}" width="{w - 40}" height="8" rx="4" fill="#000" fill-opacity=".55"/>'
                f'<rect x="20" y="{h - 40}" width="{bw}" height="8" rx="4" fill="url(#tt)" style="transform-origin:20px 0;animation:grow 2s ease-out both"/>'
                f'<text x="{w - 20}" y="{h - 48}" font-size="13" letter-spacing="3" text-anchor="end" class="bl" fill="{acc}">{state}</text>' + brackets(w, h, acc, .9, 7, 11))
        (A / f"panel-sys-{n}.svg").write_text(wrap(w, h, body, common_defs(w, h, 6, TINT[pal], acc), label=f"System {n} {title}"))


# ---------------------------------------------------------------- missions
MISSIONS = [
    ("01", "Deep-PPG-Research-Core", "End-to-end research framework for PPG-based BP prediction.", "PYTHON · PYTORCH", "sunset", ("kv4", .0, .02, .75)),
    ("02", "Cuffless-BP-IoT-System", "Real-time cuffless BP with edge AI on STM32 + Android.", "C · EDGE AI", "neon", ("kv2", .0, .05, .9)),
    ("03", "Video-Translation-Tool", "AI-powered video translation pipeline.", "PYTHON · LLM", "dawn", ("kv4", .25, .30, .7)),
    ("04", "prompt-master-for-codex", "Turns rough requests into scoped, testable work.", "PYTHON · CODEX", "fire", ("kv4", .3, .14, .7)),
    ("05", "PPG2BP-Deep-Learning", "CNN-LSTM, U-Net, ResNet, Transformer models for BP from PPG.", "PYTHON · TENSORFLOW", "ocean", ("kv2", .1, .30, .8)),
    ("06", "IoT Data Pipeline", "STM32 + Android pipeline: PPG capture to model-ready data.", "JUPYTER · PYTHON", "aurora", ("kv3", .0, .20, 1.0)),
]


def missions():
    w, h = 492, 190
    for n, title, brief, stack, pal, (k, x, y, wf) in MISSIONS:
        acc = ACC[pal]
        sw = 18 + len(stack) * 8
        body = (frame(w, h, 6, pal, photo(k, x, y, wf, w, h), int(n) * 17) +
                f'<text x="{w - 10}" y="{h - 14}" font-size="150" text-anchor="end" fill="#fff" opacity=".16">{n}</text>'
                f'<text x="20" y="34" font-size="15" letter-spacing="6" fill="{acc}" stroke="#12061F" stroke-width=".7" paint-order="stroke">MISSION {n}</text>'
                f'<text x="20" y="76" font-size="38" letter-spacing="1" fill="#fff" stroke="#12061F" stroke-width="1.1" paint-order="stroke">{title}</text>'
                f'<text x="20" y="104" font-size="18" fill="#fff" stroke="#12061F" stroke-width=".8" paint-order="stroke">{brief}</text>'
                f'<rect x="20" y="120" width="{sw}" height="24" rx="12" fill="{acc}"/>'
                f'<text x="{20 + sw / 2}" y="137" font-size="15" letter-spacing="2" text-anchor="middle" fill="#1A0830">{stack}</text>' + brackets(w, h, acc, .9, 7, 12))
        (A / f"panel-ms-{n}.svg").write_text(wrap(w, h, body, common_defs(w, h, 6, TINT[pal], acc), label=f"Mission {n} {title}"))


# ---------------------------------------------------------------- comms
COMMS = [("GITHUB", "BuccKyy", "sunset", ("kv4", .5, .05, .5)), ("LINKEDIN", "Tran Trung Duc", "ocean", ("kv2", .2, .2, .6)),
         ("WEBSITE", "bucckyy.github.io", "neon", ("kv2", .1, .05, .7)), ("EMAIL", "trantrungduc313", "fire", ("kv4", .1, .55, .6))]


def comms():
    w, h = 244, 76
    for k, v, pal, (ik, x, y, wf) in COMMS:
        acc = ACC[pal]
        body = (frame(w, h, 8, pal, photo(ik, x, y, wf, w, h), len(k) * 13) +
                f'<text x="16" y="30" font-size="14" letter-spacing="5" fill="{acc}" stroke="#12061F" stroke-width=".7" paint-order="stroke">{k}</text>'
                f'<text x="16" y="58" font-size="26" fill="#fff" stroke="#12061F" stroke-width="1" paint-order="stroke">{v}</text>'
                f'<circle class="bl" cx="{w - 14}" cy="14" r="4" fill="{acc}"/>' + brackets(w, h, acc, .9, 5, 9))
        (A / f"panel-link-{k.lower()}.svg").write_text(wrap(w, h, body, common_defs(w, h, 8, TINT[pal], acc), label=f"{k} {v}"))


EXPERIENCE = [
    ("01", "AI Engineer / Agent Builder", "MaxflowAI  ·  Ho Chi Minh City", "2026 - PRESENT", "sunset", ("kv4", .0, .02, 1.0),
     ["Built multi-agent systems for real clients: event ops, B2B sales automation, inventory logistics, email pipelines, HR.",
      "Python + JSON orchestration, event triggers, scheduled jobs, CRM / SMS / SMTP connectors, Playwright QA scripts."]),
    ("02", "AI Engineer Intern", "ITR VN  ·  Ho Chi Minh City", "NOV 2024 - JAN 2025", "neon", ("kv2", .0, .05, 1.0),
     ["PPG2BP-Net for cuffless BP: SBP MAE 9.76 ± 8.99 mmHg, DBP MAE 5.25 ± 5.26 mmHg on MIMIC-III.",
      "NumPy vectorisation cut processing latency ~40%; built an STM32 + MAX30102 + Bluetooth prototype."]),
    ("03", "Product Reviewer / QA Collaborator", "SNOW Vietnam  ·  Ho Chi Minh City", "APR - OCT 2025", "fire", ("kv4", .0, .33, 1.0),
     ["Reviewed AI AR filters and computer-vision effects; found low-light and occlusion failures.",
      "Documented defect patterns for the CV research team to improve output quality."]),
]


def experience():
    w, h = 1000, 150
    for n, role, org, dates, pal, (k, x, y, wf), bullets in EXPERIENCE:
        acc = ACC[pal]
        dw = 24 + len(dates) * 9
        body = (frame(w, h, 6, pal, photo(k, x, y, wf, w, h, q=74), int(n) * 19) +
                f'<text x="26" y="40" font-size="40" letter-spacing="1.5" fill="#fff" stroke="#12061F" stroke-width="1.2" paint-order="stroke">{role}</text>'
                f'<text x="26" y="66" font-size="19" letter-spacing="3" fill="{acc}" stroke="#12061F" stroke-width=".9" paint-order="stroke">{org.upper()}</text>'
                f'<rect x="{w - dw - 24}" y="18" width="{dw}" height="26" rx="13" fill="{acc}"/>'
                f'<text x="{w - 24 - dw / 2}" y="37" font-size="16" letter-spacing="2" text-anchor="middle" fill="#1A0830">{dates}</text>'
                f'<text x="26" y="100" font-size="21" fill="#fff" stroke="#12061F" stroke-width="1" paint-order="stroke">▸ {bullets[0]}</text>'
                f'<text x="26" y="128" font-size="21" fill="#fff" stroke="#12061F" stroke-width="1" paint-order="stroke">▸ {bullets[1]}</text>' + brackets(w, h, acc, .9, 7, 12))
        (A / f"panel-exp-{n}.svg").write_text(wrap(w, h, body, common_defs(w, h, 6, TINT[pal], acc), label=f"{role} at {org}"))


def awards():
    w, h = 1000, 120
    items = [("AWARD  ·  2025", "VPBank Technology Hackathon", "Senior Track", "#FFD56A"),
             ("AWARD  ·  2025", "BME Innovation Competition", "Team Lead, IoT BP monitor", "#7FE7FF"),
             ("EDUCATION  ·  2021 - 2025", "B.Eng. Electronics &amp; Telecom", "VNU-HCM  ·  GPA 3.4 / 4.0", "#FF7AA8")]
    cw = w // 3
    cols = ""
    for i, (tag, t1, t2, c) in enumerate(items):
        x = 24 + i * cw
        cols += (f'<text x="{x}" y="34" font-size="15" letter-spacing="4" fill="{c}" stroke="#12061F" stroke-width=".8" paint-order="stroke">{tag}</text>'
                 f'<text x="{x}" y="68" font-size="24" fill="#fff" stroke="#12061F" stroke-width="1" paint-order="stroke">{t1}</text>'
                 f'<text x="{x}" y="96" font-size="19" fill="#fff" opacity=".95" stroke="#12061F" stroke-width=".9" paint-order="stroke">{t2}</text>')
        if i:
            cols += f'<rect x="{i * cw - 8}" y="20" width="1" height="{h - 40}" fill="#fff" opacity=".35"/>'
    body = frame(w, h, 6, "dawn", photo("kv4", .0, .48, 1.0, w, h, q=72), 71) + cols + brackets(w, h, "#FFD56A", .9, 7, 12)
    (A / "panel-awards.svg").write_text(wrap(w, h, body, common_defs(w, h, 6, TINT["dawn"], "#FFD56A"), label="Awards and education"))


def ctas():
    specs = [("cta-portfolio.svg", 1000, 110, "SEC.00 // LAUNCH", "ENTER PORTFOLIO", "sunset", ("kv4", .0, .05, 1.0), 62),
             ("cta-repos.svg", 332, 100, "ARCHIVE", "REPOSITORIES", "neon", ("kv2", .1, .1, .8), 38),
             ("cta-cv.svg", 332, 100, "RESUME // PDF", "DOWNLOAD CV", "dawn", ("kv4", .3, .25, .7), 38),
             ("cta-contact.svg", 332, 100, "OPEN CHANNEL", "CONTACT", "fire", ("kv4", .2, .5, .7), 38)]
    for name, w, h, tag, title, pal, (k, x, y, wf), fs in specs:
        acc = ACC[pal]
        body = (frame(w, h, 8, pal, photo(k, x, y, wf, w, h, q=76), len(name)) +
                f'<text x="22" y="34" font-size="14" letter-spacing="5" fill="{acc}" stroke="#12061F" stroke-width=".8" paint-order="stroke">{tag}</text>'
                f'<text x="26" y="{h - 24}" font-size="{fs}" letter-spacing="{6 if w > 400 else 3}" fill="#fff" stroke="#12061F" stroke-width="1.2" paint-order="stroke">{title}</text>'
                f'<path d="M{w - 46} {h // 2 - 12}l20 12-20 12" fill="none" stroke="{acc}" stroke-width="3"/>'
                f'<circle class="bl" cx="{w - 16}" cy="16" r="4" fill="{acc}"/>' + brackets(w, h, acc, .95, 6, 12))
        (A / name).write_text(wrap(w, h, body, common_defs(w, h, 8, TINT[pal], acc), label=title))


if __name__ == "__main__":
    banners()
    pilot()
    systems()
    missions()
    comms()
    experience()
    awards()
    ctas()
    sizes = {p.name: p.stat().st_size // 1024 for p in sorted(A.glob("*.svg"))}
    print(sizes)
