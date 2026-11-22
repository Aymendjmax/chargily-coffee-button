#!/usr/bin/env python3
"""
chargily-coffee-button — مولّد أزرار «شارجيلي» (مع تخصيص الألوان)
-----------------------------------------------------------------
يقرأ الشعار العربي من brand/chargily-logo-ar.svg، ويرسم الكلمات الإضافية برمجياً بنفس هندسة
خط «شارجيلي»، ثم يكتب أزراراً جاهزة بأي ألوان تريد.

الخانات اللونية الست (بأسماء على طريقة Buy Me a Coffee: HEX بدون #):
    button_colour        خلفية الزر                       --button-colour
    outline_colour       الإطار                           --outline-colour
    font_colour          الحروف والنقاط                   --font-colour
    logo_colour          الوجه الأمامي لعلامة الشعار      --logo-colour
    accent_colour        لون التمييز: الطبقة الوسطى للعلامة + نقطة الجيم   --accent-colour
    accent_light_colour  الطبقة الخلفية الفاتحة للعلامة   --accent-light-colour

التشغيل:
    python3 src/build_button.py                              # كل العبارات × كل الإعدادات الجاهزة → assets/
    python3 src/build_button.py sarf --preset mono           # عبارة واحدة، إعداد جاهز واحد → assets/
    python3 src/build_button.py coffee --button-colour 0B3D2E --font-colour FFFFFF --name green
                                                             # ألوان مخصصة → out/chargily-coffee-green.svg
    python3 src/build_button.py --list-presets

العبارات: coffee | sarf        الإعدادات الجاهزة: purple | light | mono | mono-dark
ملفات PNG تحتاج cairosvg (اختياري). كما يُولَّد builder/index.html (صفحة اختيار الألوان) مع التوليد الكامل.
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOGO = ROOT / "brand" / "chargily-logo-ar.svg"

# ── ألوان الهوية ─────────────────────────────────────────────────────────────
PURPLE, CYAN, PALE = "#7D00D6", "#12d1fa", "#b0f5ff"   # ألوان الشعار الأصلية (مفاتيح الاستبدال)
WHITE = "#FFFFFF"

# ── هندسة الخط (مقيسة من ملف الشعار الأصلي، بوحدات viewBox الأصلية 874.52 × 258.54) ──
Y1, Y2 = 151.8, 173.4       # حدّا خط الأساس (الشريط الأفقي الذي تقف عليه الحروف)
S = Y2 - Y1                 # سماكة الخط ≈ 21.6
DOT, PITCH = 22.24, 30.8    # النقطة المربعة والمسافة بين نقطتين متجاورتين
LOGO_W, LOGO_H = 874.52, 258.54


def f(v: float) -> str:
    """تنسيق رقم عشري مختصر داخل SVG."""
    return ("%.2f" % v).rstrip("0").rstrip(".")


# ── عناصر أساسية ─────────────────────────────────────────────────────────────
def path(d: str, fill: str, evenodd: bool = True) -> str:
    rule = ' fill-rule="evenodd"' if evenodd else ""
    return f'<path d="{d}" fill="{fill}"{rule}/>'


def band(x1: float, x2: float, fill: str) -> str:
    """شريط خط الأساس الواصل بين الحروف المتصلة."""
    return f'<rect x="{f(x1)}" y="{Y1}" width="{f(x2 - x1)}" height="{f(S)}" fill="{fill}"/>'


def dots(cx: float, y_top: float, n: int, fill: str) -> str:
    """n نقاط مربعة متساوية المسافة ومتمركزة حول cx."""
    width = DOT + PITCH * (n - 1)
    x0 = cx - width / 2
    return "".join(
        f'<rect x="{f(x0 + i * PITCH)}" y="{f(y_top)}" width="{DOT}" height="{DOT}" fill="{fill}"/>'
        for i in range(n)
    )


# ── الحروف: كل دالة تأخذ حافتها اليمنى xr وتعيد (SVG، الحافة اليسرى) ───────────
def qaf(xr: float, ink: str):
    """ق (بداية الكلمة): حلقة قوسية كبيرة تقف على خط الأساس + نقطتان."""
    w, top = 92, 91.5
    xl, r = xr - w, w / 2
    cy, ri = top + r, w / 2 - S
    outer = (f"M{f(xl)},{Y2}V{f(cy)}A{f(r)} {f(r)} 0 0 1 {f(xr)},{f(cy)}"
             f"V{f(Y2 - 18)}A18 18 0 0 1 {f(xr - 18)},{Y2}Z")
    inner = f"M{f(xl + S)},{Y1}V{f(cy)}A{f(ri)} {f(ri)} 0 0 1 {f(xr - S)},{f(cy)}V{Y1}Z"
    return path(outer + inner, ink) + dots(xl + r, top - 11.5 - DOT, 2, ink), xl


def heh(xr: float, ink: str, w: float = 74, gap: float = 17):
    """ـهـ (وسطية): حلقة بيضاوية يعبرها خط الأساس من منتصفها (العينان العلوية والسفلية)."""
    xl = xr - w
    cy = (Y1 + Y2) / 2
    h = 3 * S + 2 * gap
    yt, yb = cy - h / 2, cy + h / 2
    r, ri = w / 2, w / 2 - S
    d = (f"M{f(xl + r)},{f(yt)}H{f(xr - r)}A{f(r)} {f(r)} 0 0 1 {f(xr)},{f(yt + r)}"
         f"V{f(yb - r)}A{f(r)} {f(r)} 0 0 1 {f(xr - r)},{f(yb)}"
         f"H{f(xl + r)}A{f(r)} {f(r)} 0 0 1 {f(xl)},{f(yb - r)}"
         f"V{f(yt + r)}A{f(r)} {f(r)} 0 0 1 {f(xl + r)},{f(yt)}Z"
         # العين العلوية (قوس) والسفلية (انعكاسها)
         f"M{f(xl + S)},{Y1}V{f(yt + r)}A{f(ri)} {f(ri)} 0 0 1 {f(xr - S)},{f(yt + r)}V{Y1}Z"
         f"M{f(xl + S)},{Y2}V{f(yb - r)}A{f(ri)} {f(ri)} 0 0 0 {f(xr - S)},{f(yb - r)}V{Y2}Z")
    return path(d, ink), xl


def waw(xr: float, ink: str):
    """ـو (نهائية): حلقة قوسية + ذيل يلتف لليسار مثل ذيل الراء في «شارجيلي»."""
    w, top = 76, 103.5
    a, r = xr - w, w / 2
    cy, ri = top + r, w / 2 - S
    ci, ro = Y2 + 1.6, 32           # مركز قوس الذيل ونصف قطره الخارجي
    rin, ty2 = ro - S, ci + ro
    outer = (f"M{f(a)},{Y2}H{f(a + w - S)}V{f(ci)}A{f(rin)} {f(rin)} 0 0 1 {f(a + w - S - rin)},{f(ci + rin)}"
             f"H{f(a)}V{f(ty2)}H{f(a + w - S - rin)}A{f(ro)} {f(ro)} 0 0 0 {f(xr)},{f(ci)}"
             f"V{f(cy)}A{f(r)} {f(r)} 0 0 0 {f(a)},{f(cy)}Z")
    inner = f"M{f(a + S)},{Y1}V{f(cy)}A{f(ri)} {f(ri)} 0 0 1 {f(xr - S)},{f(cy)}V{Y1}Z"
    return path(outer + inner, ink), a


def teh_marbuta(xr: float, ink: str):
    """ة (منفصلة): حلقة قوسية مغلقة + نقطتان (تشبهان بخار الفنجان)."""
    w, top = 80, 103.5
    xl, r = xr - w, w / 2
    cy, ri = top + r, w / 2 - S
    outer = (f"M{f(xl)},{f(Y2 - 18)}V{f(cy)}A{f(r)} {f(r)} 0 0 1 {f(xr)},{f(cy)}V{f(Y2 - 18)}"
             f"A18 18 0 0 1 {f(xr - 18)},{Y2}H{f(xl + 18)}A18 18 0 0 1 {f(xl)},{f(Y2 - 18)}Z")
    inner = f"M{f(xl + S)},{Y1}V{f(cy)}A{f(ri)} {f(ri)} 0 0 1 {f(xr - S)},{f(cy)}V{Y1}Z"
    return path(outer + inner, ink) + dots(xl + r, top - 11.5 - DOT, 2, ink), xl


# ── حروف «شويا صرف» ───────────────────────────────────────────────────────────
TOOTH_TOP, TALL_TOP, DESC_TOP = 103.5, 51.5, 185.0   # سقف السنّة، سقف الألف، بداية منطقة النقاط السفلية


def yeh_initial(xr: float, ink: str):
    """ي (بداية): سنّة قصيرة على خط الأساس + نقطتان تحتها."""
    d = (f"M{f(xr - S)},{TOOTH_TOP}H{f(xr)}V{f(Y2 - 18)}A18 18 0 0 1 {f(xr - 18)},{Y2}"
         f"H{f(xr - S - 1)}V{TOOTH_TOP}Z")
    return path(d, ink, False) + dots(xr - S / 2, DESC_TOP, 2, ink), xr - S


def alef_final(xl: float, ink: str):
    """ا (نهاية): ساق عالية بزاوية سفلية مدوّرة (مثل ألف الشعار)."""
    d = f"M{f(xl)},{f(Y2 - 18)}V{TALL_TOP}H{f(xl + S)}V{Y2}H{f(xl + 18)}A18 18 0 0 1 {f(xl)},{f(Y2 - 18)}Z"
    return path(d, ink, False), xl


def sad_initial(xr: float, ink: str, w: float = 100, top: float = 106, r: float = 34):
    """ص (بداية): حلقة عريضة منخفضة على خط الأساس (عينها أفقية)."""
    xl, ri = xr - w, r - S
    outer = (f"M{f(xl)},{Y2}V{f(top + r)}A{r} {r} 0 0 1 {f(xl + r)},{f(top)}H{f(xr - r)}"
             f"A{r} {r} 0 0 1 {f(xr)},{f(top + r)}V{f(Y2 - 18)}A18 18 0 0 1 {f(xr - 18)},{Y2}Z")
    inner = (f"M{f(xl + S)},{Y1}V{f(top + r)}A{f(ri)} {f(ri)} 0 0 1 {f(xl + S + ri)},{f(top + S)}"
             f"H{f(xr - S - ri)}A{f(ri)} {f(ri)} 0 0 1 {f(xr - S)},{f(top + r)}V{Y1}Z")
    return path(outer + inner, ink), xl


def reh_final(xe: float, ink: str, ro: float = 32, tail: float = 64):
    """ـر (نهاية): الخط يلتف لأسفل ويمتد ذيله لليسار (نفس ذيل الواو)."""
    ci = Y2 + 1.6
    rin, xt = ro - S, xe - tail
    d = (f"M{f(xe - S)},{f(Y1 + 18)}A18 18 0 0 1 {f(xe - S + 18)},{Y1}H{f(xe)}V{f(ci)}"
         f"A{ro} {ro} 0 0 1 {f(xe - ro)},{f(ci + ro)}H{f(xt)}V{f(ci + ro - S)}H{f(xe - ro)}"
         f"A{f(rin)} {f(rin)} 0 0 0 {f(xe - S)},{f(ci)}Z")
    return path(d, ink, False), xt


def feh_isolated(xr: float, ink: str, w: float = 84, tail: float = 52):
    """ف (منفصلة): حلقة قوسية + نقطة فوقها + ذيل على خط الأساس نحو اليسار."""
    top = TOOTH_TOP
    xl, r = xr - w, w / 2
    cy, ri = top + r, w / 2 - S
    outer = (f"M{f(xl)},{Y2}V{f(cy)}A{f(r)} {f(r)} 0 0 1 {f(xr)},{f(cy)}"
             f"V{f(Y2 - 18)}A18 18 0 0 1 {f(xr - 18)},{Y2}Z")
    inner = f"M{f(xl + S)},{Y1}V{f(cy)}A{f(ri)} {f(ri)} 0 0 1 {f(xr - S)},{f(cy)}V{Y1}Z"
    tl = xl - tail
    t = f"M{f(tl)},{f(Y2 - 18)}V{Y1}H{f(xl + 2)}V{Y2}H{f(tl + 18)}A18 18 0 0 1 {f(tl)},{f(Y2 - 18)}Z"
    return path(outer + inner, ink) + path(t, ink, False) + dots(xl + r, top - 11.5 - DOT, 1, ink), tl


# ── الشعار الأصلي ────────────────────────────────────────────────────────────
def load_logo():
    """يفصل الشعار الأصلي إلى (العلامة = أول 3 مسارات، النص = الباقي)."""
    src = LOGO.read_text(encoding="utf-8").strip()
    body = re.sub(r"^<svg[^>]*>|</svg>\s*$", "", src)
    elems = re.findall(r"<(?:path|rect)[^>]*>(?:</path>|</rect>)?", body)
    return elems[:3], elems[3:]


# ── نصّ الشعار الأصلي: حدود حرف «ش» (يُقصّ منه لإعادة استخدامه في «شويا») ─────────
SHIN_L, SHIN_R = 453.2, 620.76   # من حافة ألف «شارجيلي» اليمنى إلى نهاية الشين


def phrase_coffee(ink: str, text_s: str):
    """«قهوة» تُوضع على يسار «شارجيلي». تعيد (SVG العناصر، أقصى امتداد أيسر)."""
    xr = -58                                   # فراغ بين «شارجيلي» و«قهوة»
    g_q, xl_q = qaf(xr, ink)
    x_h = xl_q - 30
    g_h, xl_h = heh(x_h, ink)
    x_w = xl_h - 30
    g_w, xl_w = waw(x_w, ink)
    x_t = xl_w - 18
    g_t, xl_t = teh_marbuta(x_t, ink)
    joins = band(x_h - 12, xl_q + 1, ink) + band(x_w - 1, xl_h + 12, ink)   # وصلات خط الأساس
    return joins + g_q + g_h + g_w + g_t, xl_t


def phrase_sarf(ink: str, text_s: str):
    """«شويا صرف» تُوضع على يسار «شارجيلي»؛ الشين مقصوصة من الشعار نفسه."""
    # شويا: ش (من الشعار) ← و ← ي ← ا
    dx = -58 - SHIN_R
    xs_l = SHIN_L + dx
    shin = (f'<clipPath id="shin"><rect x="{SHIN_L}" y="0" width="{f(SHIN_R - SHIN_L + 2)}" height="260"/></clipPath>'
            f'<g transform="translate({f(dx)} 0)"><g clip-path="url(#shin)">{text_s}</g></g>')
    xw_r = xs_l - 30
    g_w, xw_l = waw(xw_r, ink)
    xy_r = xw_l - 40
    g_y, xy_l = yeh_initial(xy_r, ink)
    xa_l = xy_l - 30 - S
    g_a, _ = alef_final(xa_l, ink)
    joins = band(xw_r - 1, xs_l + 1, ink) + band(xa_l + S - 1, xy_l + 1, ink)
    # صرف: ص ← ر ، ثم ف منفصلة
    xs_r = xa_l - 58
    g_s, xs_lft = sad_initial(xs_r, ink)
    xe = xs_lft - 22
    g_r, xt = reh_final(xe, ink)
    joins += band(xe - 1, xs_lft + 1, ink)
    g_f, xf_l = feh_isolated(xt - 30, ink)
    return shin + joins + g_w + g_y + g_a + g_s + g_r + g_f, xf_l


PHRASES = {
    "coffee": (phrase_coffee, "شارجيلي قهوة"),
    "sarf": (phrase_sarf, "شارجيلي شويا صرف"),
}

# ── الخانات اللونية ───────────────────────────────────────────────────────────
# (المفتاح الداخلي، اسم المعامل بأسلوب Buy Me a Coffee، علامة القالب، يقبل «شفاف»؟)
SLOTS = [
    ("button", "button_colour", "@@BUTTON@@", True),
    ("outline", "outline_colour", "@@OUTLINE@@", True),
    ("font", "font_colour", "@@FONT@@", False),
    ("logo", "logo_colour", "@@LOGO@@", False),
    ("accent", "accent_colour", "@@ACCENT@@", False),
    ("accent_light", "accent_light_colour", "@@ACCENT_LIGHT@@", False),
]
SLOT_PARAM = {key: param for key, param, _, _ in SLOTS}
SLOT_TOKEN = {key: tok for key, _, tok, _ in SLOTS}
TRANSPARENT_OK = {key for key, _, _, tr in SLOTS if tr}

# الإعدادات الجاهزة. الأولان هما الأصل، و«mono» مثال أبيض/أسود/رمادي.
PRESETS = {
    "purple": dict(button="#7D00D6", outline="#7D00D6", font="#FFFFFF", logo="#FFFFFF",
                   accent="#12d1fa", accent_light="#b0f5ff"),
    "light": dict(button="#FFFFFF", outline="#7D00D6", font="#7D00D6", logo="#7D00D6",
                  accent="#12d1fa", accent_light="#b0f5ff"),
    "mono": dict(button="#FFFFFF", outline="#111111", font="#111111", logo="#111111",
                 accent="#8C8C8C", accent_light="#D4D4D4"),
    "mono-dark": dict(button="#111111", outline="#111111", font="#FFFFFF", logo="#FFFFFF",
                      accent="#A0A0A0", accent_light="#5C5C5C"),
}


def normalize_color(value: str, slot: str) -> str:
    """يقبل ABC أو AABBCC أو #AABBCC، وتُقبل none/transparent للخلفية والإطار فقط. يعيد #RRGGBB أو none."""
    v = value.strip().lower()
    if v in ("none", "transparent"):
        if slot in TRANSPARENT_OK:
            return "none"
        raise ValueError(f"اللون «شفاف» غير مسموح لـ {SLOT_PARAM[slot]}")
    v = v.lstrip("#")
    if re.fullmatch(r"[0-9a-f]{3}", v):
        v = "".join(c * 2 for c in v)
    if not re.fullmatch(r"[0-9a-f]{6}", v):
        raise ValueError(f"قيمة لون غير صالحة لـ {SLOT_PARAM[slot]}: «{value}» (استخدم HEX مثل 7D00D6)")
    return "#" + v.upper()


