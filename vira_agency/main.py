"""
ربات تلگرام آژانس هوشمند «دستیار ویرا»
توسعه‌دهنده: حسین داودیان
مجهز به منوی کامل تولید استوری، کاروسل‌های سفارشی، ریلز و تحلیل بازار.
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
                InlineKeyboardButton("📲 ساخت استوری تخصصی", callback_data=f"act:{slug}:story"),
                InlineKeyboardButton("🖼️ ساخت کاروسل", callback_data=f"act:{slug}:carousel"),
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
            cats = [
                ("📈 تحلیل بازار و وضعیت بیت‌کوین", "t_market"),
                ("📰 اخبار زنده فارکس و کریپتو", "t_news"),
                ("⚡ کوییز تریدری (اینجا وارد شویم؟)", "t_quiz"),
                ("🧠 روانشناسی ترید و کنترل طمع", "t_psyc"),
                ("🎯 هشدار تله نقدینگی و استاپ‌هانت", "t_hunt"),
                ("🐂 نبرد حماسی گاو و خرس", "t_bull"),
            ]
        elif slug == "dark_psych":
            cats = [
                ("🔥 چالشی و دو راهی اخلاقی (شوالیه)", "d_chal"),
                ("🧠 پند رابطه و روباه مکار", "d_edu"),
                ("💍 رازهای تاریک روابط (گرگ)", "d_mar"),
                ("🎭 تست شخصیت (مسیر تاریک)", "d_opt"),
                ("🩸 راز زبان بدن (کنت دراکولا)", "d_sec"),
            ]
        else:
            cats = [
                ("📲 ایده استوری فروش و پشت صحنه", "behind"),
                ("🖼️ معرفی اثر جدید و جزئیات دکور", "showcase"),
                ("🛠️ آموزش تکنیک خمیر و چسب", "workshop"),
            ]

        kb = [[InlineKeyboardButton(label, callback_data=f"st_cat:{key}:{slug}")] for label, key in cats]
        kb.append([InlineKeyboardButton("🔙 بازگشت", callback_data=f"page_hub:{slug}")])
        return InlineKeyboardMarkup(kb)

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data.clear()
        await update.effective_message.reply_text(
            "سلام! من **«دستیار ویرا»** هستم ✨🤖\n"
            "آماده‌ام تا هر ۳ پیج تو را با تم‌های اختصاصی (بنفش سلطنتی ترید و گوتیک تاریک) مدیریت کنم!",
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
                        f"📲 **انتخاب سبک استوری برای «{page['title']}»:**",
                        reply_markup=self._story_cats_menu(page),
                        parse_Mode="Markdown",
                    )
                else:
                    context.user_data["vira_task"] = {"slug": slug, "kind": kind}
                    await q.edit_message_text(f"✍️ موضوع یا درخواست خود را برای ساخت *{kind}* در پیج *{page['title']}* بنویسید:")
        elif data.startswith("st_cat:"):
            _, cat_key, slug = data.split(":")
            page = self.db.get_page_by_slug(slug)
            if page:
                await q.edit_message_text(f"⏳ دستیار ویرا در حال تولید استوری حرفه‌ای برای پیج «{page['title']}»...")
                prompt = f"یک استوری در سبک {cat_key} برای پیج {page['title']} بساز."
                ans = await self.llm.generate_text(prompt, VIRA_SYSTEM_IDENTITY, slug, temperature=0.8)
                self.db.save_content(page["id"], "story", f"{cat_key}: {ans[:40]}", {"text": ans})
                await q.message.reply_text(f"✅ **استوری تخصصی آماده شد:**\n\n{ans}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data=f"page_hub:{slug}")]]))

        elif data == "dept:trading:market_pulse":
            await q.edit_message_text("⏳ در حال تحلیل نبض بازار و بررسی وضعیت کریپتو...")
            ans = await self.llm.generate_text(
                "یک گزارش تحلیلی، جذاب و کاربردی درباره وضعیت بازار کریپتو، بیت‌کوین و تله‌های نقدینگی بنویس.",
                VIRA_SYSTEM_IDENTITY,
                "trading",
            )
            await q.message.reply_text(ans, reply_markup=self._main_menu())
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
                f"۵ ایده جذاب، جدید و فروش‌محور {kind} برای پیج مجسمه‌های دست‌ساز پاپیه‌ماشه بده.",
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

            wait = await msg.reply_text(f"⏳ دستیار ویرا در حال ساخت «{kind}» با موضوع «{user_text}»...")
            ans = await self.llm.generate_text(
                f"محتوای کامل {kind} برای پیج {page['title']} ({page['niche']}) درباره: {user_text}",
                VIRA_SYSTEM_IDENTITY,
                slug,
            )
            await wait.delete()
            self.db.save_content(page["id"], kind, user_text, {"text": ans})
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
