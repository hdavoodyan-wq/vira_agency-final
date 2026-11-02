"""
موتور رندرینگ گرافیکی حرفه‌ای دستیار ویرا
تصویر یک‌دست تمام‌صفحه، بلور و گرادیان شیشه‌ای، و رنگ‌آمیزی متمایز کلمات کلیدی
"""
import os
import re
import urllib.request
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FONT_DIR = "data/fonts"
FONT_PATH = os.path.join(FONT_DIR, "Vazirmatn-Bold.ttf")

TAG_LABELS_FA = {
    # ترید
    "t_market": "تحلیل بازار",
    "t_news": "اخبار داغ",
    "t_quiz": "کوییز تریدری",
    "t_psyc": "روانشناسی ترید",
    "t_hunt": "شکار استاپ",
    "t_bull": "نبرد گاو و خرس",
    # روانشناسی تاریک
    "d_chal": "چالش روز",
    "d_edu": "ترفند تاریک",
    "d_mar": "قوانین رابطه",
    "d_opt": "تست شخصیت",
    "d_sec": "زبان بدن",
    # پاپیه‌ماشه
    "behind": "پشت صحنه",
    "showcase": "معرفی اثر",
    "workshop": "نکته کارگاه",
}


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
    if not text:
        return ""
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)
    except Exception:
        return text


def _get_theme(tag_or_slug: str):
    s = (tag_or_slug or "").lower()
    if s.startswith("t_") or "trad" in s:
        return {
            "border": (139, 92, 246, 220),         # بنفش نئونی
            "glass_tint": (15, 10, 32, 215),        # شیشه‌ای تیره بنفش
            "accent": (74, 222, 128),               # سبز نئونی برای کلمات مهم
            "text": (255, 255, 255),               # سفید خالص برای تیتر
            "sub": (226, 232, 240),                # خاکستری خیلی روشن برای بدنه
            "watermark": "@tradebazehn | تحلیل بازار"
        }
    elif s.startswith("d_") or "dark" in s:
        return {
            "border": (220, 38, 38, 220),          # قرمز گوتیک
            "glass_tint": (16, 12, 14, 225),        # شیشه‌ای تیره ذغالی
            "accent": (239, 68, 68),                # قرمز آتشین برای کلمات کلیدی
            "text": (255, 255, 255),
            "sub": (229, 231, 235),
            "watermark": "@tradebazehn | روانشناسی تاریک"
        }
    else:
        return {
            "border": (217, 119, 6, 220),          # کهربایی گرم
            "glass_tint": (32, 24, 18, 220),        # شیشه‌ای گرم کارگاهی
            "accent": (249, 115, 22),               # نارنجی سفالی برای نکات مهم
            "text": (254, 243, 199),               # کرم روشن
            "sub": (253, 230, 138),                # کرم طلایی
            "watermark": "@papermache_art | هنر دست‌ساز"
        }


def _tokenize_text(text: str) -> list[tuple[str, bool]]:
    """تجزیه متن به کلمات معمولی و کلمات هایلایت شده با **کلمه**"""
    tokens = []
    parts = re.split(r"(\*\*.*?\*\*)", text)
    for p in parts:
        if not p:
            continue
        if p.startswith("**") and p.endswith("**") and len(p) > 4:
            clean = p[2:-2].strip()
            for w in clean.split():
                if w:
                    tokens.append((w, True))
        else:
            for w in p.split():
                if w:
                    tokens.append((w, False))
    return tokens


def _wrap_tokens(tokens: list[tuple[str, bool]], font: ImageFont.ImageFont, max_width_px: int) -> list[list[tuple[str, bool]]]:
    """شکستن خطوط فارسی بر اساس عرض واقعی پیکسل‌ها"""
    lines = []
    current_line = []
    current_w = 0

    space_w = font.getbbox(" ")[2] - font.getbbox(" ")[0] if font else 10

    for word, is_hl in tokens:
        shaped = _shape_persian(word)
        bbox = font.getbbox(shaped) if font else (0, 0, len(word) * 12, 20)
        word_w = bbox[2] - bbox[0]

        add_w = word_w if not current_line else word_w + space_w

        if current_w + add_w <= max_width_px:
            current_line.append((word, is_hl))
            current_w += add_w
        else:
            if current_line:
                lines.append(current_line)
            current_line = [(word, is_hl)]
            current_w = word_w

    if current_line:
        lines.append(current_line)
    return lines


