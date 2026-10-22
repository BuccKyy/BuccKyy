#!/usr/bin/env python3
"""Generate assets/hero.svg: animated violet-orange sunset mobile-suit scene.

Palette sampled from the Hathaway key visual mood (violet sky, magenta/orange
horizon, cyan beam, amber flare). All artwork is original vector work.
Run: python3 tools/hero_gen.py
"""
import base64
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from panels_gen import FONT as _SUBSET_FONT, photo  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
FONT = _SUBSET_FONT

CX = 640  # mech centre line


def half(extra=""):
    """Right half of the mech in local coords (x=0 is the centre line)."""
    return f"""
<g {extra}>
  <polygon points="14,70 26,60 30,128 18,132" fill="#2A1646"/>
  <polygon points="26,136 66,128 78,150 60,176 34,176" fill="url(#armor)" stroke="#FF9A5C" stroke-opacity=".7"/>
  <polygon points="60,176 80,160 94,196 78,226 58,214" fill="url(#armor2)" stroke="#FF9A5C" stroke-opacity=".6"/>
  <polygon points="78,226 96,206 112,250 96,270 74,252" fill="#3A2058" stroke="#FFB35C" stroke-opacity=".8"/>
  <polygon points="0,134 26,140 34,176 24,214 0,220" fill="url(#armor)" stroke="#FF9A5C" stroke-opacity=".5"/>
  <polygon points="4,150 18,154 16,164 4,162" fill="#FF8A3D"/>
  <polygon points="0,220 22,216 26,240 0,248" fill="#2A1646"/>
  <polygon points="22,216 48,222 56,270 44,330 24,340 14,300 18,250" fill="url(#armor2)" stroke="#FF9A5C" stroke-opacity=".6"/>
  <polygon points="0,100 14,100 18,116 14,128 6,134 0,134" fill="#E9DDF7"/>
  <polygon points="4,104 34,62 38,64 12,110" fill="#FFD56A"/>
  <polygon points="0,92 6,96 0,100" fill="#FFD56A"/>
  <polygon points="118,150 132,148 138,300 124,302" fill="#CBB6E8" stroke="#FF9A5C" stroke-opacity=".7"/>
</g>"""


def mech():
    return f"""
<g id="mech" transform="translate({CX} 0)">
{half()}
{half('transform="scale(-1 1)"')}
  <rect class="visor" x="-9" y="116" width="18" height="5" rx="2" fill="#7FE7FF"/>
</g>"""


COMETS = [
    (80, 40, 0.0), (220, -10, 1.3), (540, 20, 2.1), (760, 10, 0.7),
    (880, 60, 3.0), (400, -30, 1.9),
]


def comets():
    out = []
    for x, y, d in COMETS:
        out.append(
            f'<g class="comet" style="animation-delay:{d}s">'
            f'<line x1="{x}" y1="{y}" x2="{x+46}" y2="{y-30}" stroke="url(#tail)" stroke-width="2.4" stroke-linecap="round"/>'
            f'<circle cx="{x}" cy="{y}" r="3.2" fill="#FFD56A"/></g>'
        )
    return "\n".join(out)


HERO = photo("kv4", .0, .07, 1.0, 1000, 440, q=62, scale=1.0)

