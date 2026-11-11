#!/usr/bin/env python3
"""Generate the animated SVGs used by the profile README.

    python3 tools/gen.py            # writes into assets/

Everything is hand-built SVG + CSS/SMIL animation: no external fonts,
images, scripts or third-party widget services.
"""
from __future__ import annotations

import math
import random
from pathlib import Path
from xml.sax.saxutils import escape as esc

OUT = Path(__file__).resolve().parent.parent / "assets"

MONO = "ui-monospace,SFMono-Regular,'JetBrains Mono',Menlo,Consolas,'Liberation Mono','PingFang SC','Microsoft YaHei',monospace"

# warm phosphor palette: one amber lead, everything else muted earth tones
BG = "#0b0907"
PANEL = "#0f0c09"
LINE = "#2b241b"
TEXT = "#e9dfcb"
MUTED = "#8c7d66"
CYAN = "#ffb347"    # phosphor amber (lead)
VIOLET = "#cbb38a"  # sand
PINK = "#d9623b"    # rust
GREEN = "#a3bd7c"   # sage
AMBER = "#86a7b6"   # steel


def tw(s: str, size: float) -> float:
    return sum(size * (1.0 if ord(ch) > 0x2E80 else 0.6) for ch in s)


# ------------------------------------------------------------------ shared
def common_defs(uid: str) -> str:
    """Neon gradient, glow filter, scanline pattern, noise-ish vignette."""
    return f"""
<linearGradient id="{uid}-neon" x1="0" y1="0" x2="1" y2="0" gradientUnits="objectBoundingBox">
  <stop offset="0" stop-color="{CYAN}"/><stop offset=".5" stop-color="#ffd59a"/><stop offset="1" stop-color="{CYAN}"/>
  <animateTransform attributeName="gradientTransform" type="rotate" values="0 .5 .5;360 .5 .5" dur="8s" repeatCount="indefinite"/>
</linearGradient>
<linearGradient id="{uid}-neonh" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0" stop-color="{CYAN}"/><stop offset="1" stop-color="#ffcf87"/>
</linearGradient>
<filter id="{uid}-glow" x="-50%" y="-50%" width="200%" height="200%">
  <feGaussianBlur stdDeviation="3" result="b"/>
  <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
</filter>
<filter id="{uid}-bigglow" x="-50%" y="-50%" width="200%" height="200%">
  <feGaussianBlur stdDeviation="9"/>
</filter>
<pattern id="{uid}-scan" width="4" height="4" patternUnits="userSpaceOnUse">
  <rect width="4" height="1" fill="#000" opacity=".28"/>
</pattern>
<pattern id="{uid}-dots" width="22" height="22" patternUnits="userSpaceOnUse">
  <circle cx="1" cy="1" r="1" fill="#c9a46a" opacity=".10"/>
</pattern>
<radialGradient id="{uid}-vig" cx=".5" cy=".5" r=".75">
  <stop offset=".6" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".65"/>
</radialGradient>
<linearGradient id="{uid}-band" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="{CYAN}" stop-opacity="0"/><stop offset=".5" stop-color="{CYAN}" stop-opacity=".07"/><stop offset="1" stop-color="{CYAN}" stop-opacity="0"/>
</linearGradient>
"""


def frame(uid: str, w: int, h: int, title: str, right: str = "") -> str:
    """Rounded panel, running neon border, title bar."""
    per = 2 * (w + h)
    return f"""
<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="14" fill="{PANEL}"/>
<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="14" fill="url(#{uid}-dots)"/>
<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="14" fill="none" stroke="{LINE}" stroke-width="1.5"/>
<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="14" fill="none" stroke="url(#{uid}-neonh)" stroke-width="2"
      stroke-dasharray="{per*0.18:.0f} {per*0.82:.0f}" filter="url(#{uid}-glow)">
  <animate attributeName="stroke-dashoffset" values="0;-{per}" dur="7s" repeatCount="indefinite"/>
</rect>
<g font-family="{MONO}">
  <circle cx="22" cy="20" r="4.5" fill="none" stroke="{MUTED}"/><circle cx="38" cy="20" r="4.5" fill="none" stroke="{MUTED}"/><circle cx="54" cy="20" r="4.5" fill="{CYAN}"/>
  <text x="72" y="24" font-size="12" fill="{MUTED}">{esc(title)}</text>
  <text x="{w-20}" y="24" font-size="12" fill="{MUTED}" text-anchor="end">{esc(right)}</text>
</g>
<line x1="14" y1="38" x2="{w-14}" y2="38" stroke="{LINE}"/>
"""