def luminance(hex_color: str) -> float:
    r, g, b = (int(hex_color[i:i + 2], 16) / 255 for i in (1, 3, 5))
    lin = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b)


def contrast(a: str, b: str) -> float:
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def contrast_warnings(p: dict) -> list:
    """تحذيرات التباين (حد WCAG للعناصر الكبيرة = 3:1)."""
    out = []
    if p["button"] != "none":
        for key, label in (("font", "الحروف"), ("logo", "وجه الشعار")):
            c = p[key] if p[key] != "none" else None
            if c and contrast(c, p["button"]) < 3:
                out.append(f"تباين {label} مع الخلفية منخفض ({contrast(c, p['button']):.1f}:1، المستحسن 3:1 فأكثر)")
    return out


# ── القالب والتلوين ───────────────────────────────────────────────────────────
def build_template(phrase: str) -> str:
    """SVG بعلامات لونية (@@FONT@@ …). الهندسة مستقلة تماماً عن الألوان."""
    compose, label = PHRASES[phrase]
    mark, text = load_logo()
    mark_s = "".join(m.replace(PURPLE, SLOT_TOKEN["logo"]).replace(CYAN, SLOT_TOKEN["accent"])
                      .replace(PALE, SLOT_TOKEN["accent_light"]) for m in mark)
    text_s = "".join(t.replace(PURPLE, SLOT_TOKEN["font"]).replace(CYAN, SLOT_TOKEN["accent"]) for t in text)
    elements, left = compose(SLOT_TOKEN["font"], text_s)

    pad = 76
    x0, y0 = left - pad, -pad
    w, h = LOGO_W - left + 2 * pad, LOGO_H + 2 * pad
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{f(x0)} {f(y0)} {f(w)} {f(h)}" '
        f'width="{f(w / 4)}" height="{f(h / 4)}" role="img" aria-label="{label}">'
        f'<title>{label}</title>'
        f'<rect x="{f(x0 + 5)}" y="{f(y0 + 5)}" width="{f(w - 10)}" height="{f(h - 10)}" rx="68" '
        f'fill="{SLOT_TOKEN["button"]}" stroke="{SLOT_TOKEN["outline"]}" stroke-width="10"/>'
        f'{mark_s}{text_s}{elements}</svg>'
    )


