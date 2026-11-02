"""
ربات تلگرام آژانس هوشمند «دستیار ویرا»
ارائه‌دهنده تحلیل‌های واقعی با اعداد لحظه‌ای بازار کریپتو و عناوین ۱۰۰٪ فارسی
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
    # ترید
    "t_market": {
        "title": "📈 تحلیل بازار و وضعیت بیت‌کوین",
        "tag_fa": "تحلیل بازار",
        "visual": "Professional crypto trader in a dark cybernetic command center with illuminated royal purple and neon emerald charts, cinematic 8k, no text"
    },
    "t_news": {
        "title": "📰 اخبار داغ و رویدادهای زنده",
        "tag_fa": "اخبار داغ",
        "visual": "Futuristic neon media room displaying breaking economic and cryptocurrency data with glowing royal purple screens, no text"
    },
    "t_quiz": {
        "title": "⚡ کوییز تریدری (اینجا وارد شویم؟)",
        "tag_fa": "کوییز تریدری",
        "visual": "Close-up of a complex breakout trading chart glowing in vibrant royal purple and neon green, dramatic lighting, no text"
    },
    "t_psyc": {
        "title": "🧠 روانشناسی ترید و کنترل طمع",
        "tag_fa": "روانشناسی ترید",
        "visual": "A disciplined trader sitting calmly in front of neon purple charts with a glowing golden aura of focus, cinematic art, no text"
    },
    "t_hunt": {
        "title": "🎯 هشدار تله نقدینگی و استاپ‌هانت",
        "tag_fa": "شکار استاپ",
        "visual": "Glowing cybernetic liquidity trap catching retail positions on a futuristic royal purple holographic trading chart, no text"
    },
    "t_bull": {
        "title": "🐂 نبرد حماسی گاو و خرس",
        "tag_fa": "نبرد گاو و خرس",
        "visual": "Epic clash of a glowing royal purple metallic Bull and an emerald green Bear amidst stormy trading charts, 8k masterpiece, no text"
    },

    # روانشناسی تاریک (تطابق کامل شخصیت‌ها با متن)
    "d_chal": {
        "title": "🔥 دوراهی شوالیه تاریک",
        "tag_fa": "چالش شوالیه",
        "visual": "A solitary dark knight with ornate black armor standing before a gloomy gothic castle under a crimson blood moon, cinematic lighting, no text"
    },
    "d_edu": {
        "title": "🦊 فریب و مکر (روباه نقاب‌دار)",
        "tag_fa": "روباه مکار",
        "visual": "A cunning anthropomorphic fox wearing an ornate Venetian mask in a misty gothic street, crimson shadows, dark oil painting, no text"
    },
    "d_mar": {
        "title": "🐺 استقلال عاطفی (گرگ خاکستری)",
        "tag_fa": "گرگ تنها",
        "visual": "A majestic silver-grey wolf standing proud on a rocky cliff under a glowing crimson moon, cinematic chiaroscuro, no text"
    },
    "d_opt": {
        "title": "🥀 اغواگری و جذابیت زنانه (بانوی مرموز)",
        "tag_fa": "راز کاریزما",
        "visual": "A breathtaking seductive aristocratic gothic woman in an elegant velvet gown, mysterious captivating eyes, dark baroque chamber, no text"
    },
    "d_sec": {
        "title": "🩸 نفوذ و هیپنوتیزم (کنت دراکولا)",
        "tag_fa": "زبان بدن دراکولا",
        "visual": "Aristocratic Count Dracula in a charcoal tailored coat with crimson lining staring intensely with piercing hypnotic gaze, dark gothic art, no text"
    },

    # هنر و پاپیه‌ماشه
    "behind": {
        "title": "📲 استوری فروش و پشت صحنه",
        "tag_fa": "پشت صحنه",
        "visual": "Artisan hands sculpting a minimalist paper mache sculpture in a sunlit warm studio, cream and terracotta tones, no text"
    },
    "showcase": {
        "title": "🖼️ معرفی اثر جدید و جزئیات دکور",
        "tag_fa": "معرفی اثر",
        "visual": "Minimalist luxury home decor shelf with a textured handmade paper mache sculpture, warm morning sunlight, cream palette, no text"
    },
    "workshop": {
        "title": "🛠️ آموزش تکنیک خمیر و چسب",
        "tag_fa": "نکته کارگاه",
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

        m = await get_live_market_summary() if slug == "trading" else {}

        if cat_key == "t_market":
            heading = f"تحلیل بیت‌کوین در {m.get('price', '67,000')}$"
            body = (
                f"بیت‌کوین در ۲۴ ساعت اخیر با نوسان {m.get('change', '0%')} در وضعیت {m.get('trend')} قرار دارد. "
                f"حمایت معتبر روی ${m.get('support')} و مقاومت کلیدی روی ${m.get('resistance')} است؛ "
                f"ورود مطمئن صرفاً با شکست این سقف یا پولبک به کف تایید می‌شود."
            )
            sticker = "خرید در کف یا شکست سقف؟"

        elif cat_key == "t_news":
            heading = "رویدادهای داغ بازار کریپتو"
            body = m.get("news") or "• تثبیت قیمت در کانال معاملاتی\n• رصد پوزیشن‌های باز فیوچرز"
            sticker = "بازار پامپ میشه یا دامپ؟"

        elif slug == "dark_psych":
            char_map = {
                "d_chal": "شوالیه تاریک و جنگجوی درون در مواجهه با دوراهی‌ها",
                "d_edu": "روباه مکار و نقاب‌دار و شناخت مکر و فریب در روابط",
                "d_mar": "گرگ خاکستری و حفظ حریم شخصی و استقلال عاطفی",
                "d_opt": "بانوی مرموز و جذاب و قوانین کاریزمای کشنده و تسلط حسی",
                "d_sec": "کنت دراکولا و هیپنوتیزم کلامی و نفوذ با زبان بدن"
            }
            subject = char_map.get(cat_key, "روانشناسی تاریک")
            prompt = (
                f"یک استوری جذاب و تأثیرگذار روانشناسی تاریک به زبان فارسی درباره: «{subject}» بنویس.\n"
                "متن باید کاملاً هماهنگ با این کاراکتر باشد. کلمات کلیدی را بین **کلمه** بگذار.\n"
                'فقط ساختار JSON: {"heading": "تیتر عمیق و جذاب", "body": "متن اصلی فارسی در ۲ الی ۳ جمله", "sticker": "سوال نظرسنجی"}'
            )
            data = await self.llm.json(prompt, temperature=0.7)
            heading = str(data.get("heading") or cat["tag_fa"])
            body = str(data.get("body") or "کسی که در اوج آرامش سکوت می‌کند، کنترل تمام بازی را به دست گرفته است.")
            sticker = str(data.get("sticker") or "موافقی؟")

        elif slug == "papermache":
            prompt = (
                f"یک استوری هنری، گرم و صمیمی فارسی برای پیج مجسمه‌سازی پاپیه‌ماشه در سبک «{cat['title']}» بساز.\n"
                "کلمات کلیدی را بین **کلمه** بگذار.\n"
                'فقط JSON: {"heading": "تیتر هنری", "body": "متن دلنشین درباره خمیر، بافت یا مجسمه", "sticker": "سوال تعاملی"}'
            )
            data = await self.llm.json(prompt, temperature=0.7)
            heading = str(data.get("heading") or cat["tag_fa"])
            body = str(data.get("body") or "هر فرم مجسمه، تبلور دست‌هایی است که به کاغذهای باطله جان دوباره می‌بخشند.")
            sticker = str(data.get("sticker") or "نظر تو چیه؟")

        else:
            prompt = (
                f"یک استوری ترید کوتاه فارسی در سبک {cat['title']} بر اساس بیت‌کوین ${m.get('price')} بساز.\n"
                'فقط JSON: {"heading": "تیتر فارسی", "body": "متن تریدری فارسی", "sticker": "سوال"}'
            )
            data = await self.llm.json(prompt, temperature=0.7)
            heading = str(data.get("heading") or cat["tag_fa"])
            body = str(data.get("body") or f"بیت‌کوین در محدوده ${m.get('price')} در حال نوسان است.")
            sticker = str(data.get("sticker") or "تحلیل تو چیه؟")

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
                    await q.edit_message_text(f"✍️ موضوع دلخواهت رو برای ساخت «{label}» بنویس:")

        elif data.startswith("st_cat:"):
            _, cat_key, slug = data.split(":")
            page = self.db.get_page_by_slug(slug)
            if page:
                await q.edit_message_text(f"⏳ دستیار ویرا در حال استعلام داده‌های زنده و ساخت استوری برای «{page['title']}»...")
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
                f"📰 **اخبار و رویدادها:**\n{m.get('news')}"
            )
            await q.message.reply_text(msg_text, reply_markup=self._main_menu(), parse_mode="Markdown")

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
            page = self.db.get_page_by_slug(slug)

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