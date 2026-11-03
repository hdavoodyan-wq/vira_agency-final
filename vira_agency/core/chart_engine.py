"""
vira_agency/core/chart_engine.py
موتور مستقل تولید چارت‌های تکنیکال واقعی و برداری سبک تریدینگ‌ویو
تضمین یکپارچگی ۱۰۰٪ بین تصویر سوال و تصویر پاسخ
"""
from PIL import Image, ImageDraw, ImageFont
import random
import os

def render_tradingview_quiz_pair(topic: str, is_bearish_trap: bool = True):
    """
    تولید دو تصویر دقیقاً یکسان با نسبت 9:16:
    تصویر ۱: چارت تمیز بدون خطوط تحلیل (سوال)
    تصویر ۲: دقیقاً روی همان چارت، خط مقاومت، زون استاپ‌هانت و فلش ریزش (پاسخ)
    """
    w, h = 1080, 1920
    # ۱. پس‌زمینه تیره مدرن چارت تریدینگ‌ویو
    base = Image.new("RGBA", (w, h), (10, 14, 23, 255))
    draw = ImageDraw.Draw(base)

    # رسم شبکه چهارخانه ملایم (Grid Lines)
    for y in range(200, 1300, 80):
        draw.line([(60, y), (w - 60, y)], fill=(22, 29, 44, 255), width=1)
    for x in range(60, w - 60, 100):
        draw.line([(x, 200), (x, 1300)], fill=(22, 29, 44, 255), width=1)

    # ۲. ایجاد کندل‌های استاندارد و پیوسته
    random.seed(42 if not topic else hash(topic) % 10000)
    prices = [600]
    for _ in range(22):
        step = random.randint(-25, 40)
        prices.append(prices[-1] + step)

    # ستاپ بریک‌اوت جعلی در انتهای چارت
    prices[-4] = 730
    prices[-3] = 780
    prices[-2] = 815  # کندل شارپ صعودی در مقاومت
    prices[-1] = 800

    start_x = 90
    candle_w = 26
    gap = 42

    candle_coords = []
    resistance_y = 1000 - int(780 * 0.7)

    for i, p in enumerate(prices):
        cx = start_x + (i * gap)
        cy = 1200 - int(p * 0.7)
        prev_p = prices[i-1] if i > 0 else p
        is_green = p >= prev_p

        c_body = (14, 203, 129, 255) if is_green else (246, 70, 93, 255)
        high_y = cy - random.randint(15, 35)
        low_y = cy + random.randint(15, 35)

        # رسم سایه کندل
        draw.line([(cx + candle_w // 2, high_y), (cx + candle_w // 2, low_y)], fill=c_body, width=3)
        # رسم بدنه کندل
        b_top = min(cy, cy + int((prev_p - p) * 0.5))
        b_bottom = max(cy, cy + int((prev_p - p) * 0.5)) + 8
        draw.rectangle([(cx, b_top), (cx + candle_w, b_bottom)], fill=c_body)
        candle_coords.append((cx, cy, high_y, low_y))

    # ذخیره تصویر ۱ به عنوان پایه خالص سوال
    img_question = base.copy()

    # ۳. رسم خطوط تحلیلی روی تصویر ۲ (پاسخ)
    img_answer = base.copy()
    draw_ans = ImageDraw.Draw(img_answer)

    # خط مقاومت داینامیک
    draw_ans.line([(80, resistance_y), (w - 80, resistance_y)], fill=(234, 179, 8, 255), width=4)
    
    # کادر قرمز تله استاپ‌هانت (Fakeout Box)
    last_x, last_y, _, _ = candle_coords[-2]
    draw_ans.rectangle(
        [(last_x - 15, resistance_y - 45), (last_x + candle_w + 35, resistance_y + 15)],
        outline=(246, 70, 93, 255), width=3
    )

    # فلش ریزش شدید
    fx_start = last_x + 50
    fy_start = resistance_y + 20
    fx_end = fx_start + 80
    fy_end = fy_start + 180
    draw_ans.line([(fx_start, fy_start), (fx_end, fy_end)], fill=(246, 70, 93, 255), width=6)
    # نوک فلش
    draw_ans.polygon([(fx_end, fy_end), (fx_end - 25, fy_end - 35), (fx_end + 15, fy_end - 20)], fill=(246, 70, 93, 255))

    return img_question, img_answer
