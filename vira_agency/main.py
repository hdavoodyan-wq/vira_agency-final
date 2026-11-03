"""
vira_agency/main.py
هماهنگ‌کننده کامل ربات تلگرام گروه ویرا با تمامی زیرمنوهای اصلی، انتخاب کاراکترها،
انتخاب موضوع خودکار یا دستی توسط کاربر، کاروسل ۳ تا ۱۰ اسلایدی و وب‌سرور پورت ۱۰۰۰۰
"""
import asyncio
import io
import os
import logging
from aiohttp import web
from PIL import Image
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

# دیکشنری کاراکترهای اختصاصی استوری ذهن زیبا
DARK_STORY_STYLES = {
    "d_knight": (
        "دوراهی شوالیه تاریک",
        "بزرگ‌ترین تله روانی این است که برای راضی نگه داشتن دیگران، مرزهای خودت را زیر پا بگذاری.",
        "Gothic skeleton knight in battle-worn obsidian armor standing at dark crossroads, cinematic dark fantasy, 8k, no text"
    ),
    "d_fox": (
        "فریب و مکر (روباه نقاب‌دار)",
        "مراقب کسانی باش که بیش از حد با تو هم‌ذات‌پنداری می‌کنند؛ روباه قبل از شکار، نقش دوست را بازی می‌کند.",
        "Cunning anthropomorphic theatrical fox wearing ornate Venetian mask in dark moody velvet room, chiaroscuro lighting, no text"
    ),
    "d_wolf": (
        "استقلال عاطفی (گرگ تنها)",
        "وقتی از تنها ماندن نترسی، هیچ‌کس نمی‌تواند با تهدید به رفتن تو را کنترل کند.",
        "Lone majestic dark werewolf in dense foggy mystical forest under moonlight, glowing amber eyes, cinematic 8k, no text"
    ),
    "d_lady": (
        "راز کاریزما و جذابیت (بانوی مرموز)",
        "همه رازهایت را فاش نکن؛ افراد پیش‌بینی‌ناپذیر همیشه ذهن مخاطب را درگیر نگه می‌دارند.",
        "Mysterious elegant gothic aristocrat lady wearing ornate lace masquerade mask, dark crimson rose, cinematic shadows, no text"
    ),
    "d_dracula": (
        "نفوذ و هیپنوتیزم (کنت دراکولا)",
        "نگاه مطمئن و مکث‌های طولانی در صحبت، قدرتمندترین سلاح برای تسخیر ناخودآگاه طرف مقابل است.",
        "Count Dracula in deep crimson velvet cape, intense hypnotic gaze, gothic castle interior, dramatic rim lighting, no text"
    )
}

async def health_check(request):
    return web.Response(text="OK", status=200)

