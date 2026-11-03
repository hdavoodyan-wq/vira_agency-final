"""
vira_agency/main.py
هماهنگ‌کننده مرکزی ربات تلگرام با وب‌سرور سلامت رندر و سیستم تولید محتوای ناظر
"""
import asyncio
import io
import os
import logging
from aiohttp import web
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

from vira_agency.agents.department_agents import DarkPsychAgent, TradingAgent, ArtAgent
from vira_agency.core.render import render_story_layout, render_carousel_slide
from vira_agency.core.cloudflare import generate_image
from vira_agency.core.content_brain import evaluate_quality_score

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("vira_agency")

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

dark_agent = DarkPsychAgent()
trade_agent = TradingAgent()
art_agent = ArtAgent()

async def health_check(request):
    return web.Response(text="OK", status=200)

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", health_check)
    app.router.add_get("/healthz", health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 10000)
    await site.start()

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "سلام! دستیار هوشمند آژانس ویرا آماده تولید محتواست 🤖✨"
    kb = [
        [InlineKeyboardButton("🎨 انتخاب پیج برای تولید محتوا", callback_data="menu_pages")],
        [InlineKeyboardButton("📈 نبض و تحلیل زنده کریپتو", callback_data="quick_crypto")]
    ]
    if update.callback_query:
        await update.callback_query.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb))
    else:
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb))

