"""
ایجنت‌های ۳ دپارتمان تخصصی آژانس هوشمند دستیار ویرا
نسخه کامل، بدون خلاصه‌سازی و دارای سناریوهای جامع:
۱. دپارتمان ترید: کوییز چارت تریدینگ‌ویو (جفت استوری ۱ و ۲)، اخبار زنده، تحلیل بیت‌کوین و روانشناسی طمع
۲. دپارتمان روانشناسی تاریک (ذهن زیبا): با حضور کامل کاراکترهای دراکولا، گرگ تنها، روباه مکار، شوالیه، اسکلت و بانوی مرموز
۳. دپارتمان گالری هنری الهه: آینه‌های وابی‌سابی، ظروف دکوراتیو و مجسمه‌های مدرن

پشتیبانی کامل از:
- متدهای make_story (شامل استوری‌های تکی و استوری جفتی کوییز)
- متدهای make_carousel با سناریوهای روایی چند اسلایدی در ابعاد ۱۰۸۰×۱۳۵۰
- متدهای make_reel با سناریوهای ۵ سکانسی
- فیلتر قطعی ضد نشت انگلیسی (Zero English Leak)
"""
import random
import re
import logging
from typing import Dict, Any, List
from vira_agency.core.chart_engine import render_tradingview_quiz_pair
from vira_agency.core.market_news import get_live_market_summary

log = logging.getLogger(__name__)


def clean_pure_persian(text: str) -> str:
    """پالایش تضمینی متن فارسی و ردگیری هر نوع نشت انگلیسی یا دستور مدل"""
    if not text:
        return ""
    low = text.lower()
    leaks = [
        "persona", "task", "role", "generator", "output", "json", "markdown",
        "create", "content persian", "senior text", "expert content", "strict rules"
    ]
    if any(lk in low for lk in leaks):
        return ""
    cleaned = re.sub(r"[a-zA-Z]", "", text)
    cleaned = re.sub(r"[{}\[\]\"']", "", cleaned)
    return cleaned.strip()