def render(template: str, palette: dict) -> str:
    for key, token in SLOT_TOKEN.items():
        template = template.replace(token, palette[key])
    return template


def build(phrase: str, preset: str = "purple", overrides: dict = None) -> str:
    palette = dict(PRESETS[preset])
    palette.update(overrides or {})
    return render(build_template(phrase), palette)


# ── العناصر المشتركة بين صفحتي الموقع والمُخصِّص (CSS + الشريط العلوي + المطوّر + التذييل) ──
GITHUB_URL = "https://github.com/Aymendjmax/chargily-coffee-button"
DEV_SITE = "https://akio-web.vercel.app"


def chrome(root: str, active: str) -> dict:
    """root = '' للصفحة الرئيسية و'../' لصفحة المُخصِّص؛ active = اسم الرابط الحالي في الشريط."""
    links = [("buttons", "الأزرار", f"{root}#buttons"), ("use", "الاستخدام", f"{root}#use"),
             ("builder", "تخصيص الألوان", f"{root}builder/"), ("dev", "المطوّر", f"{root}#dev")]
    nav = "".join(f'<a href="{href}"' + (' aria-current="page"' if key == active else "") + f'>{label}</a>'
                  for key, label, href in links)
    header = (
        f'<header class="site-header"><div class="wrap bar">'
        f'<a class="brand" href="{root or "#top"}"><span class="dots" aria-hidden="true"><i></i><i></i></span>شارجيلي قهوة</a>'
        f'<button id="menu" type="button" aria-label="القائمة" aria-expanded="false" aria-controls="nav">☰</button>'
        f'<nav id="nav" aria-label="التنقل">{nav}<a class="gh" href="{GITHUB_URL}" rel="noopener">GitHub</a></nav>'
        f'</div></header>'
        '<script>(function(){var b=document.getElementById("menu"),n=document.getElementById("nav");'
        'b.addEventListener("click",function(){var o=n.classList.toggle("open");b.setAttribute("aria-expanded",o)});'
        'n.addEventListener("click",function(e){if(e.target.closest("a")){n.classList.remove("open");b.setAttribute("aria-expanded",false)}})})();</script>')
    dev = (
        '<section id="dev" class="devsec"><div class="wrap"><div class="dev">'
        '<div class="av" aria-hidden="true">A</div>'
        '<div class="who"><h2>طوّره Akio</h2><p>مطوّر ومصمم. المشروع غير رسمي وليس تابعاً لشارجيلي.</p></div>'
        f'<div class="links"><a class="btn" href="{DEV_SITE}" target="_blank" rel="noopener">موقعي الشخصي ↗</a>'
        '<a class="btn alt" href="https://github.com/Aymendjmax" target="_blank" rel="noopener">GitHub</a></div>'
        '</div></div></section>')
    footer = (
        '<footer><div class="wrap"><span>الكود بترخيص MIT. اسم شارجيلي وشعارها ملك لأصحابهما — '
        f'<a href="{GITHUB_URL}/blob/main/NOTICE.md">تنبيه العلامة التجارية</a>.</span><span>© 2026 Akio</span></div></footer>')
    css = (ROOT / "src" / "shared.css").read_text(encoding="utf-8")
    return {"/*__SHARED_CSS__*/": css, "__HEADER__": header, "__DEV__": dev, "__FOOTER__": footer}


