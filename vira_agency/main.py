"""
ربات تلگرام آژانس هوشمند «دستیار ویرا»
شامل اسامی و آیدی‌های رسمی ۳ پیج:
۱. روانشناسی معامله‌گری (@tradebazehn)
۲. ذهن زیبا (@zehnayetaarik)
۳. گالری هنری الهه (ELART GALLERY) (@elartgallery.ir)

دارای:
- منوی سه‌گزینه‌ای انتخاب موضوع برای کاروسل و ریلز
- دکمه‌های بازگشت و ساخت مجدد زیر تمام خروجی‌ها
- اتصال مستقیم به ایجنت‌های تخصصی ۳ دپارتمان
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
from vira_agency.core.video import build_reel

logging.basicConfig(format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", level=logging.INFO)
log = logging.getLogger("vira_agency")

STORY_MENU_TITLES = {
    # روانشناسی معامله‌گری
    "t_market": "📈 تحلیل بازار و وضعیت بیت‌کوین",
    "t_news": "📰 اخبار داغ و رویدادهای زنده",
    "t_quiz": "⚡ کوییز تریدری (اینجا وارد شویم؟)",
    "t_psyc": "🧠 روانشناسی ترید و کنترل طمع",
    "t_hunt": "🎯 هشدار تله نقدینگی و استاپ‌هانت",
    "t_bull": "🐂 نبرد حماسی گاو و خرس",
    # ذهن زیبا
    "d_chal": "🔥 دوراهی شوالیه تاریک",
    "d_edu": "🦊 فریب و مکر (روباه نقاب‌دار)",
    "d_mar": "🐺 استقلال عاطفی (گرگ تنها)",
    "d_opt": "🥀 راز کاریزما و جذابیت (بانوی مرموز)",
    "d_sec": "🩸 نفوذ و هیپنوتیزم (کنت دراکولا)",
    # گالری هنری الهه
    "art_mirror": "🪞 آینه موج‌دار وابی‌سابی (ترند دکور)",
    "art_decor": "🏺 ظروف و کاسه‌های دکوراتیو کنسول",
    "art_sculpture": "🗿 مجسمه فرم آزاد و مینیمال",
    "behind": "📲 پشت صحنه سفارشات و گالری",
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
            [InlineKeyboardButton("🪞 کالکشن ترند گالری الهه (آینه و دکور)", callback_data="dept:papermache:idea_hub")],
            [InlineKeyboardButton("📈 نبض و تحلیل زنده کریپتو", callback_data="dept:trading:market_pulse")],
        ])

    def _page_selection_menu(self) -> InlineKeyboardMarkup:
        pages = self.db.get_pages(active_only=True)
        kb = [[InlineKeyboardButton(p["title"], callback_data=f"page_hub:{p['slug']}")] for p in pages]
        kb.append([InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="menu:main")])
        return InlineKeyboardMarkup(kb)

    def _department_menu(self, page: dict) -> InlineKeyboardMarkup:
        slug = page["slug"]
        kb = [
            [
                InlineKeyboardButton("📲 ساخت استوری تخصصی", callback_data=f"act:{slug}:story"),
                InlineKeyboardButton("🖼️ ساخت کاروسل اسلایدی", callback_data=f"car_menu:{slug}"),
            ],
            [InlineKeyboardButton("🎬 ساخت ریلز ۵ سکانسی", callback_data=f"reel_menu:{slug}")],
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

        kb = [[InlineKeyboardButton(STORY_MENU_TITLES[k], callback_data=f"st_cat:{k}:{slug}")] for k in keys]
        kb.append([InlineKeyboardButton("🔙 بازگشت به پیج", callback_data=f"page_hub:{slug}")])
        return InlineKeyboardMarkup(kb)

    def _topic_selection_menu(self, slug: str, kind: str) -> InlineKeyboardMarkup:
        """منوی سه‌گزینه‌ای انتخاب موضوع برای کاروسل و ریلز"""
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🌟 موضوعات ترند خودکار", callback_data=f"gen_auto:{slug}:{kind}")],
            [InlineKeyboardButton("✍️ انتخاب موضوع توسط کاربر", callback_data=f"gen_manual:{slug}:{kind}")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data=f"page_hub:{slug}")],
        ])

    def _result_actions_menu(self, slug: str, kind: str, param: str) -> InlineKeyboardMarkup:
        """دکمه‌های دوقلو زیر تمام خروجی‌ها: ساخت مجدد و بازگشت"""
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🔄 ساخت مجدد (یکی دیگه بساز)", callback_data=f"regen:{slug}:{kind}:{param}"),
                InlineKeyboardButton("🔙 بازگشت به منوی پیج", callback_data=f"page_hub:{slug}"),
            ]
        ])

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        context.user_data.clear()
        await update.effective_message.reply_text(
            "سلام! من **«دستیار ویرا»** هستم ✨🤖\n"
            "مدیرعامل هوشمند آژانس تبلیغاتی؛ آماده تولید محتوا برای ۳ پیج:\n"
            "• روانشناسی معامله‌گری (@tradebazehn)\n"
            "• ذهن زیبا (@zehnayetaarik)\n"
            "• گالری هنری الهه (@elartgallery.ir)",
            reply_markup=self._main_menu(),
            parse_mode="Markdown",
        )

    async def _produce_and_send_story(self, q_or_msg, slug: str, cat_key: str):
        page = self.db.get_page_by_slug(slug)
        agent = self.ceo.get_department_agent(slug)

        wait_msg = await (q_or_msg.message.reply_text if hasattr(q_or_msg, "message") else q_or_msg.reply_text)(
            f"⏳ در حال تصویرسازی و رندر استوری برای «{page['title']}»..."
        )

        story_data = await agent.make_story(cat_key)
        out_dir = f"data/outputs/{page['id']}/story_{int(time.time())}"
        os.makedirs(out_dir, exist_ok=True)

        art_path = os.path.join(out_dir, "art.jpg")
        img_ok = await self.llm.generate_image(story_data["visual"], art_path)

        out_path = os.path.join(out_dir, "story_final.jpg")
        render_story(None, story_data, out_path, 0, [], None, cat_key, art_path if img_ok else None)
        self.db.save_content(page["id"], "story", story_data["heading"], {"body": story_data["body"], "file": out_path})

        clean_caption = f"✅ {story_data['heading']}\n\n{story_data['body']}".replace("*", "").replace("_", "")[:950]

        await wait_msg.delete()
        with open(out_path, "rb") as photo_file:
            target = q_or_msg.message if hasattr(q_or_msg, "message") else q_or_msg
            await target.reply_photo(
                photo=photo_file,
                caption=clean_caption,
                reply_markup=self._result_actions_menu(slug, "story", cat_key),
            )

    async def _produce_and_send_carousel(self, q_or_msg, slug: str, topic: str, count: int = 4):
        page = self.db.get_page_by_slug(slug)
        agent = self.ceo.get_department_agent(slug)

        target = q_or_msg.message if hasattr(q_or_msg, "message") else q_or_msg
        wait = await target.reply_text(f"⏳ در حال تصویرسازی و ساخت کاروسل {count} اسلایدی برای «{topic}»...")

        car_data = await agent.make_carousel(topic, count)
        slides = car_data.get("slides") or []

        out_dir = f"data/outputs/{page['id']}/carousel_{int(time.time())}"
        os.makedirs(out_dir, exist_ok=True)

        arts = []
        for idx, s in enumerate(slides):
            art_file = os.path.join(out_dir, f"art_{idx}.jpg")
            v_prompt = s.get("visual", "cinematic digital art, no text")
            ok = await self.llm.generate_image(v_prompt, art_file)
            arts.append(art_file if ok else None)

        files = await asyncio.to_thread(render_carousel, None, slides, out_dir, [], None, arts, slug)
        await wait.delete()

        for fpath in files:
            with open(fpath, "rb") as ph:
                await target.reply_photo(photo=ph)

        await target.reply_text(
            car_data.get("caption", "✅ کاروسل آماده شد."),
            reply_markup=self._result_actions_menu(slug, "carousel", topic[:30]),
        )

    async def _produce_and_send_reel(self, q_or_msg, slug: str, topic: str):
        page = self.db.get_page_by_slug(slug)
        agent = self.ceo.get_department_agent(slug)

        target = q_or_msg.message if hasattr(q_or_msg, "message") else q_or_msg
        wait = await target.reply_text(f"⏳ در حال تولید فریم‌ها و تدوین ریلز برای «{topic}»...")

        reel_data = await agent.make_reel(topic)
        scenes = reel_data.get("scenes") or []

        out_dir = f"data/outputs/{page['id']}/reel_{int(time.time())}"
        os.makedirs(out_dir, exist_ok=True)

        arts = []
        for idx, s in enumerate(scenes):
            art_file = os.path.join(out_dir, f"art_{idx}.jpg")
            v_prompt = s.get("visual", "cinematic art, no text")
            ok = await self.llm.generate_image(v_prompt, art_file)
            arts.append(art_file if ok else None)

        frames = []
        texts = []
        for i, s in enumerate(scenes):
            f_path = os.path.join(out_dir, f"frame_{i}.jpg")
            render_reel_frame(None, s.get("text", ""), f_path, i, [], None, arts[i] if i < len(arts) else None, slug)
            frames.append(f_path)
            texts.append(s.get("text", ""))

        video_path = os.path.join(out_dir, "reel_final.mp4")
        audios = [None] * len(scenes)
        await asyncio.to_thread(build_reel, frames, audios, texts, video_path)

        await wait.delete()
        with open(video_path, "rb") as vf:
            await target.reply_video(
                video=vf,
                caption=reel_data.get("caption", "✅ ریلز ۵ سکانسی آماده شد."),
                reply_markup=self._result_actions_menu(slug, "reel", topic[:30]),
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
        elif data.startswith("act:") and data.endswith(":story"):
            slug = data.split(":")[1]
            page = self.db.get_page_by_slug(slug)
            if page:
                await q.edit_message_text(
                    f"📲 **انتخاب سبک استوری برای «{page['title']}»:**",
                    reply_markup=self._story_cats_menu(page),
                    parse_mode="Markdown",
                )

        # منوی ۳ گزینه‌ای کاروسل و ریلز
        elif data.startswith("car_menu:"):
            slug = data.split(":")[1]
            page = self.db.get_page_by_slug(slug)
            await q.edit_message_text(
                f"🖼️ **ساخت کاروسل اسلایدی برای «{page['title']}»**\nلطفاً نحوه انتخاب موضوع را مشخص کن:",
                reply_markup=self._topic_selection_menu(slug, "carousel"),
                parse_mode="Markdown",
            )
        elif data.startswith("reel_menu:"):
            slug = data.split(":")[1]
            page = self.db.get_page_by_slug(slug)
            await q.edit_message_text(
                f"🎬 **ساخت ریلز ۵ سکانسی برای «{page['title']}»**\nلطفاً نحوه انتخاب موضوع را مشخص کن:",
                reply_markup=self._topic_selection_menu(slug, "reel"),
                parse_mode="Markdown",
            )

        # موضوعات ترند خودکار
        elif data.startswith("gen_auto:"):
            _, slug, kind = data.split(":")
            agent = self.ceo.get_department_agent(slug)
            trend_topic = agent.get_random_trend()
            if kind == "carousel":
                await q.edit_message_text(f"🌟 موضوع ترند انتخاب شد: «{trend_topic}»\nدر حال شروع ساخت کاروسل...")
                await self._produce_and_send_carousel(q, slug, trend_topic, 4)
            else:
                await q.edit_message_text(f"🌟 موضوع ترند انتخاب شد: «{trend_topic}»\nدر حال شروع تدوین ریلز...")
                await self._produce_and_send_reel(q, slug, trend_topic)

        # انتخاب موضوع دستی توسط کاربر
        elif data.startswith("gen_manual:"):
            _, slug, kind = data.split(":")
            context.user_data["vira_task"] = {"slug": slug, "kind": kind}
            label = "کاروسل تصویری" if kind == "carousel" else "ریلز ۵ سکانسی"
            await q.edit_message_text(f"✍️ لطفاً موضوع دلخواهت را برای ساخت «{label}» تایپ کن و بفرست:")

        # ساخت استوری
        elif data.startswith("st_cat:"):
            _, cat_key, slug = data.split(":")
            await self._produce_and_send_story(q, slug, cat_key)

        # دکمه ساخت مجدد (یکی دیگه بساز)
        elif data.startswith("regen:"):
            _, slug, kind, param = data.split(":", 3)
            if kind == "story":
                await self._produce_and_send_story(q, slug, param)
            elif kind == "carousel":
                agent = self.ceo.get_department_agent(slug)
                topic = param if len(param) > 4 else agent.get_random_trend()
                await self._produce_and_send_carousel(q, slug, topic, 4)
            elif kind == "reel":
                agent = self.ceo.get_department_agent(slug)
                topic = param if len(param) > 4 else agent.get_random_trend()
                await self._produce_and_send_reel(q, slug, topic)

        elif data == "dept:trading:market_pulse":
            await q.edit_message_text("⏳ در حال دریافت تحلیل زنده بازار...")
            agent = self.ceo.trading_dept
            story_res = await agent.make_story("t_market")
            msg_text = f"📊 **نبض مارکت و تحلیل بیت‌کوین:**\n\n{story_res['body']}"
            await q.message.reply_text(msg_text, reply_markup=self._main_menu())

        elif data == "dept:papermache:idea_hub":
            kb = [
                [InlineKeyboardButton("🪞 آینه موج‌دار وابی‌سابی", callback_data="st_cat:art_mirror:papermache")],
                [InlineKeyboardButton("🏺 ظروف دکوراتیو و کنسول", callback_data="st_cat:art_decor:papermache")],
                [InlineKeyboardButton("🗿 مجسمه فرم آزاد و مینیمال", callback_data="st_cat:art_sculpture:papermache")],
                [InlineKeyboardButton("📲 پشت صحنه و بسته‌بندی", callback_data="st_cat:behind:papermache")],
                [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="menu:main")],
            ]
            await q.edit_message_text("🎨 **کالکشن محصولات ترند گالری هنری الهه**", reply_markup=InlineKeyboardMarkup(kb), parse_mode="Markdown")

        elif data == "dept:papermache:workshop_q":
            context.user_data["vira_task"] = {"slug": "papermache", "kind": "workshop"}
            await q.edit_message_text("🛠️ سوالت را درباره فرمول خمیر، چسب یا روش ضدترک بنویس:")

    async def on_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        msg = update.effective_message
        user_text = (msg.text or "").strip()
        active_task = context.user_data.get("vira_task")

        if active_task:
            context.user_data.pop("vira_task", None)
            slug = active_task.get("slug", "trading")
            kind = active_task.get("kind", "carousel")

            if kind == "carousel":
                await self._produce_and_send_carousel(msg, slug, user_text, 4)
                return
            elif kind == "reel":
                await self._produce_and_send_reel(msg, slug, user_text)
                return
            else:
                page = self.db.get_page_by_slug(slug)
                wait = await msg.reply_text("⏳ در حال آماده‌سازی پاسخ تخصصی...")
                ans = await self.llm.generate_text(
                    f"به عنوان مشاور ارشد پیج «{page['title']}» به این سوال پاسخ کامل و کاربردی بده: {user_text}",
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
