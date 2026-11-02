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
    # روانشناسی تاریک
    "d_chal": {
        "title": "🔥 چالشی و دو راهی اخلاقی (شوالیه)",
        "tag_fa": "چالش روز",
        "visual": "A solitary dark knight standing before a gloomy gothic castle under a crimson blood moon, dark oil painting masterpiece, no text"
    },
    "d_edu": {
        "title": "🧠 پند رابطه و روباه مکار",
        "tag_fa": "ترفند تاریک",
        "visual": "A cunning fox wearing a mysterious theatrical mask in a shadowy forest, dark gothic oil painting with crimson shadows, no text"
    },
    "d_mar": {
        "title": "💍 رازهای تاریک روابط (گرگ)",
        "tag_fa": "قوانین رابطه",
        "visual": "A majestic grey wolf standing alone on a snowy cliff under starry night, dark gothic oil painting, chiaroscuro lighting, no text"
    },
    "d_opt": {
        "title": "🎭 تست شخصیت (مسیر تاریک)",
        "tag_fa": "تست شخصیت",
        "visual": "Two distinct symbolic paths diverging in a dark gothic forest leading to a glowing crimson castle, dark oil painting, no text"
    },
    "d_sec": {
        "title": "🩸 راز زبان بدن (کنت دراکولا)",
        "tag_fa": "زبان بدن",
        "visual": "Aristocratic Count Dracula in a deep charcoal coat with crimson lining staring intensely, dark gothic oil painting, no text"
    },
    # پاپیه‌ماشه
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

        # تولید متن دقیق بر اساس داده‌های لحظه‌ای بازار
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
            body = (
                f"آخرین تحولات اقتصادی و مارکت: {m.get('news')[:120]}... "
                f"نوسانات با ثبت بالاترین قیمت ۲۴ساعته در ${m.get('high')} و کف ${m.get('low')} همراه بوده است؛ "
                f"معامله‌گران باید ریسک فیوچرز را به شدت کنترل کنند."
            )
            sticker = "بازار پامپ میشه یا دامپ؟"

        elif slug == "trading":
            prompt = (
                f"یک استوری ترید کوتاه و کوبنده فارسی در موضوع {cat['title']} بر اساس بیت‌کوین ${m.get('price')} بنویس.\n"
                'فقط این ساختار JSON: {"heading": "تیتر جذاب فارسی", "body": "متن تخصصی فارسی", "sticker": "سوال نظرسنجی"}'
            )
            data = await self.llm.json(prompt, temperature=0.7)
            heading = str(data.get("heading") or cat["tag_fa"])
            body = str(data.get("body") or f"بیت‌کوین در محدوده ${m.get('price')} در حال تثبیت است؛ حد ضرر فراموش نشود.")
            sticker = str(data.get("sticker") or "تحلیل تو چیه؟")

        else:
            prompt = (
                f"یک استوری جذاب و اختصاصی فارسی برای پیج «{page['title']}» در سبک {cat['title']} بساز.\n"
                'فقط ساختار JSON: {"heading": "تیتر فارسی", "body": "متن جذاب فارسی", "sticker": "سوال تعاملی"}'
            )
            data = await self.llm.json(prompt, temperature=0.7)
            heading = str(data.get("heading") or cat["tag_fa"])
            body = str(data.get("body") or "اصالت و جذابیت در تک تک جزئیات خلق شده است.")
            sticker = str(data.get("sticker") or "نظر تو چیه؟")

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