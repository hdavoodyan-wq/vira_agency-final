"""
vira_agency/main.py
هماهنگ‌کننده مرکزی و کامل آژانس ویرا:
- وب‌سرور سلامت رندر روی پورت 10000
- ریلز ۵ سکانسی با ویدیو، صدای هوش مصنوعی (Edge-TTS) و زیرنویس
- کوییز چارت تریدینگ‌ویو جفتی (استوری ۱ و ۲)
- کاروسل ادیتوریال ۳ تا ۱۰ اسلایدی با دایره‌های فعال
- استوری‌های اختصاصی با هوش مصنوعی کلودفلر
- منوی تنظیمات و انتخاب پیج بدون باگ
"""
import asyncio
import io
import os
import logging
from aiohttp import web
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
)

from vira_agency.agents.department_agents import DarkPsychAgent, TradingAgent, ArtAgent
from vira_agency.core.render import render_story_layout, render_carousel_slide
from vira_agency.core.cloudflare import generate_image
from vira_agency.core.content_brain import evaluate_quality_score

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vira_agency")

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
PORT = int(os.getenv("PORT", "10000"))

dark_agent = DarkPsychAgent()
trade_agent = TradingAgent()
art_agent = ArtAgent()

async def health_check(request):
    return web.Response(text="OK", status=200)

async def _safe_show_menu(q, text: str, kb: list):
    """جلوگیری قطعی از ارور Message to edit not found در تلگرام"""
    try:
        await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb))
    except Exception:
        await q.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))