def overlay(uid: str, w: int, h: int) -> str:
    """CRT scanlines + travelling scan band, clipped to the panel."""
    return f"""
<clipPath id="{uid}-clip"><rect x="1" y="1" width="{w-2}" height="{h-2}" rx="14"/></clipPath>
<g clip-path="url(#{uid}-clip)" pointer-events="none">
  <rect width="{w}" height="{h}" fill="url(#{uid}-scan)"/>
  <rect x="0" y="-120" width="{w}" height="120" fill="url(#{uid}-band)">
    <animate attributeName="y" values="-120;{h}" dur="6s" repeatCount="indefinite"/>
  </rect>
</g>
"""


def svg(w: int, h: int, label: str, body: str) -> str:
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
            f'role="img" aria-label="{esc(label)}">\n{body}\n</svg>\n')


def typed(uid: str, x: float, y: float, s: str, size: float, color: str, begin: float, cps: float = 18,
          weight: str = "normal") -> tuple[str, str, float]:
    """Text revealed char-by-char with a discrete clip animation. Returns (defs, body, end_time)."""
    n = max(len(s), 1)
    full = tw(s, size) + 6
    vals = ";".join(f"{full*k/n:.1f}" for k in range(n + 1))
    dur = n / cps
    d = (f'<clipPath id="{uid}"><rect x="{x-2}" y="{y-size*1.1:.1f}" height="{size*1.6:.1f}" width="0">'
         f'<animate attributeName="width" values="{vals}" calcMode="discrete" begin="{begin:.2f}s" dur="{dur:.2f}s" fill="freeze"/>'
         f'</rect></clipPath>')
    b = (f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{color}" '
         f'font-family="{MONO}" clip-path="url(#{uid})" xml:space="preserve">{esc(s)}</text>')
    return d, b, begin + dur


