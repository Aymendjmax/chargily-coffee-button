#!/usr/bin/env python3
"""
chargily-coffee-button — مولّد زر «شارجيلي قهوة»
-------------------------------------------------
يقرأ الشعار العربي من brand/chargily-logo-ar.svg، ويرسم كلمة «قهوة» برمجياً بنفس هندسة
خط «شارجيلي» (سماكة موحّدة، خط أساس واحد، نقاط مربعة، أنصاف أقطار ثابتة)، ثم يكتب:

    assets/svg/chargily-coffee-purple.svg   assets/svg/chargily-coffee-light.svg
    assets/png/chargily-coffee-purple.png   assets/png/chargily-coffee-light.png   (إن توفرت cairosvg)

التشغيل:   python3 src/build_button.py
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOGO = ROOT / "brand" / "chargily-logo-ar.svg"

# ── ألوان الهوية ─────────────────────────────────────────────────────────────
PURPLE, CYAN = "#7D00D6", "#12d1fa"
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


# ── الشعار الأصلي ────────────────────────────────────────────────────────────
def load_logo():
    """يفصل الشعار الأصلي إلى (العلامة = أول 3 مسارات، النص = الباقي)."""
    src = LOGO.read_text(encoding="utf-8").strip()
    body = re.sub(r"^<svg[^>]*>|</svg>\s*$", "", src)
    elems = re.findall(r"<(?:path|rect)[^>]*>(?:</path>|</rect>)?", body)
    return elems[:3], elems[3:]


def build(variant: str) -> str:
    """variant = 'light' (خلفية بيضاء، إطار بنفسجي) أو 'purple' (خلفية بنفسجية، حروف بيضاء)."""
    if variant == "light":
        bg, ink, front = WHITE, PURPLE, PURPLE
    else:
        bg, ink, front = PURPLE, WHITE, WHITE
    mark, text = load_logo()

    # التخطيط من اليمين إلى اليسار، بإحداثيات الشعار الأصلي (النص الأصلي يبدأ من x=0)
    xr = -58                                   # فراغ بين «شارجيلي» و«قهوة»
    g_q, xl_q = qaf(xr, ink)
    x_h = xl_q - 30
    g_h, xl_h = heh(x_h, ink)
    x_w = xl_h - 30
    g_w, xl_w = waw(x_w, ink)
    x_t = xl_w - 18
    g_t, xl_t = teh_marbuta(x_t, ink)
    joins = band(x_h - 12, xl_q + 1, ink) + band(x_w - 1, xl_h + 12, ink)   # وصلات خط الأساس

    pad = 76
    x0, y0 = xl_t - pad, -pad
    w, h = LOGO_W - xl_t + 2 * pad, LOGO_H + 2 * pad
    mark_s = "".join(m.replace(PURPLE, front) for m in mark)
    text_s = "".join(t.replace(PURPLE, ink) for t in text)

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{f(x0)} {f(y0)} {f(w)} {f(h)}" '
        f'width="{f(w / 4)}" height="{f(h / 4)}" role="img" aria-label="شارجيلي قهوة">'
        f'<title>شارجيلي قهوة</title>'
        f'<rect x="{f(x0 + 5)}" y="{f(y0 + 5)}" width="{f(w - 10)}" height="{f(h - 10)}" rx="68" '
        f'fill="{bg}" stroke="{PURPLE}" stroke-width="10"/>'
        f'{mark_s}{text_s}{joins}{g_q}{g_h}{g_w}{g_t}</svg>'
    )


def main():
    svg_dir, png_dir = ROOT / "assets" / "svg", ROOT / "assets" / "png"
    svg_dir.mkdir(parents=True, exist_ok=True)
    png_dir.mkdir(parents=True, exist_ok=True)
    try:
        import cairosvg
    except ImportError:
        cairosvg = None
        print("تنبيه: cairosvg غير مثبّتة، سيتم توليد SVG فقط (pip install cairosvg).")
    for variant in ("purple", "light"):
        name = f"chargily-coffee-{variant}"
        out = svg_dir / f"{name}.svg"
        out.write_text(build(variant), encoding="utf-8")
        print("✔", out.relative_to(ROOT))
        if cairosvg:
            png = png_dir / f"{name}.png"
            cairosvg.svg2png(url=str(out), write_to=str(png), output_width=1200)
            print("✔", png.relative_to(ROOT))


if __name__ == "__main__":
    main()
