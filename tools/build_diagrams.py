#!/usr/bin/env python3
"""事業ページの「ハブ + 6項目」図をアニメーション付きSVGとして生成する。

使い方:
    python3 tools/build_diagrams.py <出力フォルダ>

出力(<出力フォルダ>に作られる):
    sns.light.svg / creative.light.svg      単体ファイル(ライト)
    sns.inline.light.svg / ...              HTMLに埋め込む用(下層ページ: sns-marketing.html / creative.html)
    *.inline.dark.desktop.svg / .mobile.svg HTMLに埋め込む用(トップ index.html のダーク版)

項目名・アイコン・ハブの文言は下の SNS / CREATIVE を書き換える。
"""
import math, sys, pathlib

CX, CY = 700, 457
R_IN, R_DASH, R_OUT = 198, 298, 398
VIOLET, CYAN = "#8B7CFF", "#43E5FF"
H = 130

# lucide風 24x24 アイコン(線のみ)
ICONS = {
    "users": '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
    "yen": '<circle cx="12" cy="12" r="10"/><path d="m8.5 8 3.5 4 3.5-4"/><path d="M12 12v6"/><path d="M8.5 12.5h7"/><path d="M8.5 15.5h7"/>',
    "click": '<path d="M14 4.1 12 6"/><path d="m5.1 8-2.9-.8"/><path d="m6 12-1.9 2"/><path d="M7.2 2.2 8 5.1"/><path d="M9.037 9.69a.498.498 0 0 1 .653-.653l11 4.5a.5.5 0 0 1-.074.949l-4.349 1.041a1 1 0 0 0-.74.739l-1.04 4.35a.5.5 0 0 1-.95.074z"/>',
    "phone": '<rect width="14" height="20" x="5" y="2" rx="2" ry="2"/><path d="M12 18h.01"/>',
    "trend": '<path d="M22 7 13.5 15.5 8.5 10.5 2 17"/><path d="M16 7h6v6"/>',
    "mega": '<path d="m3 11 18-5v12L3 14v-3z"/><path d="M11.6 16.8a3 3 0 1 1-5.8-1.6"/>',
    "share": '<circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><path d="m8.59 13.51 6.83 3.98"/><path d="m15.41 6.51-6.82 3.98"/>',
    "tv": '<rect width="20" height="15" x="2" y="7" rx="2" ry="2"/><path d="m17 2-5 5-5-5"/>',
    "globe": '<circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/>',
    "video": '<path d="m16 13 5.223 3.482a.5.5 0 0 0 .777-.416V7.87a.5.5 0 0 0-.752-.432L16 10.5"/><rect x="2" y="6" width="14" height="12" rx="2"/>',
    "clap": '<path d="M20.2 6 3 11l-.9-2.4c-.3-1.1.3-2.2 1.3-2.5l13.5-4c1.1-.3 2.2.3 2.5 1.3Z"/><path d="m6.2 5.3 3.1 3.9"/><path d="m12.4 3.4 3.1 4"/><path d="M3 11h18v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2Z"/>',
    "camera": '<path d="M13.997 4a2 2 0 0 1 1.76 1.05l.486.9A2 2 0 0 0 18.003 7H20a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V9a2 2 0 0 1 2-2h1.997a2 2 0 0 0 1.759-1.048l.489-.904A2 2 0 0 1 10.004 4z"/><circle cx="12" cy="13" r="3"/>',
    "cube": '<path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/><path d="m3.3 7 8.7 5 8.7-5"/><path d="M12 22V12"/>',
    "film": '<rect width="18" height="18" x="3" y="3" rx="2"/><path d="M7 3v18"/><path d="M3 7.5h4"/><path d="M3 12h18"/><path d="M3 16.5h4"/><path d="M17 3v18"/><path d="M17 7.5h4"/><path d="M17 16.5h4"/>',
}

# カードの位置(時計回り: 左上 → 右上 → 右 → 右下 → 左下 → 左)。(x, y, 幅) と ハブからの角度
# 上下は文字を大きくするため幅470(中心位置は従来どおり)、左右は端まで使って382
SLOTS = [
    ((142, 1, 470), 120),
    ((788, 1, 470), 60),
    ((1017, 392, 382), 0),
    ((788, 783, 470), -60),
    ((142, 783, 470), -120),
    ((1, 392, 382), 180),
]


def _cards(items):
    """items: [(ラベル, 色, アイコン名)] ×6 → 位置を付けたカード定義"""
    assert len(items) == 6
    return [(lab, rect, col, icon, deg) for (lab, col, icon), (rect, deg) in zip(items, SLOTS)]


