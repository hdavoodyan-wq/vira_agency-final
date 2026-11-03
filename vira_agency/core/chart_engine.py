"""
vira_agency/core/chart_engine.py
موتور اختصاصی و مستقل تولید چارت‌های تکنیکال برداری به سبک تریدینگ‌ویو (TradingView)
تضمین یکپارچگی ۱۰۰٪ و تطابق کامل تصویر پایه بین استوری ۱ (سوال) و استوری ۲ (پاسخ تحلیلی)
بدون وابستگی به مدل‌های تصویری فانتزی
"""
import os
import random
from PIL import Image, ImageDraw, ImageFont


def _get_chart_font(size: int):
    """بارگذاری فونت خوانا برای اعداد و برچسب‌های چارت"""
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "data/fonts/Vazirmatn-Bold.ttf"
    ]
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                return ImageFont.truetype(fp, size)
            except Exception:
                pass
    return ImageFont.load_default()


def render_tradingview_quiz_pair(topic: str = "", is_bearish_trap: bool = True):
    """
    تولید دو تصویر مجزا اما با بیس کاملاً یکسان با ابعاد استاندارد ۹:۱۶ (1080x1920):
    خروجی اول (img_question): چارت تکنیکال تمیز همراه با بریک‌اوت مشکوک بدون هیچ خط راهنما
    خروجی دوم (img_answer): دقیقاً همان چارت همراه با رسم خط مقاومت، کادر قرمز تله استاپ‌هانت (Bull Trap) و فلش شکست و ریزش
    """
    w, h = 1080, 1920

    # ۱. ایجاد بوم پایه چارت تیره استاندارد تریدینگ‌ویو
    base = Image.new("RGBA", (w, h), (13, 17, 28, 255))
    draw = ImageDraw.Draw(base)

    # رسم خطوط شطرنجی پس‌زمینه (Grid Lines)
    grid_color = (24, 32, 50, 255)
    for y in range(160, 1260, 75):
        draw.line([(50, y), (w - 50, y)], fill=grid_color, width=1)
    for x in range(70, w - 50, 95):
        draw.line([(x, 160), (x, 1260)], fill=grid_color, width=1)

    # ۲. تولید دیتای پیوسته قیمت با دانه مشخص بر اساس تاپیک برای ثبات خروجی
    seed_val = 1373 if not topic else (abs(hash(topic)) % 50000)
    rng = random.Random(seed_val)

    candle_count = 21
    prices = [680]
    for _ in range(candle_count - 4):
        delta = rng.randint(-22, 36)
        prices.append(prices[-1] + delta)

    # ایجاد الگوی تله گاوی (Bull Trap) در انتهای چارت:
    # صعود پرقدرت به سمت مقاومت، شکست ناگهانی و برگشت
    prices.append(810)  # کندل ماقبل مقاومت
    prices.append(855)  # کندل شکست پرقدرت مقاومت (Bullish Breakout)
    prices.append(875)  # بالاترین قیمت لحظه‌ای
    prices.append(860)  # تثبیت اولیه مشکوک

    # پارامترهای هندسی چارت
    start_x = 85
    candle_w = 26
    gap = 43
    floor_y = 1200
    scale_factor = 0.82

    candle_positions = []
    font_axis = _get_chart_font(20)

    # رسم محور قیمت در سمت راست چارت
    for level_price in range(650, 920, 50):
        level_y = floor_y - int(level_price * scale_factor)
        draw.line([(w - 110, level_y), (w - 95, level_y)], fill=(75, 85, 110, 255), width=2)
        draw.text((w - 90, level_y - 10), f"{level_price * 100:,}", fill=(100, 115, 145, 255), font=font_axis)

    # رسم کندل‌استیک‌ها
    for i, p in enumerate(prices):
        cx = start_x + (i * gap)
        cy = floor_y - int(p * scale_factor)
        prev_p = prices[i - 1] if i > 0 else (p - 10)
        is_green = p >= prev_p

        # رنگ‌های رسمی تریدینگ‌ویو
        c_fill = (14, 203, 129, 255) if is_green else (246, 70, 93, 255)

        high_offset = rng.randint(18, 42)
        low_offset = rng.randint(18, 42)
        high_y = cy - high_offset
        low_y = cy + low_offset

        # خط سایه کندل (Wick)
        draw.line([(cx + candle_w // 2, high_y), (cx + candle_w // 2, low_y)], fill=c_fill, width=3)

        # بدنه مستطیلی کندل (Body)
        body_top = min(cy, cy + int((prev_p - p) * scale_factor * 0.45))
        body_bottom = max(cy, cy + int((prev_p - p) * scale_factor * 0.45)) + 10
        draw.rectangle([(cx, body_top), (cx + candle_w, body_bottom)], fill=c_fill)

        candle_positions.append((cx, cy, high_y, low_y))

    # سطح مقاومت تکنیکال
    resistance_price = 835
    resistance_y = floor_y - int(resistance_price * scale_factor)

    # استوری اول: چارت سوال خالص (بدون خطوط کمکی و خط‌چین)
    img_question = base.copy()

    # استوری دوم: همان چارت با رسم دقیق خط مقاومت، زون استاپ‌هانت و فلش قرمز ریزش
    img_answer = base.copy()
    draw_ans = ImageDraw.Draw(img_answer)

    # رسم خط افقی مقاومت با رنگ زرد هشدار
    draw_ans.line([(70, resistance_y), (w - 70, resistance_y)], fill=(245, 158, 11, 240), width=4)

    # کادر قرمز ناحیه استاپ‌هانت و فیک‌بریک (Fakeout Zone)
    target_cx, target_cy, _, _ = candle_positions[-3]
    zone_x1 = target_cx - 15
    zone_y1 = resistance_y - 55
    zone_x2 = target_cx + (candle_w * 2) + 30
    zone_y2 = resistance_y + 20
    draw_ans.rectangle([(zone_x1, zone_y1), (zone_x2, zone_y2)], outline=(246, 70, 93, 255), width=3)

    # برچسب Fakeout بالای کادر قرمز
    font_lbl = _get_chart_font(22)
    draw_ans.text((zone_x1, zone_y1 - 32), "Fakeout / Bull Trap", fill=(246, 70, 93, 255), font=font_lbl)

    # فلش بزرگ و ضخیم قرمز نشان‌دهنده ریزش آبشاری بعدی مارکت
    arrow_start_x = target_cx + candle_w + 35
    arrow_start_y = resistance_y + 15
    arrow_end_x = arrow_start_x + 95
    arrow_end_y = arrow_start_y + 210

    draw_ans.line([(arrow_start_x, arrow_start_y), (arrow_end_x, arrow_end_y)], fill=(246, 70, 93, 255), width=7)

    # نوک فلش
    draw_ans.polygon(
        [
            (arrow_end_x, arrow_end_y),
            (arrow_end_x - 30, arrow_end_y - 35),
            (arrow_end_x + 12, arrow_end_y - 22),
        ],
        fill=(246, 70, 93, 255),
    )

    return img_question, img_answer
