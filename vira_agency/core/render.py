"""
vira_agency/core/render.py
موتور رندر گرافیکی: رفع کامل مشکل برعکس شدن حروف فارسی در لینوکس + دایره‌های فعال (Pagination Dots)
"""
import os
from PIL import Image, ImageDraw, ImageFont, features

FONT_CANDIDATES = [
    "vira_agency/assets/fonts/Vazirmatn-Bold.ttf",
    "assets/fonts/Vazirmatn-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
]

def _get_font_path() -> str:
    for p in FONT_CANDIDATES:
        if os.path.exists(p):
            return p
    return "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

FONT_PATH = _get_font_path()

# بررسی اینکه آیا موتور libraqm روی سیستم نصب است (که خودش متن را راست‌به‌چپ می‌کند)
HAS_RAQM = False
try:
    HAS_RAQM = features.check("raqm")
except Exception:
    HAS_RAQM = False

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    HAS_RESHAPER = True
except Exception:
    HAS_RESHAPER = False

def _f(size: int):
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except Exception:
        return ImageFont.load_default()

def _shape(text: str) -> str:
    """
    تنظیم هوشمند متن فارسی:
    اگر Pillow دارای raqm باشد، خودش شکل‌دهی و جهت راست‌به‌چپ را انجام می‌دهد و نباید get_display صدا زده شود.
    """
    if not text:
        return ""
    clean = str(text).replace("«", "").replace("»", "").replace("موضوع:", "").strip()
    if HAS_RAQM:
        return clean
    if HAS_RESHAPER:
        try:
            reshaped = arabic_reshaper.reshape(clean)
            return get_display(reshaped)
        except Exception:
            return clean
    return clean

def _wrap_tokens(text: str, max_chars: int = 36) -> list:
    words = str(text).split()
    lines = []
    curr = []
    for w in words:
        curr.append(w)
        if len(" ".join(curr)) > max_chars:
            lines.append(" ".join(curr))
            curr = []
    if curr:
        lines.append(" ".join(curr))
    return lines

def render_story_layout(bg_image: Image.Image, badge: str, title: str, text: str, page_name: str, watermark: str) -> Image.Image:
    """رندر استوری ۹:۱۶ با گرادینت سینمایی و فونت فارسی استاندارد"""
    w, h = 1080, 1920
    canvas = Image.new("RGBA", (w, h), (10, 12, 18, 255))

    if bg_image:
        bg_resized = bg_image.convert("RGBA").resize((w, h), Image.Resampling.LANCZOS)
        canvas.paste(bg_resized, (0, 0))

    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    for y in range(1100, h):
        alpha = int(((y - 1100) / (h - 1100)) * 245)
        odraw.line([(0, y), (w, y)], fill=(6, 8, 14, alpha))
    canvas = Image.alpha_composite(canvas, overlay)
    draw = ImageDraw.Draw(canvas)

    if badge:
        draw.text((w // 2, 1330), _shape(badge), font=_f(28), fill=(234, 179, 8, 255), anchor="mm")

    draw.text((w // 2, 1410), _shape(title), font=_f(44), fill=(255, 255, 255, 255), anchor="mm")
    draw.line([(w // 2 - 110, 1455), (w // 2 + 110, 1455)], fill=(225, 29, 72, 255), width=4)

    lines = _wrap_tokens(text, max_chars=36)
    start_y = 1515
    for line in lines[:5]:
        draw.text((w // 2, start_y), _shape(line), font=_f(32), fill=(226, 232, 240, 255), anchor="mm")
        start_y += 54

    draw.text((w // 2, 1850), watermark or page_name, font=_f(24), fill=(148, 163, 184, 255), anchor="mm")
    return canvas.convert("RGB")

def render_carousel_slide(bg_image: Image.Image, slide_num: int, total_slides: int, hook_title: str, body_text: str, brand_tag: str) -> Image.Image:
    """رندر کاروسل ۱۰۸۰×۱۳۵۰ همراه با دایره‌های فعال (Pagination Dots) و راست‌چین دقیق"""
    w, h = 1080, 1350
    canvas = Image.new("RGBA", (w, h), (8, 10, 15, 255))

    if bg_image:
        bg_resized = bg_image.convert("RGBA").resize((w, h), Image.Resampling.LANCZOS)
        canvas.paste(bg_resized, (0, 0))

    shadow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow)
    for y in range(620, h):
        alpha = int(((y - 620) / (h - 620)) * 245)
        sdraw.line([(0, y), (w, y)], fill=(6, 8, 12, alpha))
    canvas = Image.alpha_composite(canvas, shadow)
    draw = ImageDraw.Draw(canvas)

    # ۱. دایره‌های نشانگر اسلاید (Pagination Dots) بالای صفحه
    dots_total_w = total_slides * 28
    start_dot_x = (w - dots_total_w) // 2
    for i in range(1, total_slides + 1):
        dot_x = start_dot_x + ((i - 1) * 28)
        dot_y = 65
        if i == slide_num:
            draw.ellipse([(dot_x - 7, dot_y - 7), (dot_x + 7, dot_y + 7)], fill=(255, 255, 255, 255))
            draw.ellipse([(dot_x - 10, dot_y - 10), (dot_x + 10, dot_y + 10)], outline=(225, 29, 72, 230), width=2)
        else:
            draw.ellipse([(dot_x - 4, dot_y - 4), (dot_x + 4, dot_y + 4)], fill=(148, 163, 184, 130))

    # ۲. شماره اسلاید بالا سمت چپ
    slide_str = f"0{slide_num} / 0{total_slides}" if total_slides < 10 else f"{slide_num} / {total_slides}"
    draw.text((80, 60), slide_str, font=_f(26), fill=(203, 213, 225, 255), anchor="la")

    # ۳. تیتر اسلاید (راست‌چین با خط قرمز زیر آن)
    clean_title = str(hook_title).replace("قلاب:", "").replace("ایجاد مسئله:", "").replace("تعلیق:", "").strip()
    draw.text((w - 80, 845), _shape(clean_title), font=_f(44), fill=(255, 255, 255, 255), anchor="ra")
    draw.line([(w - 80, 910), (w - 250, 910)], fill=(225, 29, 72, 255), width=4)

    # ۴. متن بدنه اسلاید (راست‌چین و خوانا)
    lines = _wrap_tokens(body_text, max_chars=35)
    curr_y = 955
    for line in lines[:4]:
        draw.text((w - 80, curr_y), _shape(line), font=_f(32), fill=(226, 232, 240, 255), anchor="ra")
        curr_y += 56

    # ۵. تگ پیج در فوتر
    draw.text((w // 2, 1285), brand_tag, font=_f(24), fill=(148, 163, 184, 255), anchor="mm")
    return canvas.convert("RGB")