SNS = dict(
    cards=_cards([
        ("キャスティング", VIOLET, "users"),
        ("成果報酬型インフルエンサー広告", CYAN, "yen"),
        ("成果報酬型SNS広告", VIOLET, "click"),
        ("アカウント運用", CYAN, "phone"),
        ("予算型SNS広告", VIOLET, "trend"),
        ("予算型インフルエンサー広告", CYAN, "mega"),
    ]),
    hub=("SNSマーケティング", "事業"), hub_icon="share", idp="snsDiagram",
    aria="SNSマーケティング事業の提供サービス：キャスティング、成果報酬型インフルエンサー広告、成果報酬型SNS広告、アカウント運用、予算型SNS広告、予算型インフルエンサー広告",
)
CREATIVE = dict(
    cards=_cards([
        ("TV CM", VIOLET, "tv"),
        ("Web CM", CYAN, "globe"),
        ("ショート動画", VIOLET, "video"),
        ("ショートドラマ", CYAN, "clap"),
        ("グラフィック撮影", VIOLET, "camera"),
        ("3Dアニメーション", CYAN, "cube"),
    ]),
    hub=("クリエイティブ", "制作事業"), hub_icon="film", idp="crDiagram",
    aria="クリエイティブ制作事業の提供サービス：TV CM、Web CM、ショート動画、ショートドラマ、グラフィック撮影、3Dアニメーション",
)


def pt(r, deg):
    a = math.radians(deg)
    return CX + r * math.cos(a), CY - r * math.sin(a)


def ray_enter_rect(deg, rect):
    """ハブから伸ばした線が、カードに最初に入る距離"""
    x, y, w = rect
    for t in range(R_IN, 520):
        px, py = pt(t, deg)
        if x <= px <= x + w and y <= py <= y + H:
            return t
    return R_OUT


def f(n):
    return f"{n:.1f}".rstrip("0").rstrip(".")


CSS = """
.sd{--sd-ease:cubic-bezier(.16,1,.3,1);display:block;width:100%;height:100%;font-family:"Noto Sans JP","Hiragino Kaku Gothic ProN","Hiragino Sans","Yu Gothic Medium","Yu Gothic","Meiryo",system-ui,sans-serif;}
.sd-label{font-weight:700;font-size:22px;fill:var(--sd-ink,#26262c);letter-spacing:0;}
.sd-hub-label{font-weight:700;font-size:34px;fill:var(--sd-ink,#26262c);letter-spacing:.01em;}
.sd-box{fill:var(--sd-box,#fff);stroke:var(--sd-line,#2b2b33);stroke-width:1.2;transition:stroke .3s ease;}
.sd-card-in{transition:transform .45s var(--sd-ease);}
.sd-card:hover .sd-card-in{transform:translateY(-5px);}
.sd-card:hover .sd-box{stroke:var(--c);}
.sd-outer{stroke:var(--sd-line,#2b2b33);}
.sd-spoke{stroke:var(--sd-spoke,#5c5c68);}
.sd-hubc{fill:var(--sd-hub-fill,#fff);stroke:var(--sd-hub-line,#1d1d25);}
.sd--dark{--sd-ink:#F7FAFF;--sd-box:rgba(255,255,255,.03);--sd-line:rgba(255,255,255,.9);--sd-spoke:rgba(255,255,255,.55);--sd-hub-fill:rgba(255,255,255,.02);--sd-hub-line:#fff;--sd-glow:.34;}
.sd-card:hover .sd-badge-ring{stroke-width:2.2;}
.sd-badge-ring{transition:stroke-width .3s ease;}

@keyframes sd-draw{from{stroke-dasharray:1;stroke-dashoffset:1}to{stroke-dasharray:1;stroke-dashoffset:0}}
@keyframes sd-fade{from{opacity:0}to{opacity:1}}
@keyframes sd-pop{from{opacity:0;transform:scale(.72)}to{opacity:1;transform:scale(1)}}
@keyframes sd-card{from{opacity:0;transform:translate(var(--fx),var(--fy)) scale(.94)}to{opacity:1;transform:none}}
@keyframes sd-spin{to{transform:rotate(360deg)}}
@keyframes sd-ripple{0%{opacity:.5;transform:scale(1)}100%{opacity:0;transform:scale(1.2)}}
@keyframes sd-breathe{from{transform:scale(1)}to{transform:scale(1.09)}}
@keyframes sd-travel{0%{opacity:0;transform:translate(0,0)}14%{opacity:1}78%{opacity:1}100%{opacity:0;transform:translate(var(--dx),var(--dy))}}

.sd-outer{animation:sd-draw 1.7s var(--sd-ease) .1s both;}
.sd-spoke{animation:sd-draw .7s var(--sd-ease) both;}
.sd-dashring{animation:sd-fade 1.2s ease .9s both;}
.sd-hub{transform-box:fill-box;transform-origin:center;animation:sd-pop .9s var(--sd-ease) .35s both;}
.sd-card{transform-box:fill-box;transform-origin:center;animation:sd-card .9s var(--sd-ease) both;}
.sd-spin{transform-origin:700px 457px;animation:sd-spin 120s linear infinite;}
.sd-orbit{transform-origin:700px 457px;animation:sd-spin 22s linear infinite;}
.sd-ripple{transform-box:fill-box;transform-origin:center;animation:sd-ripple 3.8s ease-out 1.6s infinite both;}
.sd-breathe{transform-box:fill-box;transform-origin:center;animation:sd-breathe 2.6s ease-in-out 1.5s infinite alternate both;}
.sd-dot{animation:sd-travel 3.4s cubic-bezier(.45,0,.25,1) infinite both;}

/* ページ側で .sd-off を付けると全アニメーションをリセット(外すと最初から再生) */
.sd-off [class]{animation:none !important;}
/* ページ側が --sd-ps:paused を設定している間は一時停止(画面に入ってから再生するため) */
.sd [class]{animation-play-state:var(--sd-ps,running);}

@media (prefers-reduced-motion:reduce){
  .sd [class]{animation:none !important;transition:none !important;}
  .sd-dot,.sd-ripple,.sd-orbit{display:none;}
}
"""


