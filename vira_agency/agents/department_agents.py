"""
ایجنت‌های ۳ دپارتمان تخصصی آژانس دستیار ویرا
۱. دپارتمان روانشناسی معامله‌گری (@tradebazehn)
۲. دپارتمان ذهن زیبا (@zehnayetaarik)
۳. دپارتمان گالری هنری الهه (@elartgallery.ir)
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
        "شکار استاپ‌لاس و تله نقدینگی در سقف قیمتی",
        "روانشناسی کنترل طمع و جلوگیری از انتقام در مارکت",
        "استراتژی تاییدیه حجم در شکست خطوط روند",
        "نبرد گاوها و خرس‌ها در سنگر حمایت هفتگی",
        "قانون طلایی ریسک به ریوارد ۱ به ۲ در معاملات فیوچرز",
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
                "visual": "A professional crypto trader looking at multiple royal purple and neon emerald glowing candlestick charts, cinematic 8k, no text"
            }
        elif cat_key == "t_news":
            return {
                "heading": "رویدادهای داغ بازار کریپتو",
                "body": m.get("news"),
                "sticker": "پامپ میشه یا اصلاح بیشتر؟",
                "visual": "Futuristic neon trading media command center displaying breaking market charts in royal purple glow, no text"
            }

        fallbacks = {
            "t_quiz": {
                "heading": "کوییز ورود به پوزیشن",
                "body": "کندل پرقدرت صعودی بسته شده اما اندیکاتور حجم ضعف نشان می‌دهد. آیا **وارد پوزیشن لانگ** می‌شوی یا منتظر تاییدیه پولبک می‌مانی؟",
                "sticker": "ورود الان یا صبر برای پولبک؟",
                "visual": "Close-up of a critical breakout trading candle chart glowing in vibrant royal purple and neon green, dramatic, no text"
            },
            "t_psyc": {
                "heading": "تله انتقام از مارکت",
                "body": "بزرگ‌ترین ضررها بعد از استاپ خوردن اول و باز کردن عجولانه پوزیشن رخ می‌دهد. وقتی تحلیلت نقض شد چارت را ببند؛ **مارکت همیشه فرصت می‌دهد**.",
                "sticker": "دچار اورترید شدی تا حالا؟",
                "visual": "A calm disciplined trader with a glowing golden aura of focus in front of cybernetic purple screens, no text"
            },
            "t_hunt": {
                "heading": "تله نقدینگی و شکار استاپ",
                "body": "حرکات شارپ قبل از بازگشایی نیویورک معمولاً برای **شکار حد ضرر تریدرهای خرد** است. ورود در موج اول اغلب بازی در زمین بازیگران اصلی است.",
                "sticker": "تا حالا طعمه استاپ‌هانت شدی؟",
                "visual": "Cybernetic liquidity trap on a futuristic royal purple holographic trading matrix, no text"
            },
            "t_bull": {
                "heading": "نبرد در سنگر خریداران",
                "body": "گاوها در تلاش برای تثبیت قیمت بالای میانگین متحرک روزانه هستند. خرس‌ها به دنبال **شکست ساختار به پایین** هستند؛ بدون تاییدیه ریسک نکنید.",
                "sticker": "برنده نبرد: گاو یا خرس؟",
                "visual": "Epic battle between a metallic royal purple Bull and an emerald green Bear amidst trading market clouds, no text"
            }
        }
        res = fallbacks.get(cat_key, fallbacks["t_quiz"])

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
            {"heading": f"استراتژی معاملاتی: {topic}", "body": "در این کاروسل مهم‌ترین زوایای معاملاتی و **نقاط کلیدی مدیریت ریسک** را بررسی می‌کنیم.", "visual": "Professional trader analyzing glowing charts in royal purple cybernetic room, no text"},
            {"heading": "تله نقدینگی در سقف‌ها", "body": "اکثر تریدرهای مبتدی در شکست‌های جعلی فریب می‌خورند. **تایید حجم معاملات** شرط نخست ورود است.", "visual": "Futuristic candlestick trading chart showing liquidity breakout in neon green and purple, no text"},
            {"heading": "فرمول طلایی ریسک به ریوارد", "body": "حتی با وین‌ریت ۴۰ درصد اگر **ریسک به ریوارد ۱ به ۲** رعایت شود، برآیند حساب شما در بلندمدت کاملاً سودده خواهد بود.", "visual": "Holographic balance scale showing risk and reward with glowing crypto coins, no text"},
            {"heading": "استراتژی ورود و خروج", "body": "پیش از ثبت هر اردر حد ضرر خود را تعیین کنید. **معامله‌گر منظم** هرگز بدون استاپ‌لاس در مارکت باقی نمی‌ماند.", "visual": "Minimalist digital trading workspace with cybernetic neon displays, no text"}
        ]
        prompt = (
            f"یک کاروسل {count} اسلایدی برای پیج روانشناسی معامله‌گری درباره موضوع «{topic}» به زبان کاملاً فارسی بنویس.\n"
            'فرمت خروجی صرفاً JSON:\n{"slides": [{"heading": "تیتر فارسی", "body": "متن فارسی با **کلمات کلیدی** ستاره‌دار"}], "caption": "کپشن کامل فارسی با هشتگ"}'
        )
        data = await self.llm.json(prompt, temperature=0.7)
        raw_slides = data.get("slides") or []
        valid_slides = []
        for s in raw_slides[:count]:
            h = clean_pure_persian(str(s.get("heading") or ""))
            b = clean_pure_persian(str(s.get("body") or ""))
            if h and b:
                valid_slides.append({
                    "heading": h,
                    "body": b,
                    "visual": "A modern cybernetic trading room with neon royal purple charts and holographic financial graphs, no text"
                })

        if len(valid_slides) < 2:
            valid_slides = default_slides[:count]

        caption = clean_pure_persian(str(data.get("caption") or "")) or f"📈 تحلیل تخصصی موضوع «{topic}» در پیج روانشناسی معامله‌گری.\nواترمارک: @tradebazehn\n#روانشناسی_معامله_گری #ترید #بیتکوین"
        return {"slides": valid_slides, "caption": caption}

    async def make_reel(self, topic: str) -> dict:
        scenes = [
            {"text": f"چرا ۹۰٪ معامله‌گران در «{topic}» سرمایه از دست می‌دهند؟", "visual": "Shocked trader in dark royal purple room glowing with red downward charts, cinematic, no text"},
            {"text": "علت اول: ورود شتاب‌زده بدون تاییدیه و اعتماد به شکست‌های فیک.", "visual": "Holographic trap closing on a candlestick chart in royal purple neon lights, no text"},
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
                "visual": "A solitary dark knight in black steel armor standing before a gothic castle under a crimson blood moon, cinematic oil painting, no text"
            },
            "d_edu": {
                "heading": "نقاب لبخند روباه مکار",
                "body": "کسانی که در اولین برخورد بیش از حد تعریفت را می‌کنند، نقشه‌ای در سر دارند. به **رفتار در بحران** اعتماد کن، نه شیرینی کلمات در آرامش.",
                "sticker": "با آدم‌های چاپلوس چه می‌کنی؟",
                "visual": "An anthropomorphic cunning fox wearing an ornate Venetian mask in a dark foggy gothic forest, crimson reflections, no text"
            },
            "d_mar": {
                "heading": "قلمرو دست‌نیافتنی گرگ تنها",
                "body": "وابستگی شدید احساسی ریشه بازی‌های روانی است. کسی که با **تنهایی و خلوت خویش** در صلح باشد، هیچ‌گاه با باج‌گیری عاطفی تسلیم نخواهد شد.",
                "sticker": "مرزهای شخصی‌ات محکمه؟",
                "visual": "A magnificent grey wolf standing solitary on a misty cliff under starry dark crimson sky, chiaroscuro lighting, no text"
            },
            "d_opt": {
                "heading": "راز کاریزمای دست‌نیافتنی",
                "body": "انسان‌ها شیفته افراد پیش‌بینی‌ناپذیرند. هرگز تمام احساساتت را فاش نکن؛ **کمی ابهام و سکوت** بیشترین جاذبه و کشش روانی را خلق می‌کند.",
                "sticker": "دست‌نیافتنی هستی یا زود وا میدی؟",
                "visual": "An enigmatic aristocratic gothic woman in an elegant velvet gown in a dark candlelit baroque hall, mysterious gaze, no text"
            },
            "d_sec": {
                "heading": "مکث طلایی دراکولا در مکالمه",
                "body": "برای نفوذ کلامی بی‌چون‌وچرا، پس از بیان نکته کلیدی **سه ثانیه مکث کن** و مستقیم به چشمان مخاطب نگاه کن. سکوت قدرت‌آفرین است.",
                "sticker": "این تکنیک رو تست کردی؟",
                "visual": "Aristocratic Count Dracula in a deep charcoal coat with crimson lining, intense hypnotic gaze, dark gothic atmosphere, no text"
            }
        }
        res = fallbacks.get(cat_key, fallbacks["d_chal"])

        prompt = (
            f"برای پیج ذهن زیبا (روانشناسی تاریک) در سبک «{cat_key}» یک استوری بنویس.\n"
            "فقط به فارسی عمیق بنویس. کلمات مهم بین **کلمه** باشند.\n"
            'فرمت خروجی صرفاً JSON:\n{"heading": "تیتر ۳ تا ۵ کلمه فارسی", "body": "متن عمیق و فلسفی فارسی در ۲ جمله", "sticker": "سوال نظرسنجی کوتاه"}'
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
            {"heading": f"قوانین ذهن زیبا: {topic}", "body": "در جهان روابط قدرت، آنکه کمتر حرف می‌زند و بیشتر مشاهده می‌کند **کنترل بازی را در دست دارد**.", "visual": "A solitary dark knight standing inside a dark gothic palace with crimson lighting, no text"},
            {"heading": "نقاب‌های فریبنده رفتاری", "body": "افراد مکار همواره با لطف‌های غیرمنتظره آغاز می‌کنند تا حس **دین‌داری و باج‌گیری پنهان** ایجاد کنند.", "visual": "A cunning fox wearing a silver baroque mask in a dark candlelit room, no text"},
            {"heading": "مرزهای فولادین شخصی", "body": "گرگ تنها گرسنگی را می‌پذیرد اما قلاده را هرگز. **حفظ استقلال عاطفی** سد دفاعی در برابر سوءاستفاده‌گران است.", "visual": "A majestic grey wolf standing on a misty cliff under a dark crimson moon, no text"},
            {"heading": "اقتدار در سکوت", "body": "برای تسلط بر مکالمات متشنج، صدای خود را پایین بیاورید و شمرده صحبت کنید. **آرامش خطرناک‌ترین واکنش است**.", "visual": "Count Dracula sitting on a gothic throne in deep shadows with crimson candles, no text"}
        ]
        prompt = (
            f"یک کاروسل {count} اسلایدی برای پیج ذهن زیبا درباره موضوع «{topic}» به زبان کاملاً فارسی بنویس.\n"
            'فرمت خروجی صرفاً JSON:\n{"slides": [{"heading": "تیتر فارسی", "body": "متن فارسی با **کلمات کلیدی** ستاره‌دار"}], "caption": "کپشن کامل فارسی با هشتگ"}'
        )
        data = await self.llm.json(prompt, temperature=0.7)
        raw_slides = data.get("slides") or []
        valid_slides = []
        for s in raw_slides[:count]:
            h = clean_pure_persian(str(s.get("heading") or ""))
            b = clean_pure_persian(str(s.get("body") or ""))
            if h and b:
                valid_slides.append({
                    "heading": h,
                    "body": b,
                    "visual": "Dark gothic atmospheric oil painting with crimson and charcoal tones, mysterious symbolic shadows, no text"
                })

        if len(valid_slides) < 2:
            valid_slides = default_slides[:count]

        caption = clean_pure_persian(str(data.get("caption") or "")) or f"🖤 رازهای عمیق «{topic}» در پیج ذهن زیبا.\nپیج رسمی: @zehnayetaarik\n#ذهن_زیبا #روانشناسی_تاریک #کاریزما"
        return {"slides": valid_slides, "caption": caption}

    async def make_reel(self, topic: str) -> dict:
        scenes = [
            {"text": f"۳ نشانه پنهان در «{topic}» که نباید نادیده بگیری.", "visual": "Dark knight looking out of a gothic castle window into the misty moonlit forest, no text"},
            {"text": "نشانه اول: لبخندهایی که به چشم‌ها نمی‌رسند؛ نقاب روباه‌های مکار.", "visual": "Cunning fox in Venetian carnival mask blending into shadows, no text"},
            {"text": "نشانه دوم: سکوت‌های معنادار برای سنجش واکنش و تسلیم شما.", "visual": "Majestic grey wolf staring calmly with piercing eyes on a cliff, no text"},
            {"text": "نشانه سوم: تغییر ناگهانی لحن پس از رسیدن به خواسته.", "visual": "Count Dracula turning his head in dark regal cloak, shadows and candles, no text"},
            {"text": "پیج ذهن زیبا (@zehnayetaarik) را دنبال کن تا قواعد نفوذ را بدانی.", "visual": "Ancient gothic library with glowing red ancient tome on the table, no text"},
        ]
        caption = f"🎬 رمزگشایی از بازی‌های روانی در «{topic}».\nپیج رسمی: @zehnayetaarik\n#ذهن_زیبا #روانشناسی_تاریک #کاریزما"
        return {"scenes": scenes, "caption": caption}


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
                "visual": "A trendy organic wavy curved mirror frame made of textured cream paper mache hanging on a modern minimalist aesthetic wall, soft natural sunlight, luxury home decor photography, no text"
            },
            "art_decor": {
                "heading": "ظروف دکوراتیو بافت‌دار روی کنسول",
                "body": "اکسسوری‌های دست‌ساز پاپیه‌ماشه ترکیبی از **سبکی باورنکردنی با استحکام بالا** هستند. این ظروف به میز جلو مبلی یا کنسول هویت می‌بخشند.",
                "sticker": "رنگ سفارشی خودت رو انتخاب کن",
                "visual": "A collection of handmade organic paper mache bowls and decorative plates in warm cream and terracotta tones displayed on a luxury oak console, editorial interior styling, no text"
            },
            "art_sculpture": {
                "heading": "مجسمه‌های مینیمال فرم آزاد",
                "body": "این مجسمه‌ها نگاه را جذب می‌کنند بدون آنکه فضا را شلوغ کنند. هر فرم با دست و **بدون هیچ قالب صنعتی** شکل گرفته است.",
                "sticker": "هنر دست‌ساز یا مجسمه قالبی؟",
                "visual": "A stunning abstract minimalist paper mache sculpture in warm neutral tones placed on a minimalist shelf, soft morning sunlight, architectural aesthetic, no text"
            },
            "behind": {
                "heading": "پشت صحنه گالری الهه",
                "body": "راز ماندگاری این آثار در ترکیب دقیق **الیاف سلولزی با چسب چوب باکیفیت** است. خشک شدن لایه‌به‌لایه‌ مانع ایجاد هرگونه ترک می‌شود.",
                "sticker": "دوست داری مراحل ساختش رو ببینی؟",
                "visual": "Artisan hands packaging a beautiful textured paper mache decor piece with linen paper and dried flowers in a warm sunlit art studio, cozy aesthetic, no text"
            }
        }
        res = fallbacks.get(cat_key, fallbacks["art_mirror"])

        prompt = (
            f"برای گالری هنری الهه در سبک «{cat_key}» یک استوری جذاب بنویس.\n"
            "فقط به فارسی صمیمی و هنری بنویس. کلمات مهم بین **کلمه** باشند.\n"
            'فرمت خروجی صرفاً JSON:\n{"heading": "تیتر ۳ تا ۵ کلمه فارسی", "body": "متن جذاب و فروش‌محور فارسی در ۲ جمله", "sticker": "دعوت به دایرکت یا سوال کوتاه"}'
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
            {"heading": f"کالکشن گالری الهه: {topic}", "body": "ترکیب بافت‌های دست‌ساز و ارگانیک با چیدمان خانه مدرن، **حس گرما و اصالت ماندگار** به فضا می‌بخشد.", "visual": "Minimalist luxury living room with handmade paper mache decor in warm neutral tones, natural light, no text"},
            {"heading": "هنر نقص‌های کامل (وابی‌سابی)", "body": "زیبایی مجسمه‌های پاپیه‌ماشه در ناصافی‌های ظریف و دست‌ساز آن است که **هیچ نمونه دومی در جهان ندارد**.", "visual": "Close-up of a textured cream paper mache organic sculpture with soft shadows, no text"},
            {"heading": "سبک‌وزن اما مستحکم", "body": "به لطف الیاف مقاوم، این ظروف و آینه‌ها سبک بوده و **در برابر جابه‌جایی مقاومت بسیار بالایی دارند**.", "visual": "A stylish handcrafted paper mache mirror hanging on a warm beige wall with linen curtains, no text"},
            {"heading": "سفارش در ابعاد اختصاصی", "body": "شما می‌توانید هر اثر را با **رنگ‌بندی هماهنگ با منزل خود** سفارش دهید. برای مشاوره به دایرکت @elartgallery.ir پیام دهید.", "visual": "Cozy artisan studio table with paper mache materials, dried plants and warm lighting, no text"}
        ]
        prompt = (
            f"یک کاروسل {count} اسلایدی برای گالری هنری الهه درباره موضوع «{topic}» به زبان کاملاً فارسی بنویس.\n"
            'فرمت خروجی صرفاً JSON:\n{"slides": [{"heading": "تیتر فارسی", "body": "متن فارسی با **کلمات کلیدی** ستاره‌دار"}], "caption": "کپشن کامل فارسی با هشتگ"}'
        )
        data = await self.llm.json(prompt, temperature=0.7)
        raw_slides = data.get("slides") or []
        valid_slides = []
        for s in raw_slides[:count]:
            h = clean_pure_persian(str(s.get("heading") or ""))
            b = clean_pure_persian(str(s.get("body") or ""))
            if h and b:
                valid_slides.append({
                    "heading": h,
                    "body": b,
                    "visual": "A warm luxury minimalist interior showcasing handmade paper mache art and organic mirrors, soft natural sunlight, no text"
                })

        if len(valid_slides) < 2:
            valid_slides = default_slides[:count]

        caption = clean_pure_persian(str(data.get("caption") or "")) or f"🎨 معرفی کالکشن اختصاصی در گالری هنری الهه.\nپیج رسمی: @elartgallery.ir\nثبت سفارش و ابعاد دلخواه در دایرکت.\n#گالری_الهه #پاپیه_ماشه #دکوراسیون_مدرن"
        return {"slides": valid_slides, "caption": caption}

    async def make_reel(self, topic: str) -> dict:
        scenes = [
            {"text": f"چطور با کالکشن «{topic}» دکور خانه را متحول کنیم؟", "visual": "Modern living room before decor, simple neutral space, daylight, no text"},
            {"text": "مرحله اول: انتخاب بافت‌های مات و فرم‌های طبیعی وابی‌سابی.", "visual": "Artisan hand smoothing organic paper mache clay texture in sunlit workshop, no text"},
            {"text": "مرحله دوم: هماهنگ‌سازی رنگ شنی و کرم با پالت مبلمان.", "visual": "Close up of textured organic cream mirror frame resting on oak floor, no text"},
            {"text": "نتیجه نهایی: فضایی گرم، منحصر‌به‌فرد و سرشار از آرامش هنری.", "visual": "Luxury styled corner with modern paper mache sculpture and wavy mirror, magazine aesthetic, no text"},
            {"text": "برای ثبت سفارش اختصاصی به گالری الهه (@elartgallery.ir) سر بزنید.", "visual": "Artisan carefully packing the sculpture in luxury packaging with ribbon, no text"},
        ]
        caption = f"🎬 صفر تا صد چیدمان با «{topic}» در گالری هنری الهه.\nپیج رسمی: @elartgallery.ir\n#گالری_الهه #پاپیه_ماشه #طراحی_داخلی"
        return {"scenes": scenes, "caption": caption}
