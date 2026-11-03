"""
vira_agency/agents/department_agents.py
ایجنت‌های تخصصی تولید محتوا با لحن ارگانیک و صمیمی، کاراکترهای اختصاصی و سناریوهای ۱۰ اسلایدی
"""
from typing import Dict, Any, List
import random
from vira_agency.core.chart_engine import render_tradingview_quiz_pair
from vira_agency.core.content_brain import is_topic_repeated_recently, record_published_topic, evaluate_quality_score

class DarkPsychAgent:
    def __init__(self):
        self.page_key = "dark_psychology"
        self.instagram_id = "@zehnayetaarik"
        self.brand_title = "ذهن زیبا"
        self.characters = [
            "Count Dracula with deep crimson velvet cape, sharp intense gaze, cinematic gothic atmosphere",
            "Lone majestic werewolf in dense foggy mystical dark woods, glowing fierce amber eyes",
            "Mysterious elegant aristocrat lady wearing ornate masquerade mask, chiaroscuro lighting",
            "Gothic skeleton knight in battle-worn obsidian armor, dark fantasy cinematic realism",
            "Cunning theatrical fox wearing ornate porcelain Venetian mask, dark fairytale aesthetic"
        ]
        self.trend_pool = [
            "سکوت انتخابی در مذاکره",
            "دستکاری از طریق القای عذاب وجدان",
            "تکنیک بمباران محبت و ناپدید شدن ناگهانی",
            "ایزوله‌سازی آرام در روابط عاطفی",
            "روانشناسی افراد چاپلوس و دورو",
            "نفوذ ناخودآگاه با زبان بدن معکوس",
            "شکستن اعتمادبه‌نفس با تمسخرهای نامحسوس",
            "سرد شدن ناگهانی بعد از صمیمیت شدید"
        ]

    def get_fresh_trend(self) -> str:
        available = [t for t in self.trend_pool if not is_topic_repeated_recently(self.page_key, t)]
        return random.choice(available) if available else random.choice(self.trend_pool)

    def make_story(self, subtype: str) -> Dict[str, Any]:
        char_prompt = random.choice(self.characters)
        stories = [
            ("قانون سکوت", "قدرتمندترین پاسخ به رفتارهای توهین‌آمیز، گرفتن توجه از طرف مقابل است.", char_prompt),
            ("راز کاریزما", "افراد غیرقابل پیش‌بینی همیشه ذهن مخاطب را تسخیر می‌کنند.", char_prompt),
            ("خط قرمز عاطفی", "وقتی محتاج تایید نباشی، دیگران نمی‌توانند تو را بازی دهند.", char_prompt),
            ("نقاب روباه", "مراقب کسانی باش که در اوج بی‌پناهی، نقش نجات‌دهنده را بازی می‌کنند.", char_prompt)
        ]
        title, text, prompt = random.choice(stories)
        return {
            "title": title,
            "badge": "روانشناسی تاریک",
            "text": text,
            "image_prompt": f"{prompt}, dark moody surreal backdrop, high resolution 8k, dramatic shadows, no text",
            "sticker": "این روش رو امتحان کردی؟"
        }

    def make_carousel(self, topic: str, count: int = 5) -> List[Dict[str, Any]]:
        char = random.choice(self.characters)
        master_slides = [
            {"slide_num": 1, "title": "کنترل نامرئی ذهن", "text": f"چگونه در مواجهه با {topic} بدون اینکه متوجه شوی افکارت را هدایت می‌کنند؟", "image_prompt": f"Surreal cinematic art, {char}, crimson and black palette, 8k, no text"},
            {"slide_num": 2, "title": "شروع نامحسوس", "text": "همه‌چیز با دلسوزی بیش از حد شروع می‌شود تا گارد دفاعی تو کاملاً پایین بیاید.", "image_prompt": "Dark gothic chess board with shadowy pieces, dramatic rim light, no text"},
            {"slide_num": 3, "title": "مکانیسم تسلیم", "text": "آرام‌آرام به تصمیم‌های خودت شک می‌کنی و برای هر کاری دنبال تایید طرف مقابل می‌گردی.", "image_prompt": "Cinematic cracked antique mirror reflecting dual personalities, surrealism, no text"},
            {"slide_num": 4, "title": "زنگ خطرهای واضح", "text": "اگر در رابطه‌ای همیشه احساس مقصر بودن داری، درون یک بازی روانی حساب‌شده افتاده‌ای.", "image_prompt": f"{char}, dramatic shadows, dark aesthetic, no text"},
            {"slide_num": 5, "title": "تکنیک خلع سلاح", "text": "توجیه نکن، بحث نکن و فقط فاصله عاطفی بگیر؛ سکوت برنده قطعی این تقابل است.", "image_prompt": "A glowing silver key breaking dark rusty iron chains, minimalist cinematic, no text"},
            {"slide_num": 6, "title": "مرزهای فولادی", "text": "اجازه نده هیچ‌کس با احساس گناه، رفتار غیرمنطقی‌اش را به تو تحمیل کند.", "image_prompt": "Obsidian castle on steep rocky cliff in thunderstorm, no text"},
            {"slide_num": 7, "title": "بازیابی قدرت", "text": "کسی که از از دست دادن دیگران نترسد، هرگز طعمه دستکاری روانی نمی‌شود.", "image_prompt": f"{char}, calm triumphant expression, cinematic lighting, no text"},
            {"slide_num": 8, "title": "قانون نهایی", "text": "آدم‌ها فقط تا جایی می‌توانند تو را برنجانند که خودت به آن‌ها اجازه می‌دهی.", "image_prompt": "Minimalist red eclipsed moon in velvet dark sky, 8k, no text"},
            {"slide_num": 9, "title": "تمرین عملی امروز", "text": "در اولین برخورد سمی پیش‌رو، هیچ واکنشی نشان نده و فقط به چشمانشان نگاه کن.", "image_prompt": "Mystical antique hourglass with crimson sand, cinematic realism, no text"},
            {"slide_num": 10, "title": "تصمیم با توست", "text": "آیا تا به حال گیر چنین آدم‌هایی افتاده‌ای یا زود متوجه بازی شدی؟", "image_prompt": f"Surreal gate opening into infinite foggy void, {char}, no text"}
        ]
        final_slides = master_slides[:count]
        qa = evaluate_quality_score(final_slides)
        record_published_topic(self.page_key, topic, final_slides[0]["text"], qa["score"])
        return final_slides

