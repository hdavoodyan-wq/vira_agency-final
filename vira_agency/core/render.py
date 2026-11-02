"""
ماژول رندرینگ گرافیکی کاروسل و استوری با تم‌های رنگی جدید (بنفش سلطنتی و گوتیک)
"""
import os
from PIL import Image, ImageDraw

def render_story(brand, story_obj, out_path, index, bgs, logo, tag, art_path=None):
    """رندر تک‌استوری تخصصی با کیفیت بالا"""
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    # تم رنگی پس‌زمینه (بنفش تیره برای ترید یا مشکی گوتیک برای روانشناسی)
    img = Image.new("RGB", (1080, 1920), color=(15, 12, 28))
    draw = ImageDraw.Draw(img)
    
    if art_path and os.path.exists(art_path):
        try:
            art = Image.open(art_path).resize((1080, 1200))
            img.paste(art, (0, 0))
        except Exception:
            pass

    # باکس متن شیک و خوانا
    draw.rectangle([60, 1300, 1020, 1800], fill=(24, 20, 37), outline=(168, 85, 247), width=3)
    draw.text((100, 1350), f"📌 [{tag}]", fill=(74, 222, 128))
    draw.text((100, 1430), story_obj.get("heading", "")[:70], fill=(255, 255, 255))
    
    body = story_obj.get("body", "")
    draw.text((100, 1530), body[:250], fill=(226, 232, 240))
    
    img.save(out_path)
    return out_path

def render_carousel(brand, slides, out_dir, bgs, logo, arts=None):
    """رندر کاروسل"""
    os.makedirs(out_dir, exist_ok=True)
    paths = []
    for i, s in enumerate(slides):
        p = os.path.join(out_dir, f"slide_{i+1:02d}.jpg")
        img = Image.new("RGB", (1080, 1080), color=(15, 12, 28))
        draw = ImageDraw.Draw(img)
        draw.text((80, 100), s.get("heading", ""), fill=(255, 255, 255))
        draw.text((80, 300), s.get("body", ""), fill=(226, 232, 240))
        img.save(p)
        paths.append(p)
    return paths

def render_reel_frame(brand, text, out_path, index, bgs, logo, art_path=None):
    """رندر فریم ریلز"""
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    img = Image.new("RGB", (1080, 1920), color=(15, 12, 28))
    draw = ImageDraw.Draw(img)
    draw.text((100, 900), text, fill=(255, 255, 255))
    img.save(out_path)
    return out_path
