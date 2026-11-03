"""
موتور رندرینگ گرافیکی دستیار ویرا
شامل:
۱. جایگاه استاندارد خط‌چین برای قرار دادن استیکر نظرسنجی (Poll) اینستاگرام
۲. ترسیم حرفه‌ای خطوط تکنیکال، کانال و فلش روی استوری پاسخ کوییز ترید
۳. تم‌های بنفش ترید، گوتیک ذهن زیبا و قلم‌موی گالری الهه
"""
import os
import re
import urllib.request
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FONT_DIR = "data/fonts"
FONT_PATH = os.path.join(FONT_DIR, "Vazirmatn-Bold.ttf")

TAG_LABELS_FA = {
    "t_market": "تحلیل بازار",
    "t_news": "اخبار داغ",
    "t_quiz": "کوییز تریدری",
    "t_psyc": "روانشناسی ترید",
    "t_hunt": "شکار استاپ",
    "t_bull": "نبرد گاو و خرس",
    "d_chal": "دوراهی شوالیه",
    "d_edu": "ترفند مکر",
    "d_mar": "قوانین رابطه",
    "d_opt": "تست شخصیت",
    "d_sec": "زبان بدن",
    "art_mirror": "آینه وابی‌سابی",
    "art_decor": "ظروف دکوراتیو",
    "art_sculpture": "مجسمه فرم آزاد",
    "behind": "پشت صحنه گالری",
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
            "border": (139, 92, 246, 230),
            "glass_tint": (15, 10, 32, 225),
            "accent": (74, 222, 128),
            "text": (255, 255, 255),
            "sub": (226, 232, 240),
            "watermark": "@tradebazehn | روانشناسی معامله‌گری"
        }
    elif s.startswith("d_") or "dark" in s:
        return {
            "border": (220, 38, 38, 230),
            "glass_tint": (16, 12, 14, 230),
            "accent": (239, 68, 68),
            "text": (255, 255, 255),
            "sub": (229, 231, 235),
            "watermark": "@zehnayetaarik | ذهن زیبا"
        }
    else:
        return {
            "border": (217, 119, 6, 230),
            "glass_tint": (32, 24, 18, 230),
            "accent": (249, 115, 22),
            "text": (254, 243, 199),
            "sub": (253, 230, 138),
            "watermark": "@elartgallery.ir | گالری هنری الهه"
        }


def _fit_image_preserve_aspect(raw_img: Image.Image, target_w: int = 1080, target_h: int = 1920) -> Image.Image:
    img_w, img_h = raw_img.size
    scale = max(target_w / img_w, target_h / img_h)
    new_w = int(img_w * scale)
    new_h = int(img_h * scale)
    resized = raw_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    left = (new_w - target_w) // 2
    top = int((new_h - target_h) * 0.15)
    top = max(0, min(top, new_h - target_h))
    return resized.crop((left, top, left + target_w, top + target_h))


def _tokenize_text(text: str) -> list[tuple[str, bool]]:
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
    cur_x = start_x
    space_w = font.getbbox(" ")[2] - font.getbbox(" ")[0] if font else 10

    for word, is_hl in line_tokens:
        shaped = _shape_persian(word)
        bbox = font.getbbox(shaped) if font else (0, 0, len(word) * 12, 20)
        word_w = bbox[2] - bbox[0]
        color = accent_color if is_hl else default_color
        draw.text((cur_x - word_w, y), shaped, fill=color, font=font)
        cur_x -= (word_w + space_w)


def _draw_dashed_rect(draw: ImageDraw.ImageDraw, bbox: list[int], color: tuple, dash_len: int = 14, space_len: int = 10, width: int = 3):
    """رسم کادر خط‌چین مدرن نئونی برای جایگاه استیکر پول اینستاگرام"""
    x1, y1, x2, y2 = bbox
    # بالا و پایین
    for x in range(x1, x2, dash_len + space_len):
        draw.line([(x, y1), (min(x + dash_len, x2), y1)], fill=color, width=width)
        draw.line([(x, y2), (min(x + dash_len, x2), y2)], fill=color, width=width)
    # چپ و راست
    for y in range(y1, y2, dash_len + space_len):
        draw.line([(x1, y), (x1, min(y + dash_len, y2))], fill=color, width=width)
        draw.line([(x2, y), (x2, min(y + dash_len, y2))], fill=color, width=width)