class TradingAgent:
    def __init__(self):
        self.page_key = "trading_psychology"
        self.instagram_id = "@tradebazehn"
        self.brand_title = "روانشناسی معامله‌گری"
        self.trend_pool = [
            "سندروم خروج زودهنگام از سود",
            "انتقام از بازار بعد از استاپ خوردن",
            "سوگیری تعصب روی تحلیل اشتباه",
            "تله فومو در صعودهای شارپ",
            "افزایش حجم احساسی بعد از چند سود پیاپی",
            "ترس از کلیک کردن روی اردر معتبر"
        ]

    def get_fresh_trend(self) -> str:
        available = [t for t in self.trend_pool if not is_topic_repeated_recently(self.page_key, t)]
        return random.choice(available) if available else random.choice(self.trend_pool)

    def make_story_quiz_pair(self, topic: str) -> Dict[str, Any]:
        img_q, img_ans = render_tradingview_quiz_pair(topic, is_bearish_trap=True)
        return {
            "story_question": {
                "badge": "کوییز تریدری",
                "title": "شکست مقاومت یا تله گاوی؟",
                "text": "کندل پرقدرت سبز بسته شد اما حجم واگرایی منفی دارد. آیا اینجا لانگ می‌گیری؟",
                "raw_image": img_q,
                "sticker": "لانگ یا شورت؟"
            },
            "story_answer": {
                "badge": "پاسخ تحلیل تکنیکال",
                "title": "نتیجه: تله استاپ‌هانت (Bull Trap)",
                "text": "این ستاپ برای جمع‌آوری نقدینگی خریداران بود. بلافاصله ریزش سنگین رخ داد و ورود اشتباه بود.",
                "raw_image": img_ans,
                "sticker": "درست پیش‌بینی کردی؟"
            }
        }

    def make_carousel(self, topic: str, count: int = 5) -> List[Dict[str, Any]]:
        master_slides = [
            {"slide_num": 1, "title": "خطای محاسباتی مغز", "text": f"چرا در مواجهه با {topic} رفتاری انجام می‌دهی که در ژورنالت ممنوع است؟", "image_prompt": "Cinematic exhausted trader sitting in dark modern office in front of glowing charts, neon blue and crimson red, no text"},
            {"slide_num": 2, "title": "ترس از پشیمانی", "text": "سود کم را زود می‌بندی چون می‌ترسی از دست برود، اما ضرر بزرگ را با امید بازگشت باز نگه می‌داری.", "image_prompt": "Surreal human brain intertwined with neon candlestick charts, dark background, no text"},
            {"slide_num": 3, "title": "درد باختن سرمایه", "text": "روانشناسی ثابت کرده درد از دست دادن پول دو برابر لذت به دست آوردن همان مقدار است.", "image_prompt": "Cinematic dark hourglass with digital gold dust fading into dark void, no text"},
            {"slide_num": 4, "title": "انضباط معاملاتی", "text": "معامله‌گر حرفه‌ای پیش از فشردن دکمه خرید، هزینه شکست احتمالی را پذیرفته است.", "image_prompt": "Futuristic modern trading setup with locked green padlock, dark aesthetic, no text"},
            {"slide_num": 5, "title": "پروتکل نجات تریدر", "text": "تنها راه مهار هیجان، خاموش کردن سیستم پس از ثبت دومین ضرر متوالی در روز است.", "image_prompt": "Minimalist calm zen stone balanced on edge of dark crystal glass, no text"},
            {"slide_num": 6, "title": "توهم کنترل بازار", "text": "بازار برای شخص تو برنامه نریخته؛ این تعصب توست که اجازه نمی‌دهد خطا را بپذیری.", "image_prompt": "Huge stormy ocean wave crashing against a tiny solid rock lighthouse, no text"},
            {"slide_num": 7, "title": "قانون حجم مناسب", "text": "وقتی استرس باز بودن یک پوزیشن را داری، یعنی حجم معامله‌ات بسیار فراتر از ظرفیت روانی‌ات است.", "image_prompt": "Precise golden mechanical scale weighing a tiny glowing crystal against heavy iron weights, no text"},
            {"slide_num": 8, "title": "تغییر هویت معامله‌گر", "text": "به جای تمرکز روی سود دلاری، تمرکزت را روی اجرای ۱۰۰ درصدی پلن معاملاتی بگذار.", "image_prompt": "Silhouette of a focused person standing firmly in front of clean glowing geometric chart lines, no text"},
            {"slide_num": 9, "title": "چک‌لیست قبل از ترید", "text": "آیا اگر این پوزیشن استاپ بخورد، آرامش ذهنی ادامه روزت را خراب نمی‌کند؟", "image_prompt": "Futuristic clean transparent tablet showing checklist, cinematic dark room, no text"},
            {"slide_num": 10, "title": "سوال صادقانه", "text": "بزرگ‌ترین ضرر ماه گذشته‌ات به خاطر تحلیل غلط بود یا عدم کنترل طمع؟", "image_prompt": "A lone chess king standing tall on mirror floor, reflections in shadows, no text"}
        ]
        final_slides = master_slides[:count]
        qa = evaluate_quality_score(final_slides)
        record_published_topic(self.page_key, topic, final_slides[0]["text"], qa["score"])
        return final_slides

