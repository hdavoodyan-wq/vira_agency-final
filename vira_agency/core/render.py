
"""
موتور رندرینگ گرافیکی حرفه‌ای (مشابه ربات قبلی)
پشتیبانی از فونت فارسی، ترکیب تصویر هوش مصنوعی با کارت متنی، و تم‌های اختصاصی هر پیج
"""
import os
import urllib.request
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FONT_DIR = "data/fonts"
FONT_PATH = os.path.join(FONT_DIR, "Vazirmatn-Bold.ttf")

# دانلود خودکار فونت فارسی وزیرمتن در صورت نبودن روی سرور رندر
def _ensure_persian_font() -> str:
    os.makedirs(FONT_DIR, exist_ok=True)
    if not os.path.exists(FONT_PATH) or os.path.getsize(FONT_PATH) < 10000:
        url = "https://github.com/rastikerdar/vazirmatn/raw/master/fonts/ttf/Vazirmatn-Bold.ttf"
        try:
            urllib.request.urlretrieve(url, FONT_PATH)
        except Exception:
            pass
    return FONT_PATH if os.path.exists(FONT_PATH) else ""


def _load_font(size: int):
    fp = _ensure_persian_font()
    if fp:
        try:
            return ImageFont.truetype(fp, size)
        except Exception:
            pass
    return ImageFont.load_default()


def _shape_persian(text: str) -> str:
    """اصلاح چسبندگی و جهت حروف فارسی در صورت نصب بودن پکیج یا حفظ ساختار استاندارد"""
    if not text:
        return ""
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)
    except Exception:
        return text


def _wrap_text(text: str, max_chars: int = 32) -> list[str]:
    words = (text or "").replace("*", "").split()
    lines = []
    cur = ""
    for w in words:
        if len(cur + " " + w) <= max_chars:
            cur = (cur + " " + w).strip()
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def _get_theme_colors(tag_or_slug: str):
    """تعیین پالت رنگی دقیقاً مثل ربات قبلی بر اساس نوع پیج"""
    s = (tag_or_slug or "").lower()
    if s.startswith("t_") or "trad" in s:
        # تم بنفش سلطنتی و نئون سبز برای ترید
        return {
            "bg": (11, 7, 26),
            "card": (22, 14, 48),
            "border": (139, 92, 246),
            "accent": (74, 222, 128),
            "text": (255, 255, 255),
            "sub": (196, 181, 253),
            "watermark": "@tradebazehn | تحلیل بازار"
        }
    elif s.startswith("d_") or "dark" in s:
        # تم گوتیک مشکی و قرمز خونین برای روانشناسی تاریک
        return {
            "bg": (12, 10, 9),
            "card": (24, 18, 20),
            "border": (220, 38, 38),
            "accent": (239, 68, 68),
            "text": (245, 245, 244),
            "sub": (214, 211, 209),
            "watermark": "@tradebazehn | روانشناسی تاریک"
        }
    else:
        # تم گرم و هنری برای پاپیه‌ماشه
        return {
            "bg": (38, 32, 28),
            "card": (58, 48, 42),
            "border": (200, 125, 85),
            "accent": (245, 208, 169),
            "text": (255, 250, 245),
            "sub": (215, 195, 180),
            "watermark": "@papermache_art | هنر دست‌ساز"
        }