def apply_chrome(html: str, root: str, active: str) -> str:
    for token, value in chrome(root, active).items():
        html = html.replace(token, value)
    return html


# ── صفحة اختيار الألوان (builder) ─────────────────────────────────────────────
def write_builder():
    src = ROOT / "src" / "builder_template.html"
    if not src.exists():
        return
    templates = {p: build_template(p) for p in PHRASES}
    slots = [{"key": k, "param": p, "token": t, "transparent": tr} for k, p, t, tr in SLOTS]
    labels = {p: lbl for p, (_, lbl) in PHRASES.items()}
    html = (src.read_text(encoding="utf-8")
            .replace("/*__TEMPLATES__*/{}", json.dumps(templates, ensure_ascii=False))
            .replace("/*__PRESETS__*/{}", json.dumps(PRESETS, ensure_ascii=False))
            .replace("/*__SLOTS__*/[]", json.dumps(slots, ensure_ascii=False))
            .replace("/*__LABELS__*/{}", json.dumps(labels, ensure_ascii=False)))
    html = apply_chrome(html, "../", "builder")
    out = ROOT / "builder" / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print("✔", out.relative_to(ROOT))


# ── الموقع (GitHub Pages) ─────────────────────────────────────────────────────
SITE_URL = "https://aymendjmax.github.io/chargily-coffee-button"
PRESET_AR = {"purple": "بنفسجي", "light": "فاتح", "mono": "أبيض وأسود", "mono-dark": "أسود وأبيض"}


