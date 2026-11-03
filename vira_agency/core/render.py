"""
vira_agency/core/render.py
رندرینگ استاندارد استوری (1080x1920) و کاروسل مجله‌ای (1080x1350)
حذف کادرهای قدیمی و اجرای تایپوگرافی بدون حباب
"""
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display
import os

FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
if not os.path.exists(FONT_PATH):
    FONT_PATH = "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"

def _f(size: int):
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except Exception:
        return ImageFont.load_default()

def _shape(text: str) -> str:
    if not text:
        return ""
    reshaped = arabic_reshaper.reshape(str(text))
    return get_display(reshaped)

def render_story_layout(bg_image: Image.Image, badge: str, title: str, text: str, page_name: str, watermark: str) -> Image.Image:
    """رندر استوری استاندارد ۹:۱۶ بدون کادرهای مزاحم روی چارت"""
    w, h = 1080, 1920
    canvas = Image.new("RGBA", (w, h), (10, 12, 18, 255))
    
    if bg_image:
        bg_resized = bg_image.convert("RGBA").resize((w, h), Image.Resampling.LANCZOS)
        canvas.paste(bg_resized, (0, 0))

    # گرادیانت تیره در پایین صفحه برای خوانایی خیره‌کننده متن
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    for y in range(1250, h):
        alpha = int(((y - 1250) / (h - 1250)) * 235)
        odraw.line([(0, y), (w, y)], fill=(8, 10, 15, alpha))
    canvas = Image.alpha_composite(canvas, overlay)
    draw = ImageDraw.Draw(canvas)

    # بج و نشان موضوع
    if badge:
        draw.text((w // 2, 1340), _shape(badge), font=_f(28), fill=(234, 179, 8, 255), anchor="mm")

    # تیتر اصلی
    draw.text((w // 2, 1420), _shape(title), font=_f(42), fill=(255, 255, 255, 255), anchor="mm")
    draw.line([(w // 2 - 120, 1465), (w // 2 + 120, 1465)], fill=(225, 29, 72, 255), width=3)

    # متن سناریو و تحلیل
    lines = [text[i:i+42] for i in range(0, len(text), 42)]
    start_y = 1520
    for l in lines[:5]:
        draw.text((w // 2, start_y), _shape(l), font=_f(31), fill=(226, 232, 240, 255), anchor="mm")
        start_y += 50

    # واترمارک و نام برند در پاورقی
    draw.text((w // 2, 1850), _shape(watermark or page_name), font=_f(24), fill=(148, 163, 184, 255), anchor="mm")
    return canvas.convert("RGB")

def render_carousel_slide(bg_image: Image.Image, slide_num: int, total_slides: int, hook_title: str, body_text: str, brand_tag: str) -> Image.Image:
    """رندر کاروسل استاندارد ۱۰۸۰ در ۱۳۵۰ با ساختار ادیتوریال و پوستر مدرن"""
    w, h = 1080, 1350
    canvas = Image.new("RGBA", (w, h), (8, 10, 15, 255))
    
    if bg_image:
        bg_resized = bg_image.convert("RGBA").resize((w, h), Image.Resampling.LANCZOS)
        canvas.paste(bg_resized, (0, 0))

    # لایه‌بندی مشکی محو برای جلوه سینمایی
    shadow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    sdraw = ImageDraw.Draw(shadow)
    for y in range(750, h):
        alpha = int(((y - 750) / (h - 750)) * 240)
        sdraw.line([(0, y), (w, y)], fill=(6, 8, 12, alpha))
    canvas = Image.alpha_composite(canvas, shadow)
    draw = ImageDraw.Draw(canvas)

    # شماره اسلاید بالا سمت چپ
    slide_str = f"{slide_num} / {total_slides}"
    draw.text((90, 80), slide_str, font=_f(28), fill=(203, 213, 225, 255), anchor="la")

    # تیتر اسلاید
    draw.text((w - 90, 860), _shape(hook_title), font=_f(46), fill=(255, 255, 255, 255), anchor="ra")
    draw.line([(w - 90, 930), (w - 290, 930)], fill=(225, 29, 72, 255), width=4)

    # متن اسلاید
    lines = [body_text[i:i+40] for i in range(0, len(body_text), 40)]
    curr_y = 980
    for l in lines[:4]:
        draw.text((w - 90, curr_y), _shape(l), font=_f(34), fill=(226, 232, 240, 255), anchor="ra")
        curr_y += 58

    # آیدی پیج در فوتر
    draw.text((w // 2, 1280), brand_tag, font=_f(24), fill=(148, 163, 184, 255), anchor="mm")
    return canvas.convert("RGB")
