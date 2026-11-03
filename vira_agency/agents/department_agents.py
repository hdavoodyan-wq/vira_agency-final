"""
vira_agency/agents/department_agents.py
ایجنت‌های اختصاصی با پشتیبانی از کاراکترهای دراکولا، گرگ، اسکلت و بانوی مرموز
و اتصال مستقیم به موتور چارت‌های تریدینگ‌ویو
"""
from typing import Dict, Any, List
import random
from vira_agency.core.chart_engine import render_tradingview_quiz_pair

class DarkPsychAgent:
    """ایجنت پیج ذهن زیبا با محوریت کاراکترهای دراکولا، گرگ تنها، اسکلت و بانوی مرموز"""
    def __init__(self):
        self.page_key = "dark_psychology"
        self.instagram_id = "@zehnayetaarik"
        self.brand_title = "ذهن زیبا"
        self.characters = [
            "Count Dracula with deep crimson velvet cape, sharp gaze, cinematic gothic atmosphere",
            "Lone majestic werewolf in dense foggy mystical dark woods, glowing fierce amber eyes",
            "Mysterious elegant aristocrat lady wearing ornate masquerade mask, chiaroscuro lighting",
            "Gothic skeleton knight in battle-worn obsidian armor, dark fantasy cinematic realism"
        ]

    def make_story(self, subtype: str) -> Dict[str, Any]:
        char_prompt = random.choice(self.characters)
        topics = {
            "d_knight": ("قانون نفوذ و تسلط", "چگونه در سکوت، کنترل بازی روانی را در دست بگیری؟", char_prompt),
            "d_manipulation": ("شناخت فریب و مکر", "آدم‌های خطرناک همیشه با لبخند و تعریف بی‌جا وارد می‌شوند.", char_prompt),
            "d_wolf": ("استقلال عاطفی", "وقتی به تایید دیگران نیاز نداری، قدرت آسیب زدن به تو از بین می‌رود.", char_prompt),
            "d_charisma": ("جذابیت تاریک", "کمتر حرف بزن و بگذار کنجکاوی دیگران درباره تو تمام نشود.", char_prompt),
            "d_hypno": ("هیپنوتیزم کلامی", "کلماتی که ناخودآگاه مخاطب را تسلیم خواسته تو می‌کنند.", char_prompt),
        }
        badge, text, prompt = topics.get(subtype, ("ذهن زیبا", "قوانین نامرئی روانشناسی تاریک", char_prompt))
        return {
            "title": "قوانین پنهان نفوذ",
            "badge": badge,
            "text": text,
            "image_prompt": f"{prompt}, dark moody surreal backdrop, high resolution 8k, dramatic shadows, no text, no captions",
            "sticker": "این اصل رو درک کردی؟"
        }

    def make_carousel(self, topic: str, count: int = 8) -> List[Dict[str, Any]]:
        slides = []
        char_prompt = random.choice(self.characters)
        slides.append({
            "slide_num": 1,
            "title": "قلاب ذهنی",
            "text": f"چطور بدون اینکه بفهمی با {topic} کنترل تصمیم‌هایت را می‌گیرند؟",
            "image_prompt": f"Surreal cinematic art, {char_prompt}, crimson and black palette, dramatic composition, 8k, no text"
        })
        slides.append({
            "slide_num": 2,
            "title": "ایجاد مسئله",
            "text": "در ظاهر همه‌چیز صمیمانه است، اما ناگهان حس می‌کنی بدهکار همیشگی هستی.",
            "image_prompt": "Dark gothic chess board with shadowy figures, dramatic shadows, no text"
        })
        slides.append({
            "slide_num": 3,
            "title": "مکانیسم دستکاری",
            "text": "تکنیک القای حس تقصیر؛ وقتی تو را مجبور به عذرخواهی برای کار نکرده می‌کنند.",
            "image_prompt": "Cinematic cracked antique mirror reflecting dual personalities, surrealism, no text"
        })
        slides.append({
            "slide_num": 4,
            "title": "نشانه‌های آشکار",
            "text": "کلماتی مثل 'تو حساسی' یا 'من فقط خیر تو را می‌خواهم' زنگ خطرهای بزرگ هستند.",
            "image_prompt": f"{char_prompt}, dramatic rim lighting, dark aesthetic, no text"
        })
        slides.append({
            "slide_num": 5,
            "title": "سلاح پادزهر",
            "text": "سکوت کامل و تایید نکردن! بازی آن‌ها روی واکنش‌های احساسی تو سوار است.",
            "image_prompt": "A glowing silver key breaking dark rusty iron chains, minimalist cinematic, no text"
        })
        slides.append({
            "slide_num": 6,
            "title": "نتیجه و تصمیم",
            "text": "قدرت در دست کسی است که کمتر محتاج تایید و تمجید دیگران باشد.",
            "image_prompt": f"{char_prompt}, looking calmly into horizon, gothic castle backdrop, no text"
        })
        return slides[:count]