# ------------------------------------------------------------------ hero
def hero() -> str:
    W, H, u = 1000, 470, "h"
    defs = [common_defs(u)]
    body = []

    # background: halftone terrain (dot radius = height field), lit by a slow sweeping glow
    body.append(f'<rect width="{W}" height="{H}" rx="14" fill="{BG}"/>')
    body.append(frame(u, W, H, "xianyu@github  ~/  —  zsh  —  120×32", "● REC"))
    defs.append(f"""
<radialGradient id="h-lamp" cx=".5" cy=".5" r=".5">
  <stop offset="0" stop-color="{CYAN}" stop-opacity=".22"/><stop offset="1" stop-color="{CYAN}" stop-opacity="0"/>
</radialGradient>""")
    body.append(f'<ellipse cx="200" cy="360" rx="260" ry="120" fill="url(#h-lamp)">'
                f'<animate attributeName="cx" values="120;880;120" dur="14s" repeatCount="indefinite" calcMode="spline" keySplines=".45 0 .55 1;.45 0 .55 1"/></ellipse>')
    dots = []
    step = 13
    for row, y in enumerate(range(306, H - 46, step)):
        for x in range(20, W - 12, step):
            hgt = (math.sin(x / 70 + row * .35) * math.cos(x / 190 - row * .2) + 1) / 2
            hgt *= (row + 3) / 14
            r = 0.4 + 2.6 * hgt
            if r < .55:
                continue
            dots.append(f'<circle cx="{x}" cy="{y}" r="{r:.1f}"/>')
    body.append(f'<g fill="{CYAN}" opacity=".5">{"".join(dots)}</g>')

    # orbit system (right)
    ox, oy = 790, 170
    orb = [f'<g transform="translate({ox} {oy})" font-family="{MONO}">']
    orb.append(f'<circle r="34" fill="{BG}" stroke="url(#h-neon)" stroke-width="2" filter="url(#h-glow)"/>')
    orb.append(f'<text y="5" text-anchor="middle" font-size="14" font-weight="700" fill="{TEXT}">xy</text>')
    rings = [(70, "Go", CYAN, 9, "0 3"), (108, "Python", AMBER, 14, "2 6"), (146, "TypeScript", VIOLET, 21, "1 4")]
    for r, lab, col, dur, dash in rings:
        orb.append(f'<ellipse rx="{r}" ry="{r*0.42:.0f}" fill="none" stroke="{col}" stroke-opacity=".35" stroke-dasharray="{dash}"/>')
        # orbiting node: animateMotion along ellipse
        path = f"M{r},0 A{r},{r*0.42:.0f} 0 1,1 {-r},0 A{r},{r*0.42:.0f} 0 1,1 {r},0"
        orb.append(f'<g><animateMotion dur="{dur}s" repeatCount="indefinite" path="{path}"/>'
                   f'<circle r="5" fill="{col}" filter="url(#h-glow)"/>'
                   f'<text x="10" y="4" font-size="11" fill="{col}">{lab}</text></g>')
    orb.append("</g>")
    body.append("".join(orb))

    # glitch title
    tx, ty = 52, 132
    title = "AAAxianyu"
    defs.append(f"""
<style>
  .gl {{ animation: gl 4.2s steps(1) infinite; }}
  .gl2 {{ animation: gl2 4.2s steps(1) infinite; }}
  @keyframes gl {{ 0%,86%,100% {{ transform: translate(0,0); opacity:0 }} 87% {{ transform: translate(-4px,1px); opacity:.85 }}
                  89% {{ transform: translate(3px,-2px); opacity:.85 }} 91% {{ transform: translate(-2px,0); opacity:.85 }} 93% {{ opacity:0 }} }}
  @keyframes gl2 {{ 0%,86%,100% {{ transform: translate(0,0); opacity:0 }} 87% {{ transform: translate(4px,-1px); opacity:.85 }}
                   89% {{ transform: translate(-3px,2px); opacity:.85 }} 91% {{ transform: translate(2px,1px); opacity:.85 }} 93% {{ opacity:0 }} }}
  .blink {{ animation: bl 1s steps(1) infinite; }} @keyframes bl {{ 50% {{ opacity:0 }} }}
  .rec {{ animation: bl 1.4s steps(1) infinite; }}
</style>
""")
    tstyle = f'font-family="{MONO}" font-size="68" font-weight="800" letter-spacing="-1"'
    body.append(f'<text x="{tx}" y="{ty}" {tstyle} fill="url(#h-neonh)" filter="url(#h-bigglow)" opacity=".55">{title}</text>')
    body.append(f'<text class="gl" x="{tx}" y="{ty}" {tstyle} fill="{AMBER}">{title}</text>')
    body.append(f'<text class="gl2" x="{tx}" y="{ty}" {tstyle} fill="{PINK}">{title}</text>')
    body.append(f'<text x="{tx}" y="{ty}" {tstyle} fill="url(#h-neonh)">{title}</text>')
    body.append(f'<rect class="rec" x="{W-92}" y="15" width="8" height="8" rx="4" fill="{PINK}"/>')

    # typed lines
    t = 0.6
    lines = [
        ("$ ", "whoami --verbose", TEXT, None),
        ("", "backend · ai infra · quant  ——  Go / Python / TypeScript", MUTED, None),
        ("$ ", "cat mission.txt", TEXT, None),
        ("", "把 AI 从「对话」推进到「可执行、可审计」的系统里", CYAN, None),
    ]
    y = 182
    for i, (p, s, col, _) in enumerate(lines):
        if p:
            body.append(f'<text x="{tx}" y="{y}" font-family="{MONO}" font-size="15" fill="{GREEN}" opacity="0">{p}'
                        f'<set attributeName="opacity" to="1" begin="{t:.2f}s" fill="freeze"/></text>')
            d, b, t = typed(f"h-t{i}", tx + tw(p, 15), y, s, 15, col, t + 0.15)
            t += 0.35
        else:
            d, b, t = typed(f"h-t{i}", tx, y, s, 15, col, t, cps=60)
            t += 0.5
        defs.append(d)
        body.append(b)
        y += 30
    body.append(f'<g opacity="0"><set attributeName="opacity" to="1" begin="{t:.2f}s" fill="freeze"/>'
                f'<text x="{tx}" y="{y}" font-family="{MONO}" font-size="15" fill="{GREEN}">$ </text>'
                f'<rect class="blink" x="{tx+20}" y="{y-14}" width="9" height="18" fill="{GREEN}"/></g>')

    # tmux status bar
    sb = H - 38
    body.append(f'<rect x="14" y="{sb}" width="{W-28}" height="24" rx="5" fill="#16110b" stroke="{LINE}"/>')
    tabs = [("0:zsh*", GREEN), ("1:LocalMind", MUTED), ("2:Wayvia", MUTED), ("3:quant", MUTED)]
    x = 26
    for lab, col in tabs:
        body.append(f'<text x="{x}" y="{sb+16}" font-family="{MONO}" font-size="12" fill="{col}">{lab}</text>')
        x += tw(lab, 12) + 22
    body.append(f'<text x="{W-26}" y="{sb+16}" font-family="{MONO}" font-size="12" fill="{MUTED}" text-anchor="end">'
                f'<tspan fill="{VIOLET}">⎇ main</tspan>  ·  uptime since 2024-09  ·  <tspan fill="{CYAN}">utf-8</tspan></text>')

    body.append(overlay(u, W, H))
    body.append(f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="14" fill="url(#h-vig)" pointer-events="none"/>')
    return svg(W, H, "AAAxianyu — backend · ai infra · quant", f"<defs>{''.join(defs)}</defs>\n" + "\n".join(body))


# ------------------------------------------------------------------ flow helpers
def node(x, y, w, h, label, sub, col, uid, extra=""):
    return (f'<g font-family="{MONO}">'
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="9" fill="#15110c" stroke="{col}" stroke-opacity=".7" {extra}/>'
            f'<text x="{x+w/2}" y="{y+h/2-2}" text-anchor="middle" font-size="12.5" font-weight="700" fill="{col}">{esc(label)}</text>'
            f'<text x="{x+w/2}" y="{y+h/2+14}" text-anchor="middle" font-size="10" fill="{MUTED}">{esc(sub)}</text></g>')


def packets(path_d, col, uid, n=3, dur=3.0, r=3.2, begin=0.0):
    out = [f'<path d="{path_d}" fill="none" stroke="{col}" stroke-opacity=".28" stroke-width="1.5"/>']
    for k in range(n):
        out.append(f'<circle r="{r}" fill="{col}" filter="url(#{uid}-glow)">'
                   f'<animateMotion dur="{dur}s" begin="{begin + k*dur/n:.2f}s" repeatCount="indefinite" path="{path_d}"/></circle>')
    return "".join(out)


def logs(x, y, entries, cycle, uid):
    """Log lines that appear one by one, hold, then clear — looping."""
    out, n = [], len(entries)
    css = [f"<style>"]
    for i, (tag, col, msg) in enumerate(entries):
        a = i / n * 0.7 * 100
        css.append(f".{uid}l{i}{{animation:{uid}k{i} {cycle}s linear infinite}}"
                   f"@keyframes {uid}k{i}{{0%,{a:.1f}%{{opacity:0}}{a+1.5:.1f}%,92%{{opacity:1}}96%,100%{{opacity:0}}}}")
        out.append(f'<text class="{uid}l{i}" x="{x}" y="{y + i*19}" font-family="{MONO}" font-size="11.5" xml:space="preserve">'
                   f'<tspan fill="{col}">{esc(tag)}</tspan><tspan fill="{TEXT}"> {esc(msg)}</tspan></text>')
    css.append("</style>")
    return "".join(css) + "".join(out)


def tags(x, y, items):
    out = []
    for lab, col in items:
        w = tw(lab, 11) + 18
        out.append(f'<rect x="{x}" y="{y-14}" width="{w:.0f}" height="20" rx="10" fill="{col}" fill-opacity=".08" stroke="{col}" stroke-opacity=".6"/>'
                   f'<text x="{x+w/2:.0f}" y="{y}" text-anchor="middle" font-family="{MONO}" font-size="11" fill="{col}">{esc(lab)}</text>')
        x += w + 8
    return "".join(out)


# ------------------------------------------------------------------ LocalMind
def localmind() -> str:
    W, H, u = 492, 372, "lm"
    b = [f'<rect width="{W}" height="{H}" rx="14" fill="{BG}"/>', frame(u, W, H, "~/LocalMind", "TypeScript")]
    b.append(f'<text x="24" y="74" font-family="{MONO}" font-size="24" font-weight="800" fill="url(#{u}-neonh)">LocalMind</text>')
    b.append(f'<text x="24" y="98" font-family="{MONO}" font-size="12" fill="{MUTED}">本地优先 AI 工作区 · 让 AI 办公任务可执行、可审计</text>')

    # pipeline
    y = 128
    ns = [("prompt", "registry", CYAN), ("run", "durable", VIOLET), ("gate", "approve", AMBER), ("worker", "queue", PINK), ("audit", "ledger", GREEN)]
    nw, gap, x0 = 80, 13, 24
    for i, (lab, sub, col) in enumerate(ns):
        x = x0 + i * (nw + gap)
        extra = ""
        if lab == "gate":
            extra = ''
        b.append(node(x, y, nw, 46, lab, sub, col, u))
        if lab == "gate":
            b.append(f'<rect x="{x}" y="{y}" width="{nw}" height="46" rx="9" fill="none" stroke-width="2">'
                     f'<animate attributeName="stroke" values="{AMBER};{AMBER};{GREEN};{GREEN}" keyTimes="0;.45;.5;1" dur="3s" repeatCount="indefinite"/></rect>')
        if i < len(ns) - 1:
            sx, ex = x + nw, x + nw + gap
            b.append(packets(f"M{sx},{y+23} L{ex},{y+23}", col, u, n=1, dur=0.9, r=2.4, begin=i * 0.3))
    # return loop
    loop = f"M{x0+4*(nw+gap)+nw/2},{y+46} C{x0+4*(nw+gap)+nw/2},{y+86} {x0+nw/2},{y+86} {x0+nw/2},{y+46}"
    b.append(packets(loop, VIOLET, u, n=2, dur=4, r=2.6))
    b.append(f'<text x="{W/2}" y="{y+82}" text-anchor="middle" font-family="{MONO}" font-size="10" fill="{MUTED}" dy="18">timeline events · retries · cancellation</text>')

    # log
    b.append(f'<rect x="24" y="246" width="{W-48}" height="88" rx="8" fill="#0a0806" stroke="{LINE}"/>')
    b.append(logs(36, 266, [
        ("[run 0421]", VIOLET, "step=plan  status=ok  1.2s"),
        ("[gate]    ", AMBER, "preview + preflight → approved"),
        ("[worker]  ", PINK, "lease acquired · executing repair"),
        ("[audit]   ", GREEN, "3 side-effects recorded ✓"),
    ], 8, "lm"))
    b.append(tags(24, H - 16, [("TypeScript", CYAN), ("AI Infra", PINK), ("Local-first", GREEN)]))
    b.append(overlay(u, W, H))
    return svg(W, H, "LocalMind", f"<defs>{common_defs(u)}</defs>" + "".join(b))


# ------------------------------------------------------------------ Wayvia
def wayvia() -> str:
    W, H, u = 492, 372, "wv"
    b = [f'<rect width="{W}" height="{H}" rx="14" fill="{BG}"/>', frame(u, W, H, "~/Wayvia", "Python")]
    b.append(f'<text x="24" y="74" font-family="{MONO}" font-size="24" font-weight="800" fill="url(#{u}-neonh)">Wayvia 途序</text>')
    b.append(f'<text x="24" y="98" font-family="{MONO}" font-size="12" fill="{MUTED}">智能分流网关 · 国内直连，海外按需走自有出口</text>')

    # devices
    devs = [("phone", 130), ("laptop", 178), ("router", 226)]
    for lab, y in devs:
        b.append(f'<rect x="24" y="{y-14}" width="70" height="28" rx="6" fill="#15110c" stroke="{LINE}"/>'
                 f'<text x="59" y="{y+4}" text-anchor="middle" font-family="{MONO}" font-size="11" fill="{TEXT}">{lab}</text>')
        b.append(packets(f"M94,{y} C140,{y} 140,178 176,178", CYAN, u, n=2, dur=1.8, r=2.4, begin=y / 300))
    # gateway
    b.append(f'<circle cx="214" cy="178" r="38" fill="#15110c" stroke="url(#{u}-neon)" stroke-width="2" filter="url(#{u}-glow)"/>')
    b.append(f'<circle cx="214" cy="178" r="48" fill="none" stroke="{VIOLET}" stroke-opacity=".3" stroke-dasharray="3 6">'
             f'<animateTransform attributeName="transform" type="rotate" values="0 214 178;360 214 178" dur="12s" repeatCount="indefinite"/></circle>')
    b.append(f'<text x="214" y="176" text-anchor="middle" font-family="{MONO}" font-size="12" font-weight="700" fill="{TEXT}">wayvia</text>'
             f'<text x="214" y="191" text-anchor="middle" font-family="{MONO}" font-size="9.5" fill="{MUTED}">policy</text>')
    # routes
    b.append(packets("M252,166 C300,136 330,132 372,132", GREEN, u, n=3, dur=1.6))
    b.append(packets("M252,190 C300,226 330,232 372,232", VIOLET, u, n=3, dur=2.4))
    b.append(node(372, 112, 96, 40, "DIRECT", "cn · lan", GREEN, u))
    b.append(node(372, 212, 96, 40, "JP exit", "aliyun → ovpn", VIOLET, u))

    # rotating policy decisions
    b.append(f'<rect x="24" y="284" width="{W-48}" height="40" rx="8" fill="#0a0806" stroke="{LINE}"/>')
    rules = [("baidu.com", "DIRECT", GREEN), ("github.com", "PROXY → JP", VIOLET), ("192.168.1.1", "LAN", GREEN), ("claude.ai", "PROXY → JP", VIOLET)]
    n = len(rules)
    css = ["<style>"]
    for i, (dom, act, col) in enumerate(rules):
        s, e = i / n * 100, (i + 1) / n * 100
        css.append(f".wvr{i}{{animation:wvk{i} 8s steps(1) infinite}}@keyframes wvk{i}{{0%{{opacity:0}}{s:.1f}%{{opacity:1}}{e:.1f}%{{opacity:0}}}}")
        b.append(f'<text class="wvr{i}" x="36" y="309" font-family="{MONO}" font-size="12.5" xml:space="preserve" opacity="0">'
                 f'<tspan fill="{MUTED}">$ wayvia policy explain </tspan><tspan fill="{TEXT}">{dom}</tspan>'
                 f'<tspan fill="{MUTED}">  →  </tspan><tspan fill="{col}" font-weight="700">{act}</tspan></text>')
    css.append("</style>")
    b.insert(2, "".join(css))
    b.append(tags(24, H - 16, [("Python", AMBER), ("Networking", GREEN), ("Mihomo", VIOLET)]))
    b.append(overlay(u, W, H))
    return svg(W, H, "Wayvia", f"<defs>{common_defs(u)}</defs>" + "".join(b))


# ------------------------------------------------------------------ quant
def quant() -> str:
    W, H, u = 492, 372, "qt"
    b = [f'<rect width="{W}" height="{H}" rx="14" fill="{BG}"/>', frame(u, W, H, "~/quant", "Go · private")]
    b.append(f'<text x="24" y="74" font-family="{MONO}" font-size="24" font-weight="800" fill="url(#{u}-neonh)">quant</text>')
    b.append(f'<text x="24" y="98" font-family="{MONO}" font-size="12" fill="{MUTED}">OKX 永续合约量化框架 · 策略只产出目标敞口</text>')

    # candles
    cx0, cy0, cw, ch = 24, 114, W - 48, 128
    b.append(f'<rect x="{cx0}" y="{cy0}" width="{cw}" height="{ch}" rx="8" fill="#0a0806" stroke="{LINE}"/>')
    for k in range(1, 4):
        yy = cy0 + ch * k / 4
        b.append(f'<line x1="{cx0+8}" y1="{yy}" x2="{cx0+cw-8}" y2="{yy}" stroke="{LINE}" stroke-dasharray="2 4"/>')
    rnd = random.Random(42)
    n, p = 40, 100.0
    data = []
    for i in range(n):
        o = p
        p = p * (1 + rnd.gauss(0.003, 0.018) + 0.014 * math.sin(i / 5))
        hi, lo = max(o, p) * (1 + abs(rnd.gauss(0, .006))), min(o, p) * (1 - abs(rnd.gauss(0, .006)))
        data.append((o, hi, lo, p))
    mx, mn = max(d[1] for d in data), min(d[2] for d in data)
    sy = lambda v: cy0 + 26 + (mx - v) / (mx - mn) * (ch - 40)
    step = (cw - 24) / n
    cand, ema, e = [], [], data[0][3]
    for i, (o, hi, lo, c) in enumerate(data):
        x = cx0 + 12 + i * step
        col = GREEN if c >= o else PINK
        cand.append(f'<line x1="{x+step*0.35:.1f}" y1="{sy(hi):.1f}" x2="{x+step*0.35:.1f}" y2="{sy(lo):.1f}" stroke="{col}"/>'
                    f'<rect x="{x:.1f}" y="{sy(max(o,c)):.1f}" width="{step*0.7:.1f}" height="{max(1, abs(sy(o)-sy(c))):.1f}" fill="{col}" fill-opacity=".85"/>')
        e = e + (c - e) * 0.2
        ema.append(f"{x+step*0.35:.1f},{sy(e):.1f}")
    sig = []
    lows = sorted(range(3, n - 3), key=lambda i: data[i][2])[:1] + [6]
    highs = sorted(range(3, n - 3), key=lambda i: -data[i][1])[:1]
    for i in lows:
        x = cx0 + 12 + i * step + step * 0.35
        sig.append(f'<path d="M{x:.1f},{sy(data[i][2])+8:.1f} l-4,7 h8 z" fill="{CYAN}" filter="url(#{u}-glow)"/>')
    for i in highs:
        x = cx0 + 12 + i * step + step * 0.35
        sig.append(f'<path d="M{x:.1f},{sy(data[i][1])-8:.1f} l-4,-7 h8 z" fill="{AMBER}" filter="url(#{u}-glow)"/>')
    b.append(f'<clipPath id="qt-rev"><rect x="{cx0}" y="{cy0}" height="{ch}" width="0">'
             f'<animate attributeName="width" values="0;{cw};{cw};{cw}" keyTimes="0;.7;.95;1" dur="9s" repeatCount="indefinite"/></rect></clipPath>')
    b.append(f'<g clip-path="url(#qt-rev)">{"".join(cand)}'
             f'<polyline points="{" ".join(ema)}" fill="none" stroke="{VIOLET}" stroke-width="1.8" filter="url(#{u}-glow)"/>{"".join(sig)}</g>')
    b.append(f'<line y1="{cy0+6}" y2="{cy0+ch-6}" stroke="{CYAN}" stroke-opacity=".6">'
             f'<animate attributeName="x1" values="{cx0};{cx0+cw};{cx0+cw};{cx0+cw}" keyTimes="0;.7;.95;1" dur="9s" repeatCount="indefinite"/>'
             f'<animate attributeName="x2" values="{cx0};{cx0+cw};{cx0+cw};{cx0+cw}" keyTimes="0;.7;.95;1" dur="9s" repeatCount="indefinite"/></line>')
    b.append(f'<text x="{cx0+12}" y="{cy0+18}" font-family="{MONO}" font-size="10.5" fill="{MUTED}">ZEC-USDT-SWAP · 5m · 示意数据</text>')

    # architecture chain (same visual language as LocalMind)
    y = 258
    ns = [("strategy", "exposure", VIOLET), ("portfolio", "sizing", CYAN), ("risk", "limits", AMBER), ("exec", "idempotent", PINK), ("venue", "okx/sim", GREEN)]
    nw, gap, x0 = 80, 13, 24
    for i, (lab, sub, col) in enumerate(ns):
        x = x0 + i * (nw + gap)
        b.append(node(x, y, nw, 46, lab, sub, col, u))
        b.append(f'<rect x="{x}" y="{y}" width="{nw}" height="46" rx="9" fill="{col}" opacity="0">'
                 f'<animate attributeName="opacity" values="0;.16;0" dur="2.5s" begin="{i*0.5:.1f}s" repeatCount="indefinite"/></rect>')
        if i < len(ns) - 1:
            b.append(packets(f"M{x+nw},{y+23} L{x+nw+gap},{y+23}", col, u, n=1, dur=0.9, r=2.4, begin=i * 0.3))
    b.append(tags(24, H - 16, [("Go", CYAN), ("Python", AMBER), ("SQLite WAL", VIOLET), ("OKX", PINK)]))
    b.append(overlay(u, W, H))
    return svg(W, H, "quant", f"<defs>{common_defs(u)}</defs>" + "".join(b))


# ------------------------------------------------------------------ contact
POSTS = ["AI agent（agent 工作流程搭建）", "AI agent（prompt 优化）", "Pytorch 学习之路 (7)", "php 反序列化学习"]


def contact() -> str:
    W, H, u = 492, 372, "ct"
    b = [f'<rect width="{W}" height="{H}" rx="14" fill="{BG}"/>', frame(u, W, H, "~/.contact", "click to open ↗")]
    b.append(f'<text x="24" y="74" font-family="{MONO}" font-size="24" font-weight="800" fill="url(#{u}-neonh)">Blog</text>')
    b.append(f'<text x="24" y="98" font-family="{MONO}" font-size="12" fill="{MUTED}">技术笔记都写在 CSDN · AI Agent / PyTorch / 安全</text>')
    # big call-to-action
    bx, by, bw, bh = 24, 116, W - 48, 64
    b.append(f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="10" fill="{CYAN}" fill-opacity=".1" stroke="{CYAN}" stroke-width="1.5">'
             f'<animate attributeName="fill-opacity" values=".06;.2;.06" dur="2.4s" repeatCount="indefinite"/></rect>')
    b.append(f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" rx="10" fill="none" stroke="{CYAN}" stroke-width="5" opacity=".25" filter="url(#{u}-glow)">'
             f'<animate attributeName="opacity" values=".1;.45;.1" dur="2.4s" repeatCount="indefinite"/></rect>')
    b.append(f'<text x="{bx+20}" y="{by+28}" font-family="{MONO}" font-size="19" font-weight="800" fill="{CYAN}">CSDN 博客 ↗</text>')
    b.append(f'<text x="{bx+20}" y="{by+48}" font-family="{MONO}" font-size="11.5" fill="{TEXT}" opacity=".8">blog.csdn.net/2401_85922036</text>')
    b.append(f'<text x="{bx+bw-20}" y="{by+38}" text-anchor="end" font-family="{MONO}" font-size="26" fill="{CYAN}" filter="url(#{u}-glow)">»</text>')
    # posts
    b.append(f'<text x="24" y="210" font-family="{MONO}" font-size="12" fill="{MUTED}"><tspan fill="{GREEN}">$</tspan> ls posts/ --recent</text>')
    for i, t in enumerate(POSTS):
        y = 236 + i * 23
        b.append(f'<g opacity="0"><set attributeName="opacity" to="1" begin="{0.4+i*0.25:.2f}s" fill="freeze"/>'
                 f'<text x="24" y="{y}" font-family="{MONO}" font-size="12.5" fill="{TEXT}"><tspan fill="{CYAN}">▸ </tspan>{esc(t)}</text></g>')
    b.append(tags(24, H - 16, [("AI Agent", CYAN), ("PyTorch", AMBER), ("Web 安全", PINK)]))
    b.append(overlay(u, W, H))
    return svg(W, H, "CSDN blog", f"<defs>{common_defs(u)}</defs>" + "".join(b))


# ------------------------------------------------------------------ htop
LANGS = [("Go", 55.3, CYAN), ("Python", 15.8, AMBER), ("TypeScript", 13.3, VIOLET), ("Dart", 4.6, "#6f8f9c"),
         ("JavaScript", 4.5, "#b79a5c"), ("HTML/CSS", 5.3, PINK), ("Shell", 0.7, GREEN)]


def htop() -> str:
    W, H, u = 1000, 250, "ht"
    b = [f'<rect width="{W}" height="{H}" rx="14" fill="{BG}"/>', frame(u, W, H, "htop --languages", "go · python · typescript")]
    y = 66
    bar_x, bar_w = 150, 560
    cells = 50
    cw = bar_w / cells
    defs = [f'<pattern id="ht-cells" width="{cw:.2f}" height="12" patternUnits="userSpaceOnUse">'
            f'<rect width="{cw-2:.2f}" height="12" rx="1.5" fill="#fff"/></pattern>'
            f'<mask id="ht-m" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}">'
            f'<rect x="{bar_x}" y="0" width="{bar_w}" height="{H}" fill="url(#ht-cells)"/></mask>']
    for i, (lab, pct, col) in enumerate(LANGS):
        full = bar_w * max(pct / 55.3, 1 / cells)
        b.append(f'<text x="24" y="{y+4}" font-family="{MONO}" font-size="13" fill="{col}">{i}  {lab}</text>')
        b.append(f'<text x="{bar_x-10}" y="{y+4}" font-family="{MONO}" font-size="13" fill="{MUTED}">[</text>')
        b.append(f'<g mask="url(#ht-m)"><rect x="{bar_x}" y="{y-8}" width="{bar_w}" height="12" fill="{LINE}"/>'
                 f'<rect x="{bar_x}" y="{y-8}" width="{full:.1f}" height="12" fill="{col}">'
                 f'<animate attributeName="width" values="0;{full:.1f}" dur="1.2s" begin="{0.2+i*0.15:.2f}s" fill="freeze" '
                 f'calcMode="spline" keySplines=".2 .8 .2 1"/></rect></g>')
        b.append(f'<text x="{bar_x+bar_w+4}" y="{y+4}" font-family="{MONO}" font-size="13" fill="{MUTED}">]</text>')
        b.append(f'<text x="{bar_x+bar_w+60}" y="{y+4}" text-anchor="end" font-family="{MONO}" font-size="13" fill="{TEXT}">{pct:.1f}%</text>')
        y += 24
    # real account stats
    sx, sw, sy0, sh = 790, 186, 54, 160
    b.append(f'<rect x="{sx}" y="{sy0}" width="{sw}" height="{sh}" rx="8" fill="#0a0806" stroke="{LINE}"/>')
    stats = [("repos", "29", CYAN), ("own projects", "19", VIOLET), ("contribs / yr", "118", GREEN), ("since", "2024-09", AMBER)]
    for k, (lab, val, col) in enumerate(stats):
        yy = sy0 + 30 + k * 36
        b.append(f'<text x="{sx+14}" y="{yy}" font-family="{MONO}" font-size="11" fill="{MUTED}">{lab}</text>'
                 f'<text x="{sx+sw-14}" y="{yy}" text-anchor="end" font-family="{MONO}" font-size="16" font-weight="700" fill="{col}">{val}</text>')
    b.append(overlay(u, W, H))
    return svg(W, H, "language breakdown", f"<defs>{common_defs(u)}{''.join(defs)}</defs>" + "".join(b))


# ------------------------------------------------------------------ divider / footer
def footer() -> str:
    W, H, u = 1000, 90, "ft"
    pts = " ".join(f"{x},{45 + 14*math.sin(x/38)*math.sin(x/170):.1f}" for x in range(0, W + 1, 6))
    pts2 = " ".join(f"{x},{45 + 10*math.sin(x/29+1)*math.cos(x/210):.1f}" for x in range(0, W + 1, 6))
    b = [f'<polyline points="{pts}" fill="none" stroke="url(#{u}-neonh)" stroke-width="2" filter="url(#{u}-glow)">'
         f'<animateTransform attributeName="transform" type="translate" values="0 0;-60 0;0 0" dur="6s" repeatCount="indefinite"/></polyline>',
         f'<polyline points="{pts2}" fill="none" stroke="{VIOLET}" stroke-opacity=".4" stroke-width="1.2">'
         f'<animateTransform attributeName="transform" type="translate" values="0 0;50 0;0 0" dur="5s" repeatCount="indefinite"/></polyline>',
         f'<rect x="{W/2-70}" y="31" width="140" height="28" rx="14" fill="{BG}" stroke="{LINE}"/>',
         f'<text x="{W/2}" y="50" text-anchor="middle" font-family="{MONO}" font-size="13" fill="{TEXT}">EOF<tspan fill="{GREEN}"> ▍</tspan></text>']
    return svg(W, H, "EOF", f"<defs>{common_defs(u)}</defs>" + "".join(b))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for old in ("quant.svg",):
        (OUT / old).unlink(missing_ok=True)
    files = {"hero.svg": hero(), "localmind.svg": localmind(), "wayvia.svg": wayvia(),
             "quant-card.svg": quant(), "contact.svg": contact(), "langs.svg": htop(), "eof.svg": footer()}
    for name, content in files.items():
        (OUT / name).write_text(content, encoding="utf-8")
        print(f"{name:14} {len(content)/1024:6.1f} KB")


if __name__ == "__main__":
    main()
