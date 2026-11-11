#!/usr/bin/env python3
"""Generate the terminal-style SVGs used by the profile README.

Run:  python3 tools/gen.py   (writes into assets/)
All assets are self-contained: no external fonts, images or services.
"""
from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path(__file__).resolve().parent.parent / "assets"

FONT = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', 'PingFang SC', 'Microsoft YaHei', monospace"
C = {
    "bg": "#0f1218",
    "bar": "#171b23",
    "border": "#2a303b",
    "text": "#d7dde6",
    "muted": "#7d8796",
    "green": "#7ee0a1",
    "blue": "#7cb8ff",
    "amber": "#f2b35e",
    "pink": "#f08bb0",
}


def text_w(s: str, size: float) -> float:
    """Rough rendered width for a monospace font with CJK fallback."""
    w = 0.0
    for ch in s:
        w += size * (1.0 if ord(ch) > 0x2E80 else 0.61)
    return w


def window(w: int, h: int, title: str, body: str, extra_defs: str = "") -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{escape(title)}">
<defs>{extra_defs}</defs>
<style>
  text {{ font-family: {FONT}; }}
  .cur {{ animation: blink 1s steps(1) infinite; }}
  @keyframes blink {{ 50% {{ opacity: 0; }} }}
</style>
<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="10" fill="{C['bg']}" stroke="{C['border']}"/>
<path d="M0.5 10.5 a10 10 0 0 1 10 -10 h{w-21} a10 10 0 0 1 10 10 v24 h-{w-1} z" fill="{C['bar']}"/>
<line x1="0.5" y1="34.5" x2="{w-0.5}" y2="34.5" stroke="{C['border']}"/>
<circle cx="20" cy="17.5" r="6" fill="#ff5f57"/><circle cx="40" cy="17.5" r="6" fill="#febc2e"/><circle cx="60" cy="17.5" r="6" fill="#28c840"/>
<text x="{w/2}" y="22" text-anchor="middle" font-size="12" fill="{C['muted']}">{escape(title)}</text>
{body}
</svg>
"""


# ---------------------------------------------------------------- hero
def hero() -> str:
    size, lh, x0, y = 15, 27, 26, 70
    script = [
        ("cmd", "whoami"),
        ("out", [("AAAxianyu", C["amber"]), ("  ·  后端 / AI 基础设施 / 量化交易", C["text"])]),
        ("cmd", "cat now.txt"),
        ("out", [("把 AI 从「对话」推进到「可执行、可审计」的系统里", C["text"])]),
        ("cmd", "echo $STACK"),
        ("out", [("Go  Python  TypeScript  Swift  Docker  Linux", C["green"])]),
        ("cmd", "ls ~/projects --pinned"),
        ("out", [("LocalMind/", C["blue"]), ("   ", C["text"]), ("Wayvia/", C["blue"]), ("   ", C["text"]), ("quant/", C["blue"])]),
    ]
    prompt = [("~", C["blue"]), (" $ ", C["muted"])]
    prompt_w = text_w("~ $ ", size)

    defs, body = [], []
    t = 0.4  # seconds
    for i, (kind, val) in enumerate(script):
        gid = f"l{i}"
        if kind == "cmd":
            spans = "".join(f'<tspan fill="{c}">{escape(s)}</tspan>' for s, c in prompt)
            body.append(f'<g opacity="0"><set attributeName="opacity" to="1" begin="{t:.2f}s" fill="freeze"/>'
                        f'<text x="{x0}" y="{y}" font-size="{size}" xml:space="preserve">{spans}</text></g>')
            n = len(val)
            dur = 0.07 * n
            full = text_w(val, size) + 4
            steps = ";".join(f"{full * k / n:.1f}" for k in range(n + 1))
            defs.append(f'<clipPath id="{gid}"><rect x="{x0 + prompt_w:.1f}" y="{y - lh + 6}" height="{lh}" width="0">'
                        f'<animate attributeName="width" values="{steps}" calcMode="discrete" begin="{t + 0.25:.2f}s" dur="{dur:.2f}s" fill="freeze"/></rect></clipPath>')
            body.append(f'<text x="{x0 + prompt_w:.1f}" y="{y}" font-size="{size}" fill="{C["text"]}" clip-path="url(#{gid})">{escape(val)}</text>')
            t += 0.25 + dur + 0.25
        else:
            spans = "".join(f'<tspan fill="{c}">{escape(s)}</tspan>' for s, c in val)
            body.append(f'<g opacity="0"><set attributeName="opacity" to="1" begin="{t:.2f}s" fill="freeze"/>'
                        f'<text x="{x0}" y="{y}" font-size="{size}" xml:space="preserve">{spans}</text></g>')
            t += 0.35
        y += lh if kind == "cmd" else lh + 8

    spans = "".join(f'<tspan fill="{c}">{escape(s)}</tspan>' for s, c in prompt)
    body.append(f'<g opacity="0"><set attributeName="opacity" to="1" begin="{t:.2f}s" fill="freeze"/>'
                f'<text x="{x0}" y="{y}" font-size="{size}" xml:space="preserve">{spans}</text>'
                f'<rect class="cur" x="{x0 + prompt_w:.1f}" y="{y - 14}" width="9" height="18" fill="{C["green"]}"/></g>')
    h = y + 26
    return window(840, h, "xianyu@github: ~ — zsh", "\n".join(body), "".join(defs))


# ---------------------------------------------------------------- cards
def card(name: str, cmd: str, lines: list[str], tags: list[tuple[str, str]], private: bool = False) -> str:
    w, h, x0 = 400, 236, 22
    out = [f'<text x="{x0}" y="66" font-size="14" xml:space="preserve"><tspan fill="{C["blue"]}">~/{escape(name)}</tspan><tspan fill="{C["muted"]}"> $ </tspan><tspan fill="{C["text"]}">{escape(cmd)}</tspan></text>']
    y = 96
    for ln in lines:
        out.append(f'<text x="{x0}" y="{y}" font-size="13.5" fill="{C["text"]}">{escape(ln)}</text>')
        y += 23
    # tags
    tx, ty = x0, h - 24
    for label, color in tags:
        tw = text_w(label, 12) + 18
        out.append(f'<rect x="{tx}" y="{ty - 15}" width="{tw:.1f}" height="22" rx="11" fill="none" stroke="{color}" stroke-opacity="0.65"/>'
                   f'<text x="{tx + tw / 2:.1f}" y="{ty}" font-size="12" text-anchor="middle" fill="{color}">{escape(label)}</text>')
        tx += tw + 8
    if private:
        out.append(f'<text x="{w - x0}" y="{ty}" font-size="12" text-anchor="end" fill="{C["muted"]}">private</text>')
    return window(w, h, name, "\n".join(out))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "hero.svg").write_text(hero(), encoding="utf-8")
    (OUT / "localmind.svg").write_text(card(
        "LocalMind", "cat README",
        ["基于 AFFiNE 的本地优先 AI 工作区",
         "持久化运行状态 · 审批闸门 · Worker 队列",
         "Prompt / Model / Provider 注册表",
         "让 AI 办公任务可执行、可审计"],
        [("TypeScript", C["blue"]), ("AI Infra", C["pink"])]), encoding="utf-8")
    (OUT / "wayvia.svg").write_text(card(
        "Wayvia", "wayvia --help",
        ["Wayvia 途序 · 智能分流代理网关",
         "国内直连，海外按需走自有出口",
         "统一 Mihomo 订阅 · 设备与订阅管理",
         "隔离 Docker 链路实验 + 完整验收"],
        [("Python", C["amber"]), ("Networking", C["green"])]), encoding="utf-8")
    (OUT / "quant.svg").write_text(card(
        "quant", "go run ./cmd/quant-runtime",
        ["OKX 永续合约模块化量化框架",
         "策略 → 组合规划 → 风控 → 执行",
         "回测回放 / 本地撮合 / demo & live",
         "SQLite WAL 日志 + 双路径交易审计"],
        [("Go", C["blue"]), ("Python", C["amber"]), ("Quant", C["pink"])], private=True), encoding="utf-8")


if __name__ == "__main__":
    main()