class ArtAgent:
    def __init__(self):
        self.page_key = "art_gallery"
        self.instagram_id = "@elartgallery.ir"
        self.brand_title = "گالری هنری الهه"
        self.trend_pool = [
            "آینه‌های ارگانیک بافت‌دار وابی‌سابی",
            "ظروف دکوراتیو مینیمال با تکنیک پاپیه‌ماشه",
            "ساعت‌های دیواری دست‌ساز با پتینه شنی",
            "مجسمه‌های فرمال انتزاعی برای ورودی منزل",
            "کاسه‌های دکوراتیو سبک جاپاندی با رنگ‌های خاکی",
            "گلدان‌های مدرن با فرم‌های مواج دست‌ساز"
        ]

    def get_fresh_trend(self) -> str:
        available = [t for t in self.trend_pool if not is_topic_repeated_recently(self.page_key, t)]
        return random.choice(available) if available else random.choice(self.trend_pool)

    def make_story(self, subtype: str) -> Dict[str, Any]:
        trend = self.get_fresh_trend()
        return {
            "title": trend,
            "badge": "کالکشن دست‌ساز",
            "text": f"طراحی ارگانیک {trend}؛ هماهنگی اصالت بافت‌های دست‌ساز با چیدمان مینیمال مدرن.",
            "image_prompt": f"Luxury modern home interior with {trend}, earthy beige and cream tones, natural sunlight, cinematic photography, architectural digest, no text",
            "sticker": "این چیدمان رو می‌پسندی؟"
        }

    def make_carousel(self, topic: str, count: int = 5) -> List[Dict[str, Any]]:
        master_slides = [
            {"slide_num": 1, "title": "هارمونی بافت و فضا", "text": f"چگونه حضور {topic} روح و گرما را به چیدمان مینیمال خانه شما بازمی‌گرداند؟", "image_prompt": f"Minimalist warm Japandi living room featuring {topic}, soft daylight, interior design masterpiece, no text"},
            {"slide_num": 2, "title": "فلسفه نقص‌های کامل", "text": "در هنر وابی‌سابی، خطوط نامتقارن و ناهمواری‌های ارگانیک نشانه اصالت دست‌ساز بودن هستند.", "image_prompt": "Close-up macro texture of handcrafted organic plaster sculpture, warm beige tones, soft shadows, no text"},
            {"slide_num": 3, "title": "استحکام در عین سبکی", "text": "به لطف الیاف فشرده سلولزی، این سازه‌ها وزن بسیار سبکی داشته و مقاومت بالایی دارند.", "image_prompt": "Elegant hands holding a beautifully finished lightweight organic paper mache bowl, no text"},
            {"slide_num": 4, "title": "پالت رنگ‌های آرامش‌بخش", "text": "ترکیب رنگ‌های کرم، خاکی و استخوانی باعث می‌شود این المان در هر فضایی بدرخشد.", "image_prompt": "Cozy reading corner with warm textured decorative wall art and wooden console, architectural digest, no text"},
            {"slide_num": 5, "title": "خلق اثری تکرارناپذیر", "text": "هر قطعه به صورت اختصاصی ساخته می‌شود و هیچ دو اثری کاملاً یکسان نخواهند بود.", "image_prompt": "Artisan studio with sculptural organic handcrafted mirrors drying in natural sunlight, no text"},
            {"slide_num": 6, "title": "ترکیب مدرنیته و سنت", "text": "روشی نوآورانه برای آوردن انرژی آرامش‌بخش طبیعت به آپارتمان‌های امروزی.", "image_prompt": "Spacious entryway with custom curved organic mirror and warm accent spot light, no text"},
            {"slide_num": 7, "title": "ارزش هنری ماندگار", "text": "وسایل دکوری کارخانه‌ای بی‌روح هستند؛ هنر دست برای نسل‌ها ارزش خود را حفظ می‌کند.", "image_prompt": "Contemporary dining room with handcrafted textured centerpiece bowl on oak table, no text"},
            {"slide_num": 8, "title": "نحوه نگهداری آسان", "text": "پوشش‌های محافظ ضد رطوبت مات، تمیزکاری این آثار را بسیار ساده و بی‌دردسر کرده است.", "image_prompt": "Minimalist clean bathroom wall with organic textured waterproof decorative frame, no text"},
            {"slide_num": 9, "title": "سفارش بر اساس ابعاد فضا", "text": "رنگ‌آمیزی و ابعاد هر کاروسل متناسب با سلیقه و نورپردازی منزل شما قابل تنظیم است.", "image_prompt": "Architectural color palette swatches next to handcrafted plaster mirror frame, no text"},
            {"slide_num": 10, "title": "مشاوره چیدمان اختصاصی", "text": "تصویر دیوار یا فضای مدنظرتان را در دایرکت بفرستید تا بهترین ابعاد را پیشنهاد دهیم.", "image_prompt": "Beautifully lit modern hallway showcasing custom organic wall art, warm interior lighting, no text"}
        ]
        final_slides = master_slides[:count]
        qa = evaluate_quality_score(final_slides)
        record_published_topic(self.page_key, topic, final_slides[0]["text"], qa["score"])
        return final_slides