class TradingAgent:
    """دپارتمان تخصصی روانشناسی معامله‌گری (@tradebazehn)"""

    TRENDING_TOPICS = [
        "چرا معامله سودده را زود می‌بندی اما ضرر را باز می‌گذاری؟",
        "تله استاپ‌هانت و شکار نقدینگی در سقف و کف روزانه",
        "قانون ۳ دقیقه توقف قبل از ورود به پوزیشن فیوچرز",
        "انتقام از بازار: چطور یک ضرر کوچک کل اکانت را نابود می‌کند؟",
        "تشخیص واگرایی منفی و بریک‌اوت جعلی در مقاومت کلیدی",
        "چگونه بعد از یک روز منفی، احساسات خود را مدیریت کنیم؟",
    ]

    QUIZ_SCENARIOS = [
        {
            "q_heading": "کوییز ستاپ: شکست یا تله؟",
            "q_body": "قیمت با یک **کندل پرقدرت سبز** مقاومت را شکسته است؛ اما اندیکاتور حجم کاهش نشان می‌دهد. با توجه به چارت بالا، آیا در این نقطه وارد معامله می‌شوی؟",
            "q_sticker": "لانگ می‌گیری یا شورت؟",
            "a_heading": "✅ پاسخ تحلیل: تله گاوی (Bull Trap)",
            "a_body": "اینجا **نباید وارد معامله لانگ شد!** شکست مقاومت بدون تاییدیه حجم، یک تله برای شکار نقدینگی بود. قیمت پس از فیک‌بریک با شدت ریخت. پوزیشن درست شورت در پولبک بود.",
            "a_sticker": "حدست درست بود یا نه؟",
        },
        {
            "q_heading": "کوییز ستاپ: شکار در کف کانال",
            "q_body": "بیت‌کوین به **حمایت معتبر روزانه** رسیده و شدوی بلندی به سمت پایین تشکیل داده است. آیا این نقطه را موقعیت ورود مطمئن می‌دانی؟",
            "q_sticker": "ورود الان یا صبر برای پولبک؟",
            "a_heading": "✅ پاسخ تحلیل: صبر برای تاییدیه کندلی",
            "a_body": "شدو نشان‌دهنده واکنش خریداران است؛ اما تا زمانی که **کندل بعدی تثبیت نشود** نباید عجله کرد. ورود مطمئن پس از پولبک و با حد ضرر مشخص زیر شدو است.",
            "a_sticker": "معامله‌گر صبوری هستی؟",
        }
    ]

    def __init__(self, llm):
        self.llm = llm
        self.page_key = "trading"
        self.instagram_id = "@tradebazehn"
        self.brand_title = "روانشناسی معامله‌گری"

    def get_random_trend(self) -> str:
        return random.choice(self.TRENDING_TOPICS)

    async def make_story(self, cat_key: str) -> Dict[str, Any]:
        """تولید استوری متناسب با دسته‌بندی انتخاب‌شده"""
        # ۱. کوییز چارت‌محور تریدینگ‌ویو با پیوستگی ۱۰۰٪ استوری ۱ و ۲
        if cat_key == "t_quiz":
            scen = random.choice(self.QUIZ_SCENARIOS)
            img_q, img_ans = render_tradingview_quiz_pair(scen["q_heading"], is_bearish_trap=True)
            return {
                "is_quiz_pair": True,
                "question": {
                    "heading": scen["q_heading"],
                    "body": scen["q_body"],
                    "sticker": scen["q_sticker"],
                    "visual": "TradingView crypto candlestick chart clean, no text",
                    "raw_image": img_q,
                    "quiz_type": "question"
                },
                "answer": {
                    "heading": scen["a_heading"],
                    "body": scen["a_body"],
                    "sticker": scen["a_sticker"],
                    "visual": "TradingView crypto candlestick chart technical breakdown, no text",
                    "raw_image": img_ans,
                    "quiz_type": "answer"
                }
            }

        # ۲. تحلیل زنده بیت‌کوین و بازار
        if cat_key == "t_market":
            m = await get_live_market_summary()
            return {
                "heading": f"تحلیل بیت‌کوین در {m.get('price')}$",
                "body": f"بیت‌کوین در ۲۴ ساعت اخیر با نوسان **{m.get('change')}** در ناحیه **{m.get('trend')}** قرار دارد. کف **${m.get('support')}** حمایت محکم روزانه و سقف **${m.get('resistance')}** مقاومت کلیدی است. بدون تاییدیه وارد نشوید.",
                "sticker": "خرید در کف یا شکست سقف؟",
                "visual": "Professional trader in a dark cybernetic room glowing with deep royal purple and neon emerald candlestick charts on multiple screens, cinematic 8k, no text, no speech bubbles"
            }

        # ۳. اخبار داغ و رویدادهای زنده
        if cat_key == "t_news":
            m = await get_live_market_summary()
            return {
                "heading": "رویدادهای داغ بازار کریپتو",
                "body": m.get("news"),
                "sticker": "پامپ میشه یا اصلاح بیشتر؟",
                "visual": "Futuristic financial trading news desk with multiple purple and emerald holographic market data streams, 8k cinematic, no text, no speech bubbles"
            }

        # سایر موارد ترید (روانشناسی، استاپ‌هانت، نبرد گاو و خرس)
        fallbacks = {
            "t_psyc": {
                "heading": "تله انتقام از مارکت",
                "body": "بزرگ‌ترین ضررها بعد از استاپ خوردن اول و باز کردن عجولانه پوزیشن رخ می‌دهد. وقتی تحلیلت رد شد چارت را ببند؛ **مارکت همیشه فرصت می‌دهد**.",
                "sticker": "دچار اورترید شدی تا حالا؟",
                "visual": "A disciplined trader sitting calmly in front of neon purple charts with a glowing golden mind of clarity and focus, cinematic art, no text"
            },
            "t_hunt": {
                "heading": "تله نقدینگی و استاپ‌هانت",
                "body": "حرکات شارپ قبل از بازگشایی نیویورک معمولاً برای **شکار حد ضرر تریدرهای خرد** است. ورود در موج اول اغلب بازی در زمین بازیگران اصلی است.",
                "sticker": "طعمه استاپ‌هانت شدی؟",
                "visual": "Glowing cybernetic liquidity trap catching retail positions on a futuristic royal purple holographic trading chart, no text, no speech bubbles"
            },
            "t_bull": {
                "heading": "نبرد در سنگر خریداران",
                "body": "گاوها در تلاش برای تثبیت قیمت بالای میانگین متحرک روزانه هستند. خرس‌ها به دنبال **شکست ساختار به پایین** هستند؛ بدون تاییدیه ریسک نکنید.",
                "sticker": "برنده نبرد: گاو یا خرس؟",
                "visual": "Epic clash of a glowing royal purple metallic Bull and an emerald green Bear amidst stormy trading charts, 8k masterpiece, no text"
            }
        }
        res = fallbacks.get(cat_key, fallbacks["t_psyc"])

        # پرامپت فارسی بدون نشت
        prompt = (
            f"برای پیج روانشناسی معامله‌گری یک استوری تخصصی در سبک «{cat_key}» بنویس.\n"
            "فقط به فارسی بنویس و عبارات مهم را بین **کلمه** بگذار.\n"
            'فرمت خروجی صرفاً JSON:\n{"heading": "تیتر فارسی ۳ تا ۵ کلمه", "body": "متن تخصصی و آموزنده فارسی در ۲ جمله", "sticker": "سوال تعاملی کوتاه"}'
        )
        try:
            data = await self.llm.json(prompt, temperature=0.7)
            h = clean_pure_persian(str(data.get("heading") or ""))
            b = clean_pure_persian(str(data.get("body") or ""))
            s = clean_pure_persian(str(data.get("sticker") or ""))
            if h and b and len(b) > 25:
                return {"heading": h, "body": b, "sticker": s or res["sticker"], "visual": res["visual"]}
        except Exception:
            pass
        return res

    async def make_carousel(self, topic: str, count: int = 4) -> Dict[str, Any]:
        """کاروسل ادیتوریال و روایی روانشناسی ترید بر اساس ساختار طلایی"""
        full_slides = [
            {
                "heading": "قلاب: خطای نامرئی ذهن",
                "body": f"شاید مشکل اصلی تو استراتژی معاملاتی‌ات نیست؛ مغزت در موضوع **«{topic}»** علیه سرمایه‌ات معامله می‌کند.",
                "visual": "Cinematic exhausted trader sitting in dark modern office in front of glowing charts, deep royal purple and red neon, moody chiaroscuro lighting, no text"
            },
            {
                "heading": "ایجاد مسئله: تکرار اشتباه",
                "body": "تصمیم می‌گیری بعد از دو ضرر متوقف شوی، اما ناگهان معامله سوم را با **حجم دو برابر و بدون تحلیل** باز می‌کنی.",
                "visual": "Minimalist conceptual art, human brain intertwined with volatile glowing stock charts, dark purple void background, dramatic lighting, no text"
            },
            {
                "heading": "تعلیق: ریشه خشم",
                "body": "این رفتار از طمع نیست! ذهن تو تلاش می‌کند با **انتقام از چارت**، درد تحقیر شدن توسط بازار را التیام دهد.",
                "visual": "Conceptual dark chess board with broken king piece glowing in deep violet neon, cinematic realism, no text"
            },
            {
                "heading": "مکانیزم: زیان‌گریزی",
                "body": "درد باختن ۲ برابر لذت سود است. مغزت برای فرار از پذیرش باخت، **معامله ضررده را تا لبه کال‌مارجین** باز نگه می‌دارد.",
                "visual": "Conceptual hourglass with gold coins slipping into dark void, illuminated by royal purple rim light, cinematic 8k, no text"
            },
            {
                "heading": "نشانه‌های خطر",
                "body": "چک کردن مداوم PnL در ثانیه، تغییر حد ضرر و جابجا کردن خطوط چارت، **هشدار تسلط هیجان** بر منطق است.",
                "visual": "Macro close-up of a trader hand trembling over a glowing neon buy button, moody dark ambience, no text"
            },
            {
                "heading": "راهکار طلایی: قانون ۳ دقیقه",
                "body": "قبل از هر کلیک، ۳ دقیقه از سیستم فاصله بگیر، حد ضرر را در سیستم ثبت کن و **دست از مانیتور بردار**.",
                "visual": "High-tech futuristic trading terminal with locked emerald green padlock, professional cybernetic aesthetic, clean composition, no text"
            },
            {
                "heading": "تثبیت انضباط",
                "body": "حرفه‌ای‌ها به نتیجه یک ترید نگاه نمی‌کنند؛ آن‌ها به **برآیند ۲۰ معامله بعدی** بر اساس قوانین متعهد می‌مانند.",
                "visual": "Calm disciplined investor meditating in front of tranquil neon charts, atmospheric balance, no text"
            },
            {
                "heading": "پایان و نتیجه‌گیری",
                "body": "آخرین باری که با حجم بالا وارد شدی، داشتی تحلیل می‌کردی یا **می‌خواستی باخت قبلی را پس بگیری؟** نظرت را بنویس.",
                "visual": "Futuristic financial vault opening with steady glowing light, royal purple aesthetic, no text"
            },
            {
                "heading": "چک‌لیست قبل ورود",
                "body": "۱. تاییدیه ستاپ ۲. نسبت ریسک به ریوارد بالای ۲ ۳. حجم متناسب با سرمایه. **اگر یکی نبود، معامله لغو است.**",
                "visual": "Glowing cyan digital holographic clipboard floating in dark trading hub, clean minimalism, no text"
            },
            {
                "heading": "ذخیره برای مرور",
                "body": "این پست را سیو کن تا هر بار قبل از باز کردن پوزیشن‌های پرریسک، **اصول انضباط فردی** را به خودت یادآوری کنی.",
                "visual": "Glowing neon emerald bookmark icon hovering inside dark cybernetic matrix, 8k cinematic, no text"
            }
        ]
        chosen_slides = full_slides[:max(1, min(count, len(full_slides)))]
        return {
            "slides": chosen_slides,
            "caption": f"📈 کاروسل تخصصی روانشناسی معامله‌گری ({len(chosen_slides)} اسلاید): {topic}\n\nآیدی اختصاصی: @tradebazehn\n#روانشناسی_معامله_گری #ترید #مدیریت_ریسک #بیت_کوین"
        }

    async def make_reel(self, topic: str) -> Dict[str, Any]:
        scenes = [
            {"text": f"چرا ۹۰٪ معامله‌گران در «{topic}» سرمایه از دست می‌دهند؟", "visual": "Shocked trader in dark royal purple room glowing with red downward charts, cinematic, no text"},
            {"text": "علت اول: ورود شتاب‌زده در سقف به دلیل ترس جا ماندن از بازار.", "visual": "Close-up of glowing crypto candlestick chart with sharp fakeout wick, royal purple neon, no text"},
            {"text": "علت دوم: جابجا کردن حد ضرر به امید بیهوده برگشت قیمت.", "visual": "Cybernetic scale showing balance tipped toward loss with intense purple laser, no text"},
            {"text": "قانون نجات‌بخش: حد ضررت را بگذار و هرگز به آن دست نزن.", "visual": "Disciplined professional trader calmly looking at organized green trade setup, no text"},
            {"text": "برای تسلط بر روانشناسی بازار، پیج @tradebazehn را ذخیره کن!", "visual": "Futuristic crypto vault opening with glowing rewards, clean purple and emerald aesthetic, no text"},
        ]
        return {"scenes": scenes, "caption": f"🎬 ۵ اصل مهم روانشناسی معامله‌گری درباره «{topic}»\nپیج رسمی: @tradebazehn"}