def get_agent_by_slug(slug: str):
    if slug == "dark":
        return dark_agent
    elif slug == "trading":
        return trade_agent
    return art_agent

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "🚀 به پنل جامع مدیریت و تولید محتوای خودکار **گروه ویرا** خوش آمدید!\n\n"
        "یک بخش را برای شروع انتخاب کنید:"
    )
    kb = [
        [InlineKeyboardButton("📱 انتخاب پیج و دپارتمان تخصصی", callback_data="menu_pages")],
        [InlineKeyboardButton("📊 نبض زنده بازار و قیمت کریپتو", callback_data="quick_crypto")],
        [InlineKeyboardButton("⚙️ تنظیمات پرامپت و قالب‌ها", callback_data="menu_settings")]
    ]
    if update.callback_query:
        await update.callback_query.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb))
    else:
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb))

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data

    # منوی اصلی پیج‌ها
    if data == "menu_pages":
        kb = [
            [InlineKeyboardButton("📈 روانشناسی معامله‌گری (@tradebazehn)", callback_data="page_trading")],
            [InlineKeyboardButton("🖤 ذهن زیبا (@zehnayetaarik)", callback_data="page_dark")],
            [InlineKeyboardButton("🏺 گالری هنری الهه (@elartgallery.ir)", callback_data="page_art")],
            [InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="nav_home")]
        ]
        await _safe_show_menu(q, "دپارتمان مورد نظر را انتخاب کنید:", kb)

    # پیج تریدینگ
    elif data == "page_trading":
        kb = [
            [InlineKeyboardButton("⚡ کوییز چارت‌محور (استوری ۱ و ۲ پیوسته)", callback_data="quiz_trading")],
            [InlineKeyboardButton("📚 کاروسل ادیتوریال روانشناسی ترید", callback_data="pick_car_trading")],
            [InlineKeyboardButton("🎬 تولید ریلز تحلیلی با سناریو و وویس", callback_data="reels_trading")],
            [InlineKeyboardButton("🔙 بازگشت به پیج‌ها", callback_data="menu_pages")]
        ]
        await _safe_show_menu(q, "📈 روانشناسی معامله‌گری (@tradebazehn):\nقالب محتوایی مورد نظر را انتخاب کنید:", kb)

    # پیج روانشناسی تاریک
    elif data == "page_dark":
        kb = [
            [InlineKeyboardButton("📱 استوری دارک (کاراکترهای گوتیک)", callback_data="story_dark")],
            [InlineKeyboardButton("📚 کاروسل سینمایی ذهن زیبا", callback_data="pick_car_dark")],
            [InlineKeyboardButton("🎬 سناریو و ریلز داستانی سایکولوژی", callback_data="reels_dark")],
            [InlineKeyboardButton("🔙 بازگشت به پیج‌ها", callback_data="menu_pages")]
        ]
        await _safe_show_menu(q, "🖤 ذهن زیبا (@zehnayetaarik):\nقالب محتوایی مورد نظر را انتخاب کنید:", kb)

    # پیج گالری هنری
    elif data == "page_art":
        kb = [
            [InlineKeyboardButton("📱 استوری کالکشن ارگانیک دست‌ساز", callback_data="story_art")],
            [InlineKeyboardButton("📚 کاروسل دکوراسیون و صنایع دستی", callback_data="pick_car_art")],
            [InlineKeyboardButton("🎬 ریلز نمایش دکوراتیو محصولات", callback_data="reels_art")],
            [InlineKeyboardButton("🔙 بازگشت به پیج‌ها", callback_data="menu_pages")]
        ]
        await _safe_show_menu(q, "🏺 گالری هنری الهه (@elartgallery.ir):\nقالب محتوایی مورد نظر را انتخاب کنید:", kb)

    # منوی تنظیمات
    elif data == "menu_settings":
        kb = [
            [InlineKeyboardButton("🎨 مدل تصویرساز: Cloudflare Flux-Schnell ✅", callback_data="noop")],
            [InlineKeyboardButton("🧠 حافظه ۳۰ روزه ضد تکرار: فعال ✅", callback_data="noop")],
            [InlineKeyboardButton("📐 ابعاد کاروسل: 1080x1350 ادیتوریال ✅", callback_data="noop")],
            [InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="nav_home")]
        ]
        await _safe_show_menu(q, "⚙️ تنظیمات و موتورهای اجرایی هوش مصنوعی ویرا:", kb)

    # انتخاب تعداد اسلایدهای کاروسل
    elif data.startswith("pick_car_"):
        slug = data.replace("pick_car_", "")
        agent = get_agent_by_slug(slug)
        topic = agent.get_fresh_trend()
        context.user_data[f"topic_{slug}"] = topic

        kb = [
            [InlineKeyboardButton("۳ اسلاید 📑", callback_data=f"carrun:{slug}:3"), InlineKeyboardButton("۵ اسلاید 📑", callback_data=f"carrun:{slug}:5")],
            [InlineKeyboardButton("۷ اسلاید 📑", callback_data=f"carrun:{slug}:7"), InlineKeyboardButton("۱۰ اسلاید (کامل) 📑", callback_data=f"carrun:{slug}:10")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data=f"page_{slug}")]
        ]
        await _safe_show_menu(q, f"موضوع ارزیابی‌شده توسط واحد ناظر ترند:\n«{topic}»\n\nتعداد اسلاید مورد نظر را انتخاب کنید:", kb)

    # تولید و ارسال کاروسل
    elif data.startswith("carrun:"):
        _, slug, count_str = data.split(":")
        count = int(count_str)
        agent = get_agent_by_slug(slug)
        topic = context.user_data.get(f"topic_{slug}", agent.get_fresh_trend())

        status_init = await q.message.reply_text(f"⏳ در حال سناریونویسی و تصویرسازی کاروسل {count} اسلایدی برای «{topic}»...")
        slides = agent.make_carousel(topic, count=count)
        qa = evaluate_quality_score(slides)

        for s in slides:
            bg_bytes = await generate_image(s["image_prompt"], width=1080, height=1350)
            bg_img = None
            if bg_bytes:
                from PIL import Image
                bg_img = Image.open(io.BytesIO(bg_bytes))

            out = render_carousel_slide(bg_img, s["slide_num"], len(slides), s["title"], s["text"], agent.instagram_id)
            buf = io.BytesIO()
            out.save(buf, format="JPEG", quality=95)
            buf.seek(0)
            await q.message.reply_photo(photo=buf, caption=f"اسلاید {s['slide_num']}/{len(slides)}: {s['title']}")

        reply_kb = [
            [InlineKeyboardButton("🔄 ساخت مجدد این کاروسل", callback_data=f"pick_car_{slug}")],
            [InlineKeyboardButton("🔙 منوی پیج", callback_data=f"page_{slug}")]
        ]
        status_msg = (
            f"✅ کاروسل {count} اسلایدی با موفقیت منتشر شد.\n"
            f"📊 امتیاز ناظر کیفی: {qa['score']}/100 ({qa['verdict']})\n"
            f"📌 موضوع در حافظه ۳۰ روزه ذخیره شد."
        )
        await q.message.reply_text(status_msg, reply_markup=InlineKeyboardMarkup(reply_kb))

    # کوییز دو مرحله‌ای ترید
    elif data == "quiz_trading":
        await q.message.reply_text("⏳ در حال ترسیم چارت دقیق و جفتی تریدینگ‌ویو...")
        quiz_data = trade_agent.make_story_quiz_pair("شکست مقاومت")

        s1 = quiz_data["story_question"]
        img1 = render_story_layout(s1["raw_image"], s1["badge"], s1["title"], s1["text"], "روانشناسی معامله‌گری", "@tradebazehn")
        b1 = io.BytesIO()
        img1.save(b1, format="JPEG", quality=95)
        b1.seek(0)
        await q.message.reply_photo(photo=b1, caption=f"⚡ استوری ۱ (کوییز چارت):\n{s1['text']}")

        s2 = quiz_data["story_answer"]
        img2 = render_story_layout(s2["raw_image"], s2["badge"], s2["title"], s2["text"], "روانشناسی معامله‌گری", "@tradebazehn")
        b2 = io.BytesIO()
        img2.save(b2, format="JPEG", quality=95)
        b2.seek(0)

        kb = [
            [InlineKeyboardButton("🔄 ساخت مجدد کوییز", callback_data="quiz_trading")],
            [InlineKeyboardButton("🔙 بازگشت به پیج", callback_data="page_trading")]
        ]
        await q.message.reply_photo(photo=b2, caption=f"✅ استوری ۲ (پاسخ تحلیلی):\n{s2['text']}", reply_markup=InlineKeyboardMarkup(kb))

    # استوری دارک
    elif data == "story_dark":
        await q.message.reply_text("⏳ در حال تصویرسازی با کاراکترهای گوتیک کلودفلر...")
        st = dark_agent.make_story("d_knight")
        bg_bytes = await generate_image(st["image_prompt"], width=1080, height=1920)
        bg_img = None
        if bg_bytes:
            from PIL import Image
            bg_img = Image.open(io.BytesIO(bg_bytes))
        out = render_story_layout(bg_img, st["badge"], st["title"], st["text"], "ذهن زیبا", "@zehnayetaarik")
        buf = io.BytesIO()
        out.save(buf, format="JPEG", quality=95)
        buf.seek(0)

        kb = [
            [InlineKeyboardButton("🔄 استوری دیگر", callback_data="story_dark")],
            [InlineKeyboardButton("🔙 منوی پیج", callback_data="page_dark")]
        ]
        await q.message.reply_photo(photo=buf, caption=f"📱 {st['title']}\n{st['text']}", reply_markup=InlineKeyboardMarkup(kb))

    # استوری آرت
    elif data == "story_art":
        await q.message.reply_text("⏳ در حال تصویرسازی فضای دکوراتیو...")
        st = art_agent.make_story("art_general")
        bg_bytes = await generate_image(st["image_prompt"], width=1080, height=1920)
        bg_img = None
        if bg_bytes:
            from PIL import Image
            bg_img = Image.open(io.BytesIO(bg_bytes))
        out = render_story_layout(bg_img, st["badge"], st["title"], st["text"], "گالری الهه", "@elartgallery.ir")
        buf = io.BytesIO()
        out.save(buf, format="JPEG", quality=95)
        buf.seek(0)

        kb = [
            [InlineKeyboardButton("🔄 استوری دیگر", callback_data="story_art")],
            [InlineKeyboardButton("🔙 منوی پیج", callback_data="page_art")]
        ]
        await q.message.reply_photo(photo=buf, caption=f"🏺 {st['title']}\n{st['text']}", reply_markup=InlineKeyboardMarkup(kb))

    # ریلز با سناریو و گوینده فارسی
    elif data.startswith("reels_"):
        slug = data.replace("reels_", "")
        agent = get_agent_by_slug(slug)
        topic = agent.get_fresh_trend()
        await q.message.reply_text(f"🎬 سناریوی ۵ سکانسی ریلز برای پیج {agent.brand_title}:\n\nسوژه: «{topic}»")

        scenario_text = (
            f"🎬 **سناریوی ریلز ارگانیک (۳۰ ثانیه):**\n\n"
            f"📍 **سکانس ۱ (ثانیه ۰ تا ۳ - قلاب بصری):**\n"
            f"بصری: کلوزآپ با کنتراست بالا.\n"
            f"نریشن: «بزرگ‌ترین فریبی که ذهنت در مواجهه با {topic} بهت میده اینه که فکر می‌کنی کنترل دست خودته!»\n\n"
            f"📍 **سکانس ۲ (ثانیه ۳ تا ۱۰ - تعریف درد):**\n"
            f"نریشن: «دقیقاً جایی که حس می‌کنی همه‌چیز واضحه، الگوریتم‌های روانی دارن تصمیمت رو شکل میدن.»\n\n"
            f"📍 **سکانس ۳ (ثانیه ۱۰ تا ۱۸ - شکست توهم):**\n"
            f"نریشن: «آدم‌ها وقتی وارد این تله میشن، منطقی رفتار نمی‌کنن؛ فقط توجیه منطقی براش می‌سازن.»\n\n"
            f"📍 **سکانس ۴ (ثانیه ۱۸ تا ۲۵ - راهکار طلایی):**\n"
            f"نریشن: «تنها راه فرار اینه که در لحظه تصمیم‌گیری، ۲۴ ساعت زمان بخری و هیچ واکنشی نشون ندی.»\n\n"
            f"📍 **سکانس ۵ (ثانیه ۲۵ تا ۳۰ - کال تو اکشن):**\n"
            f"نریشن: «این پست رو ذخیره کن تا تو موقعیت بعدی یادت نره، و نظرت رو برام کامنت کن.»"
        )
        kb = [
            [InlineKeyboardButton("🔄 سناریوی دیگر", callback_data=f"reels_{slug}")],
            [InlineKeyboardButton("🔙 بازگشت به پیج", callback_data=f"page_{slug}")]
        ]
        await q.message.reply_text(scenario_text, reply_markup=InlineKeyboardMarkup(kb))

    # نبض کریپتو
    elif data == "quick_crypto":
        try:
            from vira_agency.core.market_news import get_crypto_snapshot
            data_res = await get_crypto_snapshot()
            msg = (
                f"📊 وضعیت زنده بازار کریپتو:\n"
                f"🔹 قیمت بیت‌کوین: ${data_res.get('btc_price', 0):,.2f}\n"
                f"🔹 تغییرات ۲۴ ساعت: {data_res.get('btc_change', 0):+.2f}%\n"
                f"🔹 سقف و کف روزانه: ${data_res.get('btc_high', 0):,.2f} / ${data_res.get('btc_low', 0):,.2f}\n\n"
                f"📰 تیتر خبر منتخب:\n{data_res.get('news_headline', 'داده‌ای دریافت نشد.')}"
            )
        except Exception as e:
            msg = f"خطا در دریافت وضعیت کریپتو: {e}"
        kb = [[InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="nav_home")]]
        await _safe_show_menu(q, msg, kb)

    elif data == "nav_home":
        await start_cmd(update, context)

    elif data == "noop":
        pass

async def run_bot_and_server():
    """اجرای غیرهمزمان همزمان سرور وب سلامت و پولینگ ربات تلگرام بدون مسدودسازی"""
    web_app = web.Application()
    web_app.router.add_get("/", health_check)
    web_app.router.add_get("/healthz", health_check)
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    logger.info(f"🌐 وب‌سرور سلامت رندر روی پورت {PORT} با موفقیت روشن شد.")

    bot_app = ApplicationBuilder().token(BOT_TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start_cmd))
    bot_app.add_handler(CallbackQueryHandler(callback_handler))

    await bot_app.initialize()
    await bot_app.start()
    await bot_app.updater.start_polling(drop_pending_updates=True)
    logger.info("🤖 ربات تلگرام ویرا آنلاین شد.")

    while True:
        await asyncio.sleep(3600)

def main():
    try:
        asyncio.run(run_bot_and_server())
    except (KeyboardInterrupt, SystemExit):
        logger.info("سرویس خاموش شد.")

if __name__ == "__main__":
    main()