def _draw_technical_analysis_overlays(draw: ImageDraw.ImageDraw, is_answer: bool = False):
    """ترسیم خودکار خطوط تکنیکال، ناحیه شکست و فلش روی چارت در استوری پاسخ"""
    if not is_answer:
        return

    # رسم خط مقاومت افقی با رنگ قرمز نئونی
    draw.line([(100, 520), (980, 520)], fill=(239, 68, 68, 240), width=4)
    # رسم خط روند صعودی شکسته شده
    draw.line([(120, 850), (700, 480)], fill=(139, 92, 246, 220), width=4)

    # رسم ناحیه شکست فیک (Fakeout Zone) به صورت مستطیل شفاف قرمز
    draw.rectangle([620, 450, 780, 530], outline=(239, 68, 68), width=3)

    # رسم فلش حرکت ریزشی شورت (پاسخ معامله)
    # بدنه فلش
    draw.line([(760, 530), (880, 780)], fill=(239, 68, 68), width=6)
    # نوک فلش
    draw.polygon([(880, 780), (840, 740), (895, 745)], fill=(239, 68, 68))


def render_story(brand, story_obj, out_path, index, bgs, logo, tag, art_path=None):
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    theme = _get_theme(tag)
    tag_lower = (tag or "").lower()
    is_dark = tag_lower.startswith("d_") or "dark" in tag_lower
    is_art = tag_lower.startswith("art_") or tag_lower in ("behind", "showcase", "workshop") or "art" in tag_lower or "papermache" in tag_lower
    is_news = tag_lower == "t_news"
    is_quiz = tag_lower == "t_quiz" or "کوییز" in str(story_obj.get("heading") or "")
    is_quiz_q = is_quiz and story_obj.get("quiz_type") == "question"
    is_quiz_a = is_quiz and story_obj.get("quiz_type") == "answer"

    if art_path and os.path.exists(art_path) and os.path.getsize(art_path) > 500:
        raw_img = Image.open(art_path).convert("RGBA")
        base_img = _fit_image_preserve_aspect(raw_img, 1080, 1920)
    else:
        base_img = Image.new("RGBA", (1080, 1920), color=theme["glass_tint"][:3] + (255,))

    font_tag = _load_font(32)
    font_head = _load_font(46)
    font_body = _load_font(35)
    font_news = _load_font(31)
    font_poll = _load_font(30)
    font_wm = _load_font(26)

    heading = str(story_obj.get("heading") or "نکته کلیدی").strip()
    body = str(story_obj.get("body") or "").strip()
    sticker = str(story_obj.get("sticker") or "").strip()

    # ۱. پیج ذهن زیبا (روانشناسی تاریک): بدون کادر، تیتر درشت و خط سرخ زیر آن
    if is_dark:
        gradient = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
        d_grad = ImageDraw.Draw(gradient)
        for y in range(900, 1920):
            alpha = int(((y - 900) / 1020) ** 1.3 * 220)
            d_grad.line([(0, y)], fill=(8, 6, 8, min(230, alpha)))

        final_canvas = Image.alpha_composite(base_img, gradient).convert("RGB")
        draw = ImageDraw.Draw(final_canvas)

        head_tokens = _tokenize_text(heading)
        head_lines = _wrap_tokens(head_tokens, font_head, max_width_px=920)
        y_cursor = 1100
        for hline in head_lines[:2]:
            total_w = sum(font_head.getbbox(_shape_persian(w))[2] - font_head.getbbox(_shape_persian(w))[0] + 8 for w, _ in hline)
            start_x = 540 + (total_w // 2)
            _draw_rich_persian_line(draw, hline, start_x, y_cursor, font_head, (255, 255, 255), (239, 68, 68))
            y_cursor += 70

        y_cursor += 15
        draw.line([(450, y_cursor), (630, y_cursor)], fill=(220, 38, 38), width=3)
        y_cursor += 40

        body_tokens = _tokenize_text(body)
        body_lines = _wrap_tokens(body_tokens, font_body, max_width_px=920)
        for bline in body_lines[:6]:
            _draw_rich_persian_line(draw, bline, 1000, y_cursor, font_body, (230, 230, 230), (239, 68, 68))
            y_cursor += 62

        draw.text((540, 1850), _shape_persian(theme["watermark"]), fill=(200, 60, 60), font=font_wm, anchor="ma")

    # ۲. پیج گالری هنری الهه: پالت کرم شنی، براش هنری و دعوت به سفارش
    elif is_art:
        overlay = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
        d_overlay = ImageDraw.Draw(overlay)
        d_overlay.rounded_rectangle([55, 1100, 1025, 1830], radius=32, fill=(247, 243, 236, 242), outline=(217, 119, 6, 230), width=3)

        final_canvas = Image.alpha_composite(base_img, overlay).convert("RGB")
        draw = ImageDraw.Draw(final_canvas)

        tag_clean = TAG_LABELS_FA.get(tag, "گالری الهه")
        draw.text((940, 1140), _shape_persian(f"✦ {tag_clean}"), fill=(40, 90, 60), font=font_tag, anchor="ra")

        head_tokens = _tokenize_text(heading)
        head_lines = _wrap_tokens(head_tokens, font_head, max_width_px=840)
        y_cursor = 1210
        for hline in head_lines[:2]:
            _draw_rich_persian_line(draw, hline, 940, y_cursor, font_head, (45, 30, 20), (194, 65, 12))
            y_cursor += 68

        y_cursor += 15
        draw.line([(140, y_cursor), (940, y_cursor)], fill=(180, 83, 9), width=2)
        y_cursor += 30

        body_tokens = _tokenize_text(body)
        body_lines = _wrap_tokens(body_tokens, font_body, max_width_px=840)
        for bline in body_lines[:5]:
            _draw_rich_persian_line(draw, bline, 940, y_cursor, font_body, (60, 45, 35), (194, 65, 12))
            y_cursor += 60

        if sticker and y_cursor < 1720:
            draw.rounded_rectangle([140, 1720, 940, 1800], radius=24, fill=(240, 230, 215, 230), outline=(194, 65, 12), width=2)
            draw.text((540, 1740), _shape_persian(sticker[:45]), fill=(180, 83, 9), font=font_tag, anchor="ma")

        draw.text((540, 1860), _shape_persian(theme["watermark"]), fill=(180, 83, 9), font=font_wm, anchor="ma")

    # ۳. پیج روانشناسی معامله‌گری: کادر شیشه‌ای بنفش سلطنتی و نئون سبز
    else:
        # اگر استوری پاسخ کوییز است، خطوط تحلیل تکنیکال را روی خود چارت رسم کن
        if is_quiz_a:
            draw_chart = ImageDraw.Draw(base_img)
            _draw_technical_analysis_overlays(draw_chart, is_answer=True)

        crop_box = (40, 1140, 1040, 1850)
        lower_crop = base_img.crop(crop_box)
        blurred_lower = lower_crop.filter(ImageFilter.GaussianBlur(radius=25))
        base_img.paste(blurred_lower, crop_box)

        overlay = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
        d_overlay = ImageDraw.Draw(overlay)
        d_overlay.rounded_rectangle([45, 1150, 1035, 1835], radius=40, fill=theme["glass_tint"], outline=theme["border"], width=3)

        # اگر استوری ۱ کوییز است: رسم باکس خط‌چین نئونی برای چسباندن استیکر نظرسنجی اینستاگرام
        if is_quiz_q:
            _draw_dashed_rect(d_overlay, [120, 940, 960, 1100], color=theme["accent"], width=3)

        final_canvas = Image.alpha_composite(base_img, overlay).convert("RGB")
        draw = ImageDraw.Draw(final_canvas)

        if is_quiz_q:
            poll_guide = "📍 محل قرار دادن استیکر نظرسنجی اینستاگرام (Poll)"
            draw.text((540, 1000), _shape_persian(poll_guide), fill=theme["accent"], font=font_poll, anchor="ma")

        tag_clean = TAG_LABELS_FA.get(tag, "روانشناسی ترید")
        draw.text((975, 1195), _shape_persian(f"• {tag_clean} •"), fill=theme["accent"], font=font_tag, anchor="ra")

        head_tokens = _tokenize_text(heading)
        head_lines = _wrap_tokens(head_tokens, font_head, max_width_px=880)
        y_cursor = 1255
        for hline in head_lines[:2]:
            _draw_rich_persian_line(draw, hline, 975, y_cursor, font_head, theme["text"], theme["accent"])
            y_cursor += 66

        y_cursor += 10
        draw.line([(105, y_cursor), (975, y_cursor)], fill=theme["border"][:3], width=2)
        y_cursor += 25

        if is_news and ("\n" in body or "•" in body):
            lines = [ln.strip() for ln in body.split("\n") if ln.strip()]
            for item in lines[:5]:
                clean_item = item if item.startswith("•") else f"• {item}"
                item_tokens = _tokenize_text(clean_item)
                item_wrapped = _wrap_tokens(item_tokens, font_news, max_width_px=880)
                for wln in item_wrapped:
                    _draw_rich_persian_line(draw, wln, 975, y_cursor, font_news, theme["sub"], theme["accent"])
                    y_cursor += 46
                y_cursor += 8
        else:
            body_tokens = _tokenize_text(body)
            body_lines = _wrap_tokens(body_tokens, font_body, max_width_px=890)
            for bline in body_lines[:5]:
                _draw_rich_persian_line(draw, bline, 975, y_cursor, font_body, theme["sub"], theme["accent"])
                y_cursor += 58

        if sticker and y_cursor < 1720:
            draw.rounded_rectangle([140, 1720, 940, 1800], radius=24, fill=(10, 10, 15, 180), outline=theme["accent"], width=2)
            draw.text((540, 1740), _shape_persian(sticker[:45]), fill=theme["accent"], font=font_tag, anchor="ma")

        draw.text((540, 1865), _shape_persian(theme["watermark"]), fill=theme["accent"], font=font_wm, anchor="ma")

    final_canvas.save(out_path, quality=94)
    return out_path


def render_carousel(brand, slides, out_dir, bgs, logo, arts=None, slug="trading"):
    os.makedirs(out_dir, exist_ok=True)
    theme = _get_theme(slug)
    font_head = _load_font(46)
    font_body = _load_font(36)
    font_wm = _load_font(26)

    paths = []
    for i, s in enumerate(slides):
        p = os.path.join(out_dir, f"slide_{i+1:02d}.jpg")
        art_path = arts[i] if (arts and i < len(arts)) else None

        if art_path and os.path.exists(art_path) and os.path.getsize(art_path) > 500:
            raw_img = Image.open(art_path).convert("RGBA")
            base_img = _fit_image_preserve_aspect(raw_img, 1080, 1350)
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
            y_c += 64

        y_c += 12
        draw.line([(95, y_c), (975, y_c)], fill=theme["border"][:3], width=2)
        y_c += 22

        body_tokens = _tokenize_text(body)
        body_lines = _wrap_tokens(body_tokens, font_body, max_width_px=890)
        for bl in body_lines[:5]:
            _draw_rich_persian_line(draw, bl, 975, y_c, font_body, theme["sub"], theme["accent"])
            y_c += 56

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
