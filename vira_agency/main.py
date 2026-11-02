
"""
ربات تلگرام آژانس هوشمند «دستیار ویرا»
مجهز به سیستم کامل تولید عکس، استوری، کاروسل و ریلز ۵ سکانسی از ربات قبلی
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

logging.basicConfig(format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", level=logging.INFO)
log = logging.getLogger("vira_agency")

# بانک سبک‌ها و پرامپت‌های تصویری استوری (دقیقاً از ربات قبلی شما)
STORY_CATS_CONFIG = {
    # پیج ترید
    "t_market": {
        "title": "📈 تحلیل بازار و وضعیت بیت‌کوین",
        "desc": "یک تحلیل کوتاه، صریح و حرفه‌ای از وضعیت فعلی بیت‌کوین و حمایت و مقاومت کلیدی بنویس.",
        "visual": "Professional trader in a dark cybernetic room glowing with deep royal purple and neon emerald candlestick charts on multiple screens, cinematic 8k, no text"
    },
    "t_news": {
        "title": "📰 اخبار زنده فارکس و کریپتو",
        "desc": "یک خبر فوری و مهم از نوسانات بازار کریپتو و فارکس و تاثیر آن بر تریدرها بنویس.",
        "visual": "Illuminated financial news terminal in a royal purple glowing room with volatile neon market data feeds, cyberpunk style, no text"
    },
    "t_quiz": {
        "title": "⚡ کوییز تریدری (اینجا وارد شویم؟)",
        "desc": "یک سوال چالش‌برانگیز تریدری طرح کن که آیا در این موقعیت چارت باید لانگ بگیریم یا شورت؟",
        "visual": "Close-up of a complex breakout trading chart glowing in vibrant royal purple and neon green, dramatic lighting, no text"
    },
    "t_psyc": {
        "title": "🧠 روانشناسی ترید و کنترل طمع",
        "desc": "یک نکته طلایی درباره کنترل طمع، ترس (FOMO) و پایبندی به مدیریت سرمایه در ترید بنویس.",
        "visual": "A disciplined trader sitting calmly in front of neon purple charts with a glowing golden aura of focus, cinematic art, no text"
    },
    "t_hunt": {
        "title": "🎯 هشدار تله نقدینگی و استاپ‌هانت",
        "desc": "یک هشدار کاربردی درباره نحوه شکار حد ضرر تریدرهای خرد (Stop Hunt) توسط نهنگ‌ها بنویس.",
        "visual": "Glowing cybernetic liquidity trap catching retail positions on a futuristic royal purple holographic trading chart, no text"
    },
    "t_bull": {
        "title": "🐂 نبرد حماسی گاو و خرس",
        "desc": "تحلیل جنگ خریداران (گاوها) و فروشندگان (خرس‌ها) در ناحیه حساس قیمتی امروز.",
        "visual": "Epic clash of a glowing royal purple metallic Bull and an emerald green Bear amidst stormy trading charts, 8k masterpiece, no text"
    },
    # پیج روانشناسی تاریک
    "d_chal": {
        "title": "🔥 چالشی و دو راهی اخلاقی (شوالیه)",
        "desc": "یک موقعیت چالشی و دوراهی اخلاقی از روانشناسی تاریک بنویس که مخاطب را به فکر فرو ببرد.",
        "visual": "A solitary dark knight standing before a gloomy gothic castle under a crimson blood moon, dark oil painting masterpiece, no text"
    },
    "d_edu": {
        "title": "🧠 پند رابطه و روباه مکار",
        "desc": "یک تکنیک عمیق برای شناسایی افراد فریب‌کار و روباه‌صفت در روابط دوستانه و کاری بنویس.",
        "visual": "A cunning fox wearing a mysterious theatrical mask in a shadowy forest, dark gothic oil painting with crimson shadows, no text"
    },
    "d_mar": {
        "title": "💍 رازهای تاریک روابط (گرگ)",
        "desc": "یک راز مهم درباره حفظ اقتدار، مرزهای شخصی و جلوگیری از وابستگی سمی در رابطه عاطفی بنویس.",
        "visual": "A majestic grey wolf standing alone on a snowy cliff under starry night, dark gothic oil painting, chiaroscuro lighting, no text"
    },
    "d_opt": {
        "title": "🎭 تست شخصیت (مسیر تاریک)",
        "desc": "یک تست شخصیت دوگزینه‌ای از روانشناسی تاریک مطرح کن که شخصیت پنهان مخاطب را آشکار کند.",
        "visual": "Two distinct symbolic paths diverging in a dark gothic forest leading to a glowing crimson castle, dark oil painting, no text"
    },
    "d_sec": {
        "title": "🩸 راز زبان بدن (کنت دراکولا)",
        "desc": "یک ترفند مخفی از زبان بدن و نگاه کردن برای تشخیص سریع دروغ و تسلط روانی فاش کن.",
        "visual": "Aristocratic Count Dracula in a deep charcoal coat with crimson lining staring intensely, dark gothic oil painting, no text"
    },
    # پیج پاپیه‌ماشه
    "behind": {
        "title": "📲 استوری فروش و پشت صحنه",
        "desc": "یک متن گرم و صمیمی درباره حس و حال ساخت مجسمه دست‌ساز پاپیه‌ماشه و دعوت به سفارش بنویس.",
        "visual": "Artisan hands sculpting a minimalist paper mache sculpture in a sunlit warm studio, cream and terracotta tones, no text"
    },
    "showcase": {
        "title": "🖼️ معرفی اثر جدید و جزئیات دکور",
        "desc": "معرفی شاعرانه یک مجسمه دکوراتیو پاپیه‌ماشه که به خانه روح و گرما می‌بخشد.",
        "visual": "Minimalist luxury home decor shelf with a textured handmade paper mache sculpture, warm morning sunlight, cream palette, no text"
    },
    "workshop": {
        "title": "🛠️ آموزش تکنیک خمیر و چسب",
        "desc": "یک نکته طلایی کارگاهی درباره ترکیب خمیر کاغذ، چسب چوب و سمباده‌زنی برای صاف شدن سطح مجسمه بنویس.",
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
                InlineKeyboardButton("🖼️ ساخت کاروسل تصویری", callback_data=f"act:{slug}:carousel"),
            ],
            [InlineKeyboardButton("🎬 ریلز ۵ سکانسی (ویدیو + نریشن)", callback_data=f"act:{slug}:reel")],
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
            "آماده‌ام تا برای هر ۳ پیج تو استوری گرافیکی، کاروسل و ریلز ۵ سکانسی با تصویر هوش مصنوعی بسازم!",
            reply_markup=self._main_menu(),
            parse_mode="Markdown",
        )

    async def _build_single_story(self, page: dict, cat_key: str) -> tuple[str, str, str]:
        """ساخت استوری به روش ربات قبلی: ۱. تولید JSON فارسی ۲. ساخت تصویر کلودفلر ۳. رندر گرافیکی"""
        cat = STORY_CATS_CONFIG.get(cat_key, STORY_CATS_CONFIG["t_market"])
        slug = page["slug"]

        prompt = (
            f"تو نویسنده ارشد پیج «{page['title']}» هستی.\n"
            f"سبک استوری: {cat['title']}\n"
            f"ماموریت: {cat['desc']}\n"
            "فقط یک JSON معتبر با کلیدهای زیر به زبان فارسی برگردان:\n"
            '{"heading": "تیتر کوتاه و جذاب فارسی (حداکثر ۶ کلمه)", "body": "متن اصلی استوری به فارسی روان و جذاب (۲ تا ۳ جمله)", "sticker": "متن کوتاه تعاملی فارسی"}'
        )
        story_data = await self.llm.json(prompt, temperature=0.75)
        heading = str(story_data.get("heading") or cat["title"]).strip()
        body = str(story_data.get("body") or "").strip()
        sticker = str(story_data.get("sticker") or "نظر تو چیه؟").strip()

        out_dir = f"data/outputs/{page['id']}/story_{int(time.time())}"
        os.makedirs(out_dir, exist_ok=True)

        # تولید تصویر اختصاصی با کلودفلر (Flux)
        art_path = os.path.join(out_dir, "art.jpg")
        img_ok = await self.llm.generate_image(cat["visual"], art_path)

        out_path = os.path.join(out_dir, "story_final.jpg")
        story_obj = {"heading": heading, "body": body, "sticker": sticker}
        render_story(None, story_obj, out_path, 0, [], None, cat_key, art_path if img_ok else None)

        return out_path, heading, body

    async def _build_carousel(self, page: dict, topic: str) -> tuple[list[str], str]:
        """ساخت کاروسل ۵ اسلایدی با تصویر هوش مصنوعی برای هر اسلاید"""
        slug = page["slug"]
        prompt = (
            f"برای پیج «{page['title']}» درباره موضوع «{topic}» یک کاروسل ۴ اسلایدی به زبان فارسی بساز.\n"
            "فقط JSON معتبر با ساختار زیر برگردان:\n"
            '{"slides": [{"heading": "تیتر فارسی", "body": "توضیح فارسی", "visual": "English image prompt without text"}], "caption": "کپشن فارسی پست"}'
        )
        data = await self.llm.json(prompt, temperature=0.75)
        slides = data.get("slides") or [
            {"heading": topic, "body": "نکات کلیدی و کاربردی که باید بدانید.", "visual": "cinematic conceptual art, 8k, no text"}
        ]
        caption = str(data.get("caption") or f"✨ کاروسل اختصاصی درباره {topic}")

        out_dir = f"data/outputs/{page['id']}/carousel_{int(time.time())}"
        os.makedirs(out_dir, exist_ok=True)

        arts = []
        for i, s in enumerate(slides[:5]):
            art_file = os.path.join(out_dir, f"art_{i}.jpg")
            v_prompt = s.get("visual") or "cinematic masterpiece, high contrast, no text"
            ok = await self.llm.generate_image(v_prompt, art_file)
            arts.append(art_file if ok else None)

        files = await asyncio.to_thread(render_carousel, None, slides[:5], out_dir, [], None, arts, slug)
        return files, caption

    async def _build_reel_video(self, page: dict, topic: str) -> tuple[str | None, list[str], str]:
        """ساخت ریلز ۵ سکانسی همانند ربات قبلی (تولید عکس + صداگذاری + رندر ویدیو)"""
        slug = page["slug"]
        prompt = (
            f"برای پیج «{page['title']}» درباره «{topic}» یک سناریوی ریلز ۵ سکانسی به زبان فارسی بنویس.\n"
            "فقط JSON معتبر با ساختار زیر برگردان:\n"
            '{"title": "عنوان ریلز", "scenes": [{"text": "متن کوتاه فارسی روی تصویر", "voice": "متن نریشن فارسی گوینده", "visual": "English image prompt without text"}]}'
        )
        data = await self.llm.json(prompt, temperature=0.75)
        scenes = (data.get("scenes") or [])[:5]
        if not scenes:
            scenes = [{"text": topic, "voice": topic, "visual": "cinematic vertical background, 8k, no text"}]

        out_dir = f"data/outputs/{page['id']}/reel_{int(time.time())}"
        os.makedirs(out_dir, exist_ok=True)

        frames = []
        audios = []
        texts = []

        for i, sc in enumerate(scenes):
            txt = str(sc.get("text") or f"بخش {i+1}")
            vce = str(sc.get("voice") or txt)
            vis = str(sc.get("visual") or "cinematic dark atmosphere, 8k, no text")
            texts.append(vce)

            art_path = os.path.join(out_dir, f"art_{i}.jpg")
            ok_img = await self.llm.generate_image(vis, art_path)

            frame_path = os.path.join(out_dir, f"frame_{i}.jpg")
            render_reel_frame(None, txt, frame_path, i, [], None, art_path if ok_img else None, slug)
            frames.append(frame_path)

            # تولید صدای فارسی در صورت وجود ماژول core.video
            aud_path = os.path.join(out_dir, f"aud_{i}.mp3")
            try:
                from core.video import synth
                ok_aud = await synth(vce, "fa-IR-FaridNeural", aud_path)
                audios.append(aud_path if ok_aud else None)
            except Exception:
                audios.append(None)

        video_path = os.path.join(out_dir, "final_reel.mp4")
        try:
            from core.video import build_reel
            await asyncio.to_thread(build_reel, frames, audios, texts, video_path)
            if os.path.exists(video_path) and os.path.getsize(video_path) > 1000:
                return video_path, frames, str(data.get("title") or topic)
        except Exception as e:
            log.warning("Video assembly fallback to frames: %s", e)

        return None, frames, str(data.get("title") or topic)

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
                    await q.edit_message_text(f"✍️ موضوع دلخواهت رو برای ساخت «{label}» در پیج «{page['title']}» بنویس:")

        elif data.startswith("st_cat:"):
            _, cat_key, slug = data.split(":")
            page = self.db.get_page_by_slug(slug)
            if page:
                await q.edit_message_text(f"⏳ در حال ساخت تصویر هوش مصنوعی و طراحی استوری برای «{page['title']}»...")
                out_path, heading, body = await self._build_single_story(page, cat_key)
                self.db.save_content(page["id"], "story", heading, {"body": body, "file": out_path})

                caption = f"✅ {heading}\n\n{body}".replace("*", "").replace("_", "")[:950]
                with open(out_path, "rb") as photo_file:
                    await q.message.reply_photo(
                        photo=photo_file,
                        caption=caption,
                        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت به پیج", callback_data=f"page_hub:{slug}")]])
                    )

        elif data == "dept:trading:market_pulse":
            await q.edit_message_text("⏳ در حال تحلیل نبض بازار و بررسی وضعیت کریپتو...")
            ans = await self.llm.generate_text(
                "یک گزارش تحلیلی، جذاب و کاربردی به زبان فارسی درباره وضعیت بازار کریپتو، بیت‌کوین و تله‌های نقدینگی بنویس.",
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

            elif kind == "reel":
                wait = await msg.reply_text(f"⏳ در حال ساخت ۵ سکانس تصویری، نریشن و تدوین ریلز برای «{user_text}»...")
                video_path, frames, title = await self._build_reel_video(page, user_text)
                await wait.delete()
                if video_path and os.path.exists(video_path):
                    with open(video_path, "rb") as vf:
                        await msg.reply_video(
                            video=vf,
                            caption=f"🎬 ریلز تخصصی: {title}",
                            reply_markup=self._department_menu(page),
                        )
                else:
                    for fp in frames:
                        with open(fp, "rb") as ph:
                            await msg.reply_photo(photo=ph)
                    await msg.reply_text(f"✅ فریم‌های ریلز «{title}» آماده شد!", reply_markup=self._department_menu(page))
                return

            else:
                wait = await msg.reply_text("⏳ در حال آماده‌سازی پاسخ کارگاهی...")
                ans = await self.llm.generate_text(
                    f"به عنوان استاد مجسمه‌سازی پاپیه‌ماشه به این سوال به زبان فارسی پاسخ دقیق بده: {user_text}",
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