class DarkPsychAgent:
    """دپارتمان ذهن زیبا (@zehnayetaarik) با محوریت کاراکترهای گوتیک"""

    TRENDING_TOPICS = [
        "تکنیک ایزوله‌سازی روانی؛ چطور بدون اینکه بفهمی تو را از جمع جدا می‌کنند؟",
        "سکوت دراکولا در برابر تخریب کلامی و توهین دیگران",
        "چگونه دست افراد چاپلوس و روباه‌های مکار را در چند ثانیه بخوانیم؟",
        "استقلال عاطفی گرگ تنها در برابر باج‌گیری و کنترل‌گری احساسی",
        "دوراهی شوالیه تاریک: بخشش بزرگوارانه یا حذف سرد و بی‌سر‌و‌صدا؟",
        "راز کاریزمای دست‌نیافتنی؛ چرا افراد پیش‌بینی‌ناپذیر جذاب‌ترند؟",
    ]

    CHARACTERS = {
        "dracula": "Aristocratic Count Dracula in a deep charcoal coat with crimson velvet lining, sharp piercing gaze, dark gothic atmospheric hall, chiaroscuro lighting, no text",
        "wolf": "A majestic lone grey wolf standing solitary on a misty cliff under a dark crimson moon and starry night, cinematic dark oil painting, no text",
        "knight": "A solitary dark knight in battle-worn obsidian plate armor standing before an ancient gloomy gothic castle, cinematic realism, no text",
        "fox": "An anthropomorphic cunning fox wearing an ornate silver baroque masquerade mask in a shadowy misty forest with crimson embers, dark oil painting, no text",
        "lady": "An enigmatic aristocratic woman in an elegant velvet masquerade mask, intense mysterious gaze, dark candlelit baroque hall, no text",
        "skeleton": "A gothic skeleton king seated on a weathered stone throne with faint crimson glow in shadows, dark surrealism, no text",
    }

    def __init__(self, llm):
        self.llm = llm
        self.page_key = "dark_psych"
        self.instagram_id = "@zehnayetaarik"
        self.brand_title = "ذهن زیبا"

    def get_random_trend(self) -> str:
        return random.choice(self.TRENDING_TOPICS)

    async def make_story(self, cat_key: str) -> Dict[str, Any]:
        stories = {
            "d_chal": {
                "heading": "دوراهی شوالیه در برابر خیانت",
                "body": "وقتی کسی اعتمادت را خدشه‌دار می‌کند، خشمگین شدن نشانه ضعف است. **سکوت سرد و حذف بی‌صدا** ضربه‌ای ویران‌کننده‌تر از هر انتقامی وارد می‌کند.",
                "sticker": "پاسخ متقابل یا حذف دائمی؟",
                "visual": self.CHARACTERS["knight"]
            },
            "d_edu": {
                "heading": "نقاب لبخند روباه مکار",
                "body": "کسانی که در اولین برخورد بیش از حد تعریفت را می‌کنند، نقشه‌ای در سر دارند. به **رفتار در بحران** اعتماد کن، نه شیرینی کلمات در آرامش.",
                "sticker": "با آدم‌های چاپلوس چه می‌کنی؟",
                "visual": self.CHARACTERS["fox"]
            },
            "d_mar": {
                "heading": "قلمرو دست‌نیافتنی گرگ تنها",
                "body": "وابستگی شدید احساسی ریشه باج‌گیری عاطفی است. کسی که با **تنهایی و خلوت خویش** در صلح باشد، هیچ‌گاه کنترل بازی را به دیگران واگذار نخواهد کرد.",
                "sticker": "مرزهای شخصی‌ات محکمه؟",
                "visual": self.CHARACTERS["wolf"]
            },
            "d_opt": {
                "heading": "راز کاریزمای دست‌نیافتنی",
                "body": "انسان‌ها شیفته افراد پیش‌بینی‌ناپذیرند. هرگز تمام احساساتت را فاش نکن؛ **کمی ابهام و سکوت** بیشترین کشش روانی را خلق می‌کند.",
                "sticker": "دست‌نیافتنی هستی یا زود وا میدی؟",
                "visual": self.CHARACTERS["lady"]
            },
            "d_sec": {
                "heading": "مکث طلایی دراکولا در مکالمه",
                "body": "برای نفوذ کلامی بی‌چون‌وچرا، پس از بیان نکته کلیدی **سه ثانیه مکث کن** و مستقیم به چشمان طرف مقابل نگاه کن. سکوت قدرت‌آفرین است.",
                "sticker": "این تکنیک رو تست کردی؟",
                "visual": self.CHARACTERS["dracula"]
            }
        }
        res = stories.get(cat_key, stories["d_chal"])

        prompt = (
            f"برای پیج روانشناسی تاریک ذهن زیبا یک استوری در سبک «{cat_key}» بنویس.\n"
            "فقط به فارسی روان بنویس. کلمات مهم بین دو ستاره **کلمه** باشند.\n"
            'فرمت خروجی صرفاً JSON:\n{"heading": "تیتر جذاب ۳ تا ۵ کلمه", "body": "متن عمیق و روانشناختی در ۲ جمله", "sticker": "سوال کوتاه تعاملی"}'
        )
        try:
            data = await self.llm.json(prompt, temperature=0.7)
            h = clean_pure_persian(str(data.get("heading") or ""))
            b = clean_pure_persian(str(data.get("body") or ""))
            s = clean_pure_persian(str(data.get("sticker") or ""))
            if h and b and len(b) > 25:
                return {"heading": h, "body": b, "sticker": s or res["sticker"], "visual": res["visual"]}
        except Exception:
            pass
        return res

    async def make_carousel(self, topic: str, count: int = 4) -> Dict[str, Any]:
        """کاروسل ادیتوریال و سینمایی با ابعاد ۱۰۸۰×۱۳۵۰ و کاراکترهای گوتیک"""
        full_slides = [
            {
                "heading": "قوانین ذهن زیبا: قلاب قدرت",
                "body": f"در جهان روابط انسانی و موضوع **«{topic}»**، آنکه کمتر حرف می‌زند و بیشتر مشاهده می‌کند بازی را کنترل می‌کند.",
                "visual": self.CHARACTERS["knight"]
            },
            {
                "heading": "نقاب روباه: مکر در قالب محبت",
                "body": "افراد دست‌کار همواره با هدیه‌ها یا تعریف‌های اغراق‌آمیز آغاز می‌کنند تا در ناخودآگاه تو **حس دین‌داری و شرمندگی** بکارند.",
                "visual": self.CHARACTERS["fox"]
            },
            {
                "heading": "تعلیق: خطای نادیده گرفتن",
                "body": "خطرناک‌ترین لحظه زمانی است که تصور می‌کنی همه چیز تحت کنترل توست، اما **قواعد بازی را از پیش برایت چیده‌اند.**",
                "visual": "Gothic antique mirror cracked down the center reflecting shadowy figures, crimson rim lighting, no text"
            },
            {
                "heading": "مرزهای گرگ: استقلال بی‌قید و شرط",
                "body": "گرگ تنها گرسنگی را تحمل می‌کند اما قلاده را نمی‌پذیرد. وقتی **نیازمند تایید دیگران نباشی**، قوی‌ترین باج‌گیران روانی خلع سلاح می‌شوند.",
                "visual": self.CHARACTERS["wolf"]
            },
            {
                "heading": "افشای تکنیک ایزوله‌سازی",
                "body": "افراد سمی آرام‌آرام دایره امن تو را از دوستان و خانواده دور می‌کنند تا **تنها پناهگاه تصمیم‌گیری‌ات خودشان باشند.**",
                "visual": "A solitary dark figure standing surrounded by fading misty silhouettes in deep gothic woods, no text"
            },
            {
                "heading": "سلاح پادزهر: سکوت سرد",
                "body": "در برابر اتهام و تحریک‌های کلامی نجنگ. **سکوت آرام و تایید نکردن**، نقاب طرف مقابل را در چند ثانیه پایین می‌کشد.",
                "visual": self.CHARACTERS["dracula"]
            },
            {
                "heading": "حفظ قلمرو شخصی",
                "body": "هر زمان احساس کردی برای جلب رضایت دیگری باید خودت را کوچک کنی، **همان لحظه عقب بنشین و مرزت را پررنگ کن.**",
                "visual": self.CHARACTERS["lady"]
            },
            {
                "heading": "پایان: خروج بی‌صدا",
                "body": "قدرت واقعی در بحث کردن نیست؛ در **بی‌تفاوتی مطلق و ترک بازی** است. اجازه نده ذهن زیبایت دستمایه بازی‌های دیگران شود.",
                "visual": self.CHARACTERS["skeleton"]
            },
            {
                "heading": "اصل نفوذ ناپذیری",
                "body": "کسی که از تنهایی نمی‌ترسد، هیچ‌گاه با تهدید به رفتن یا قهر تسلیم خواسته‌های غیرمنطقی دیگران نخواهد شد.",
                "visual": self.CHARACTERS["knight"]
            },
            {
                "heading": "ذخیره قوانین قدرت",
                "body": "این کاروسل را ذخیره کن تا هر زمان مرزهایت مورد هجوم قرار گرفت، **قوانین محافظت از خود** را مرور کنی.",
                "visual": "Ancient gothic book bound in black leather with silver glowing seal, dramatic crimson shadows, no text"
            }
        ]
        chosen_slides = full_slides[:max(1, min(count, len(full_slides)))]
        return {
            "slides": chosen_slides,
            "caption": f"🖤 رازهای عمیق کنترل ذهن و کاریزما در «{topic}» ({len(chosen_slides)} اسلاید).\n\nپیج رسمی: @zehnayetaarik\n#ذهن_زیبا #روانشناسی_تاریک #کاریزما #نفوذ_روانی"
        }

    async def make_reel(self, topic: str) -> Dict[str, Any]:
        scenes = [
            {"text": f"۳ قانون طلایی در «{topic}» که قدرت درونت را بیدار می‌کند.", "visual": self.CHARACTERS["knight"]},
            {"text": "قانون اول: به لبخندهای سریع و چاپلوسی‌های اغراق‌آمیز اعتماد نکن.", "visual": self.CHARACTERS["fox"]},
            {"text": "قانون دوم: مرزهایت را حفظ کن؛ گرگ تنها باج عاطفی نمی‌دهد.", "visual": self.CHARACTERS["wolf"]},
            {"text": "قانون سوم: سکوت شمرده و نگاه نافذ، برنده تمام بازی‌های روانی است.", "visual": self.CHARACTERS["dracula"]},
            {"text": "برای کشف قوانین نامرئی قدرت، پیج @zehnayetaarik را دنبال کن.", "visual": self.CHARACTERS["lady"]},
        ]
        return {"scenes": scenes, "caption": f"🎬 رمزگشایی از بازی‌های روانی در «{topic}».\nپیج رسمی: @zehnayetaarik"}


