"""
نقطه شروع ربات تلگرام آژانس هوشمند «دستیار ویرا» (نسخه نهایی با پورت وب Flask برای رندر رایگان)
توسعه‌دهنده: حسین داودیان
"""
import logging
import os
import threading
from flask import Flask
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters
from vira_agency.core.config import AgencyConfig, VIRA_SYSTEM_IDENTITY
from vira_agency.core.database import AgencyDatabase
from vira_agency.core.llm_router import LLMRouter
from vira_agency.core.orchestrator import ViraOrchestrator

logging.basicConfig(format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", level=logging.INFO)
log = logging.getLogger("vira_agency")

# راه‌اندازی وب‌سرور سبک Flask برای رفع خطای No open ports detected در رندر رایگان
web_app = Flask("ViraAgencyWeb")

@web_app.route("/")
def health_check():
    return "Vira Agency Bot is running live and active! 🚀", 200

def run_web_server():
    port = int(os.getenv("PORT", "10000"))
    web_app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)


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
                InlineKeyboardButton("📲 ساخت استوری", callback_data=f"act:{slug}:story"),
                InlineKeyboardButton("🖼️ کاروسل (۱ تا ۱۰ صفحه)", callback_data=f"act:{slug}:carousel_ask_count"),
            ],
            [InlineKeyboardButton("🎬 ساخت ریلز ۵ سکانسی", callback_data=f"act:{slug}:reel")],
        ]
        if slug == "papermache":
            kb.append([InlineKeyboardButton("💡 ایده‌پرداز ترند پاپیه‌ماشه", callback_data="dept:papermache:idea_hub")])
            kb.append([InlineKeyboardButton("🛠️ مشاور کارگاه (خمیر، چسب، رنگ)", callback_data="dept:papermache:workshop_q")])
        kb.append([InlineKeyboardButton("🔙 تغییر پیج", callback_data="menu:select_page")])
        return InlineKeyboardMarkup(kb)

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data.clear()
        await update.effective_message.reply_text(
            "سلام! من **«دستیار ویرا»** هستم ✨🤖\n"
            "آماده‌ام تا هر ۳ پیج تو (ترید، روانشناسی تاریک و هنر پاپیه‌ماشه) رو به صورت کاملاً مجزا مدیریت کنم!",
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
                await q.edit_message_text(f"✨ **پیج: {page['title']}**\nچه کاری انجام دهیم؟", reply_markup=self._department_menu(page), parse_mode="Markdown")
        elif data.startswith("act:") and data.endswith(":carousel_ask_count"):
            slug = data.split(":")[1]
            btns = [
                [InlineKeyboardButton("۱ صفحه", callback_data=f"carousel_cnt:{slug}:1"), InlineKeyboardButton("۳ صفحه", callback_data=f"carousel_cnt:{slug}:3")],
                [InlineKeyboardButton("۵ صفحه", callback_data=f"carousel_cnt:{slug}:5"), InlineKeyboardButton("۷ صفحه", callback_data=f"carousel_cnt:{slug}:7")],
                [InlineKeyboardButton("۱۰ صفحه", callback_data=f"carousel_cnt:{slug}:10")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data=f"page_hub:{slug}")],
            ]
            await q.edit_message_text("🖼️ کاروسل چند صفحه باشد؟", reply_markup=InlineKeyboardMarkup(btns))
        elif data.startswith("carousel_cnt:"):
            _, slug, cnt = data.split(":")
            context.user_data["vira_task"] = {"type": "carousel", "slug": slug, "slides": int(cnt)}
            await q.edit_message_text(f"✅ کاروسل {cnt} صفحه‌ای انتخاب شد! موضوع دلخواهت رو بنویس:")
        elif data == "dept:papermache:idea_hub":
            kb = [
                [InlineKeyboardButton("📲 ایده استوری فروش و تعامل", callback_data="art_idea:story")],
                [InlineKeyboardButton("🖼️ ایده کاروسل دکور و معرفی اثر", callback_data="art_idea:carousel")],
                [InlineKeyboardButton("🎬 ایده ریلز قبل و بعد ساخت", callback_data="art_idea:reel")],
                [InlineKeyboardButton("🛠️ مشاوره کارگاه پاپیه‌ماشه", callback_data="dept:papermache:workshop_q")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="page_hub:papermache")],
            ]
            await q.edit_message_text("🎨 **ایده‌پرداز تخصصی پاپیه‌ماشه**", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
        elif data.startswith("art_idea:"):
            kind = data.split(":")[1]
            await q.edit_message_text("⏳ دستیار ویرا در حال ایده‌پردازی...")
            ans = await self.llm.generate_text(f"۵ ایده جذاب و فروش‌محور {kind} برای پیج مجسمه‌های دست‌ساز پاپیه‌ماشه بده.", VIRA_SYSTEM_IDENTITY, "Art")
            await q.message.reply_text(ans, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="dept:papermache:idea_hub")]]))
        elif data == "dept:papermache:workshop_q":
            context.user_data["vira_task"] = {"type": "workshop_qa", "slug": "papermache"}
            await q.edit_message_text("🛠️ سوالت رو درباره ساخت خمیر، چسب چوب، سمباده یا رنگ‌آمیزی پاپیه‌ماشه بنویس:")

    async def on_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        msg = update.effective_message
        user_text = (msg.text or "").strip()
        active_task = context.user_data.get("vira_task")
        if active_task:
            context.user_data.pop("vira_task", None)
            slug = active_task.get("slug", "trading")
            page = self.db.get_page_by_slug(slug)
            wait = await msg.reply_text("⏳ دستیار ویرا در حال آماده‌سازی پاسخ...")
            ans = await self.llm.generate_text(user_text, VIRA_SYSTEM_IDENTITY, slug)
            await wait.delete()
            await msg.reply_text(ans, reply_markup=self._department_menu(page))
            return

        intent_data = await self.ceo.detect_intent(user_text)
        if intent_data.get("intent") in ("create_story", "create_carousel", "create_reel"):
            slug = intent_data.get("target_page_slug", "unknown")
            if slug != "unknown":
                page = self.db.get_page_by_slug(slug)
                await msg.reply_text(f"😎 بریم سراغ پیج **{page['title']}**:", reply_markup=self._department_menu(page), parse_mode="Markdown")
            else:
                await msg.reply_text("✨ برای کدوم پیجت می‌خوای بسازم؟", reply_markup=self._page_selection_menu())
            return

        wait = await msg.reply_text("🤔 ...")
        reply = await self.ceo.chat_with_vira(user_text)
        await wait.delete()
        await msg.reply_text(reply, reply_markup=self._main_menu())

    def run(self):
        # روشن کردن سرور وب در یک ترد جداگانه برای پاسخ به پورتهای رندر
        t = threading.Thread(target=run_web_server, daemon=True)
        t.start()
        log.info("Flask web server started on port %s", os.getenv("PORT", "10000"))

        app = Application.builder().token(self.cfg.telegram_token).build()
        app.add_handler(CommandHandler("start", self.cmd_start))
        app.add_handler(CallbackQueryHandler(self.on_callback))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.on_text_message))
        log.info("Vira AI Agency Bot started successfully!")
        app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    ViraTelegramBot().run()