async def _safe_show_menu(q, text: str, kb: list):
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
    context.user_data["awaiting_custom_topic"] = None
    msg = (
        "🚀 دستیار هوشمند تولید محتوای **گروه ویرا** آماده دریافت دستورات است.\n\n"
        "لطفاً بخش مورد نظر خود را انتخاب کنید:"
    )
    kb = [
        [InlineKeyboardButton("📈 روانشناسی معامله‌گری (@tradebazehn)", callback_data="page_trading")],
        [InlineKeyboardButton("🖤 ذهن زیبا (@zehnayetaarik)", callback_data="page_dark")],
        [InlineKeyboardButton("🏺 گالری هنری الهه (@elartgallery.ir)", callback_data="page_art")],
        [InlineKeyboardButton("📊 نبض زنده بازار و قیمت کریپتو", callback_data="quick_crypto")]
    ]
    if update.callback_query:
        await _safe_show_menu(update.callback_query, msg, kb)
    else:
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb))

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data

    if data in ["nav_home", "menu_pages"]:
        await start_cmd(update, context)

    # منوی پیج‌ها
    elif data == "page_trading":
        kb = [
            [InlineKeyboardButton("⚡ کوییز چارت‌محور (استوری ۱ و ۲ پیوسته)", callback_data="quiz_trading")],
            [InlineKeyboardButton("🖼️ ساخت کاروسل اسلایدی", callback_data="carmode_trading")],
            [InlineKeyboardButton("🎬 سناریوی ریلز تحلیلی", callback_data="reels_trading")],
            [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="nav_home")]
        ]
        await _safe_show_menu(q, "📈 بخش «روانشناسی معامله‌گری» (@tradebazehn):\nقالب محتوا را انتخاب کن:", kb)

    elif data == "page_dark":
        kb = [
            [InlineKeyboardButton("📲 انتخاب سبک استوری (کاراکترهای دارک)", callback_data="storymenu_dark")],
            [InlineKeyboardButton("🖼️ ساخت کاروسل اسلایدی", callback_data="carmode_dark")],
            [InlineKeyboardButton("🎬 سناریوی ریلز روانشناسی تاریک", callback_data="reels_dark")],
            [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="nav_home")]
        ]
        await _safe_show_menu(q, "🖤 بخش «ذهن زیبا» (@zehnayetaarik):\nقالب محتوا را انتخاب کن:", kb)

    elif data == "page_art":
        kb = [
            [InlineKeyboardButton("📲 ساخت استوری کالکشن هنری", callback_data="story_art")],
            [InlineKeyboardButton("🖼️ ساخت کاروسل اسلایدی", callback_data="carmode_art")],
            [InlineKeyboardButton("🎬 سناریوی ریلز دکوراتیو", callback_data="reels_art")],
            [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="nav_home")]
        ]
        await _safe_show_menu(q, "🏺 بخش «گالری هنری الهه» (@elartgallery.ir):\nقالب محتوا را انتخاب کن:", kb)

    # زیرمنوی انتخاب کاراکتر استوری برای ذهن زیبا (مطابق اسکرین‌شات)
    elif data == "storymenu_dark":
        kb = [
            [InlineKeyboardButton("🔥 دوراهی شوالیه تاریک", callback_data="dstory:d_knight")],
            [InlineKeyboardButton("🦊 فریب و مکر (روباه نقاب‌دار)", callback_data="dstory:d_fox")],
            [InlineKeyboardButton("🐺 استقلال عاطفی (گرگ تنها)", callback_data="dstory:d_wolf")],
            [InlineKeyboardButton("🥀 راز کاریزما و جذابیت (بانوی مرموز)", callback_data="dstory:d_lady")],
            [InlineKeyboardButton("🩸 نفوذ و هیپنوتیزم (کنت دراکولا)", callback_data="dstory:d_dracula")],
            [InlineKeyboardButton("🔙 بازگشت به پیج", callback_data="page_dark")]
        ]
        await _safe_show_menu(q, "📲 انتخاب سبک استوری برای «🖤 ذهن زیبا»:", kb)

    # اجرای استوری کاراکتر انتخاب‌شده در ذهن زیبا
    elif data.startswith("dstory:"):
        style_key = data.split(":")[1]
        title, text, prompt = DARK_STORY_STYLES.get(style_key, DARK_STORY_STYLES["d_knight"])
        await q.message.reply_text(f"⏳ در حال تصویرسازی کلودفلر برای استوری «{title}»...")

        bg_bytes = await generate_image(prompt, width=1080, height=1920)
        bg_img = Image.open(io.BytesIO(bg_bytes)) if bg_bytes else None

        out = render_story_layout(bg_img, "روانشناسی تاریک", title, text, "ذهن زیبا", "@zehnayetaarik")
        buf = io.BytesIO()
        out.save(buf, format="JPEG", quality=95)
        buf.seek(0)

        kb = [
            [InlineKeyboardButton("🔄 ساخت مجدد همین سبک", callback_data=f"dstory:{style_key}")],
            [InlineKeyboardButton("📲 انتخاب کاراکتر دیگر", callback_data="storymenu_dark")],
            [InlineKeyboardButton("🔙 بازگشت به پیج", callback_data="page_dark")]
        ]
        await q.message.reply_photo(photo=buf, caption=f"🖤 **{title}**\n\n{text}\n\n🆔 @zehnayetaarik", reply_markup=InlineKeyboardMarkup(kb))

    # زیرمنوی نحوه انتخاب موضوع کاروسل (موضوعات ترند خودکار یا انتخاب توسط کاربر)
    elif data.startswith("carmode_"):
        slug = data.replace("carmode_", "")
        agent = get_agent_by_slug(slug)
        kb = [
            [InlineKeyboardButton("🌟 موضوعات ترند خودکار", callback_data=f"pick_car_{slug}")],
            [InlineKeyboardButton("✍️ انتخاب موضوع توسط کاربر", callback_data=f"custom_car_{slug}")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data=f"page_{slug}")]
        ]
        await _safe_show_menu(
            q,
            f"🖼️ ساخت کاروسل اسلایدی برای «{agent.brand_title}»\nلطفاً نحوه انتخاب موضوع را مشخص کن:",
            kb
        )

    # حالت دریافت موضوع دستی از کاربر
    elif data.startswith("custom_car_"):
        slug = data.replace("custom_car_", "")
        context.user_data["awaiting_custom_topic"] = slug
        kb = [[InlineKeyboardButton("🔙 انصراف و بازگشت", callback_data=f"carmode_{slug}")]]
        await _safe_show_menu(
            q,
            "✍️ لطفاً موضوع یا ایده مدنظرت را همین الان در چت تایپ کن و بفرست:",
            kb
        )

    # انتخاب تعداد اسلاید برای موضوع ترند خودکار
    elif data.startswith("pick_car_"):
        slug = data.replace("pick_car_", "")
        agent = get_agent_by_slug(slug)
        topic = agent.get_fresh_trend()
        context.user_data[f"topic_{slug}"] = topic

        kb = [
            [InlineKeyboardButton("۳ اسلاید 📑", callback_data=f"carrun:{slug}:3"), InlineKeyboardButton("۵ اسلاید 📑", callback_data=f"carrun:{slug}:5")],
            [InlineKeyboardButton("۷ اسلاید 📑", callback_data=f"carrun:{slug}:7"), InlineKeyboardButton("۱۰ اسلاید (کامل) 📑", callback_data=f"carrun:{slug}:10")],
            [InlineKeyboardButton("🔄 تغییر موضوع ترند", callback_data=f"pick_car_{slug}")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data=f"carmode_{slug}")]
        ]
        await _safe_show_menu(
            q,
            f"🌟 موضوع پیشنهاد شده توسط واحد ترند (غیرتکراری در ۳۰ روز اخیر):\n«{topic}»\n\nتعداد اسلایدهای کاروسل را انتخاب کن:",
            kb
        )

    # اجرای ساخت کاروسل
    elif data.startswith("carrun:"):
        _, slug, count_str = data.split(":")
        count = int(count_str)
        agent = get_agent_by_slug(slug)
        topic = context.user_data.get(f"topic_{slug}", agent.get_fresh_trend())

        await q.message.reply_text(f"⏳ در حال تولید کاروسل {count} اسلایدی با موضوع:\n«{topic}»\nلطفاً چند لحظه صبر کنید...")
        slides = agent.make_carousel(topic, count=count)
        qa = evaluate_quality_score(slides)

        for s in slides:
            bg_bytes = await generate_image(s["image_prompt"], width=1080, height=1350)
            bg_img = Image.open(io.BytesIO(bg_bytes)) if bg_bytes else None

            out = render_carousel_slide(bg_img, s["slide_num"], len(slides), s["title"], s["text"], agent.instagram_id)
            buf = io.BytesIO()
            out.save(buf, format="JPEG", quality=95)
            buf.seek(0)
            await q.message.reply_photo(photo=buf, caption=f"اسلاید {s['slide_num']}/{len(slides)}: {s['title']}")

        reply_kb = [
            [InlineKeyboardButton("🔄 ساخت مجدد (یکی دیگه بساز)", callback_data=f"pick_car_{slug}")],
            [InlineKeyboardButton("🔙 بازگشت به منوی پیج", callback_data=f"page_{slug}")]
        ]
        caption_summary = (
            f"✅ کاروسل {count} اسلایدی «{agent.brand_title}» آماده شد!\n"
            f"📌 موضوع: {topic}\n"
            f"📊 امتیاز کیفی محتوا: {qa['score']}/100 ({qa['verdict']})\n\n"
            f"آیدی اختصاصی: {agent.instagram_id}"
        )
        await q.message.reply_text(caption_summary, reply_markup=InlineKeyboardMarkup(reply_kb))

    # کوییز چارت تریدینگ‌ویو
    elif data == "quiz_trading":
        await q.message.reply_text("⏳ در حال ترسیم جفت چارت استاندارد تریدینگ‌ویو...")
        quiz_data = trade_agent.make_story_quiz_pair("شکست مقاومت")

        s1 = quiz_data["story_question"]
        img1 = render_story_layout(s1["raw_image"], s1["badge"], s1["title"], s1["text"], "روانشناسی معامله‌گری", "@tradebazehn")
        b1 = io.BytesIO()
        img1.save(b1, format="JPEG", quality=95)
        b1.seek(0)
        await q.message.reply_photo(photo=b1, caption=f"⚡ استوری ۱ (سوال کوییز):\n{s1['text']}")

        s2 = quiz_data["story_answer"]
        img2 = render_story_layout(s2["raw_image"], s2["badge"], s2["title"], s2["text"], "روانشناسی معامله‌گری", "@tradebazehn")
        b2 = io.BytesIO()
        img2.save(b2, format="JPEG", quality=95)
        b2.seek(0)

        kb = [
            [InlineKeyboardButton("🔄 ساخت کوییز جدید", callback_data="quiz_trading")],
            [InlineKeyboardButton("🔙 بازگشت به منوی پیج", callback_data="page_trading")]
        ]
        await q.message.reply_photo(photo=b2, caption=f"✅ استوری ۲ (پاسخ تحلیلی):\n{s2['text']}", reply_markup=InlineKeyboardMarkup(kb))

    # استوری گالری هنری
    elif data == "story_art":
        await q.message.reply_text("⏳ در حال تصویرسازی استوری گالری هنری الهه...")
        st = art_agent.make_story("art_general")
        bg_bytes = await generate_image(st["image_prompt"], width=1080, height=1920)
        bg_img = Image.open(io.BytesIO(bg_bytes)) if bg_bytes else None
        out = render_story_layout(bg_img, st["badge"], st["title"], st["text"], "گالری الهه", "@elartgallery.ir")
        buf = io.BytesIO()
        out.save(buf, format="JPEG", quality=95)
        buf.seek(0)

        kb = [
            [InlineKeyboardButton("🔄 ساخت استوری دیگر", callback_data="story_art")],
            [InlineKeyboardButton("🔙 بازگشت به منوی پیج", callback_data="page_art")]
        ]
        await q.message.reply_photo(photo=buf, caption=f"🏺 {st['title']}\n\n{st['text']}\n\n🆔 @elartgallery.ir", reply_markup=InlineKeyboardMarkup(kb))

    # سناریوی ریلز
    elif data.startswith("reels_"):
        slug = data.replace("reels_", "")
        agent = get_agent_by_slug(slug)
        topic = agent.get_fresh_trend()
        scenario_text = (
            f"🎬 **سناریوی ریلز ۵ سکانسی ({agent.brand_title})**\n"
            f"📌 موضوع: «{topic}»\n\n"
            f"1️⃣ **سکانس اول (ثانیه ۰ تا ۳ - قلاب):**\n"
            f"«فکر می‌کنی در برابر {topic} کاملاً منطقی تصمیم می‌گیری؟ سخت در اشتباهی!»\n\n"
            f"2️⃣ **سکانس دوم (ثانیه ۳ تا ۱۰ - باز کردن مسئله):**\n"
            f"«ذهن ما دقیقاً در لحظات هیجانی، میان‌برهایی می‌زنه که به ضرر ما تموم میشه.»\n\n"
            f"3️⃣ **سکانس سوم (ثانیه ۱۰ تا ۱۸ - نقطه اوج):**\n"
            f"«وقتی متوجه این تله میشی که کار از کار گذشته و هزینه سنگینی دادی.»\n\n"
            f"4️⃣ **سکانس چهارم (ثانیه ۱۸ تا ۲۵ - راهکار عملی):**\n"
            f"«قانون طلایی: در اوج هیجان، دست نگه دار و تصمیم رو به فردا موکول کن.»\n\n"
            f"5️⃣ **سکانس پنجم (ثانیه ۲۵ تا ۳۰ - دعوت به اقدام):**\n"
            f"«این پست رو ذخیره کن و برای کسی که بهش نیاز داره بفرست. آیدی: {agent.instagram_id}»"
        )
        kb = [
            [InlineKeyboardButton("🔄 تولید سناریوی جدید", callback_data=f"reels_{slug}")],
            [InlineKeyboardButton("🔙 بازگشت به منوی پیج", callback_data=f"page_{slug}")]
        ]
        await _safe_show_menu(q, scenario_text, kb)

    # نبض بازار کریپتو
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
            msg = f"خطا در دریافت اطلاعات بازار: {e}"
        kb = [[InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="nav_home")]]
        await _safe_show_menu(q, msg, kb)