class ArtAgent:
    """دپارتمان گالری هنری الهه (@elartgallery.ir)"""

    TRENDING_TOPICS = [
        "آینه موج‌دار وابی‌سابی؛ امضای مینیمال دکوراسیون مدرن",
        "کاسه‌ها و ظروف دکوراتیو بافت‌دار برای میز کنسول و پذیرایی",
        "مجسمه‌های فرم آزاد مینیمال؛ خلق حس آرامش در سکوت فضا",
        "فرمول طلایی چسب چوب و تکنیک جلوگیری از ترک در پاپیه‌ماشه",
        "چرا اکسسوری‌های دست‌ساز ارزش دکوراسیون خانه را دوچندان می‌کنند؟",
    ]

    def __init__(self, llm):
        self.llm = llm
        self.page_key = "papermache"
        self.instagram_id = "@elartgallery.ir"
        self.brand_title = "گالری هنری الهه (ELART GALLERY)"

    def get_random_trend(self) -> str:
        return random.choice(self.TRENDING_TOPICS)

    async def make_story(self, cat_key: str) -> Dict[str, Any]:
        fallbacks = {
            "art_mirror": {
                "heading": "آینه موج‌دار وابی‌سابی؛ امضای مدرن",
                "body": "چرا آینه‌های فرم آزاد ترند شدند؟ چون انحنای ارگانیک و **بافت مات خمیر دست‌ساز**، خشکی خطوط دیوار را به لطافت و گرما تبدیل می‌کند.",
                "sticker": "ابعاد دلخواهت رو دایرکت بفرست",
                "visual": "A trendy organic wavy curved mirror frame made of textured cream paper mache hanging on a modern minimalist wall, soft natural morning sunlight, luxury home decor photography, no text"
            },
            "art_decor": {
                "heading": "ظروف دکوراتیو بافت‌دار روی کنسول",
                "body": "اکسسوری‌های دست‌ساز پاپیه‌ماشه ترکیبی از **سبکی باورنکردنی با استحکام بالا** هستند. این ظروف به میز جلو مبلی یا کنسول هویت می‌بخشند.",
                "sticker": "رنگ سفارشی خودت رو انتخاب کن",
                "visual": "A collection of handmade organic paper mache bowls and decorative plates in warm cream and terracotta tones on an oak console, no text"
            },
            "art_sculpture": {
                "heading": "مجسمه‌های مینیمال فرم آزاد",
                "body": "این مجسمه‌ها نگاه را جذب می‌کنند بدون آنکه فضا را شلوغ کنند. هر فرم با دست و **بدون هیچ قالب صنعتی** شکل گرفته است.",
                "sticker": "هنر دست‌ساز یا مجسمه قالبی؟",
                "visual": "A stunning abstract minimalist paper mache sculpture in warm neutral cream tones placed on an art shelf, soft natural lighting, no text"
            },
            "behind": {
                "heading": "پشت صحنه گالری الهه",
                "body": "راز ماندگاری این آثار در ترکیب دقیق **الیاف سلولزی با چسب چوب باکیفیت** است. خشک شدن لایه‌به‌لایه‌ مانع ایجاد هرگونه ترک می‌شود.",
                "sticker": "دوست داری مراحل ساختش رو ببینی؟",
                "visual": "Artisan hands packaging a textured paper mache decor piece with linen paper and dried flowers in a warm art studio, cozy aesthetic, no text"
            }
        }
        return fallbacks.get(cat_key, fallbacks["art_mirror"])

    async def make_carousel(self, topic: str, count: int = 4) -> Dict[str, Any]:
        full_slides = [
            {
                "heading": f"کالکشن گالری الهه: {topic}",
                "body": "ترکیب بافت‌های دست‌ساز و ارگانیک با چیدمان خانه مدرن، **حس گرما و اصالت ماندگار** به فضا می‌بخشد.",
                "visual": "Minimalist luxury living room with handmade paper mache decor in warm neutral tones, natural light, no text"
            },
            {
                "heading": "هنر نقص‌های کامل (وابی‌سابی)",
                "body": "زیبایی مجسمه‌های پاپیه‌ماشه در ناصافی‌های ظریف و دست‌ساز آن است که **هیچ نمونه دومی در جهان ندارد**.",
                "visual": "Close-up of a textured cream paper mache organic sculpture with soft shadows, natural window light, no text"
            },
            {
                "heading": "سبک‌وزن اما مستحکم",
                "body": "به لطف الیاف مقاوم سلولزی، این ظروف و آینه‌ها سبک بوده و **در برابر ضربه و جابه‌جایی مقاومت بسیار بالایی دارند**.",
                "visual": "A stylish handcrafted paper mache wavy mirror hanging on a warm beige wall with linen curtains, no text"
            },
            {
                "heading": "سازگار با انواع چیدمان",
                "body": "رنگ‌های نود، شنی و خاکستری مات باعث می‌شوند این اکسسوری‌ها با **هر پالت رنگی مبلمان و دکوراسیون** به زیبایی ست شوند.",
                "visual": "Modern entryway console table decorated with organic paper mache bowl and dried pampas grass, warm sunlight, no text"
            },
            {
                "heading": "پوشش محافظ ضد رطوبت",
                "body": "تمامی قطعات با وارنیش‌های مات و بی‌رنگ عایق می‌شوند تا **گردگیری با دستمال مرطوب** بدون آسیب به بافت انجام شود.",
                "visual": "Artisan hand holding a delicate textured paper mache vessel under soft warm studio lighting, no text"
            },
            {
                "heading": "تلاقی آرامش و فرم مینیمال",
                "body": "حضور المان‌های طبیعی در خانه، اضطراب روزمره را کاهش داده و **فضایی امن و چشم‌نواز** خلق می‌کند.",
                "visual": "Cozy living room corner with a comfortable boucle armchair and minimalist handmade paper mache table lamp, no text"
            },
            {
                "heading": "سفارش در ابعاد اختصاصی",
                "body": "شما می‌توانید هر اثر را با **رنگ‌بندی و سایز هماهنگ با منزل خود** سفارش دهید. برای مشاوره به دایرکت پیام دهید.",
                "visual": "Cozy artisan studio table with paper mache sculpting tools, textured clay samples and warm morning light, no text"
            },
            {
                "heading": "پایان: اصالت اثر دست‌ساز",
                "body": "خانه‌ای که با هنر دست آراسته شده، داستانی برای گفتن دارد. **کدام فرم و بافت را برای منزلتان بیشتر می‌پسندید؟**",
                "visual": "Artisan carefully placing a unique organic sculpture inside an elegant luxury gift box, aesthetic packaging, no text"
            },
            {
                "heading": "ارسال ایمن به سراسر کشور",
                "body": "بسته‌بندی ضربه‌گیر چندلایه متضمن رسیدن **کاملاً سالم و بدون آسیب اثر** به دست شماست.",
                "visual": "Carefully wrapped delicate ceramic-like paper mache craft package with linen ribbon, no text"
            },
            {
                "heading": "ذخیره کالکشن",
                "body": "این پست را ذخیره کنید تا هنگام تغییر چیدمان یا خرید هدیه، **ایده‌های مدرن دکوراسیون** را در دسترس داشته باشید.",
                "visual": "Minimalist beige bookmark icon resting beside an aesthetic textured sculpture on oak shelf, no text"
            }
        ]
        chosen_slides = full_slides[:max(1, min(count, len(full_slides)))]
        return {
            "slides": chosen_slides,
            "caption": f"🎨 معرفی کالکشن اختصاصی در گالری هنری الهه (ELART GALLERY) - {len(chosen_slides)} اسلاید.\nپیج رسمی: @elartgallery.ir\n#گالری_الهه #پاپیه_ماشه #دکوراسیون_مدرن #صنایع_دستی"
        }

    async def make_reel(self, topic: str) -> Dict[str, Any]:
        scenes = [
            {"text": f"چطور با کالکشن «{topic}» دکور خانه را متحول کنیم؟", "visual": "Modern living room before decor, simple neutral space, daylight, no text"},
            {"text": "مرحله اول: انتخاب بافت‌های مات و فرم‌های طبیعی وابی‌سابی.", "visual": "Artisan hand smoothing organic paper mache clay texture in sunlit workshop, no text"},
            {"text": "مرحله دوم: هماهنگ‌سازی رنگ شنی و کرم با پالت مبلمان.", "visual": "Close up of textured organic cream mirror frame resting on oak floor, no text"},
            {"text": "نتیجه نهایی: فضایی گرم، منحصربه‌فرد و سرشار از آرامش هنری.", "visual": "Luxury styled corner with modern paper mache sculpture and wavy mirror, no text"},
            {"text": "برای ثبت سفارش اختصاصی به گالری الهه (@elartgallery.ir) سر بزنید.", "visual": "Artisan carefully packing the sculpture in luxury packaging with ribbon, no text"},
        ]
        return {"scenes": scenes, "caption": f"🎬 هنر و ظرافت دست‌ساز در «{topic}» | گالری هنری الهه\nپیج رسمی: @elartgallery.ir"}
