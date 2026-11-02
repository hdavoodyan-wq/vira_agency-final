"""
ربات تلگرام آژانس هوشمند «دستیار ویرا»
طراحی کاربردی استوری‌ها: محصولات ترند پاپیه‌ماشه (آینه‌ها، اکسسوری دکور، مجسمه مینیمال)
تحلیل زنده کریپتو و روانشناسی تاریک بدون افت کیفیت یا نشت زبان انگلیسی
"""
import asyncio
import logging
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

from vira_agency.core.config import AgencyConfig, VIRA_SYSTEM_IDENTITY
from vira_agency.core.database import AgencyDatabase
from vira_agency.core.llm_router import LLMRouter
from vira_agency.core.orchestrator import ViraOrchestrator
from vira_agency.core.render import render_story, render_carousel, render_reel_frame
from vira_agency.core.market_news import get_live_market_summary

logging.basicConfig(format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", level=logging.INFO)
log = logging.getLogger("vira_agency")

STORY_CATS_CONFIG = {
    # پیج ترید
    "t_market": {
        "title": "📈 تحلیل بازار و وضعیت بیت‌کوین",
        "tag_fa": "تحلیل بازار",
        "visual": "A professional crypto trader looking at multiple royal purple and neon emerald glowing candlestick charts, cinematic 8k, no text"
    },
    "t_news": {
        "title": "📰 اخبار داغ و رویدادهای زنده",
        "tag_fa": "اخبار داغ",
        "visual": "Futuristic neon trading media command center displaying breaking market charts in royal purple glow, no text"
    },
    "t_quiz": {
        "title": "⚡ کوییز تریدری (اینجا وارد شویم؟)",
        "tag_fa": "کوییز تریدری",
        "visual": "Close-up of a critical breakout trading candle chart glowing in vibrant royal purple and neon green, dramatic, no text"
    },
    "t_psyc": {
        "title": "🧠 روانشناسی ترید و کنترل طمع",
        "tag_fa": "روانشناسی ترید",
        "visual": "A calm disciplined trader with a glowing golden aura of focus in front of cybernetic purple screens, no text"
    },
    "t_hunt": {
        "title": "🎯 هشدار تله نقدینگی و استاپ‌هانت",
        "tag_fa": "شکار استاپ",
        "visual": "Cybernetic liquidity trap on a futuristic royal purple holographic trading matrix, no text"
    },
    "t_bull": {
        "title": "🐂 نبرد حماسی گاو و خرس",
        "tag_fa": "نبرد گاو و خرس",
        "visual": "Epic battle between a metallic royal purple Bull and an emerald green Bear amidst trading market clouds, no text"
    },
    # پیج روانشناسی تاریک
    "d_chal": {
        "title": "🔥 دوراهی شوالیه تاریک",
        "tag_fa": "چالش شوالیه",
        "visual": "A solitary dark knight in black steel armor standing before a gothic castle under a crimson blood moon, cinematic oil painting, no text"
    },
    "d_edu": {
        "title": "🦊 فریب و مکر (روباه نقاب‌دار)",
        "tag_fa": "روباه مکار",
        "visual": "An anthropomorphic cunning fox wearing an ornate Venetian mask in a dark foggy gothic forest, crimson reflections, no text"
    },
    "d_mar": {
        "title": "🐺 استقلال عاطفی (گرگ خاکستری)",
        "tag_fa": "گرگ تنها",
        "visual": "A magnificent grey wolf standing solitary on a misty cliff under starry dark crimson sky, chiaroscuro lighting, no text"
    },
    "d_opt": {
        "title": "🥀 اغواگری و جذابیت زنانه (بانوی مرموز)",
        "tag_fa": "راز کاریزما",
        "visual": "An enigmatic aristocratic gothic woman in an elegant velvet gown in a dark candlelit baroque hall, mysterious gaze, no text"
    },
    "d_sec": {
        "title": "🩸 نفوذ و هیپنوتیزم (کنت دراکولا)",
        "tag_fa": "زبان بدن دراکولا",
        "visual": "Aristocratic Count Dracula in a deep charcoal coat with crimson lining, intense hypnotic gaze, dark gothic atmosphere, no text"
    },
    # پیج هنر و دست‌سازه‌های پاپیه‌ماشه (کاملاً کاربردی، دکوراتیو و فروش‌محور)
    "art_mirror": {
        "title": "🪞 آینه موج‌دار وابی‌سابی (ترند دکور)",
        "tag_fa": "آینه ترند دکور",
        "visual": "A trendy organic wavy curved mirror frame made of textured cream paper mache hanging on a modern minimalist aesthetic wall, soft natural sunlight, luxury home decor photography, no text"
    },
    "art_decor": {
        "title": "🏺 ظروف و کاسه‌های دکوراتیو کنسول",
        "tag_fa": "اکسسوری مدرن",
        "visual": "A collection of handmade organic paper mache bowls and decorative plates in warm cream and terracotta tones displayed on a luxury oak console, editorial interior styling, no text"
    },
    "art_sculpture": {
        "title": "🗿 مجسمه فرم آزاد و مینیمال",
        "tag_fa": "مجسمه فرم آزاد",
        "visual": "A stunning abstract minimalist paper mache sculpture in warm neutral tones placed on a minimalist shelf, soft morning sunlight, architectural aesthetic, no text"
    },
    "behind": {
        "title": "📲 پشت صحنه سفارشات و بسته‌بندی",
        "tag_fa": "سفارش اختصاصی",
        "visual": "Artisan hands packaging a beautiful textured paper mache decor piece with linen paper and dried flowers in a warm sunlit art studio, cozy aesthetic, no text"
    },
}

FALLBACK_CONTENT = {
    "art_mirror": {
        "heading": "آینه موج‌دار ارگانیک؛ امضای دکور مدرن",
        "body": "چرا آینه‌های پاپیه‌ماشه ترند شدند؟ چون فرم نامتقارن و **بافت مات و دست‌ساز** آن، خطوط خشک و بی‌روح دیوارهای خانه را می‌شکند و حس آرامش می‌بخشد.",
        "sticker": "سفارش در ابعاد دلخواه دایرکت"
    },
    "art_decor": {
        "heading": "جلوه طبیعی خمیر روی میز کنسول",
        "body": "اکسسوری‌های دست‌ساز با رنگ **کرم شنی و وابی‌سابی**، بهترین انتخاب برای چیدمان روی کنسول و جزیره هستند. هر قطعه هویتی اصیل و تکرارنشدنی دارد.",
        "sticker": "ثبت سفارش اختصاصی دایرکت"
    },
    "art_sculpture": {
        "heading": "فرم‌های آزاد و سکوت در فضا",
        "body": "مجسمه‌های مینیمال پاپیه‌ماشه نگاه را جذب می‌کنند بدون اینکه فضا را شلوغ کنند. ترکیب **سبکی باورنکردنی کاغذ** با استحکامی شبیه به سنگ و سفال.",
        "sticker": "این مدل رو برای دکورت می‌پسندی؟"
    },
    "behind": {
        "heading": "از خمیر خام تا قطعه‌ای ماندگار",
        "body": "تمام آثار با **کاغذ بازیافتی و فرمول ضدترک** ساخته شده و با لایه‌ای ضدآب محافظت می‌شوند. امکان اجرا در رنگ‌بندی متناسب با پالت خانه شما.",
        "sticker": "مشاوره رایگان انتخاب رنگ دایرکت"
    },
    "t_quiz": {
        "heading": "دوراهی ورود در ناحیه تراکم",
        "body": "کندل تاییدیه بالای سطح کلیدی بسته شده اما حجم معاملات مشکوک است. آیا اینجا پوزیشن لانگ باز می‌کنی یا منتظر **پولبک مطمئن** می‌مانی؟",
        "sticker": "ورود الان یا صبر برای پولبک؟"
    },
    "t_psyc": {
        "heading": "تله انتقام از مارکت",
        "body": "بزرگ‌ترین ضررها بعد از یک معامله منفی و تلاش برای **جبران فوری** رخ می‌دهد. اگر استاپ خوردی چارت را ببند؛ بازار همیشه فرصت می‌دهد.",
        "sticker": "تا حالا دچار اورترید شدی؟"
    },
    "t_hunt": {
        "heading": "شکار حد ضرر خریداران هیجانی",
        "body": "بریک‌اوت‌های ناگهانی در ابتدای سشن معاملاتی معمولاً با هدف **جارو کردن استاپ‌ها** ایجاد می‌شوند. ورود در اولین شکست افتادن در دام مارکت‌میکر است.",
        "sticker": "قربانی استاپ‌هانت شدی؟"
    },
    "t_bull": {
        "heading": "نبرد نفس‌گیر در سنگر خریداران",
        "body": "گاوها در حال دفاع از کف معتبر هستند و خرس‌ها برای شکستن این حمایت تلاش می‌کنند. شکست این سطح به معنای **ریزش آبشاری** خواهد بود.",
        "sticker": "برنده این راند کیه؟"
    },
    "d_chal": {
        "heading": "دوراهی شوالیه در برابر خیانت",
        "body": "وقتی کسی اعتمادت را خدشه‌دار می‌کند، واکنش نشان دادن نشانه ضعف است. **سکوت سرد و حذف بی‌صدا** ضربه‌ای ویران‌کننده‌تر از هر بحثی وارد می‌کند.",
        "sticker": "پاسخ متقابل یا حذف دائمی؟"
    },
    "d_edu": {
        "heading": "نقاب لبخند روباه‌های مکار",
        "body": "کسانی که در ابتدای آشنایی فراتر از حد چاپلوسی می‌کنند، نقشه پنهانی در سر دارند. به **رفتار در بحران** اعتماد کن، نه کلمات شیرین در آرامش.",
        "sticker": "با آدم‌های نقاب‌دار چه می‌کنی؟"
    },
    "d_mar": {
        "heading": "مرزهای فولادین گرگ تنها",
        "body": "وابستگی روانی بزرگ‌ترین عامل شکست در روابط است. کسی که **تنهایی پر از آرامش** خودش را دوست دارد، هرگز تحت کنترل احساسی دیگران قرار نمی‌گیرد.",
        "sticker": "مرزهایت رو حفظ می‌کنی؟"
    },
    "d_opt": {
        "heading": "رمزگشایی از جاذبه تاریک",
        "body": "آدم‌ها جذب کسانی می‌شوند که پیش‌بینی‌ناپذیرند و برای جلب تایید تلاش نمی‌کنند. **استقلال و دست‌نیافتنی بودن** بالاترین سطح کاریزماست.",
        "sticker": "دست‌نیافتنی هستی یا در دسترس؟"
    },
    "d_sec": {
        "heading": "هیپنوتیزم با مردمک چشم",
        "body": "اگر می‌خواهی تسلط کلامی خود را حفظ کنی، بعد از گفتن نکته مهم **۳ ثانیه سکوت** کن و مستقیماً به چشمان طرف مقابل نگاه کن؛ سکوت تایید می‌آورد.",
        "sticker": "این تکنیک رو امتحان کردی؟"
    },
}


class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write("Vira Agency Bot is running live and active! 🚀".encode("utf-8"))

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):
        pass