def write_site():
    """يولّد index.html (صفحة الهبوط) من src/site_template.html مع بطاقات الأزرار وروابطها المباشرة."""
    src = ROOT / "src" / "site_template.html"
    if not src.exists():
        return
    tabs, groups = [], []
    for i, (phrase, (_, label)) in enumerate(PHRASES.items()):
        tabs.append(f'<button class="tab" role="tab" data-g="g-{phrase}" aria-selected="{str(i == 0).lower()}">{label}</button>')
        cards = []
        for preset in PRESETS:
            stem = f"chargily-{phrase}-{preset}"
            url = f"{SITE_URL}/assets/svg/{stem}.svg"
            md = f"[![{label}]({url})](رابط_الدفع_الخاص_بك)"
            html = f'<a href="رابط_الدفع_الخاص_بك"><img src="{url}" width="240" alt="{label}"></a>'
            esc = lambda t: t.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;")
            cards.append(
                f'<article class="card"><div class="pv"><img src="assets/svg/{stem}.svg" alt="{label} — {PRESET_AR[preset]}" loading="lazy"></div>'
                f'<h3>{PRESET_AR[preset]}<small>{preset}</small></h3><div class="acts">'
                f'<button class="btn sm" data-copy="{url}" data-msg="تم نسخ رابط SVG">رابط SVG</button>'
                f'<button class="btn sm alt" data-copy="{esc(md)}" data-msg="تم نسخ Markdown">Markdown</button>'
                f'<button class="btn sm alt" data-copy="{esc(html)}" data-msg="تم نسخ HTML">HTML</button>'
                f'<a class="btn sm alt" href="assets/svg/{stem}.svg" download>SVG ↓</a>'
                f'<a class="btn sm alt" href="assets/png/{stem}.png" download>PNG ↓</a></div></article>')
        groups.append(f'<div class="group" id="g-{phrase}" role="tabpanel"{"" if i == 0 else " hidden"}><div class="grid">{"".join(cards)}</div></div>')
    html = (src.read_text(encoding="utf-8").replace("__TABS__", "".join(tabs))
            .replace("__GROUPS__", "".join(groups)).replace("__SITE_URL__", SITE_URL))
    html = apply_chrome(html, "", "")
    (ROOT / "index.html").write_text(html, encoding="utf-8")
    (ROOT / ".nojekyll").write_text("", encoding="utf-8")
    print("✔ index.html")


