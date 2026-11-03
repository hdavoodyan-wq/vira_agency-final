"""
vira_agency/core/render.py
موتور رندر گرافیکی: استوری استاندارد (1080x1920) و کاروسل ادیتوریال مدرن (1080x1350)
همراه با دایره‌های فعال اسلاید (Pagination Dots)، پشتیبانی فونت فارسی و حذف کادرهای قدیمی
"""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import arabic_reshaper
from bidi.algorithm import get_display

FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
if not os.path.exists(FONT_PATH):
    FONT_PATH = "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"
if not os.path.exists(FONT_PATH):
    FONT_PATH = "DejaVuSans-Bold.ttf"

def _f(size: int):
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except Exception:
        return ImageFont.load_default()

def _shape(text: str) -> str:
    if not text:
        return ""
    clean = str(text).replace("«", "").replace("»", "").replace("موضوع", "").strip()
    reshaped = arabic_reshaper.reshape(clean)
    return get_display(reshaped)

def _wrap_tokens(text: str, max_chars: int = 34) -> list:
    words = text.split()
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
    """رندر استوری استاندارد ۹:۱۶ بدون کادرهای خط‌چین مزاحم روی چارت"""
    w, h = 1080, 1920
    canvas = Image.new("RGBA", (w, h), (10, 12, 18, 255))
    
    if bg_image:
        bg_resized = bg_image.convert("RGBA").resize((w, h), Image.Resampling.LANCZOS)
        canvas.paste(bg_resized, (0, 0))

    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    for y in range(1150, h):
        alpha = int(((y - 1150) / (h - 1150)) * 245)
        odraw.line([(0, y), (w, y)], fill=(6, 8, 12, alpha))
    canvas = Image.alpha_composite(canvas, overlay)
    draw = ImageDraw.Draw(canvas)

    if badge:
        draw.text((w // 2, 1340), _shape(badge), font=_f(28), fill=(234, 179, 8, 255), anchor="mm")

    draw.text((w // 2, 1420), _shape(title), font=_f(44), fill=(255, 255, 255, 255), anchor="mm")
    draw.line([(w // 2 - 100, 1465), (w // 2 + 100, 1465)], fill=(225, 29, 72, 255), width=3)

    lines = _wrap_tokens(text, max_chars=36)
    start_y = 1520
    for l in lines[:5]:
        draw.text((w // 2, start_y), _shape(l), font=_f(32), fill=(226, 232, 240, 255), anchor="mm")
        start_y += 52

    draw.text((w // 2, 1850), _shape(watermark or page_name), font=_f(24), fill=(148, 163, 184, 255), anchor="mm")
    return canvas.convert("RGB")

def render_carousel_slide(bg_image: Image.Image, slide_num: int, total_slides: int, hook_title: str, body_text: str, brand_tag: str) -> Image.Image:
    """رندر کاروسل ادیتوریال ۱۰۸۰×۱۳۵۰ همراه با دایره‌های فعال اسلاید (Pagination Dots)"""
    w, h = 1080, 1350
    canvas = Image.new("RGBA", (w, h), (8, 10, 15, 255))
    
    if bg_image:
        bg_resized = bg_image.convert("RGBA").resize((w, h), Image.Resampling.LANCZOS)
        canvas.paste(bg_resized, (0, 0))

    shadow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow)
    for y in range(650, h):
        alpha = int(((y - 650) / (h - 650)) * 242)
        sdraw.line([(0, y), (w, y)], fill=(6, 8, 12, alpha))
    canvas = Image.alpha_composite(canvas, shadow)
    draw = ImageDraw.Draw(canvas)

    # ۱. دایره‌های تعاملی ورق زدن (Pagination Dots) بالای اسلاید
    dots_total_w = total_slides * 28
    start_dot_x = (w - dots_total_w) // 2
    for i in range(1, total_slides + 1):
        dot_x = start_dot_x + ((i - 1) * 28)
        dot_y = 65
        if i == slide_num:
            draw.ellipse([(dot_x - 7, dot_y - 7), (dot_x + 7, dot_y + 7)], fill=(255, 255, 255, 255))
            draw.ellipse([(dot_x - 10, dot_y - 10), (dot_x + 10, dot_y + 10)], outline=(225, 29, 72, 220), width=2)
        else:
            draw.ellipse([(dot_x - 4, dot_y - 4), (dot_x + 4, dot_y + 4)], fill=(148, 163, 184, 120))

    # ۲. شماره اسلاید عددی بالا سمت چپ
    slide_str = f"0{slide_num} / 0{total_slides}" if total_slides < 10 else f"{slide_num} / {total_slides}"
    draw.text((80, 60), slide_str, font=_f(26), fill=(203, 213, 225, 255), anchor="la")

    # ۳. تیتر اصلی اسلاید (بدون پیشوندهای قالبی کلیشه‌ای)
    clean_title = hook_title.replace("قلاب:", "").replace("ایجاد مسئله:", "").replace("تعلیق:", "").strip()
    draw.text((w - 80, 850), _shape(clean_title), font=_f(46), fill=(255, 255, 255, 255), anchor="ra")
    draw.line([(w - 80, 915), (w - 240, 915)], fill=(225, 29, 72, 255), width=4)

    # ۴. متن ارگانیک اسلاید
    lines = _wrap_tokens(body_text, max_chars=34)
    curr_y = 965
    for l in lines[:4]:
        draw.text((w - 80, curr_y), _shape(l), font=_f(34), fill=(226, 232, 240, 255), anchor="ra")
        curr_y += 58

    # ۵. شناسه برند در فوتر
    draw.text((w // 2, 1285), brand_tag, font=_f(24), fill=(148, 163, 184, 255), anchor="mm")
    return canvas.convert("RGB")
