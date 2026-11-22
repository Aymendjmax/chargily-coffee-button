#!/usr/bin/env python3
"""
chargily-coffee-button — مولّد أزرار «شارجيلي»
-----------------------------------------------
يقرأ الشعار العربي من brand/chargily-logo-ar.svg، ويرسم الكلمات الإضافية برمجياً بنفس هندسة
خط «شارجيلي» (سماكة موحّدة، خط أساس واحد، نقاط مربعة، أنصاف أقطار ثابتة)، ثم يكتب لكل عبارة نسختين:

    «شارجيلي قهوة»      →  assets/{svg,png}/chargily-coffee-{purple,light}.{svg,png}
    «شارجيلي شويا صرف»  →  assets/{svg,png}/chargily-sarf-{purple,light}.{svg,png}

التشغيل:
    python3 src/build_button.py            # كل العبارات
    python3 src/build_button.py sarf       # عبارة واحدة (coffee | sarf)

ملفات PNG تحتاج cairosvg (اختياري).
"""
import re
import sys
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


def build(phrase: str, variant: str) -> str:
    """phrase = coffee | sarf ، variant = 'light' (خلفية بيضاء، إطار بنفسجي) أو 'purple' (خلفية بنفسجية، حروف بيضاء)."""
    compose, label = PHRASES[phrase]
    if variant == "light":
        bg, ink, front = WHITE, PURPLE, PURPLE
    else:
        bg, ink, front = PURPLE, WHITE, WHITE
    mark, text = load_logo()
    mark_s = "".join(m.replace(PURPLE, front) for m in mark)
    text_s = "".join(t.replace(PURPLE, ink) for t in text)
    elements, left = compose(ink, text_s)

    pad = 76
    x0, y0 = left - pad, -pad
    w, h = LOGO_W - left + 2 * pad, LOGO_H + 2 * pad
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{f(x0)} {f(y0)} {f(w)} {f(h)}" '
        f'width="{f(w / 4)}" height="{f(h / 4)}" role="img" aria-label="{label}">'
        f'<title>{label}</title>'
        f'<rect x="{f(x0 + 5)}" y="{f(y0 + 5)}" width="{f(w - 10)}" height="{f(h - 10)}" rx="68" '
        f'fill="{bg}" stroke="{PURPLE}" stroke-width="10"/>'
        f'{mark_s}{text_s}{elements}</svg>'
    )


def main():
    wanted = sys.argv[1:] or list(PHRASES)
    unknown = [p for p in wanted if p not in PHRASES]
    if unknown:
        sys.exit(f"عبارة غير معروفة: {unknown} — المتاح: {', '.join(PHRASES)}")
    svg_dir, png_dir = ROOT / "assets" / "svg", ROOT / "assets" / "png"
    svg_dir.mkdir(parents=True, exist_ok=True)
    png_dir.mkdir(parents=True, exist_ok=True)
    try:
        import cairosvg
    except ImportError:
        cairosvg = None
        print("تنبيه: cairosvg غير مثبّتة، سيتم توليد SVG فقط (pip install cairosvg).")
    for phrase in wanted:
        for variant in ("purple", "light"):
            name = f"chargily-{phrase}-{variant}"
            out = svg_dir / f"{name}.svg"
            out.write_text(build(phrase, variant), encoding="utf-8")
            print("✔", out.relative_to(ROOT))
            if cairosvg:
                png = png_dir / f"{name}.png"
                cairosvg.svg2png(url=str(out), write_to=str(png), output_width=1200)
                print("✔", png.relative_to(ROOT))


if __name__ == "__main__":
    main()