SVG = f"""<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="440" viewBox="0 0 1000 440" role="img" aria-labelledby="t d">
<title id="t">BuccKyy — AI Engineer</title>
<desc id="d">Animated violet and orange sunset battle scene with a mobile suit, a cyan beam and flares.</desc>
<style>
@font-face{{font-family:BC;src:url(data:font/ttf;base64,{FONT})}}
.ti{{font-family:BC,'Arial Narrow',sans-serif;letter-spacing:.22em}}
#scene{{animation:grade 14s ease-in-out infinite}}
@keyframes grade{{0%{{filter:brightness(2.2) saturate(1.6)}}7%{{filter:none}}93%{{filter:none}}100%{{filter:brightness(.35)}}}}
#world{{transform-origin:500px 260px;animation:zoom 14s ease-out infinite}}
@keyframes zoom{{0%{{transform:scale(1.14)}}100%{{transform:scale(1)}}}}
#mech{{animation:float 5s ease-in-out infinite}}
@keyframes float{{0%,100%{{transform:translate({CX}px,0)}}50%{{transform:translate({CX}px,-7px)}}}}
.visor{{animation:glow 1.8s ease-in-out infinite}}
@keyframes glow{{0%,100%{{opacity:.5}}50%{{opacity:1}}}}
.beam{{animation:beam 14s ease-in-out infinite;transform-origin:320px 0}}
@keyframes beam{{0%,12%{{opacity:0;transform:rotate(-8deg)}}18%{{opacity:1}}30%{{transform:rotate(0)}}60%{{transform:rotate(5deg);opacity:.85}}74%{{opacity:1}}100%{{opacity:.7;transform:rotate(-3deg)}}}}
.comet{{animation:fly 3.6s linear infinite;opacity:0}}
@keyframes fly{{0%{{opacity:0;transform:translate(-60px,50px)}}12%{{opacity:1}}100%{{opacity:0;transform:translate(260px,-170px)}}}}
.cloud{{animation:drift 22s linear infinite alternate}}
@keyframes drift{{from{{transform:translateX(-40px)}}to{{transform:translateX(60px)}}}}
.chalk{{stroke-dasharray:6 8;animation:dash 6s linear infinite}}
@keyframes dash{{to{{stroke-dashoffset:-140}}}}
.pillar{{animation:pillar 5s ease-in-out infinite}}
@keyframes pillar{{0%,100%{{opacity:.55}}50%{{opacity:.95}}}}
.bar-t{{transform-box:fill-box;transform-origin:top;animation:barT 14s ease-out infinite}}
.bar-b{{transform-box:fill-box;transform-origin:bottom;animation:barB 14s ease-out infinite}}
@keyframes barT{{0%{{transform:scaleY(2.4)}}8%,100%{{transform:none}}}}
@keyframes barB{{0%{{transform:scaleY(2.4)}}8%,100%{{transform:none}}}}
#wipe1{{animation:wipe 14s cubic-bezier(.7,0,.2,1) infinite}}
#wipe2{{animation:wipe 14s cubic-bezier(.7,0,.2,1) .5s infinite}}
@keyframes wipe{{0%,6%{{width:0}}20%,92%{{width:560px}}100%{{width:0}}}}
.scan{{animation:scan 9s linear infinite}}
@keyframes scan{{from{{transform:translateY(-440px)}}to{{transform:translateY(440px)}}}}
.pulse{{animation:glow 1.4s ease-in-out infinite}}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}
</style>
<defs>
<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
<stop offset="0" stop-color="#2B1370"/><stop offset=".26" stop-color="#7A2BA8"/><stop offset=".46" stop-color="#D93E7E"/>
<stop offset=".64" stop-color="#FF7A3A"/><stop offset=".8" stop-color="#FFD05C"/><stop offset="1" stop-color="#FF9A4D"/></linearGradient>
<linearGradient id="mesa" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FF6A3D"/><stop offset="1" stop-color="#8A1F58"/></linearGradient>
<linearGradient id="armor" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#6A4A9E"/><stop offset="1" stop-color="#26123F"/></linearGradient>
<linearGradient id="armor2" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#E7D8F6"/><stop offset="1" stop-color="#7A66C0"/></linearGradient>
<linearGradient id="tail" x1="0" y1="1" x2="1" y2="0"><stop offset="0" stop-color="#FFD56A" stop-opacity="0"/><stop offset="1" stop-color="#FFF1B8"/></linearGradient>
<linearGradient id="beamg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#C8FBFF" stop-opacity=".0"/><stop offset=".25" stop-color="#7FE7FF"/><stop offset=".6" stop-color="#2FD0F0"/><stop offset="1" stop-color="#C8FBFF" stop-opacity=".1"/></linearGradient>
<linearGradient id="pil" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#FFE9A8" stop-opacity="0"/><stop offset=".55" stop-color="#FFD56A"/><stop offset="1" stop-color="#FFB35C" stop-opacity="0"/></linearGradient>
<linearGradient id="fade" x1="0" y1="0" x2="0" y2="1"><stop offset=".55" stop-color="#0B0414" stop-opacity="0"/><stop offset="1" stop-color="#0B0414" stop-opacity=".95"/></linearGradient>
<linearGradient id="ttl" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#FFF1B8"/><stop offset=".5" stop-color="#FFB35C"/><stop offset="1" stop-color="#FF5C9A"/></linearGradient>
<linearGradient id="tn" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#7A2BA8" stop-opacity=".25"/><stop offset="1" stop-color="#FF9A5C" stop-opacity=".12"/></linearGradient>
<linearGradient id="lft" x1="0" x2="1"><stop offset="0" stop-color="#0B0414" stop-opacity=".7"/><stop offset="1" stop-color="#0B0414" stop-opacity="0"/></linearGradient>
<filter id="blur" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="14"/></filter>
<filter id="blur2"><feGaussianBlur stdDeviation="3"/></filter>
<pattern id="sl" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="1" fill="#fff" fill-opacity=".05"/></pattern>
<clipPath id="frame"><rect width="1000" height="440"/></clipPath>
<clipPath id="c1"><rect id="wipe1" x="44" y="318" width="560" height="64"/></clipPath>
<clipPath id="c2"><rect id="wipe2" x="44" y="388" width="560" height="20"/></clipPath>
</defs>
<g clip-path="url(#frame)">
<g id="scene">
<g id="world">
  <image href="{HERO}" width="1000" height="440" preserveAspectRatio="xMidYMid slice"/>
  <rect width="1000" height="440" fill="url(#tn)"/>
  {comets()}
</g>
<rect width="1000" height="440" fill="url(#fade)"/>
<rect width="620" height="440" fill="url(#lft)"/>
</g>
<rect class="scan" y="0" width="1000" height="120" fill="#fff" fill-opacity=".035"/>
<rect width="1000" height="440" fill="url(#sl)"/>
<path d="M18 40V30H32M968 30H982V40M982 400V410H968M32 410H18V400" fill="none" stroke="#7FE7FF" stroke-width="2" opacity=".9"/>
<text class="ti" x="44" y="370" font-size="72" fill="url(#ttl)" stroke="#0B0414" stroke-width="1.2" paint-order="stroke">BUCCKYY</text>
<text class="ti" x="46" y="408" font-size="26" fill="#7FE7FF" stroke="#0B0414" stroke-width="1" paint-order="stroke">AGENTIC AI ENGINEER  //  HO CHI MINH</text>
<circle class="pulse" cx="966" cy="52" r="6" fill="#FF5C9A"/>
<text class="ti" x="946" y="60" font-size="22" fill="#FFE9A8" text-anchor="end" stroke="#0B0414" stroke-width="1" paint-order="stroke">OPEN TO REMOTE ROLES</text>
</g>
</svg>
"""

out = ROOT / "assets/hero.svg"
out.write_text(SVG)
print(out, out.stat().st_size, "bytes")