def build(spec, standalone=False, dark=False, sfx="", with_style=True, start_off=False) -> str:
    cards, hub, hub_icon, aria, idp = spec["cards"], spec["hub"], spec["hub_icon"], spec["aria"], spec["idp"]
    out = []
    ns = ' xmlns="http://www.w3.org/2000/svg"' if standalone else ""
    out.append(
        f'<svg class="sd{" sd--dark" if dark else ""}{" sd-off" if start_off else ""}" id="{idp}{sfx}"{ns} '
        f'viewBox="0 0 1400 914" fill="none" role="img" aria-label="{aria}">'
    )
    if with_style:
        out.append(f"<style>{CSS}</style>")
    out.append(
        "<defs>"
        f'<radialGradient id="sdGlow{sfx}" cx="50%" cy="50%" r="50%">'
        f'<stop offset="0" stop-color="{VIOLET}" style="stop-opacity:var(--sd-glow,.16)"/>'
        f'<stop offset="1" stop-color="{VIOLET}" stop-opacity="0"/>'
        "</radialGradient>"
        f'<mask id="sdMask{sfx}" maskUnits="userSpaceOnUse" x="0" y="0" width="1400" height="914">'
        '<rect width="1400" height="914" fill="#fff"/>'
        + "".join(f'<rect x="{x - 1}" y="{y - 1}" width="{w + 2}" height="{H + 2}" rx="27" fill="#000"/>' for _, (x, y, w), _, _, _ in cards)
        + "</mask></defs>"
    )

    # ハブ背後の淡い光 / 外円(描画アニメ)
    out.append(f'<circle class="sd-dashring" cx="{CX}" cy="{CY}" r="{R_DASH + 30}" fill="url(#sdGlow{sfx})"/>')
    out.append(
        f'<circle class="sd-outer" cx="{CX}" cy="{CY}" r="{R_OUT}" pathLength="1" stroke-width="1.5" mask="url(#sdMask{sfx})"/>'
    )
    # 破線リング + 周回する点
    out.append(
        f'<g class="sd-dashring"><g class="sd-spin"><circle cx="{CX}" cy="{CY}" r="{R_DASH}" '
        f'stroke="{VIOLET}" stroke-opacity=".38" stroke-width="1.3" stroke-dasharray="3 9" stroke-linecap="round"/></g>'
        f'<g class="sd-orbit"><circle cx="{CX}" cy="{CY - R_DASH}" r="9" fill="{VIOLET}" fill-opacity=".18"/>'
        f'<circle cx="{CX}" cy="{CY - R_DASH}" r="4" fill="{VIOLET}"/></g></g>'
    )

    # スポーク
    for i, (_, rect, col, _, deg) in enumerate(cards):
        t_end = ray_enter_rect(deg, rect)
        x1, y1 = pt(R_IN, deg)
        x2, y2 = pt(t_end, deg)
        out.append(
            f'<path class="sd-spoke" d="M{f(x1)} {f(y1)}L{f(x2)} {f(y2)}" pathLength="1" '
            f'stroke-width="1.5" style="animation-delay:{0.9 + i * 0.09:.2f}s"/>'
        )

    # スポークを流れる光の粒
    for i, (_, rect, col, _, deg) in enumerate(cards):
        t_end = ray_enter_rect(deg, rect)
        x1, y1 = pt(R_IN + 6, deg)
        x2, y2 = pt(t_end - 6, deg)
        out.append(
            f'<g class="sd-dot" style="--dx:{f(x2 - x1)}px;--dy:{f(y2 - y1)}px;animation-delay:{2.1 + i * 0.55:.2f}s">'
            f'<circle cx="{f(x1)}" cy="{f(y1)}" r="9" fill="{col}" fill-opacity=".28"/>'
            f'<circle cx="{f(x1)}" cy="{f(y1)}" r="4" fill="{col}"/></g>'
        )

    # ハブ
    hub_icon_c = (CX, CY - 58)
    out.append('<g class="sd-hub">')
    out.append(f'<circle class="sd-ripple" cx="{CX}" cy="{CY}" r="{R_IN}" stroke="{VIOLET}" stroke-width="2"/>')
    out.append(f'<circle cx="{CX}" cy="{CY}" r="{R_IN}" stroke-width="2" class="sd-hubc"/>')
    out.append('<g class="sd-breathe">')
    out.append(f'<circle cx="{hub_icon_c[0]}" cy="{hub_icon_c[1]}" r="37" fill="#0D1420" stroke="{VIOLET}" stroke-width="1.5"/>')
    s = 1.4
    out.append(
        f'<g transform="translate({f(hub_icon_c[0] - 12 * s)} {f(hub_icon_c[1] - 12 * s)}) scale({s})" '
        f'stroke="{VIOLET}" stroke-width="1.45" stroke-linecap="round" stroke-linejoin="round">{ICONS[hub_icon]}</g>'
    )
    out.append("</g>")
    out.append(f'<text class="sd-hub-label" x="{CX}" y="{CY + 36}" text-anchor="middle">{hub[0]}</text>')
    out.append(f'<text class="sd-hub-label" x="{CX}" y="{CY + 82}" text-anchor="middle">{hub[1]}</text>')
    out.append("</g>")

    # カード(ハブから広がるように登場)
    for i, (label, (x, y, w), col, icon, deg) in enumerate(cards):
        cxm, cym = x + w / 2, y + H / 2
        vx, vy = CX - cxm, CY - cym
        n = math.hypot(vx, vy)
        fx, fy = vx / n * 46, vy / n * 46
        icx, icy = x + 42, y + H / 2
        out.append(
            f'<g class="sd-card" style="--c:{col};--fx:{f(fx)}px;--fy:{f(fy)}px;animation-delay:{1.0 + i * 0.12:.2f}s">'
            f'<rect x="{x - 4}" y="{y - 8}" width="{w + 8}" height="{H + 16}" fill="transparent"/>'
            '<g class="sd-card-in">'
            f'<rect class="sd-box" x="{x}" y="{y}" width="{w}" height="{H}" rx="26"/>'
            f'<circle class="sd-badge-ring" cx="{icx}" cy="{f(icy)}" r="26" fill="#0D1420" stroke="{col}" stroke-width="1.5"/>'
            f'<g transform="translate({f(icx - 12)} {f(icy - 12)})" stroke="{col}" stroke-width="1.8" '
            f'stroke-linecap="round" stroke-linejoin="round">{ICONS[icon]}</g>'
            f'<text class="sd-label" x="{x + 80}" y="{f(icy + 8)}">{label}</text>'
            "</g></g>"
        )

    out.append("</svg>")
    return "".join(out)


def write_all(dest: pathlib.Path):
    dest.mkdir(parents=True, exist_ok=True)
    for name, spec, sfx_top in (("sns", SNS, "Top"), ("creative", CREATIVE, "CrTop")):
        w = lambda fn, s: (dest / fn).write_text(s, encoding="utf-8")
        w(f"{name}.light.svg", build(spec, standalone=True))
        w(f"{name}.inline.light.svg", build(spec, sfx=("Cr" if name == "creative" else "")))
        w(f"{name}.inline.dark.desktop.svg", build(spec, dark=True, sfx=sfx_top, start_off=True, with_style=(name == "sns")))
        w(f"{name}.inline.dark.mobile.svg", build(spec, dark=True, sfx=sfx_top + "Sp", with_style=False, start_off=True))
        w(f"{name}.dark.svg", build(spec, standalone=True, dark=True))


if __name__ == "__main__":
    write_all(pathlib.Path(sys.argv[1]))
    print("ok")