def run_web_server():
    port = int(os.getenv("PORT", "10000"))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    log.info("Render Web Server bound on port %d", port)
    server.serve_forever()


class ViraTelegramBot:
    def __init__(self):
        self.cfg = AgencyConfig()
        self.db = AgencyDatabase(self.cfg.db_path)
        self.llm = LLMRouter(self.cfg, self.db)
        self.ceo = ViraOrchestrator(self.cfg, self.db, self.llm)

    def _main_menu(self) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🎨 تولید محتوا (انتخاب پیج)", callback_data="menu:select_page")],
            [InlineKeyboardButton("🪞 کالکشن ترند پاپیه‌ماشه (آینه و دکور)", callback_data="dept:papermache:idea_hub")],
            [InlineKeyboardButton("📈 نبض و تحلیل زنده کریپتو", callback_data="dept:trading:market_pulse")],
        ])

    def _page_selection_menu(self) -> InlineKeyboardMarkup:
        pages = self.db.get_pages(active_only=True)
        kb = [[InlineKeyboardButton(p["title"], callback_data=f"page_hub:{p['slug']}")] for p in pages]
        kb.append([InlineKeyboardButton("🔙 بازگشت", callback_data="menu:main")])
        return InlineKeyboardMarkup(kb)

    def _department_menu(self, page: dict) -> InlineKeyboardMarkup:
        slug = page["slug"]
        kb = [
            [
                InlineKeyboardButton("📲 ساخت استوری تخصصی", callback_data=f"act:{slug}:story"),
                InlineKeyboardButton("🖼️ ساخت کاروسل تصویری", callback_data=f"act:{slug}:carousel"),
            ],
            [InlineKeyboardButton("🎬 ریلز ۵ سکانسی", callback_data=f"act:{slug}:reel")],
        ]
        if slug == "papermache":
            kb.append([InlineKeyboardButton("🪞 معرفی محصولات ترند (آینه، ظروف، مجسمه)", callback_data="dept:papermache:idea_hub")])
            kb.append([InlineKeyboardButton("🛠️ فرمول‌های کارگاه (خمیر، ضدترک)", callback_data="dept:papermache:workshop_q")])
        kb.append([InlineKeyboardButton("🔙 تغییر پیج", callback_data="menu:select_page")])
        return InlineKeyboardMarkup(kb)

    def _story_cats_menu(self, page: dict) -> InlineKeyboardMarkup:
        slug = page["slug"]
        if slug == "trading":
            keys = ["t_market", "t_news", "t_quiz", "t_psyc", "t_hunt", "t_bull"]
        elif slug == "dark_psych":
            keys = ["d_chal", "d_edu", "d_mar", "d_opt", "d_sec"]
        else:
            keys = ["art_mirror", "art_decor", "art_sculpture", "behind"]

        kb = [[InlineKeyboardButton(STORY_CATS_CONFIG[k]["title"], callback_data=f"st_cat:{k}:{slug}")] for k in keys]
        kb.append([InlineKeyboardButton("🔙 بازگشت", callback_data=f"page_hub:{slug}")])
        return InlineKeyboardMarkup(kb)

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data.clear()
        await update.effective_message.reply_text(
            "سلام! من **«دستیار ویرا»** هستم ✨🤖\n"
            "آماده‌ام برای هر ۳ پیج با سبک‌های اختصاصی و محصولات ترند محتوا بسازم!",
            reply_markup=self._main_menu(),
            parse_mode="Markdown",
        )

    async def _build_single_story(self, page: dict, cat_key: str) -> tuple[str, str, str]:
        cat = STORY_CATS_CONFIG.get(cat_key, STORY_CATS_CONFIG["t_market"])
        slug = page["slug"]
        m = await get_live_market_summary() if slug == "trading" else {}

        if cat_key == "t_market":
            heading = f"تحلیل بیت‌کوین در {m.get('price')}$"
            body = (
                f"بیت‌کوین در ۲۴ ساعت اخیر با نوسان **{m.get('change')}** در وضعیت **{m.get('trend')}** قرار دارد. "
                f"حمایت معتبر روی **${m.get('support')}** و مقاومت کلیدی روی **${m.get('resistance')}** است؛ "
                f"ورود مطمئن صرفاً با شکست این سقف یا پولبک به کف تایید می‌شود."
            )
            sticker = "خرید در کف یا شکست سقف؟"

        elif cat_key == "t_news":
            heading = "رویدادهای داغ بازار کریپتو"
            body = m.get("news")
            sticker = "بازار پامپ میشه یا دامپ؟"

        else:
            fb = FALLBACK_CONTENT.get(cat_key, {
                "heading": cat["tag_fa"],
                "body": "محتوای تخصصی و کاربردی برای ارتقای پیج.",
                "sticker": "نظرت رو بنویس"
            })

            prompt = (
                f"به عنوان کارشناس ارشد محتوا برای پیج «{page['title']}»، یک استوری در سبک «{cat['title']}» بساز.\n"
                "کلمات کلیدی مهم را بین دو ستاره مانند **کلمه** بگذار تا هایلایت شوند.\n"
                'تنها یک شیء JSON استاندارد فارسی با این کلیدها تولید کن:\n'
                '{"heading": "تیتر جذاب فارسی ۳ تا ۵ کلمه", "body": "متن تخصصی و کاربردی فارسی در ۲ الی ۳ جمله", "sticker": "دعوت به اقدام کوتاه"}'
            )
            ai_data = await self.llm.json(prompt, temperature=0.7)

            heading = str(ai_data.get("heading") or fb["heading"]).strip()
            body = str(ai_data.get("body") or fb["body"]).strip()
            sticker = str(ai_data.get("sticker") or fb["sticker"]).strip()

        out_dir = f"data/outputs/{page['id']}/story_{int(time.time())}"
        os.makedirs(out_dir, exist_ok=True)

        art_path = os.path.join(out_dir, "art.jpg")
        img_ok = await self.llm.generate_image(cat["visual"], art_path)

        out_path = os.path.join(out_dir, "story_final.jpg")
        story_obj = {"heading": heading, "body": body, "sticker": sticker}
        render_story(None, story_obj, out_path, 0, [], None, cat_key, art_path if img_ok else None)

        return out_path, heading, body

    async def on_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        q = update.callback_query
        await q.answer()
        data = q.data or ""

        if data == "menu:main":
            await q.edit_message_text("🏢 **منوی اصلی دستیار ویرا**", reply_markup=self._main_menu(), parse_mode="Markdown")
        elif data == "menu:select_page":
            await q.edit_message_text("🎯 برای کدام پیج می‌خواهی محتوا بسازی؟", reply_markup=self._page_selection_menu())
        elif data.startswith("page_hub:"):
            slug = data.split(":")[1]
            page = self.db.get_page_by_slug(slug)
            if page:
                await q.edit_message_text(
                    f"✨ **پیج: {page['title']}**\nچه نوع محتوایی می‌خواهی تولید کنی؟",
                    reply_markup=self._department_menu(page),
                    parse_mode="Markdown",
                )
        elif data.startswith("act:"):
            _, slug, kind = data.split(":")
            page = self.db.get_page_by_slug(slug)
            if page:
                if kind == "story":
                    await q.edit_message_text(
                        f"📲 **انتخاب سبک استوری برای «{page['title']}»:**",
                        reply_markup=self._story_cats_menu(page),
                        parse_mode="Markdown",
                    )
                else:
                    context.user_data["vira_task"] = {"slug": slug, "kind": kind}
                    label = "کاروسل تصویری" if kind == "carousel" else "ریلز ۵ سکانسی"
                    await q.edit_message_text(f"✍️ موضوع دلخواهت را برای ساخت «{label}» بنویس:")

        elif data.startswith("st_cat:"):
            _, cat_key, slug = data.split(":")
            page = self.db.get_page_by_slug(slug)
            if page:
                await q.edit_message_text(f"⏳ دستیار ویرا در حال آماده‌سازی و رندر استوری برای «{page['title']}»...")
                out_path, heading, body = await self._build_single_story(page, cat_key)
                self.db.save_content(page["id"], "story", heading, {"body": body, "file": out_path})

                clean_caption = f"✅ {heading}\n\n{body}".replace("*", "").replace("_", "")[:950]
                with open(out_path, "rb") as photo_file:
                    await q.message.reply_photo(
                        photo=photo_file,
                        caption=clean_caption,
                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت به پیج", callback_data=f"page_hub:{slug}")]])
                    )

        elif data == "dept:trading:market_pulse":
            await q.edit_message_text("⏳ در حال استعلام آخرین داده‌های قیمت و اخبار زنده کریپتو...")
            m = await get_live_market_summary()
            msg_text = (
                f"📊 **نبض لحظه‌ای مارکت بیت‌کوین:**\n\n"
                f"💵 قیمت لحظه‌ای: **${m.get('price')}**\n"
                f"📈 نوسان ۲۴ساعته: **{m.get('change')}**\n"
                f"🔍 وضعیت بازار: **{m.get('trend')}**\n"
                f"🛡️ حمایت معتبر: **${m.get('support')}**\n"
                f"🎯 مقاومت کلیدی: **${m.get('resistance')}**\n\n"
                f"📰 **رویدادهای داغ:**\n{m.get('news')}"
            )
            await q.message.reply_text(msg_text, reply_markup=self._main_menu(), parse_mode="Markdown")

        elif data == "dept:papermache:idea_hub":
            kb = [
                [InlineKeyboardButton("🪞 آینه موج‌دار وابی‌سابی", callback_data="st_cat:art_mirror:papermache")],
                [InlineKeyboardButton("🏺 ظروف دکوراتیو و کنسول", callback_data="st_cat:art_decor:papermache")],
                [InlineKeyboardButton("🗿 مجسمه فرم آزاد و مینیمال", callback_data="st_cat:art_sculpture:papermache")],
                [InlineKeyboardButton("📲 پشت صحنه و بسته‌بندی", callback_data="st_cat:behind:papermache")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="menu:main")],
            ]
            await q.edit_message_text("🎨 **کالکشن محصولات ترند و فروش‌محور پاپیه‌ماشه**", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

        elif data == "dept:papermache:workshop_q":
            context.user_data["vira_task"] = {"slug": "papermache", "kind": "workshop"}
            await q.edit_message_text("🛠️ سوالت را درباره ساخت خمیر، چسب یا فرمول ضدترک بنویس:")

    async def on_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        msg = update.effective_message
        user_text = (msg.text or "").strip()
        active_task = context.user_data.get("vira_task")

        if active_task:
            context.user_data.pop("vira_task", None)
            slug = active_task.get("slug", "trading")
            page = self.db.get_page_by_slug(slug)

            wait = await msg.reply_text("⏳ در حال آماده‌سازی پاسخ تخصصی...")
            ans = await self.llm.generate_text(
                f"به عنوان مشاور ارشد برای پیج «{page['title']}» به این سوال پاسخ کامل و کاربردی بده: {user_text}",
                VIRA_SYSTEM_IDENTITY,
                slug,
            )
            await wait.delete()
            await msg.reply_text(ans, reply_markup=self._department_menu(page))
            return

        wait = await msg.reply_text("🤔 ...")
        reply = await self.ceo.chat_with_vira(user_text)
        await wait.delete()
        await msg.reply_text(reply, reply_markup=self._main_menu())

    def run(self):
        t_web = threading.Thread(target=run_web_server, daemon=True)
        t_web.start()

        app = Application.builder().token(self.cfg.telegram_token).build()
        app.add_handler(CommandHandler("start", self.cmd_start))
        app.add_handler(CallbackQueryHandler(self.on_callback))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.on_text_message))
        log.info("Vira AI Agency Bot started successfully!")
        app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    ViraTelegramBot().run()