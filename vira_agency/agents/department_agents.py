"""
ایجنت‌های ۳ دپارتمان تخصصی آژانس دستیار ویرا
شامل چارت‌های شفاف تریدینگ‌ویو بدون هیچ حباب گفت‌وگو یا متن اضافه
و تفکیک کامل استوری ۱ (سوال کوییز) و استوری ۲ (پاسخ تحلیلی با خطوط تکنیکال)
"""
import random
import re
import logging
from vira_agency.core.market_news import get_live_market_summary

log = logging.getLogger(__name__)


def clean_pure_persian(text: str) -> str:
    if not text:
        return ""
    low = text.lower()
    leaks = ["persona", "task", "role", "generator", "output", "json", "markdown", "create", "content persian", "senior text", "expert content"]
    if any(lk in low for lk in leaks):
        return ""
    cleaned = re.sub(r"[a-zA-Z]", "", text)
    cleaned = re.sub(r"[{}\[\]\"']", "", cleaned)
    return cleaned.strip()


class TradingAgent:
    """دپارتمان روانشناسی معامله‌گری (@tradebazehn)"""

    TRENDING_TOPICS = [
        "کوییز تحلیلی چارت: آیا در این شکست کندلی وارد می‌شوی؟",
        "شکار استاپ‌لاس و تله نقدینگی در سقف قیمتی",
        "روانشناسی کنترل طمع و جلوگیری از انتقام در مارکت",
        "استراتژی تاییدیه حجم در شکست خطوط روند",
        "قانون طلایی ریسک به ریوارد ۱ به ۲ در معاملات فیوچرز",
    ]

    QUIZ_CHART_SCENARIOS = [
        {
            "q_heading": "کوییز چارت: لانگ یا شورت؟",
            "q_body": "قیمت با یک **کندل پرقدرت سبز** مقاومت را شکسته است؛ اما اندیکاتور حجم کاهش نشان می‌دهد. با توجه به چارت بالا، آیا در این نقطه وارد معامله می‌شوی؟",
            "q_sticker": "لانگ می‌گیری یا شورت؟",
            # پرامپت با تاکید موکد بر عدم رسم هرگونه حباب گفت‌وگو، بالون یا متن
            "q_visual": "Crystal clear high-resolution screenshot of a TradingView cryptocurrency candlestick chart, sharp green breakout candle reaching upper resistance line, dark royal purple technical user interface, clean financial chart, completely without text, absolutely no speech bubbles, no cartoon dialogue balloons, no callout boxes, no typography, professional 8k",

            "a_heading": "✅ پاسخ تحلیل: تله گاوی (Fakeout)",
            "a_body": "اینجا **نباید وارد معامله لانگ شد!** شکست مقاومت بدون تاییدیه حجم، یک تله برای شکار نقدینگی است. صبر می‌کنیم یا در صورت تشکیل کندل بازگشتی، وارد پوزیشن شورت می‌شویم.",
            "a_sticker": "حدست درست بود یا نه؟",
            "a_visual": "Macro close-up TradingView cryptocurrency candlestick chart showing a sharp red rejection candle dropping down from resistance line, vibrant royal purple and neon emerald indicators, clean financial trading chart, absolutely no speech bubbles, no dialogue boxes, no text, crisp 8k"
        },
        {
            "q_heading": "کوییز ستاپ: شکار در کف کانال",
            "q_body": "بیت‌کوین به **حمایت معتبر روزانه** رسیده و شدوی بلندی به سمت پایین تشکیل داده است. آیا این نقطه را موقعیت ورود مطمئن می‌دانی؟",
            "q_sticker": "ورود الان یا صبر برای پولبک؟",
            "q_visual": "Professional clean TradingView crypto candlestick chart focused on lower support trendline bounce with long wick rejection candlestick, royal purple theme, highly detailed market candles, absolutely no speech bubbles, no cartoon text boxes, no typography, clean 8k",

            "a_heading": "✅ پاسخ تحلیل: ورود در تاییدیه",
            "a_body": "شدو نشان‌دهنده ورود خریداران است؛ اما تا زمانی که **کندل بعدی تثبیت نشود** نباید عجله کرد. ورود مطمئن پس از پولبک و ثبت حد ضرر در زیر شدو است.",
            "a_sticker": "معامله‌گر صبوری هستی؟",
            "a_visual": "Crisp TradingView candlestick chart displaying successful bounce and green continuation candle moving upward from support line, cybernetic royal purple aesthetic, sharp candles, no speech bubbles, no dialogue boxes, no text, 8k"
        }
    ]

    def __init__(self, llm):
        self.llm = llm

    def get_random_trend(self) -> str:
        return random.choice(self.TRENDING_TOPICS)

    async def make_story(self, cat_key: str) -> dict:
        m = await get_live_market_summary()

        if cat_key == "t_market":
            return {
                "heading": f"تحلیل بیت‌کوین در {m.get('price')}$",
                "body": f"بیت‌کوین در ۲۴ ساعت اخیر با نوسان **{m.get('change')}** در ناحیه **{m.get('trend')}** قرار دارد. کف **${m.get('support')}** حمایت محکم روزانه و سقف **${m.get('resistance')}** مقاومت کلیدی است. بدون تاییدیه وارد نشوید.",
                "sticker": "خرید در کف یا شکست سقف؟",
                "visual": "A professional crypto trader looking at multiple royal purple and neon emerald glowing candlestick charts, cinematic 8k, absolutely no speech bubbles, no text"
            }
        elif cat_key == "t_news":
            return {
                "heading": "رویدادهای داغ بازار کریپتو",
                "body": m.get("news"),
                "sticker": "پامپ میشه یا اصلاح بیشتر؟",
                "visual": "Futuristic financial trading media command center displaying breaking crypto charts in royal purple glow, no text, no speech bubbles"
            }
        elif cat_key == "t_quiz":
            scen = random.choice(self.QUIZ_CHART_SCENARIOS)
            return {
                "is_quiz_pair": True,
                "question": {
                    "heading": scen["q_heading"],
                    "body": scen["q_body"],
                    "sticker": scen["q_sticker"],
                    "visual": scen["q_visual"],
                    "quiz_type": "question"
                },
                "answer": {
                    "heading": scen["a_heading"],
                    "body": scen["a_body"],
                    "sticker": scen["a_sticker"],
                    "visual": scen["a_visual"],
                    "quiz_type": "answer"
                }
            }

        fallbacks = {
            "t_psyc": {
                "heading": "تله انتقام از مارکت",
                "body": "بزرگ‌ترین ضررها بعد از استاپ خوردن اول و باز کردن عجولانه پوزیشن رخ می‌دهد. وقتی تحلیلت نقض شد چارت را ببند؛ **مارکت همیشه فرصت می‌دهد**.",
                "sticker": "دچار اورترید شدی تا حالا؟",
                "visual": "A calm disciplined trader with a glowing golden aura of focus in front of cybernetic purple screens, no speech bubbles, no text"
            },
            "t_hunt": {
                "heading": "تله نقدینگی و شکار استاپ",
                "body": "حرکات شارپ قبل از بازگشایی نیویورک معمولاً برای **شکار حد ضرر تریدرهای خرد** است. ورود در موج اول اغلب بازی در زمین بازیگران اصلی است.",
                "sticker": "تا حالا طعمه استاپ‌هانت شدی؟",
                "visual": "Cybernetic liquidity trap on a futuristic royal purple holographic trading matrix, no speech bubbles, no text"
            },
            "t_bull": {
                "heading": "نبرد در سنگر خریداران",
                "body": "گاوها در تلاش برای تثبیت قیمت بالای میانگین متحرک روزانه هستند. خرس‌ها به دنبال **شکست ساختار به پایین** هستند؛ بدون تاییدیه ریسک نکنید.",
                "sticker": "برنده نبرد: گاو یا خرس؟",
                "visual": "Epic battle between a metallic royal purple Bull and an emerald green Bear amidst trading market clouds, no speech bubbles, no text"
            }
        }
        res = fallbacks.get(cat_key, fallbacks["t_psyc"])

        prompt = (
            f"برای پیج روانشناسی معامله‌گری در سبک «{cat_key}» یک استوری بنویس.\n"
            "فقط به فارسی روان بنویس. کلمات مهم بین **کلمه** باشند.\n"
            'فرمت خروجی صرفاً JSON:\n{"heading": "تیتر ۳ تا ۵ کلمه فارسی", "body": "متن تخصصی و آموزنده فارسی در ۲ جمله", "sticker": "سوال نظرسنجی کوتاه"}'
        )
        data = await self.llm.json(prompt, temperature=0.7)
        h = clean_pure_persian(str(data.get("heading") or ""))
        b = clean_pure_persian(str(data.get("body") or ""))
        s = clean_pure_persian(str(data.get("sticker") or ""))
        if h and b and len(b) > 25:
            return {"heading": h, "body": b, "sticker": s or res["sticker"], "visual": res["visual"]}
        return res

    async def make_carousel(self, topic: str, count: int = 4) -> dict:
        default_slides = [
            {
                "heading": "اسلاید ۱: بررسی چارت تحلیلی",
                "body": "به چارت بالا با دقت نگاه کنید؛ کندل تاییدیه در مقاومت با **واگرایی منفی حجم** مواجه شده است. آیا اینجا ورود منطقی است؟",
                "visual": "Macro screenshot of a TradingView cryptocurrency candlestick chart with clear trendlines, royal purple interface, crisp 4k, no text, no speech bubbles"
            },
            {
                "heading": "اسلاید ۲: تله نقدینگی و فریب تریدرها",
                "body": "بسیاری از معامله‌گران هیجانی در این سقف لانگ گرفتند غافل از اینکه مارکت‌میکرها **برای شکار استاپ‌ها** قیمت را بالا برده‌اند.",
                "visual": "Macro TradingView chart showing liquidity grab with long wick above resistance, neon purple and green, no speech bubbles, no text"
            },
            {
                "heading": "اسلاید ۳: پاسخ و استراتژی ورود صحیح",
                "body": "تصمیم حرفه‌ای: **صبر برای بازگشت به زیر مقاومت** و سپس باز کردن پوزیشن شورت با استاپ بالای شدو. مدیریت سرمایه همیشه اولویت است.",
                "visual": "Clean technical chart showing downward continuation with clear green stop-loss and red target levels, TradingView style, no speech bubbles, no text"
            },
            {
                "heading": "اسلاید ۴: جمع‌بندی روانشناسی معامله‌گری",
                "body": "ترید بازی صبر و آمار است نه پیش‌گویی. اگر این پست برایت مفید بود آن را ذخیره کن و به جمع ما در **@tradebazehn** بپیوند.",
                "visual": "Futuristic trader workstation with neon screens and clean royal purple aesthetic, no speech bubbles, no text"
            }
        ]
        return {"slides": default_slides[:count], "caption": f"📈 کاروسل تحلیلی چارت و تصمیم‌گیری در ترید.\nآیدی اختصاصی: @tradebazehn\n#روانشناسی_معامله_گری #ترید #تحلیل_تکنیکال"}

    async def make_reel(self, topic: str) -> dict:
        scenes = [
            {"text": f"چرا ۹۰٪ معامله‌گران در «{topic}» سرمایه از دست می‌دهند؟", "visual": "Shocked trader in dark royal purple room glowing with red downward charts, cinematic, no text, no speech bubbles"},
            {"text": "علت اول: ورود شتاب‌زده بدون تاییدیه و اعتماد به شکست‌های فیک.", "visual": "TradingView candlestick chart screenshot showing fakeout wick, royal purple neon, no speech bubbles, no text"},
            {"text": "علت دوم: جابجا کردن حد ضرر به امید بازگشت قیمت مارکت.", "visual": "Cybernetic scale showing loss balance with intense purple and emerald lasers, no text"},
            {"text": "قانون نجات‌بخش: فقط در پولبک و با تاییدیه حجم اردر بذار.", "visual": "Disciplined professional trader calmly pointing at green breakout candle, no text"},
            {"text": "این پست رو ذخیره کن و به پیج @tradebazehn ملحق شو!", "visual": "Futuristic crypto vault opening with golden and emerald rewards, no text"},
        ]
        caption = f"🎬 بررسی ۵ نکته کلیدی روانشناسی معامله‌گری در «{topic}».\nپیج رسمی: @tradebazehn\n#روانشناسی_معامله_گری #مدیریت_ریسک"
        return {"scenes": scenes, "caption": caption}