# ── سطر الأوامر ───────────────────────────────────────────────────────────────
def parse_args(argv):
    ap = argparse.ArgumentParser(description="مولّد أزرار شارجيلي — مع تخصيص الألوان",
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("phrases", nargs="*", help="coffee و/أو sarf (الافتراضي: الاثنتان)")
    ap.add_argument("--preset", choices=list(PRESETS), help="إعداد جاهز؛ يكون أساس الألوان المخصصة أيضاً (الافتراضي purple)")
    for key, param, _, tr in SLOTS:
        flag = "--" + param.replace("_", "-")
        alias = flag.replace("colour", "color")
        ap.add_argument(flag, alias, dest=key, metavar="HEX",
                        help=f"{param}" + (" (أو none للشفاف)" if tr else ""))
    ap.add_argument("--name", help="اسم الملف الناتج للألوان المخصصة (الافتراضي custom)")
    ap.add_argument("--out", help="مجلد الإخراج للألوان المخصصة (الافتراضي out/)")
    ap.add_argument("--width", type=int, default=1200, help="عرض PNG بالبكسل (الافتراضي 1200)")
    ap.add_argument("--no-png", action="store_true", help="توليد SVG فقط")
    ap.add_argument("--list-presets", action="store_true", help="عرض الإعدادات الجاهزة وخروج")
    return ap.parse_args(argv)


def save(phrase, name, palette, out_svg: Path, out_png: Path, width: int, cairosvg):
    out_svg.parent.mkdir(parents=True, exist_ok=True)
    out_svg.write_text(render(build_template(phrase), palette), encoding="utf-8")
    print("✔", out_svg.relative_to(ROOT) if ROOT in out_svg.parents else out_svg)
    for w in contrast_warnings(palette):
        print("  ⚠", w)
    if cairosvg:
        out_png.parent.mkdir(parents=True, exist_ok=True)
        cairosvg.svg2png(url=str(out_svg), write_to=str(out_png), output_width=width)
        print("✔", out_png.relative_to(ROOT) if ROOT in out_png.parents else out_png)


def main(argv=None):
    args = parse_args(argv)
    if args.list_presets:
        for name, p in PRESETS.items():
            print(f"{name:10s}", "  ".join(f"{SLOT_PARAM[k]}={v}" for k, v in p.items()))
        return
    phrases = args.phrases or list(PHRASES)
    bad = [p for p in phrases if p not in PHRASES]
    if bad:
        sys.exit(f"عبارة غير معروفة: {bad} — المتاح: {', '.join(PHRASES)}")

    overrides = {}
    try:
        for key in SLOT_PARAM:
            val = getattr(args, key)
            if val is not None:
                overrides[key] = normalize_color(val, key)
    except ValueError as e:
        sys.exit(f"خطأ: {e}")

    try:
        import cairosvg
    except ImportError:
        cairosvg = None
    if cairosvg is None and not args.no_png:
        print("تنبيه: cairosvg غير مثبّتة، سيتم توليد SVG فقط (pip install cairosvg).")
    if args.no_png:
        cairosvg = None

    if overrides or args.name:                     # وضع الألوان المخصصة
        base = PRESETS[args.preset or "purple"]
        palette = {**base, **overrides}
        out = Path(args.out) if args.out else ROOT / "out"
        name = args.name or "custom"
        for phrase in phrases:
            stem = f"chargily-{phrase}-{name}"
            save(phrase, name, palette, out / f"{stem}.svg", out / f"{stem}.png", args.width, cairosvg)
        return

    presets = [args.preset] if args.preset else list(PRESETS)       # الإعدادات الجاهزة → assets/
    for phrase in phrases:
        for preset in presets:
            stem = f"chargily-{phrase}-{preset}"
            save(phrase, preset, PRESETS[preset], ROOT / "assets" / "svg" / f"{stem}.svg",
                 ROOT / "assets" / "png" / f"{stem}.png", args.width, cairosvg)
    if not args.phrases and not args.preset:
        write_builder()
        write_site()


if __name__ == "__main__":
    main()
