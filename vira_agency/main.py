"""
vira_agency/main.py
هماهنگ‌کننده ربات تلگرام با تحویل قطعی استوری‌های جفتی چارت و کاروسل‌های مدرن
"""
import asyncio
import io
import os
import logging
from aiohttp import web
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

from vira_agency.agents.department_agents import DarkPsychAgent, TradingAgent, ArtAgent
from vira_agency.core.render import render_story_layout, render_carousel_slide
from vira_agency.core.cloudflare import generate_image

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
    msg = (
        "سلام! به دستیار هوشمند آژانس ویرا خوش آمدید 🤖✨\n\n"
        "برای شروع، بخش مورد نظرتان را انتخاب کنید:"
    )
    kb = [
        [InlineKeyboardButton("🎨 تولید محتوا (انتخاب پیج)", callback_data="menu_pages")],
        [InlineKeyboardButton("📈 نبض و تحلیل زنده کریپتو", callback_data="quick_crypto")]
    ]
    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(kb))

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data

    if data == "menu_pages":
        kb = [
            [InlineKeyboardButton("📈 روانشناسی معامله‌گری (@tradebazehn)", callback_data="page_trading")],
            [InlineKeyboardButton("🖤 ذهن زیبا (@zehnayetaarik)", callback_data="page_dark")],
            [InlineKeyboardButton("🏺 گالری هنری الهه (@elartgallery.ir)", callback_data="page_art")],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="nav_home")]
        ]
        await q.edit_message_text("یک پیج را جهت تولید محتوا انتخاب کنید:", reply_markup=InlineKeyboardMarkup(kb))

    elif data == "page_trading":
        kb = [
            [InlineKeyboardButton("⚡ کوییز چارت‌محور (استوری ۱ و ۲ پیوسته)", callback_data="quiz_trading")],
            [InlineKeyboardButton("📚 کاروسل ادیتوریال روانشناسی ترید", callback_data="carousel_trading")],
            [InlineKeyboardButton("🔙 بازگشت به پیج‌ها", callback_data="menu_pages")]
        ]
        await q.edit_message_text("بخش مورد نظر برای «روانشناسی معامله‌گری»:", reply_markup=InlineKeyboardMarkup(kb))

    elif data == "page_dark":
        kb = [
            [InlineKeyboardButton("📱 استوری دارک (کاراکترهای گوتیک)", callback_data="story_dark")],
            [InlineKeyboardButton("📚 کاروسل سینمایی ذهن زیبا", callback_data="carousel_dark")],
            [InlineKeyboardButton("🔙 بازگشت به پیج‌ها", callback_data="menu_pages")]
        ]
        await q.edit_message_text("بخش مورد نظر برای «ذهن زیبا»:", reply_markup=InlineKeyboardMarkup(kb))

    elif data == "quiz_trading":
        await q.message.reply_text("⏳ در حال ساخت جفت چارت تریدینگ‌ویو (استوری ۱: سوال + استوری ۲: پاسخ)...")
        quiz_data = trade_agent.make_story_quiz_pair("شکست مقاومت تریدینگ‌ویو")

        # رندر استوری ۱: سوال
        s1 = quiz_data["story_question"]
        img1 = render_story_layout(s1["raw_image"], s1["badge"], s1["title"], s1["text"], "روانشناسی معامله‌گری", "@tradebazehn | روانشناسی معامله‌گری")
        b1 = io.BytesIO()
        img1.save(b1, format="JPEG", quality=95)
        b1.seek(0)
        await q.message.reply_photo(photo=b1, caption=f"⚡ **استوری ۱ (سوال کوییز چارت):**\n\n{s1['text']}\n\n📍 استیکر: {s1['sticker']}")

        # رندر استوری ۲: پاسخ
        s2 = quiz_data["story_answer"]
        img2 = render_story_layout(s2["raw_image"], s2["badge"], s2["title"], s2["text"], "روانشناسی معامله‌گری", "@tradebazehn | روانشناسی معامله‌گری")
        b2 = io.BytesIO()
        img2.save(b2, format="JPEG", quality=95)
        b2.seek(0)
        
        reply_kb = [
            [InlineKeyboardButton("🔄 ساخت مجدد کوییز", callback_data="quiz_trading")],
            [InlineKeyboardButton("🔙 بازگشت به پیج", callback_data="page_trading")]
        ]
        await q.message.reply_photo(photo=b2, caption=f"✅ **استوری ۲ (پاسخ تحلیلی چارت):**\n\n{s2['text']}", reply_markup=InlineKeyboardMarkup(reply_kb))

    elif data in ["carousel_dark", "carousel_trading"]:
        is_dark = data == "carousel_dark"
        agent = dark_agent if is_dark else trade_agent
        topic = "ایزوله‌سازی روانی" if is_dark else "ترس از دست دادن سود"
        await q.message.reply_text("⏳ در حال طراحی کاروسل مجله‌ای (۱۰۸۰×۱۳۵۰) با کاراکترهای اختصاصی...")

        slides = agent.make_carousel(topic, count=4)
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
            [InlineKeyboardButton("🔄 ساخت مجدد کاروسل", callback_data=data)],
            [InlineKeyboardButton("🔙 بازگشت به پیج", callback_data="page_dark" if is_dark else "page_trading")]
        ]
        await q.message.reply_text("✅ تمام اسلایدهای کاروسل با موفقیت رندر شدند.", reply_markup=InlineKeyboardMarkup(reply_kb))

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