class DarkPsychAgent:
    """دپارتمان ذهن زیبا (@zehnayetaarik)"""

    TRENDING_TOPICS = [
        "چرا افراد پیش‌بینی‌ناپذیر بیشترین کاریزما را دارند؟",
        "تکنیک سکوت دراکولا در برابر توهین و تخریب کلامی",
        "چگونه دست افراد چاپلوس و روباه‌های مکار را بخوانیم؟",
        "حفظ استقلال عاطفی گرگ تنها در برابر باج‌گیری احساسی",
        "دوراهی شوالیه تاریک: بخشش یا حذف بی‌سر‌و‌صدا؟",
    ]

    def __init__(self, llm):
        self.llm = llm

    def get_random_trend(self) -> str:
        return random.choice(self.TRENDING_TOPICS)

    async def make_story(self, cat_key: str) -> dict:
        fallbacks = {
            "d_chal": {
                "heading": "دوراهی شوالیه در برابر خیانت",
                "body": "وقتی کسی اعتمادت را خدشه‌دار می‌کند، فریاد زدن نشانه ضعف است. **سکوت سرد و حذف بی‌صدا** ضربه‌ای ویران‌کننده‌تر از هر انتقامی وارد می‌کند.",
                "sticker": "پاسخ متقابل یا حذف دائمی؟",
                "visual": "A solitary dark knight in black steel armor standing before a gothic castle under a crimson blood moon, cinematic oil painting, no text, no speech bubbles"
            },
            "d_edu": {
                "heading": "نقاب لبخند روباه مکار",
                "body": "کسانی که در اولین برخورد بیش از حد تعریفت را می‌کنند، نقشه‌ای در سر دارند. به **رفتار در بحران** اعتماد کن، نه شیرینی کلمات در آرامش.",
                "sticker": "با آدم‌های چاپلوس چه می‌کنی؟",
                "visual": "An anthropomorphic cunning fox wearing an ornate Venetian mask in a dark foggy gothic forest, crimson reflections, no text, no speech bubbles"
            },
            "d_mar": {
                "heading": "قلمرو دست‌نیافتنی گرگ تنها",
                "body": "وابستگی شدید احساسی ریشه بازی‌های روانی است. کسی که با **تنهایی و خلوت خویش** در صلح باشد، هیچ‌گاه با باج‌گیری عاطفی تسلیم نخواهد شد.",
                "sticker": "مرزهای شخصی‌ات محکمه؟",
                "visual": "A magnificent grey wolf standing solitary on a misty cliff under starry dark crimson sky, chiaroscuro lighting, no text, no speech bubbles"
            },
            "d_opt": {
                "heading": "راز کاریزمای دست‌نیافتنی",
                "body": "انسان‌ها شیفته افراد پیش‌بینی‌ناپذیرند. هرگز تمام احساساتت را فاش نکن؛ **کمی ابهام و سکوت** بیشترین جاذبه و کشش روانی را خلق می‌کند.",
                "sticker": "دست‌نیافتنی هستی یا زود وا میدی؟",
                "visual": "An enigmatic aristocratic gothic woman in an elegant velvet gown in a dark candlelit baroque hall, mysterious gaze, no text, no speech bubbles"
            },
            "d_sec": {
                "heading": "مکث طلایی دراکولا در مکالمه",
                "body": "برای نفوذ کلامی بی‌چون‌وچرا، پس از بیان نکته کلیدی **سه ثانیه مکث کن** و مستقیم به چشمان مخاطب نگاه کن. سکوت قدرت‌آفرین است.",
                "sticker": "این تکنیک رو تست کردی؟",
                "visual": "Aristocratic Count Dracula in a deep charcoal coat with crimson lining, intense hypnotic gaze, dark gothic atmosphere, no text, no speech bubbles"
            }
        }
        res = fallbacks.get(cat_key, fallbacks["d_chal"])
        return res

    async def make_carousel(self, topic: str, count: int = 4) -> dict:
        default_slides = [
            {"heading": f"قوانین ذهن زیبا: {topic}", "body": "در جهان روابط قدرت، آنکه کمتر حرف می‌زند و بیشتر مشاهده می‌کند **کنترل بازی را در دست دارد**.", "visual": "A solitary dark knight standing inside a dark gothic palace with crimson lighting, no text, no speech bubbles"},
            {"heading": "نقاب‌های فریبنده رفتاری", "body": "افراد مکار همواره با لطف‌های غیرمنتظره آغاز می‌کنند تا حس **دین‌داری و باج‌گیری پنهان** ایجاد کنند.", "visual": "A cunning fox wearing a silver baroque mask in a dark candlelit room, no text, no speech bubbles"},
            {"heading": "مرزهای فولادین شخصی", "body": "گرگ تنها گرسنگی را می‌پذیرد اما قلاده را هرگز. **حفظ استقلال عاطفی** سد دفاعی در برابر سوءاستفاده‌گران است.", "visual": "A majestic grey wolf standing on a misty cliff under a dark crimson moon, no text, no speech bubbles"},
            {"heading": "اقتدار در سکوت", "body": "برای تسلط بر مکالمات متشنج، صدای خود را پایین بیاورید و شمرده صحبت کنید. **آرامش خطرناک‌ترین واکنش است**.", "visual": "Count Dracula sitting on a gothic throne in deep shadows with crimson candles, no text, no speech bubbles"}
        ]
        return {"slides": default_slides[:count], "caption": f"🖤 رازهای عمیق «{topic}» در پیج ذهن زیبا.\nپیج رسمی: @zehnayetaarik\n#ذهن_زیبا #روانشناسی_تاریک"}

    async def make_reel(self, topic: str) -> dict:
        scenes = [
            {"text": f"۳ نشانه پنهان در «{topic}» که نباید نادیده بگیری.", "visual": "Dark knight looking out of a gothic castle window into the misty moonlit forest, no text, no speech bubbles"},
            {"text": "نشانه اول: لبخندهایی که به چشم‌ها نمی‌رسند؛ نقاب روباه‌های مکار.", "visual": "Cunning fox in Venetian carnival mask blending into shadows, no text, no speech bubbles"},
            {"text": "نشانه دوم: سکوت‌های معنادار برای سنجش واکنش و تسلیم شما.", "visual": "Majestic grey wolf staring calmly with piercing eyes on a cliff, no text, no speech bubbles"},
            {"text": "نشانه سوم: تغییر ناگهانی لحن پس از رسیدن به خواسته.", "visual": "Count Dracula turning his head in dark regal cloak, shadows and candles, no text, no speech bubbles"},
            {"text": "پیج ذهن زیبا (@zehnayetaarik) را دنبال کن تا قواعد نفوذ را بدانی.", "visual": "Ancient gothic library with glowing red ancient tome on the table, no text, no speech bubbles"},
        ]
        return {"scenes": scenes, "caption": f"🎬 رمزگشایی از بازی‌های روانی در «{topic}».\nپیج رسمی: @zehnayetaarik"}


