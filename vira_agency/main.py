"""
ربات تلگرام آژانس هوشمند «دستیار ویرا»
توسعه‌دهنده: حسین داودیان
متصل به موتور گرافیکی رندر تصویر و استوری
"""
import logging
import os
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

from vira_agency.core.config import AgencyConfig, VIRA_SYSTEM_IDENTITY
from vira_agency.core.database import AgencyDatabase
from vira_agency.core.llm_router import LLMRouter
from vira_agency.core.orchestrator import ViraOrchestrator
from vira_agency.core.render import render_story

logging.basicConfig(format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", level=logging.INFO)
log = logging.getLogger("vira_agency")


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
            [InlineKeyboardButton("📈 نبض و تحلیل بازار ترید", callback_data="dept:trading:market_pulse")],
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
                InlineKeyboardButton("📲 ساخت استوری گرافیکی", callback_data=f"act:{slug}:story"),
                InlineKeyboardButton("🖼️ ساخت کاروسل", callback_data=f"act:{slug}:carousel"),
            ],
            [InlineKeyboardButton("🎬 ریلز ۵ سکانسی", callback_data=f"act:{slug}:reel")],
        ]
        if slug == "papermache":
            kb.append([InlineKeyboardButton("💡 ایده‌پرداز ترند پاپیه‌ماشه", callback_data="dept:papermache:idea_hub")])
            kb.append([InlineKeyboardButton("🛠️ مشاور کارگاه", callback_data="dept:papermache:workshop_q")])
        kb.append([InlineKeyboardButton("🔙 تغییر پیج", callback_data="menu:select_page")])
        return InlineKeyboardMarkup(kb)

    def _story_cats_menu(self, page: dict) -> InlineKeyboardMarkup:
        slug = page["slug"]
        if slug == "trading":
            cats = [
                ("📈 تحلیل بازار و وضعیت بیت‌کوین", "t_market"),
                ("📰 اخبار زنده فارکس و کریپتو", "t_news"),
                ("⚡ کوییز تریدری", "t_quiz"),
                ("🧠 روانشناسی ترید و طمع", "t_psyc"),
            ]
        elif slug == "dark_psych":
            cats = [
                ("🔥 دو راهی اخلاقی (شوالیه)", "d_chal"),
                ("🧠 پند رابطه (روباه مکار)", "d_edu"),
                ("💍 رازهای تاریک (گرگ)", "d_mar"),
                ("🩸 زبان بدن (کنت دراکولا)", "d_sec"),
            ]
        else:
            cats = [
                ("📲 ایده پشت صحنه و فروش", "behind"),
                ("🖼️ معرفی اثر جدید دکور", "showcase"),
                ("🛠️ آموزش خمیر و چسب", "workshop"),
            ]

        kb = [[InlineKeyboardButton(label, callback_data=f"st_cat:{key}:{slug}")] for label, key in cats]
        kb.append([InlineKeyboardButton("🔙 بازگشت", callback_data=f"page_hub:{slug}")])
        return InlineKeyboardMarkup(kb)

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data.clear()
        await update.effective_message.reply_text(
            "سلام! من **«دستیار ویرا»** هستم ✨🤖\n"
            "آماده‌ام تا استوری‌های گرافیکی بی‌نقص برای پیج‌های تو بسازم!",
            reply_markup=self._main_menu(),
            parse_mode="Markdown",
        )

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
                        f"📲 **انتخاب سبک استوری گرافیکی برای «{page['title']}»:**",
                        reply_markup=self._story_cats_menu(page),
                        parse_mode="Markdown",
                    )
                else:
                    context.user_data["vira_task"] = {"slug": slug, "kind": kind}
                    await q.edit_message_text(f"✍️ موضوع دلخواه خود را برای ساخت *{kind}* بنویسید:")
        elif data.startswith("st_cat:"):
            _, cat_key, slug = data.split(":")
            page = self.db.get_page_by_slug(slug)
            if page:
                await q.edit_message_text(f"⏳ دستیار ویرا در حال رندر گرافیکی استوری برای پیج «{page['title']}»...")
                
                # تولید محتوای کوتاه و ساختاریافته برای استوری
                prompt = f"یک تیتر کوبنده و متن کوتاه استوری در سبک {cat_key} برای پیج {page['title']} در قالب JSON با کلیدهای heading و body بنویس."
                raw_text = await self.llm.generate_text(prompt, VIRA_SYSTEM_IDENTITY, slug, temperature=0.7)
                
                heading = "تحلیل روز بازار"
                body = raw_text[:200] if raw_text else "محتوای استوری تخصصی"

                # رندر گرافیکی استوری
                out_dir = f"data/outputs/{page['id']}/story_{int(time.time())}"
                os.makedirs(out_dir, exist_ok=True)
                out_path = os.path.join(out_dir, "story.jpg")
                
                story_obj = {"heading": heading, "body": body}
                render_story(None, story_obj, out_path, 0, [], None, cat_key)

                # ارسال تصویر نهایی استوری به کاربر
                with open(out_path, "rb") as photo_file:
                    await q.message.reply_photo(
                        photo=photo_file,
                        caption=f"✅ **استوری گرافیکی آماده شد!**\n\n📌 سبک: {cat_key}",
                        parse_mode="Markdown",
                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت به منوی پیج", callback_data=f"page_hub:{slug}")]])
                    )

        elif data == "dept:trading:market_pulse":
            await q.edit_message_text("⏳ در حال تحلیل نبض بازار...")
            ans = await self.llm.generate_text("یک گزارش تحلیلی کوتاه و حرفه‌ای درباره بازار کریپتو بنویس.", VIRA_SYSTEM_IDENTITY, "trading")
            await q.message.reply_text(ans, reply_markup=self._main_menu())
        elif data == "dept:papermache:idea_hub":
            kb = [
                [InlineKeyboardButton("📲 ایده استوری فروش", callback_data="art_idea:story")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="menu:main")],
            ]
            await q.edit_message_text("🎨 **ایده‌پرداز تخصصی پاپیه‌ماشه**", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
        elif data.startswith("art_idea:"):
            ans = await self.llm.generate_text("۳ ایده جذاب فروش‌محور برای مجسمه پاپیه‌ماشه بده.", VIRA_SYSTEM_IDENTITY, "Art")
            await q.message.reply_text(ans, reply_markup=self._main_menu())

    async def on_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        msg = update.effective_message
        user_text = (msg.text or "").strip()
        active_task = context.user_data.get("vira_task")

        if active_task:
            context.user_data.pop("vira_task", None)
            slug = active_task.get("slug", "trading")
            page = self.db.get_page_by_slug(slug)
            wait = await msg.reply_text("⏳ در حال ساخت محتوا...")
            ans = await self.llm.generate_text(user_text, VIRA_SYSTEM_IDENTITY, slug)
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
