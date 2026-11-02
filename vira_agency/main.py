```python
"""
ربات تلگرام آژانس هوشمند «دستیار ویرا»
متصل به واحد تحلیل زنده بازار کریپتو و سیستم رندر گرافیکی استوری، کاروسل و ریلز
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
        "desc": "با توجه به قیمت و تغییرات لحظه‌ای بازار، یک تحلیل صریح درباره محدوده نقدینگی، حمایت و مقاومت و استراتژی ورود بنویس.",
        "visual": "Professional trader in a dark cybernetic room glowing with deep royal purple and neon emerald candlestick charts on multiple screens, cinematic 8k, no text"
    },
    "t_news": {
        "title": "📰 اخبار زنده فارکس و کریپتو",
        "desc": "یک خبر داغ و اضطراری از نوسانات لحظه‌ای و تحرکات نهنگ‌های مارکت بنویس.",
        "visual": "Illuminated financial news terminal in a royal purple glowing room with volatile neon market data feeds, cyberpunk style, no text"
    },
    "t_quiz": {
        "title": "⚡ کوییز تریدری (اینجا وارد شویم؟)",
        "desc": "یک دوراهی چالش‌برانگیز بین ورود به پوزیشن یا صبر کردن به همراه دلیل تکنیکال طرح کن.",
        "visual": "Close-up of a complex breakout trading chart glowing in vibrant royal purple and neon green, dramatic lighting, no text"
    },
    "t_psyc": {
        "title": "🧠 روانشناسی ترید و کنترل طمع",
        "desc": "یک هشدار روانشناسی ترید برای جلوگیری از طمع، اورترید (Overtrading) و انتقام از مارکت بنویس.",
        "visual": "A disciplined trader sitting calmly in front of neon purple charts with a glowing golden aura of focus, cinematic art, no text"
    },
    "t_hunt": {
        "title": "🎯 هشدار تله نقدینگی و استاپ‌هانت",
        "desc": "توضیح بده که چطور مارکت‌میکرها قبل از حرکت اصلی، حد ضررهای خریداران و فروشندگان هیجانی را جارو می‌کنند.",
        "visual": "Glowing cybernetic liquidity trap catching retail positions on a futuristic royal purple holographic trading chart, no text"
    },
    "t_bull": {
        "title": "🐂 نبرد حماسی گاو و خرس",
        "desc": "روایت جنگ خریداران و فروشندگان در سنگر قیمتی امروز با لحنی پرهیجان و تحلیلی.",
        "visual": "Epic clash of a glowing royal purple metallic Bull and an emerald green Bear amidst stormy trading charts, 8k masterpiece, no text"
    },
    # پیج روانشناسی تاریک
    "d_chal": {
        "title": "🔥 چالشی و دو راهی اخلاقی (شوالیه)",
        "desc": "یک دوراهی اخلاقی و چالش رفتاری عمیق درباره قدرت، سکوت یا انتقام طراحی کن.",
        "visual": "A solitary dark knight standing before a gloomy gothic castle under a crimson blood moon, dark oil painting masterpiece, no text"
    },
    "d_edu": {
        "title": "🧠 پند رابطه و روباه مکار",
        "desc": "ترفندی عمیق برای تشخیص لبخندهای فریبنده و رفتارهای چاپلوسانه در روابط کاری و شخصی بنویس.",
        "visual": "A cunning fox wearing a mysterious theatrical mask in a shadowy forest, dark gothic oil painting with crimson shadows, no text"
    },
    "d_mar": {
        "title": "💍 رازهای تاریک روابط (گرگ)",
        "desc": "روشی قاطع برای حفظ استقلال عاطفی و نشکستن حریم شخصی در برابر افراد کنترل‌گر بنویس.",
        "visual": "A majestic grey wolf standing alone on a snowy cliff under starry night, dark gothic oil painting, chiaroscuro lighting, no text"
    },
    "d_opt": {
        "title": "🎭 تست شخصیت (مسیر تاریک)",
        "desc": "یک تست روانشناسی دوراهی: وفاداری خطرناک یا هوشمندی بی‌رحمانه؟",
        "visual": "Two distinct symbolic paths diverging in a dark gothic forest leading to a glowing crimson castle, dark oil painting, no text"
    },
    "d_sec": {
        "title": "🩸 راز زبان بدن (کنت دراکولا)",
        "desc": "رمزگشایی از جهت مردمک چشم و مکث در کلام برای کشف افکار واقعی طرف مقابل.",
        "visual": "Aristocratic Count Dracula in a deep charcoal coat with crimson lining staring intensely, dark gothic oil painting, no text"
    },
    # پیج پاپیه‌ماشه
    "behind": {
        "title": "📲 استوری فروش و پشت صحنه",
        "desc": "روایتی گرم و جذاب از حس لطیف ساخت اثر با دست و دعوت به ثبت سفارش اختصاصی.",
        "visual": "Artisan hands sculpting a minimalist paper mache sculpture in a sunlit warm studio, cream and terracotta tones, no text"
    },
    "showcase": {
        "title": "🖼️ معرفی اثر جدید و جزئیات دکور",
        "desc": "توصیف حس آرامش و بافت ارگانیک مجسمه در هماهنگی با چیدمان خانه مدرن.",
        "visual": "Minimalist luxury home decor shelf with a textured handmade paper mache sculpture, warm morning sunlight, cream palette, no text"
    },
    "workshop": {
        "title": "🛠️ آموزش تکنیک خمیر و چسب",
        "desc": "نکته‌ای طلایی درباره مقاومت سازه، جلوگیری از ترک و سنباده‌زنی بی‌نقص.",
        "visual": "Close-up of artistic paper mache clay texture and wooden sculpting tools on a warm linen table, natural lighting, no text"
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
    log.info("Render Web Server bound and listening on 0.0.0.0:%d", port)
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
            [InlineKeyboardButton("💡 ایده‌پرداز و کارگاه پاپیه‌ماشه", callback_data="dept:papermache:idea_hub")],
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
            kb.append([InlineKeyboardButton("💡 ایده‌پرداز ترند پاپیه‌ماشه", callback_data="dept:papermache:idea_hub")])
            kb.append([InlineKeyboardButton("🛠️ مشاور کارگاه (خمیر، چسب، رنگ)", callback_data="dept:papermache:workshop_q")])
        kb.append([InlineKeyboardButton("🔙 تغییر پیج", callback_data="menu:select_page")])
        return InlineKeyboardMarkup(kb)

    def _story_cats_menu(self, page: dict) -> InlineKeyboardMarkup:
        slug = page["slug"]
        if slug == "trading":
            keys = ["t_market", "t_news", "t_quiz", "t_psyc", "t_hunt", "t_bull"]
        elif slug == "dark_psych":
            keys = ["d_chal", "d_edu", "d_mar", "d_opt", "d_sec"]
        else:
            keys = ["behind", "showcase", "workshop"]

        kb = [[InlineKeyboardButton(STORY_CATS_CONFIG[k]["title"], callback_data=f"st_cat:{k}:{slug}")] for k in keys]
        kb.append([InlineKeyboardButton("🔙 بازگشت", callback_data=f"page_hub:{slug}")])
        return InlineKeyboardMarkup(kb)

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data.clear()
        await update.effective_message.reply_text(
            "سلام! من **«دستیار ویرا»** هستم ✨🤖\n"
            "آماده‌ام تا برای هر ۳ پیج تو محتوای گرافیکی و تحلیلی درجه یک بسازم!",
            reply_markup=self._main_menu(),
            parse_mode="Markdown",
        )

    async def _build_single_story(self, page: dict, cat_key: str) -> tuple[str, str, str]:
        cat = STORY_CATS_CONFIG.get(cat_key, STORY_CATS_CONFIG["t_market"])
        slug = page["slug"]

        market_info = ""
        if slug == "trading":
            market_info = await get_live_market_summary()

        prompt = (
            f"تو کارشناس ارشد محتوا برای پیج «{page['title']}» هستی.\n"
            f"سبک استوری: {cat['title']}\n"
            f"دستور کار: {cat['desc']}\n"
            f"{market_info}\n"
            "مهم‌ترین قانون: فقط و فقط یک فرمت JSON معتبر فارسی شامل موارد زیر تولید کن. هیچ کلمه انگلیسی یا دستور تکراری ننویس:\n"
            '{"heading": "تیتر جذاب فارسی حداکثر ۵ کلمه", "body": "متن تخصصی و صریح فارسی در ۲ الی ۳ جمله", "sticker": "سوال تعاملی کوتاه"}'
        )

        story_data = await self.llm.json(prompt, temperature=0.7)
        heading = str(story_data.get("heading") or "").strip()
        body = str(story_data.get("body") or "").strip()
        sticker = str(story_data.get("sticker") or "تحلیل تو چیه؟").strip()

        # فیلتر امنیتی: اگر به هر دلیلی متن هنوز حاوی عبارات انگلیسی مدل بود، جایگزینی هوشمند فارسی
        if not body or "Professional Persian" in body or len(body) < 15:
            if slug == "trading":
                heading = "نوسان شدید در محدوده نقدینگی"
                body = "بیت‌کوین در تلاش برای شکست مقاومت کلیدی است. مراقب تله‌های نقدینگی و ورودهای هیجانی در سقف باشید؛ تاییدیه کندلی شرط اول معامله است."
                sticker = "لانگ می‌گیری یا شورت؟"
            elif slug == "dark_psych":
                heading = "سکوت؛ قوی‌ترین سلاح اقتدار"
                body = "کسی که تمام برگ‌های برنده‌اش را در مکالمه اول رو می‌کند، پیش از آغاز بازی مات شده است. رازهایت را حتی در صمیمی‌ترین جمع‌ها فاش نکن."
                sticker = "موافقی با این استراتژی؟"
            else:
                heading = "هنر خلق روح در کاغذ و آب"
                body = "هر مجسمه سفری است از تکه‌های باطله تا فرمی ماندگار بر روی میز شما. اصالت دست‌ساز تکرارناپذیر است."
                sticker = "سفارش یا آموزش؟"

        out_dir = f"data/outputs/{page['id']}/story_{int(time.time())}"
        os.makedirs(out_dir, exist_ok=True)

        art_path = os.path.join(out_dir, "art.jpg")
        img_ok = await self.llm.generate_image(cat["visual"], art_path)

        out_path = os.path.join(out_dir, "story_final.jpg")
        story_obj = {"heading": heading, "body": body, "sticker": sticker}
        render_story(None, story_obj, out_path, 0, [], None, cat_key, art_path if img_ok else None)

        return out_path, heading, body

    async def _build_carousel(self, page: dict, topic: str) -> tuple[list[str], str]:
        slug = page["slug"]
        market_info = await get_live_market_summary() if slug == "trading" else ""
        prompt = (
            f"برای پیج «{page['title']}» درباره «{topic}» یک کاروسل ۴ اسلایدی فارسی بساز.\n"
            f"{market_info}\n"
            "فقط JSON استاندارد:\n"
            '{"slides": [{"heading": "تیتر فارسی", "body": "متن فارسی", "visual": "English visual prompt"}], "caption": "کپشن کامل فارسی با هشتگ"}'
        )
        data = await self.llm.json(prompt, temperature=0.7)
        slides = data.get("slides") or [
            {"heading": topic, "body": "بررسی مهم‌ترین زوایای این موضوع و نکات کلیدی برای پیاده‌سازی.", "visual": "cinematic conceptual 8k art, no text"}
        ]
        caption = str(data.get("caption") or f"✨ کاروسل تخصصی: {topic}")

        out_dir = f"data/outputs/{page['id']}/carousel_{int(time.time())}"
        os.makedirs(out_dir, exist_ok=True)

        arts = []
        for i, s in enumerate(slides[:5]):
            art_file = os.path.join(out_dir, f"art_{i}.jpg")
            v_prompt = s.get("visual") or "cinematic digital art masterpiece, no text"
            ok = await self.llm.generate_image(v_prompt, art_file)
            arts.append(art_file if ok else None)

        files = await asyncio.to_thread(render_carousel, None, slides[:5], out_dir, [], None, arts, slug)
        return files, caption

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
                    await q.edit_message_text(f"✍️ موضوع دلخواهت رو برای ساخت «{label}» بنویس:")

        elif data.startswith("st_cat:"):
            _, cat_key, slug = data.split(":")
            page = self.db.get_page_by_slug(slug)
            if page:
                await q.edit_message_text(f"⏳ دستیار ویرا در حال رصد بازار، تصویرسازی و ساخت استوری برای «{page['title']}»...")
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
            summary = await get_live_market_summary()
            ans = await self.llm.generate_text(
                f"با توجه به این داده‌های زنده بازار:\n{summary}\nیک گزارش کوتاه، جذاب، حرفه‌ای و کاربردی با لحن قاطع تریدری برای استوری یا کپشن تلگرام بنویس.",
                VIRA_SYSTEM_IDENTITY,
                "trading",
            )
            msg_text = f"📊 **نبض لحظه‌ای مارکت:**\n\n{summary}\n\n💡 **تحلیل دستیار ویرا:**\n{ans}"
            await q.message.reply_text(msg_text, reply_markup=self._main_menu())

        elif data == "dept:papermache:idea_hub":
            kb = [
                [InlineKeyboardButton("📲 ایده استوری فروش و تعامل", callback_data="art_idea:story")],
                [InlineKeyboardButton("🖼️ ایده کاروسل دکور و معرفی اثر", callback_data="art_idea:carousel")],
                [InlineKeyboardButton("🎬 ایده ریلز قبل و بعد ساخت", callback_data="art_idea:reel")],
                [InlineKeyboardButton("🛠️ مشاوره کارگاه پاپیه‌ماشه", callback_data="dept:papermache:workshop_q")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="menu:main")],
            ]
            await q.edit_message_text("🎨 **ایده‌پرداز تخصصی پاپیه‌ماشه**", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

        elif data.startswith("art_idea:"):
            kind = data.split(":")[1]
            await q.edit_message_text("⏳ دستیار ویرا در حال ایده‌پردازی...")
            ans = await self.llm.generate_text(
                f"۵ ایده جذاب، جدید و فروش‌محور {kind} به زبان فارسی برای پیج مجسمه‌های دست‌ساز پاپیه‌ماشه بنویس.",
                VIRA_SYSTEM_IDENTITY,
                "Art",
            )
            await q.message.reply_text(
                ans,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="dept:papermache:idea_hub")]]),
            )
        elif data == "dept:papermache:workshop_q":
            context.user_data["vira_task"] = {"slug": "papermache", "kind": "workshop"}
            await q.edit_message_text("🛠️ سوالت رو درباره ساخت خمیر، چسب چوب، سمباده یا رنگ‌آمیزی پاپیه‌ماشه بنویس:")

    async def on_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        msg = update.effective_message
        user_text = (msg.text or "").strip()
        active_task = context.user_data.get("vira_task")

        if active_task:
            context.user_data.pop("vira_task", None)
            slug = active_task.get("slug", "trading")
            kind = active_task.get("kind", "carousel")
            page = self.db.get_page_by_slug(slug)

            if kind == "carousel":
                wait = await msg.reply_text(f"⏳ در حال ساخت تصاویر هوش مصنوعی و طراحی کاروسل برای «{user_text}»...")
                files, caption = await self._build_carousel(page, user_text)
                await wait.delete()
                for fpath in files:
                    with open(fpath, "rb") as ph:
                        await msg.reply_photo(photo=ph)
                await msg.reply_text(caption[:950], reply_markup=self._department_menu(page))
                return

            else:
                wait = await msg.reply_text("⏳ در حال آماده‌سازی پاسخ تخصصی...")
                ans = await self.llm.generate_text(
                    f"به عنوان مشاور متخصص برای پیج {page['title']} به این سوال یا موضوع پاسخ کامل فارسی بده: {user_text}",
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
```