def _draw_rich_persian_line(draw: ImageDraw.ImageDraw, line_tokens: list[tuple[str, bool]], start_x: int, y: int, font: ImageFont.ImageFont, default_color: tuple, accent_color: tuple):
    """رسم کلمات خط فارسی از راست به چپ با رنگ متمایز برای کلمات هایلایت شده"""
    cur_x = start_x
    space_w = font.getbbox(" ")[2] - font.getbbox(" ")[0] if font else 10

    for word, is_hl in line_tokens:
        shaped = _shape_persian(word)
        bbox = font.getbbox(shaped) if font else (0, 0, len(word) * 12, 20)
        word_w = bbox[2] - bbox[0]

        color = accent_color if is_hl else default_color
        draw.text((cur_x - word_w, y), shaped, fill=color, font=font)
        cur_x -= (word_w + space_w)


def _draw_brush_background(draw: ImageDraw.ImageDraw, x1: int, y1: int, x2: int, y2: int, fill_color, stroke_color):
    """ایجاد فرم آزاد ارگانیک شبیه پالت رنگ یا رد قلم‌مو برای پیج هنر"""
    points = [
        (x1 + 30, y1), (x2 - 40, y1 + 10),
        (x2, y1 + 60), (x2 - 15, y2 - 40),
        (x2 - 60, y2), (x1 + 45, y2 - 10),
        (x1, y2 - 70), (x1 + 15, y1 + 35)
    ]
    draw.polygon(points, fill=fill_color, outline=stroke_color)


