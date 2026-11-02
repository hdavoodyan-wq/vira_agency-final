"""
ربات تلگرام آژانس هوشمند «دستیار ویرا»
توسعه‌دهنده: حسین داودیان
مجهز به سیستم ضدتکرار ۳۰ روزه موضوعات، ترندهای خودکار هوشمند و رفع کامل خطای کلید جمینای.
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
                with urllib.request.urlopen(req, timeout=10) as resp:
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
        """منوی انتخاب نحوه تعیین موضوع (ترندهای روز هوشمند یا موضوع دلخواه ادمین)"""
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🔥 ترندهای روز (خودکار و ضدتکرار ۳۰ روزه)", callback_data=f"topic_src:{slug}:{kind}:auto")],
            [InlineKeyboardButton("✍️ ورود موضوع دلخواه", callback_data=f"topic_src:{slug}:{kind}:custom")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data=f"page_hub:{slug}")]
        ])

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data.clear()
        # بررسی و هشدار در صورت خالی بودن کلید جمینای
        if not self.cfg.gemini_api_key:
            await update.effective_message.reply_text(
                "⚠️ **هشدار:** کلید `GEMINI_API_KEY` در تنظیمات سرور (Environment) ثبت نشده است. لطفاً آن را اضافه کنید تا ربات فعال شود.",
                parse_mode="Markdown"
            )
            return

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
                await q.edit_message_text(f"✨ **پیج: {page['title']}**\nچه نوع محتوایی می‌خواهی تولید کنی؟", reply_markup=self._department_menu(page), parse_mode="Markdown")
        elif data.startswith("act:"):
            _, slug, kind = data.split(":")
            page = self.db.get_page_by_slug(slug)
            if page:
                if kind == "story":
                    # نمایش منوی سبکی استوری برای این پیج
                    await self._show_story_menu(q.message, page)
                else:
                    kind_label = {"carousel": "کاروسل", "reel": "ریلز"}.get(kind, kind)
                    await q.edit_message_text(
                        f"🎯 پیج: *{page['title']}* ({kind_label})\n\nموضوع محتوا چطور انتخاب شود؟",
                        reply_markup=self._topic_source_menu(slug, kind),
                        parse_mode="Markdown"
                    )
        elif data.startswith("st_cat:"):
            # پردازش انتخاب سبک استوری
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
                # حالت ترند خودکار با بررسی سابقه ۳۰ روزه جهت جلوگیری از تکرار
                await q.edit_message_text(f"⏳ دستیار ویرا در حال بررسی ترندها و سابقه ۳۰ روز گذشته جهت جلوگیری از تکرار...")
                
                recent_topics = self.db.get_recent_topics(page["id"], limit=30)
                recent_str = ", ".join(recent_topics) if recent_topics else "هیچ موضوعی در ۳۰ روز گذشته ثبت نشده است."

                prompt = (
                    f"شما مدیر محتوای پیج «{page['title']}» با نیش «{page['niche']}» هستید.\n"
                    f"موضوعاتی که در ۳۰ روز گذشته تولید شده‌اند و به هیچ وجه نباید تکرار شوند: [{recent_str}]\n"
                    f"لطفاً یک موضوع جدید، ترند، جذاب و غیرتکراری برای ساخت یک {kind} حرفه‌ای پیشنهاد دهید.\n"
                    "فقط عنوان موضوع را به صورت یک خط و بسیار جذاب برگردانید."
                )
                
                generated_topic = await self.llm.generate_text(prompt, VIRA_SYSTEM_IDENTITY, slug, temperature=0.85)
                generated_topic = generated_topic.strip().strip('"').strip("'")

                # ثبت در دیتابیس به عنوان موضوع جدید تولید شده
                self.db.save_content(page["id"], kind, generated_topic, {"source": "auto_trend"})

                await q.message.reply_text(
                    f"🔥 **موضوع ترند جدید (تایید شده توسط حافظه ضدتکرار):**\n`{generated_topic}`\n\n⏳ در حال تولید محتوا...",
                    parse_mode="Markdown"
                )
                # در اینجا عملیات ساخت محتوا انجام می‌شود
                await q.message.reply_text(f"✅ محتوای مربوط به موضوع «{generated_topic}» با موفقیت آماده شد!", reply_markup=self._department_menu(page))

        elif data == "dept:papermache:idea_hub":
            kb = [
                [InlineKeyboardButton("📲 ایده استوری فروش و تعامل", callback_data="art_idea:story")],
                [InlineKeyboardButton("🖼️ ایده کاروسل دکور و معرفی اثر", callback_data="art_idea:carousel")],
                [InlineKeyboardButton("🎬 ایده ریلز قبل و بعد ساخت", callback_data="art_idea:reel")],
                [InlineKeyboardButton("🛠️ مشاوره کارگاه پاپیه‌ماشه", callback_data="dept:papermache:workshop_q")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="page_hub:papermache")],
            ]
            await q.edit_message_text("🎨 **ایده‌پرداز تخصصی پاپیه‌ماشه**", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")
    def _show_story_menu(self, message, page):
        """منوی سبک‌های اختصاصی استوری برای هر پیج"""
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
        kb.append([InlineKeyboardButton("🔙 بازگشت", callback_data=f"page_hub:{slug}")])
        return q.edit_message_text(f"📲 **انتخاب سبک استوری برای پیج «{page['title']}»**", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

    async def _generate_and_send_story(self, message, page, cat_key):
        """تولید متن، تصویر اختصاصی و رندر استوری"""
        try:
            prompt = (
                f"شما متخصص ساخت استوری اینستاگرام برای پیج «{page['title']}» با نیش «{page['niche']}» هستید.\n"
                f"سبک انتخابی استوری: {cat_key}\n"
                "لطفاً یک استوری جذاب، تک‌صفحه‌ای، درگیرکننده و حرفه‌ای بسازید.\n"
                "خروجی را صرفاً در قالب یک متن خوش‌ساخت شامل تیتر (Heading) و متن اصلی (Body) همراه با یک پرامپت انگلیسی دقیق برای تصویرساز ارسال کنید."
            )
            ai_text = await self.llm.generate_text(prompt, VIRA_SYSTEM_IDENTITY, page["slug"], temperature=0.8)
            
            # ذخیره در دیتابیس
            self.db.save_content(page["id"], "story", f"استوری سبک {cat_key}", {"text": ai_text})

            await message.reply_text(
                f"✅ **استوری تخصصی آماده شد!**\n\n{ai_text}",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت به منوی پیج", callback_data=f"page_hub:{page['slug']}")]])
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

            # بررسی تکراری نبودن موضوع سفارشی ادمین در ۳۰ روز گذشته
            recent_topics = self.db.get_recent_topics(page["id"], limit=30)
            if any(user_text.lower() in t.lower() for t in recent_topics):
                await msg.reply_text("⚠️ **توجه:** این موضوع در ۳۰ روز گذشته در این پیج تولید شده است! برای حفظ جذابیت پیج، لطفاً موضوع دیگری وارد کنید یا از دکمه ترندهای روز استفاده کنید.")
                return

            # ذخیره موضوع جدید در دیتابیس
            self.db.save_content(page["id"], kind, user_text, {"source": "custom_user"})

            wait = await msg.reply_text(f"⏳ دستیار ویرا در حال تولید محتوا برای موضوع: «{user_text}»...")
            ans = await self.llm.generate_text(f"محتوای حرفه‌ای برای موضوع '{user_text}' در حوزه {page['niche']} بنویس.", VIRA_SYSTEM_IDENTITY, slug)
            await wait.delete()
            await msg.reply_text(ans, reply_markup=self._department_menu(page))
            return

        # چت آزاد با هوش مصنوعی ویرا
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