def render_story(brand, story_obj, out_path, index, bgs, logo, tag, art_path=None):
    """رندر تک‌استوری تخصصی ۱۰۸۰×۱۹۲۰ با تصویر هوش مصنوعی در بالا و کارت متن فارسی در پایین"""
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    theme = _get_theme_colors(tag)

    canvas = Image.new("RGB", (1080, 1920), color=theme["bg"])
    draw = ImageDraw.Draw(canvas)

    # ۱. قرار دادن تصویر ساخته‌شده توسط هوش مصنوعی در بخش بالایی استوری
    if art_path and os.path.exists(art_path) and os.path.getsize(art_path) > 500:
        try:
            art = Image.open(art_path).convert("RGB")
            art = art.resize((1080, 1180), Image.Resampling.LANCZOS)
            canvas.paste(art, (0, 0))
            # گرادینت نرم بین تصویر بالا و باکس پایین
            for y in range(980, 1180):
                alpha = int(((y - 980) / 200.0) * 255)
                draw.line([(0, y), (1080, y)], fill=theme["bg"], width=1)
        except Exception:
            pass
    else:
        # اگر تصویر آماده نبود، قاب گرافیکی شیک در بالا رسم شود
        draw.rounded_rectangle([60, 100, 1020, 1050], radius=36, fill=theme["card"], outline=theme["border"], width=3)

    # ۲. باکس متنی اصلی استوری
    draw.rounded_rectangle([55, 1120, 1025, 1820], radius=40, fill=theme["card"], outline=theme["border"], width=4)

    font_tag = _load_font(34)
    font_head = _load_font(52)
    font_body = _load_font(40)
    font_wm = _load_font(30)

    heading = str(story_obj.get("heading") or "نکته کلیدی امروز").strip()
    body = str(story_obj.get("body") or "").strip()
    sticker = str(story_obj.get("sticker") or "").strip()

    # تگ بالای باکس
    draw.text((960, 1160), _shape_persian(f"• {tag} •"), fill=theme["accent"], font=font_tag, anchor="ra")

    # تیتر استوری
    head_lines = _wrap_text(heading, max_chars=26)
    y_cursor = 1235
    for hl in head_lines[:2]:
        draw.text((965, y_cursor), _shape_persian(hl), fill=theme["text"], font=font_head, anchor="ra")
        y_cursor += 70

    # خط جداکننده
    y_cursor += 15
    draw.line([(120, y_cursor), (965, y_cursor)], fill=theme["border"], width=2)
    y_cursor += 35

    # متن بدنه استوری
    body_lines = _wrap_text(body, max_chars=34)
    for bl in body_lines[:6]:
        draw.text((965, y_cursor), _shape_persian(bl), fill=theme["sub"], font=font_body, anchor="ra")
        y_cursor += 58

    # استیکر تعاملی در صورت وجود
    if sticker:
        draw.rounded_rectangle([180, 1710, 900, 1790], radius=25, fill=theme["bg"], outline=theme["accent"], width=2)
        draw.text((540, 1732), _shape_persian(sticker[:40]), fill=theme["accent"], font=font_tag, anchor="ma")

    # واترمارک پایین
    draw.text((540, 1855), _shape_persian(theme["watermark"]), fill=theme["accent"], font=font_wm, anchor="ma")

    canvas.save(out_path, quality=92)
    return out_path


def render_carousel(brand, slides, out_dir, bgs, logo, arts=None, slug="trading"):
    """رندر اسلایدهای کاروسل ۱۰۸۰×۱۳۵۰ با تصویر هوش مصنوعی و متن فارسی"""
    os.makedirs(out_dir, exist_ok=True)
    theme = _get_theme_colors(slug)
    font_head = _load_font(50)
    font_body = _load_font(38)
    font_wm = _load_font(28)

    paths = []
    for i, s in enumerate(slides):
        p = os.path.join(out_dir, f"slide_{i+1:02d}.jpg")
        canvas = Image.new("RGB", (1080, 1350), color=theme["bg"])
        draw = ImageDraw.Draw(canvas)

        art_path = arts[i] if (arts and i < len(arts)) else None
        if art_path and os.path.exists(art_path) and os.path.getsize(art_path) > 500:
            try:
                art = Image.open(art_path).convert("RGB").resize((1080, 760), Image.Resampling.LANCZOS)
                canvas.paste(art, (0, 0))
            except Exception:
                pass

        draw.rounded_rectangle([50, 720, 1030, 1260], radius=36, fill=theme["card"], outline=theme["border"], width=4)

        heading = str(s.get("heading") or f"اسلاید {i+1}")
        body = str(s.get("body") or "")

        y_c = 770
        for hl in _wrap_text(heading, 28)[:2]:
            draw.text((980, y_c), _shape_persian(hl), fill=theme["accent"], font=font_head, anchor="ra")
            y_c += 65

        y_c += 20
        for bl in _wrap_text(body, 36)[:6]:
            draw.text((980, y_c), _shape_persian(bl), fill=theme["text"], font=font_body, anchor="ra")
            y_c += 55

        draw.text((540, 1290), _shape_persian(f"{theme['watermark']}  •  {i+1}/{len(slides)}"), fill=theme["sub"], font=font_wm, anchor="ma")
        canvas.save(p, quality=92)
        paths.append(p)
    return paths


def render_reel_frame(brand, text, out_path, index, bgs, logo, art_path=None, slug="trading"):
    """رندر فریم ریلز ۱۰۸۰×۱۹۲۰ همانند ربات قبلی"""
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    return render_story(
        brand=brand,
        story_obj={"heading": f"سکانس {index + 1}", "body": text, "sticker": ""},
        out_path=out_path,
        index=index,
        bgs=bgs,
        logo=logo,
        tag=slug,
        art_path=art_path,
    )