def render_story(brand, story_obj, out_path, index, bgs, logo, tag, art_path=None):
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    theme = _get_theme(tag)
    tag_lower = (tag or "").lower()
    is_dark = tag_lower.startswith("d_") or "dark" in tag_lower
    is_art = tag_lower in ("behind", "showcase", "workshop") or "art" in tag_lower

    # ۱. بارگذاری تصویر تمام‌صفحه
    if art_path and os.path.exists(art_path) and os.path.getsize(art_path) > 500:
        base_img = Image.open(art_path).convert("RGBA")
        base_img = base_img.resize((1080, 1920), Image.Resampling.LANCZOS)
    else:
        base_img = Image.new("RGBA", (1080, 1920), color=theme["glass_tint"][:3] + (255,))

    font_tag = _load_font(32)
    font_head = _load_font(52)
    font_body = _load_font(38)
    font_wm = _load_font(26)

    heading = str(story_obj.get("heading") or "نکته کلیدی").strip()
    body = str(story_obj.get("body") or "").strip()
    sticker = str(story_obj.get("sticker") or "").strip()

    # جلوگیری از چاپ کلمات بدون فرمت
    if "**" not in body:
        words = body.split()
        if len(words) >= 6:
            words[1] = f"**{words[1]}**"
            if len(words) > 10:
                words[7] = f"**{words[7]}**"
            body = " ".join(words)

    # ------------------ استایل ۱: روانشناسی تاریک (بدون کادر، متن مستقیم، خط سرخ) ------------------
    if is_dark:
        # گرادیان ملایم تیره در پایین تصویر بدون تاریکی شدید سوژه
        gradient = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
        d_grad = ImageDraw.Draw(gradient)
        for y in range(850, 1920):
            alpha = int(((y - 850) / 1070) ** 1.4 * 220)
            d_grad.line([(0, y), (1080, y)], fill=(8, 6, 8, min(235, alpha)))

        final_canvas = Image.alpha_composite(base_img, gradient).convert("RGB")
        draw = ImageDraw.Draw(final_canvas)

        # تیتر وسط‌چین درشت
        head_tokens = _tokenize_text(heading)
        head_lines = _wrap_tokens(head_tokens, font_head, max_width_px=920)
        y_cursor = 1050
        for hline in head_lines[:2]:
            total_w = sum(font_head.getbbox(_shape_persian(w))[2] - font_head.getbbox(_shape_persian(w))[0] + 8 for w, _ in hline)
            start_x = 540 + (total_w // 2)
            _draw_rich_persian_line(draw, hline, start_x, y_cursor, font_head, (255, 255, 255), (239, 68, 68))
            y_cursor += 75

        # خط باریک سرخ خونین زیر تیتر
        y_cursor += 15
        draw.line([(450, y_cursor), (630, y_cursor)], fill=(220, 38, 38), width=3)
        y_cursor += 45

        # بدنه متن مستقیم روی تصویر
        body_tokens = _tokenize_text(body)
        body_lines = _wrap_tokens(body_tokens, font_body, max_width_px=920)
        for bline in body_lines[:6]:
            _draw_rich_persian_line(draw, bline, 1000, y_cursor, font_body, (230, 230, 230), (239, 68, 68))
            y_cursor += 62

        draw.text((540, 1850), _shape_persian(theme["watermark"]), fill=(180, 50, 50), font=font_wm, anchor="ma")

    # ------------------ استایل ۲: هنر و پاپیه‌ماشه (فرم براش و پالت کرم/سبز/نارنجی) ------------------
    elif is_art:
        overlay = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
        d_overlay = ImageDraw.Draw(overlay)
        # فرم براش با رنگ کرم گرم و خط سفالی
        _draw_brush_background(
            d_overlay, 60, 1080, 1020, 1820,
            fill_color=(247, 243, 236, 235),
            stroke_color=(217, 119, 6, 230)
        )

        final_canvas = Image.alpha_composite(base_img, overlay).convert("RGB")
        draw = ImageDraw.Draw(final_canvas)

        tag_clean = TAG_LABELS_FA.get(tag, "هنر دست‌ساز")
        draw.text((940, 1130), _shape_persian(f"✦ {tag_clean}"), fill=(40, 90, 60), font=font_tag, anchor="ra")

        head_tokens = _tokenize_text(heading)
        head_lines = _wrap_tokens(head_tokens, font_head, max_width_px=840)
        y_cursor = 1200
        for hline in head_lines[:2]:
            _draw_rich_persian_line(draw, hline, 940, y_cursor, font_head, (45, 30, 20), (194, 65, 12))
            y_cursor += 70

        y_cursor += 15
        draw.line([(140, y_cursor), (940, y_cursor)], fill=(180, 83, 9), width=2)
        y_cursor += 30

        body_tokens = _tokenize_text(body)
        body_lines = _wrap_tokens(body_tokens, font_body, max_width_px=840)
        for bline in body_lines[:5]:
            _draw_rich_persian_line(draw, bline, 940, y_cursor, font_body, (60, 45, 35), (194, 65, 12))
            y_cursor += 60

        draw.text((540, 1855), _shape_persian(theme["watermark"]), fill=(180, 83, 9), font=font_wm, anchor="ma")

    # ------------------ استایل ۳: ترید (کادر شیشه‌ای بنفش و سبز نئونی محبوب) ------------------
    else:
        crop_box = (40, 1050, 1040, 1850)
        lower_crop = base_img.crop(crop_box)
        blurred_lower = lower_crop.filter(ImageFilter.GaussianBlur(radius=25))
        base_img.paste(blurred_lower, crop_box)

        overlay = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
        d_overlay = ImageDraw.Draw(overlay)
        d_overlay.rounded_rectangle([45, 1080, 1035, 1830], radius=42, fill=theme["glass_tint"], outline=theme["border"], width=3)

        final_canvas = Image.alpha_composite(base_img, overlay).convert("RGB")
        draw = ImageDraw.Draw(final_canvas)

        tag_clean = TAG_LABELS_FA.get(tag, tag.replace("_", " "))
        draw.text((975, 1120), _shape_persian(f"• {tag_clean} •"), fill=theme["accent"], font=font_tag, anchor="ra")

        head_tokens = _tokenize_text(heading)
        head_lines = _wrap_tokens(head_tokens, font_head, max_width_px=880)
        y_cursor = 1190
        for hline in head_lines[:2]:
            _draw_rich_persian_line(draw, hline, 975, y_cursor, font_head, theme["text"], theme["accent"])
            y_cursor += 72

        y_cursor += 15
        draw.line([(105, y_cursor), (975, y_cursor)], fill=theme["border"][:3], width=2)
        y_cursor += 30

        body_tokens = _tokenize_text(body)
        body_lines = _wrap_tokens(body_tokens, font_body, max_width_px=890)
        for bline in body_lines[:5]:
            _draw_rich_persian_line(draw, bline, 975, y_cursor, font_body, theme["sub"], theme["accent"])
            y_cursor += 62

        if sticker:
            draw.rounded_rectangle([140, 1720, 940, 1800], radius=24, fill=(10, 10, 15, 180), outline=theme["accent"], width=2)
            draw.text((540, 1740), _shape_persian(sticker[:45]), fill=theme["accent"], font=font_tag, anchor="ma")

        draw.text((540, 1865), _shape_persian(theme["watermark"]), fill=theme["accent"], font=font_wm, anchor="ma")

    final_canvas.save(out_path, quality=94)
    return out_path


def render_carousel(brand, slides, out_dir, bgs, logo, arts=None, slug="trading"):
    """رندر کاروسل با تصویر تمام‌صفحه و باکس شیشه‌ای بلور در پایین اسلایدها"""
    os.makedirs(out_dir, exist_ok=True)
    theme = _get_theme(slug)
    font_head = _load_font(48)
    font_body = _load_font(38)
    font_wm = _load_font(26)

    paths = []
    for i, s in enumerate(slides):
        p = os.path.join(out_dir, f"slide_{i+1:02d}.jpg")

        art_path = arts[i] if (arts and i < len(arts)) else None
        if art_path and os.path.exists(art_path) and os.path.getsize(art_path) > 500:
            base_img = Image.open(art_path).convert("RGBA").resize((1080, 1350), Image.Resampling.LANCZOS)
        else:
            base_img = Image.new("RGBA", (1080, 1350), color=theme["glass_tint"][:3] + (255,))

        crop_box = (40, 720, 1040, 1300)
        lower_crop = base_img.crop(crop_box)
        blurred_lower = lower_crop.filter(ImageFilter.GaussianBlur(radius=20))
        base_img.paste(blurred_lower, crop_box)

        overlay = Image.new("RGBA", (1080, 1350), (0, 0, 0, 0))
        d_overlay = ImageDraw.Draw(overlay)
        d_overlay.rounded_rectangle([45, 730, 1035, 1280], radius=38, fill=theme["glass_tint"], outline=theme["border"], width=3)

        final_canvas = Image.alpha_composite(base_img, overlay).convert("RGB")
        draw = ImageDraw.Draw(final_canvas)

        heading = str(s.get("heading") or f"اسلاید {i+1}")
        body = str(s.get("body") or "")

        head_tokens = _tokenize_text(heading)
        head_lines = _wrap_tokens(head_tokens, font_head, max_width_px=890)
        y_c = 770
        for hl in head_lines[:2]:
            _draw_rich_persian_line(draw, hl, 975, y_c, font_head, theme["text"], theme["accent"])
            y_c += 68

        y_c += 15
        draw.line([(95, y_c), (975, y_c)], fill=theme["border"][:3], width=2)
        y_c += 25

        if "**" not in body:
            words = body.split()
            if len(words) >= 5:
                words[1] = f"**{words[1]}**"
                if len(words) > 12:
                    words[7] = f"**{words[7]}**"
                body = " ".join(words)

        body_tokens = _tokenize_text(body)
        body_lines = _wrap_tokens(body_tokens, font_body, max_width_px=890)
        for bl in body_lines[:5]:
            _draw_rich_persian_line(draw, bl, 975, y_c, font_body, theme["sub"], theme["accent"])
            y_c += 58

        draw.text((540, 1315), _shape_persian(f"{theme['watermark']}  •  {i+1}/{len(slides)}"), fill=theme["accent"], font=font_wm, anchor="ma")

        final_canvas.save(p, quality=94)
        paths.append(p)
    return paths


def render_reel_frame(brand, text, out_path, index, bgs, logo, art_path=None, slug="trading"):
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