async def _safe_show_menu(q, text: str, kb: list):
    try:
        await q.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb))
    except Exception:
        await q.message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb))

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data

    if data == "menu_pages":
        kb = [
            [InlineKeyboardButton("📈 روانشناسی معامله‌گری (@tradebazehn)", callback_data="page_trading")],
            [InlineKeyboardButton("🖤 ذهن زیبا (@zehnayetaarik)", callback_data="page_dark")],
            [InlineKeyboardButton("🏺 گالری هنری الهه (@elartgallery.ir)", callback_data="page_art")],
            [InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="nav_home")]
        ]
        await _safe_show_menu(q, "پیج مورد نظر را انتخاب کنید:", kb)

    elif data == "page_trading":
        kb = [
            [InlineKeyboardButton("⚡ کوییز چارت‌محور (استوری ۱ و ۲ پیوسته)", callback_data="quiz_trading")],
            [InlineKeyboardButton("📚 کاروسل ادیتوریال روانشناسی ترید", callback_data="pick_car_trading")],
            [InlineKeyboardButton("🔙 بازگشت به پیج‌ها", callback_data="menu_pages")]
        ]
        await _safe_show_menu(q, "روانشناسی معامله‌گری (@tradebazehn):", kb)

    elif data == "page_dark":
        kb = [
            [InlineKeyboardButton("📱 استوری دارک (کاراکترهای گوتیک)", callback_data="story_dark")],
            [InlineKeyboardButton("📚 کاروسل سینمایی ذهن زیبا", callback_data="pick_car_dark")],
            [InlineKeyboardButton("🔙 بازگشت به پیج‌ها", callback_data="menu_pages")]
        ]
        await _safe_show_menu(q, "ذهن زیبا (@zehnayetaarik):", kb)

    elif data == "page_art":
        kb = [
            [InlineKeyboardButton("📱 استوری کالکشن ارگانیک", callback_data="story_art")],
            [InlineKeyboardButton("📚 کاروسل دکوراسیون و صنایع دستی", callback_data="pick_car_art")],
            [InlineKeyboardButton("🔙 بازگشت به پیج‌ها", callback_data="menu_pages")]
        ]
        await _safe_show_menu(q, "گالری هنری الهه (@elartgallery.ir):", kb)

    elif data.startswith("pick_car_"):
        slug = data.replace("pick_car_", "")
        agent = dark_agent if slug == "dark" else (trade_agent if slug == "trading" else art_agent)
        topic = agent.get_fresh_trend()
        context.user_data[f"topic_{slug}"] = topic

        kb = [
            [InlineKeyboardButton("۳ اسلاید 📑", callback_data=f"carrun:{slug}:3"), InlineKeyboardButton("۵ اسلاید 📑", callback_data=f"carrun:{slug}:5")],
            [InlineKeyboardButton("۷ اسلاید 📑", callback_data=f"carrun:{slug}:7"), InlineKeyboardButton("۱۰ اسلاید (کامل) 📑", callback_data=f"carrun:{slug}:10")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data=f"page_{slug}")]
        ]
        await _safe_show_menu(q, f"موضوع ارزیابی‌شده توسط ناظر محتوا:\n«{topic}»\n\nتعداد اسلاید مورد نظر را انتخاب کنید:", kb)

    elif data.startswith("carrun:"):
        _, slug, count_str = data.split(":")
        count = int(count_str)
        agent = dark_agent if slug == "dark" else (trade_agent if slug == "trading" else art_agent)
        topic = context.user_data.get(f"topic_{slug}", agent.get_fresh_trend())

        await q.message.reply_text(f"⏳ در حال پردازش کاروسل {count} اسلایدی با سوژه: «{topic}»...")
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
            await q.message.reply_photo(photo=buf, caption=f"اسلاید {s['slide_num']}: {s['title']}")

        reply_kb = [
            [InlineKeyboardButton("🔄 ساخت مجدد همین بخش", callback_data=f"pick_car_{slug}")],
            [InlineKeyboardButton("🔙 بازگشت به منوی پیج", callback_data=f"page_{slug}")]
        ]
        status_msg = f"✅ کاروسل {count} اسلایدی با موفقیت منتشر شد.\n📊 ارزیابی کیفی ناظر محتوا: {qa['score']}/100 ({qa['verdict']})"
        await q.message.reply_text(status_msg, reply_markup=InlineKeyboardMarkup(reply_kb))

    elif data == "quiz_trading":
        await q.message.reply_text("⏳ در حال ترسیم جفت چارت تریدینگ‌ویو...")
        quiz_data = trade_agent.make_story_quiz_pair("شکست مقاومت")

        s1 = quiz_data["story_question"]
        img1 = render_story_layout(s1["raw_image"], s1["badge"], s1["title"], s1["text"], "روانشناسی معامله‌گری", "@tradebazehn")
        b1 = io.BytesIO()
        img1.save(b1, format="JPEG", quality=95)
        b1.seek(0)
        await q.message.reply_photo(photo=b1, caption=f"⚡ استوری ۱ (سوال):\n{s1['text']}")

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

    elif data == "story_dark":
        await q.message.reply_text("⏳ در حال تولید استوری دارک گوتیک...")
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
            [InlineKeyboardButton("🔄 ساخت مجدد استوری", callback_data="story_dark")],
            [InlineKeyboardButton("🔙 بازگشت به پیج", callback_data="page_dark")]
        ]
        await q.message.reply_photo(photo=buf, caption=f"📱 {st['title']}\n{st['text']}", reply_markup=InlineKeyboardMarkup(kb))

    elif data == "story_art":
        await q.message.reply_text("⏳ در حال تولید استوری کالکشن گالری...")
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
            [InlineKeyboardButton("🔄 ساخت مجدد استوری", callback_data="story_art")],
            [InlineKeyboardButton("🔙 بازگشت به پیج", callback_data="page_art")]
        ]
        await q.message.reply_photo(photo=buf, caption=f"🏺 {st['title']}\n{st['text']}", reply_markup=InlineKeyboardMarkup(kb))

    elif data == "quick_crypto":
        from vira_agency.core.market_news import get_crypto_snapshot
        data_res = await get_crypto_snapshot()
        msg = (
            f"📊 وضعیت زنده بازار کریپتو:\n"
            f"🔹 قیمت بیت‌کوین: ${data_res.get('btc_price', 0):,.2f}\n"
            f"🔹 تغییرات ۲۴ ساعت: {data_res.get('btc_change', 0):+.2f}%\n"
            f"🔹 سقف و کف روزانه: ${data_res.get('btc_high', 0):,.2f} / ${data_res.get('btc_low', 0):,.2f}\n\n"
            f"📰 تیتر خبر منتخب:\n{data_res.get('news_headline', 'داده‌ای دریافت نشد.')}"
        )
        kb = [[InlineKeyboardButton("🔙 بازگشت به خانه", callback_data="nav_home")]]
        await _safe_show_menu(q, msg, kb)

    elif data == "nav_home":
        await start_cmd(update, context)

def main():
    asyncio.run(start_web_server())
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CallbackQueryHandler(callback_handler))
    logger.info("دستیار ویرا آنلاین است.")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