class ArtAgent:
    """دپارتمان گالری هنری الهه (@elartgallery.ir)"""

    TRENDING_TOPICS = [
        "آینه موج‌دار وابی‌سابی؛ امضای مینیمال دکوراسیون مدرن",
        "کاسه‌ها و ظروف دکوراتیو بافت‌دار برای میز کنسول",
        "مجسمه‌های فرم آزاد و بدون قالب صنعتی",
        "فرمول طلایی چسب چوب و ضدترک کارگاه پاپیه‌ماشه",
        "چرا اکسسوری‌های دست‌ساز به خانه روح و گرما می‌بخشند؟",
    ]

    def __init__(self, llm):
        self.llm = llm

    def get_random_trend(self) -> str:
        return random.choice(self.TRENDING_TOPICS)

    async def make_story(self, cat_key: str) -> dict:
        fallbacks = {
            "art_mirror": {
                "heading": "آینه موج‌دار وابی‌سابی؛ امضای دکور مدرن",
                "body": "چرا آینه‌های فرم آزاد ترند شدند؟ چون انحنای ارگانیک و **بافت مات خمیر دست‌ساز**، خشکی خطوط دیوار را به لطافت و گرما تبدیل می‌کند.",
                "sticker": "ابعاد دلخواهت رو دایرکت بفرست",
                "visual": "A trendy organic wavy curved mirror frame made of textured cream paper mache hanging on a modern minimalist aesthetic wall, soft natural sunlight, luxury home decor photography, absolutely no speech bubbles, no text"
            },
            "art_decor": {
                "heading": "ظروف دکوراتیو بافت‌دار روی کنسول",
                "body": "اکسسوری‌های دست‌ساز پاپیه‌ماشه ترکیبی از **سبکی باورنکردنی با استحکام بالا** هستند. این ظروف به میز جلو مبلی یا کنسول هویت می‌بخشند.",
                "sticker": "رنگ سفارشی خودت رو انتخاب کن",
                "visual": "A collection of handmade organic paper mache bowls and decorative plates in warm cream and terracotta tones displayed on a luxury oak console, editorial interior styling, no speech bubbles, no text"
            },
            "art_sculpture": {
                "heading": "مجسمه‌های مینیمال فرم آزاد",
                "body": "این مجسمه‌ها نگاه را جذب می‌کنند بدون آنکه فضا را شلوغ کنند. هر فرم با دست و **بدون هیچ قالب صنعتی** شکل گرفته است.",
                "sticker": "هنر دست‌ساز یا مجسمه قالبی؟",
                "visual": "A stunning abstract minimalist paper mache sculpture in warm neutral tones placed on a minimalist shelf, soft morning sunlight, architectural aesthetic, no speech bubbles, no text"
            },
            "behind": {
                "heading": "پشت صحنه گالری الهه",
                "body": "راز ماندگاری این آثار در ترکیب دقیق **الیاف سلولزی با چسب چوب باکیفیت** است. خشک شدن لایه‌به‌لایه‌ مانع ایجاد هرگونه ترک می‌شود.",
                "sticker": "دوست داری مراحل ساختش رو ببینی؟",
                "visual": "Artisan hands packaging a beautiful textured paper mache decor piece with linen paper and dried flowers in a warm sunlit art studio, cozy aesthetic, no speech bubbles, no text"
            }
        }
        return fallbacks.get(cat_key, fallbacks["art_mirror"])

    async def make_carousel(self, topic: str, count: int = 4) -> dict:
        default_slides = [
            {"heading": f"کالکشن گالری الهه: {topic}", "body": "ترکیب بافت‌های دست‌ساز و ارگانیک با چیدمان خانه مدرن، **حس گرما و اصالت ماندگار** به فضا می‌بخشد.", "visual": "Minimalist luxury living room with handmade paper mache decor in warm neutral tones, natural light, no text, no speech bubbles"},
            {"heading": "هنر نقص‌های کامل (وابی‌سابی)", "body": "زیبایی مجسمه‌های پاپیه‌ماشه در ناصافی‌های ظریف و دست‌ساز آن است که **هیچ نمونه دومی در جهان ندارد**.", "visual": "Close-up of a textured cream paper mache organic sculpture with soft shadows, no text, no speech bubbles"},
            {"heading": "سبک‌وزن اما مستحکم", "body": "به لطف الیاف مقاوم، این ظروف و آینه‌ها سبک بوده و **در برابر جابه‌جایی مقاومت بسیار بالایی دارند**.", "visual": "A stylish handcrafted paper mache mirror hanging on a warm beige wall with linen curtains, no text, no speech bubbles"},
            {"heading": "سفارش در ابعاد اختصاصی", "body": "شما می‌توانید هر اثر را با **رنگ‌بندی هماهنگ با منزل خود** سفارش دهید. برای مشاوره به دایرکت @elartgallery.ir پیام دهید.", "visual": "Cozy artisan studio table with paper mache materials, dried plants and warm lighting, no text, no speech bubbles"}
        ]
        return {"slides": default_slides[:count], "caption": f"🎨 معرفی کالکشن اختصاصی در گالری هنری الهه.\nپیج رسمی: @elartgallery.ir\n#گالری_الهه #پاپیه_ماشه"}

    async def make_reel(self, topic: str) -> dict:
        scenes = [
            {"text": f"چطور با کالکشن «{topic}» دکور خانه را متحول کنیم؟", "visual": "Modern living room before decor, simple neutral space, daylight, no text, no speech bubbles"},
            {"text": "مرحله اول: انتخاب بافت‌های مات و فرم‌های طبیعی وابی‌سابی.", "visual": "Artisan hand smoothing organic paper mache clay texture in sunlit workshop, no text, no speech bubbles"},
            {"text": "مرحله دوم: هماهنگ‌سازی رنگ شنی و کرم با پالت مبلمان.", "visual": "Close up of textured organic cream mirror frame resting on oak floor, no text, no speech bubbles"},
            {"text": "نتیجه نهایی: فضایی گرم، منحصر‌به‌فرد و سرشار از آرامش هنری.", "visual": "Luxury styled corner with modern paper mache sculpture and wavy mirror, magazine aesthetic, no text, no speech bubbles"},
            {"text": "برای ثبت سفارش اختصاصی به گالری الهه (@elartgallery.ir) سر بزنید.", "visual": "Artisan carefully packing the sculpture in luxury packaging with ribbon, no text, no speech bubbles"},
        ]
        return {"scenes": scenes, "caption": f"🎬 صفر تا صد چیدمان با «{topic}» در گالری هنری الهه.\nپیج رسمی: @elartgallery.ir"}
