```python
"""
ربات تلگرام آژانس هوشمند «دستیار ویرا»
توسعه‌دهنده: حسین داودیان
مجهز به استوری‌ساز کامل، ترندهای روز (ضدتکرار ۳۰ روزه)، و مسیریاب چندموتوره بدون خطا.
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


def start_self_ping_worker():
    def pinger():
        app_url = os.getenv("RENDER_EXTERNAL_URL", "").strip()
        if not app_url:
            port = os.getenv("PORT", "10000")
            app_url = f"http://127.0.0.1:{port}"
        while True:
            time.sleep(300)
            try:
                req = urllib.request.Request(app_url, headers={"User-Agent": "ViraKeepAliveBot"})
                with urllib.request.urlopen(req, timeout=10):
                    pass
            except Exception:
                pass

    t = threading.Thread(target=pinger, daemon=True)
    t.start()


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
                InlineKeyboardButton("📲 استوری", callback_data=f"act:{slug}:story"),
                InlineKeyboardButton("🖼️ کاروسل", callback_data=f"act:{slug}:carousel"),
            ],
            [InlineKeyboardButton("🎬 ریلز ۵ سکانسی", callback_data=f"act:{slug}:reel")],
        ]
        if slug == "papermache":
            kb.append([InlineKeyboardButton("💡 ایده‌پرداز ترند پاپیه‌ماشه", callback_data="dept:papermache:idea_hub")])
            kb.append([InlineKeyboardButton("🛠️ مشاور کارگاه (خمیر، چسب، رنگ)", callback_data="dept:papermache:workshop_q")])
        kb.append([InlineKeyboardButton("🔙 تغییر پیج", callback_data="menu:select_page")])
        return InlineKeyboardMarkup(kb)

    def _topic_source_menu(self, slug: str, kind: str) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🔥 ترندهای روز (خودکار و ضدتکرار ۳۰ روزه)", callback_data=f"topic_src:{slug}:{kind}:auto")],
            [InlineKeyboardButton("✍️ ورود موضوع دلخواه", callback_data=f"topic_src:{slug}:{kind}:custom")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data=f"page_hub:{slug}")],
        ])

    def _story_cats_menu(self, page: dict) -> InlineKeyboardMarkup:
        slug = page["slug"]
        if slug == "trading":
            cats = [
                ("📈 تحلیل وضعیت بازار و بیت‌کوین", "market"),
                ("📰 اخبار و رویدادهای ۲۴ ساعت اخیر", "news"),
                ("🧠 روانشناسی ترید و کنترل طمع", "psych"),
                ("⚡ چالش لحظه‌ای معامله‌گران", "challenge"),
            ]
        elif slug == "dark_psych":
            cats = [
                ("🔥 موقعیت چالشی و سوالی", "challenge"),
                ("🧠 پند عمیق رابطه و رفتار سمی", "tip"),
                ("🩸 زبان بدن و خواندن ذهن", "body_lang"),
                ("🎭 تست گزینه‌ای (انتخاب مخاطب)", "quiz"),
            ]
        else:
            cats = [
                ("📲 ایده استوری فروش و پشت صحنه", "behind"),
                ("🖼️ معرفی اثر جدید و جزئیات دکور", "showcase"),
                ("🛠️ آموزش تکنیک خمیر و چسب", "workshop"),
            ]

        kb = [[InlineKeyboardButton(label, callback_data=f"st_cat:{key}:{slug}")] for label, key in cats]
        kb.append([InlineKeyboardButton("🔥 ترند روز استوری (خودکار)", callback_data=f"topic_src:{slug}:story:auto")])
        kb.append([InlineKeyboardButton("✍️ ورود موضوع دلخواه استوری", callback_data=f"topic_src:{slug}:story:custom")])
        kb.append([InlineKeyboardButton("🔙 بازگشت", callback_data=f"page_hub:{slug}")])
        return InlineKeyboardMarkup(kb)

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data.clear()
        await update.effective_message.reply_text(
            "سلام! من **«دستیار ویرا»** هستم ✨🤖\n"
            "آماده‌ام تا هر ۳ پیج تو را به صورت کاملاً حرفه‌ای مدیریت کنم!",
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
                        f"📲 **انتخاب سبک یا موضوع استوری برای «{page['title']}»:**",
                        reply_markup=self._story_cats_menu(page),
                        parse_mode="Markdown",
                    )
                else:
                    kind_label = {"carousel": "کاروسل", "reel": "ریلز"}.get(kind, kind)
                    await q.edit_message_text(
                        f"🎯 پیج: *{page['title']}* ({kind_label})\n\nموضوع محتوا چطور انتخاب شود؟",
                        reply_markup=self._topic_source_menu(slug, kind),
                        parse_mode="Markdown",
                    )
        elif data.startswith("st_cat:"):
            _, cat_key, slug = data.split(":")
            page = self.db.get_page_by_slug(slug)
            if page:
                await q.edit_message_text(f"⏳ دستیار ویرا در حال تولید استوری حرفه‌ای برای پیج «{page['title']}»...")
                await self._generate_and_send_story(q.message, page, cat_key)
        elif data.startswith("topic_src:"):
            _, slug, kind, mode = data.split(":")
            page = self.db.get_page_by_slug(slug)
            if not page:
                return

            if mode == "custom":
                context.user_data["vira_task"] = {"slug": slug, "kind": kind, "mode": "custom"}
                await q.edit_message_text(f"✍️ موضوع دلخواه خود را برای «{kind}» در پیج «{page['title']}» بنویسید:")
            else:
                await q.edit_message_text("⏳ دستیار ویرا در حال بررسی ترندهای روز و سابقه ۳۰ روز گذشته (ضدتکرار)...")
                recent_topics = self.db.get_recent_topics(page["id"], limit=30)
                recent_str = "، ".join(recent_topics) if recent_topics else "هیچ موضوعی ثبت نشده"

                prompt = (
                    f"تو مدیر محتوای پیج «{page['title']}» با نیش «{page['niche']}» هستی.\n"
                    f"موضوعات ۳۰ روز گذشته که هرگز نباید تکرار شوند: [{recent_str}]\n"
                    f"یک موضوع کاملاً جدید، ترند روز و وایرال برای {kind} انتخاب کن و بلافاصله محتوای کامل و حرفه‌ای آن را بنویس."
                )
                ans = await self.llm.generate_text(prompt, VIRA_SYSTEM_IDENTITY, slug, temperature=0.8)
                first_line = ans.splitlines()[0][:80] if ans else "ترند روز"
                self.db.save_content(page["id"], kind, first_line, {"text": ans, "source": "auto_trend"})
                await q.message.reply_text(ans, reply_markup=self._department_menu(page))

        elif data == "dept:trading:market_pulse":
            await q.edit_message_text("⏳ در حال تحلیل نبض بازار و روانشناسی معامله‌گران...")
            ans = await self.llm.generate_text(
                "یک گزارش تحلیلی، جذاب و کاربردی برای استوری و پست امروز پیج ترید درباره وضعیت روانی بازار کریپتو، تله‌های نقدینگی و نکات مدیریت سرمایه بنویس.",
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
            context.user_data["vira_task"] = {"slug": "papermache", "kind": "workshop", "mode": "custom"}
            await q.edit_message_text("🛠️ سوالت رو درباره ساخت خمیر، چسب چوب، سمباده یا رنگ‌آمیزی پاپیه‌ماشه بنویس:")

    async def _generate_and_send_story(self, message, page, cat_key):
        try:
            recent_topics = self.db.get_recent_topics(page["id"], limit=30)
            recent_str = "، ".join(recent_topics) if recent_topics else "—"
            prompt = (
                f"تو متخصص استوری اینستاگرام برای پیج «{page['title']}» ({page['niche']}) هستی.\n"
                f"سبک انتخابی: {cat_key}\n"
                f"موضوعات ۳۰ روز اخیر که نباید تکرار شوند: {recent_str}\n"
                "یک استوری تک‌صفحه‌ای فوق‌العاده جذاب شامل: ۱. تیتر کوبنده ۲. متن اصلی استوری ۳. سوال یا استیکر تعاملی ۴. پرامپت انگلیسی دقیق تصویر بنویس."
            )
            ai_text = await self.llm.generate_text(prompt, VIRA_SYSTEM_IDENTITY, page["slug"], temperature=0.8)
            self.db.save_content(page["id"], "story", f"{cat_key}: {ai_text[:40]}", {"text": ai_text})

            await message.reply_text(
                f"✅ **استوری تخصصی آماده شد:**\n\n{ai_text}",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت به منوی پیج", callback_data=f"page_hub:{page['slug']}")]]),
            )
        except Exception as e:
            await message.reply_text(f"❌ خطا در ساخت استوری: {str(e)[:200]}")

    async def on_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        msg = update.effective_message
        user_text = (msg.text or "").strip()
        active_task = context.user_data.get("vira_task")

        if active_task:
            context.user_data.pop("vira_task", None)
            slug = active_task.get("slug", "trading")
            kind = active_task.get("kind", "post")
            page = self.db.get_page_by_slug(slug)

            if kind != "workshop":
                recent_topics = self.db.get_recent_topics(page["id"], limit=30)
                if any(user_text.lower() == t.lower() for t in recent_topics):
                    await msg.reply_text(
                        "⚠️ این موضوع دقیقاً در ۳۰ روز گذشته تولید شده است! لطفاً موضوع جدیدتری بنویسید یا از دکمه ترندهای روز استفاده کنید."
                    )
                    return
                self.db.save_content(page["id"], kind, user_text, {"source": "custom_user"})

            wait = await msg.reply_text(f"⏳ دستیار ویرا در حال آماده‌سازی «{user_text}»...")
            ans = await self.llm.generate_text(
                f"درخواست کاربر برای پیج {page['title']} ({page['niche']}) در قالب {kind}:\n{user_text}",
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
        start_self_ping_worker()

        app = Application.builder().token(self.cfg.telegram_token).build()
        app.add_handler(CommandHandler("start", self.cmd_start))
        app.add_handler(CallbackQueryHandler(self.on_callback))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.on_text_message))
        log.info("Vira AI Agency Bot started successfully!")
        app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    ViraTelegramBot().run()
```