"""
vira_agency/core/cloudflare.py
موتور اختصاصی و پایدار تولید تصویر با Cloudflare Workers AI (@cf/black-forest-labs/flux-1-schnell)
دارای لاگ شفاف، مدیریت خطای توکن و اعتبارسنجی خروجی بایت‌ها
"""
import os
import aiohttp
import logging
from typing import Optional

logger = logging.getLogger("vira_agency.cloudflare")

CF_ACCOUNT_ID = os.getenv("CLOUDFLARE_ACCOUNT_ID", "")
CF_API_TOKEN = os.getenv("CLOUDFLARE_API_TOKEN", "")
MODEL_NAME = "@cf/black-forest-labs/flux-1-schnell"

async def generate_image(prompt: str, width: int = 1080, height: int = 1350) -> Optional[bytes]:
    """
    تولید تصویر با کیفیت بالا از Cloudflare Workers AI
    خروجی: بایت‌های تصویر JPEG/PNG برای چسباندن روی بوم رندر
    """
    account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID", CF_ACCOUNT_ID).strip()
    api_token = os.getenv("CLOUDFLARE_API_TOKEN", CF_API_TOKEN).strip()

    if not account_id or not api_token:
        logger.error("❌ خطای احراز هویت: CLOUDFLARE_ACCOUNT_ID یا CLOUDFLARE_API_TOKEN در متغیرهای محیطی ست نشده است!")
        return None

    url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{MODEL_NAME}"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    # بهینه‌سازی پرامپت جهت حذف هرگونه متن انگلیسی و افزایش کیفیت بصری
    clean_prompt = f"{prompt}, high resolution, ultra realistic, masterpiece, cinematic lighting, 8k, sharp focus, absolutely no text, no letters, no words, no watermark"
    
    payload = {
        "prompt": clean_prompt,
        "steps": 4
    }

    logger.info(f"🎨 در حال ارسال درخواست به کلودفلر برای سوژه: {prompt[:60]}...")

    try:
        timeout = aiohttp.ClientTimeout(total=45)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status == 200:
                    image_bytes = await response.read()
                    if image_bytes and len(image_bytes) > 1000:
                        logger.info(f"✅ تصویر کلودفلر با موفقیت دریافت شد (حجم: {len(image_bytes)} بایت).")
                        return image_bytes
                    else:
                        logger.warning("⚠️ بایت‌های تصویر دریافتی از کلودفلر نامعتبر یا بسیار کم‌حجم است.")
                        return None
                else:
                    error_text = await response.text()
                    logger.error(f"❌ خطای پاسخ از کلودفلر (کد {response.status}): {error_text}")
                    return None
    except Exception as e:
        logger.error(f"❌ خطا در برقراری ارتباط با سرویس کلودفلر: {e}")
        return None