class TradingAgent:
    """ایجنت تخصصی پیج روانشناسی معامله‌گری و کوییزهای جفتی چارت تریدینگ‌ویو"""
    def __init__(self):
        self.page_key = "trading_psychology"
        self.instagram_id = "@tradebazehn"
        self.brand_title = "روانشناسی معامله‌گری"

    def make_story_quiz_pair(self, topic: str) -> Dict[str, Any]:
        """تولید دو استوری چارت پیوسته و یکسان با موتور تریدینگ‌ویو"""
        img_q, img_ans = render_tradingview_quiz_pair(topic, is_bearish_trap=True)
        return {
            "story_question": {
                "badge": "کوییز تریدری",
                "title": "کوییز ستاپ: شکست یا تله؟",
                "text": "کندل پرقدرت سبز مقاومت را شکست، اما حجم افت کرد! آیا لانگ می‌گیری یا شورت؟",
                "raw_image": img_q,
                "sticker": "لانگ می‌گیری یا شورت؟"
            },
            "story_answer": {
                "badge": "تحلیل تکنیکال",
                "title": "پاسخ تحلیل: تله گاوی (Bull Trap)",
                "text": "این یک شکست فیک بود! استاپ‌هانت نقدینگی شکل گرفت و بازار با مومنتوم ریخت. ورود اشتباه بود.",
                "raw_image": img_ans,
                "sticker": "حدست درست بود؟"
            }
        }

    def make_carousel(self, topic: str, count: int = 8) -> List[Dict[str, Any]]:
        slides = []
        slides.append({
            "slide_num": 1,
            "title": "تله روانشناسی",
            "text": f"چرا در {topic} مغزت دقیقاً خلاف منطق چارت عمل می‌کند؟",
            "image_prompt": "Cinematic exhausted trader sitting in dark modern office in front of glowing charts, neon blue and crimson red, no text"
        })
        slides.append({
            "slide_num": 2,
            "title": "آناتومی اشتباه",
            "text": "سود کم را سریع می‌بندی اما اجازه می‌دهی ضرر کل سرمایه‌ات را ببلعد.",
            "image_prompt": "Minimalist surreal human brain intertwined with glowing financial stock charts, dark background, no text"
        })
        slides.append({
            "slide_num": 3,
            "title": "سوگیری زیان‌گریزی",
            "text": "درد باختن دو برابر لذت بردن است؛ به همین دلیل به امید بازگشت قیمت می‌مانی.",
            "image_prompt": "Cinematic conceptual sandglass with gold coins falling into dark void, no text"
        })
        slides.append({
            "slide_num": 4,
            "title": "قانون نجات سرمایه",
            "text": "قبل از کلیک روی بای، حد ضرر را بگذار و دست به آن نزن. بازار جای انتقام نیست.",
            "image_prompt": "High-tech futuristic trading terminal with locked green padlock, dark aesthetic, no text"
        })
        return slides[:count]

class ArtAgent:
    """ایجنت گالری هنری الهه"""
    def __init__(self):
        self.page_key = "art_gallery"
        self.instagram_id = "@elartgallery.ir"
        self.brand_title = "گالری هنری الهه"

    def make_story(self, subtype: str) -> Dict[str, Any]:
        return {
            "title": "کالکشن آینه‌های وابی‌سابی",
            "badge": "دکوراسیون ترند",
            "text": "آینه‌های ارگانیک پاپیه‌ماشه؛ بافتی گرم و دست‌ساز برای درخشش دکور خانه شما. سفارش در دایرکت.",
            "image_prompt": "Wabi-sabi organic wavy mirror with handcrafted paper mache frame on warm textured plaster wall, minimalist interior design, no text",
            "sticker": "این مدل رو می‌پسندی؟"
        }