async def text_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت موضوع دلخواه تایپ‌شده توسط کاربر برای ساخت کاروسل"""
    slug = context.user_data.get("awaiting_custom_topic")
    if not slug:
        return

    custom_topic = update.message.text.strip()
    context.user_data["awaiting_custom_topic"] = None
    context.user_data[f"topic_{slug}"] = custom_topic

    kb = [
        [InlineKeyboardButton("۳ اسلاید 📑", callback_data=f"carrun:{slug}:3"), InlineKeyboardButton("۵ اسلاید 📑", callback_data=f"carrun:{slug}:5")],
        [InlineKeyboardButton("۷ اسلاید 📑", callback_data=f"carrun:{slug}:7"), InlineKeyboardButton("۱۰ اسلاید (کامل) 📑", callback_data=f"carrun:{slug}:10")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data=f"carmode_{slug}")]
    ]
    await update.message.reply_text(
        f"✅ موضوع دلخواهت ثبت شد:\n«{custom_topic}»\n\nحالا تعداد اسلایدهای کاروسل را انتخاب کن:",
        reply_markup=InlineKeyboardMarkup(kb)
    )

async def run_bot_and_server():
    web_app = web.Application()
    web_app.router.add_get("/", health_check)
    web_app.router.add_get("/healthz", health_check)
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    logger.info(f"🌐 وب‌سرور سلامت روی پورت {PORT} روشن شد.")

    bot_app = ApplicationBuilder().token(BOT_TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start_cmd))
    bot_app.add_handler(CallbackQueryHandler(callback_handler))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_message_handler))

    await bot_app.initialize()
    await bot_app.start()
    await bot_app.updater.start_polling(drop_pending_updates=True)
    logger.info("🤖 ربات تلگرام گروه ویرا آماده به کار است.")

    while True:
        await asyncio.sleep(3600)

def main():
    try:
        asyncio.run(run_bot_and_server())
    except (KeyboardInterrupt, SystemExit):
        logger.info("سرویس متوقف شد.")

if __name__ == "__main__":
    main()
