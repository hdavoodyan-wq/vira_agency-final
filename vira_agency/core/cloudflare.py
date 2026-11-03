"""
vira_agency/core/cloudflare.py
موتور تولید تصویر Cloudflare Workers AI با پشتیبانی کامل از Base64 JSON و Binary
"""
import os
import base64
import aiohttp
import logging
from typing import Optional

logger = logging.getLogger("vira_agency.cloudflare")

MODEL_NAME = "@cf/black-forest-labs/flux-1-schnell"

async def generate_image(prompt: str, width: int = 1080, height: int = 1350) -> Optional[bytes]:
    account_id = (
        os.getenv("CLOUDFLARE_ACCOUNT_ID")
        or os.getenv("CF_ACCOUNT_ID")
        or ""
    ).strip()
    api_token = (
        os.getenv("CLOUDFLARE_API_TOKEN")
        or os.getenv("CF_API_TOKEN")
        or ""
    ).strip()

    if not account_id or not api_token:
        logger.error("❌ CLOUDFLARE_ACCOUNT_ID یا CLOUDFLARE_API_TOKEN در متغیرهای محیطی یافت نشد!")
        return None

    url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{MODEL_NAME}"
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }

    clean_prompt = (
        f"{prompt}, masterpiece, cinematic lighting, ultra detailed, 8k resolution, "
        "sharp focus, photorealistic, no text, no letters, no watermark, no signature"
    )
    payload = {
        "prompt": clean_prompt,
        "steps": 4
    }

    try:
        timeout = aiohttp.ClientTimeout(total=50)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, headers=headers, json=payload) as resp:
                if resp.status != 200:
                    err = await resp.text()
                    logger.error(f"❌ خطای کلودفلر ({resp.status}): {err}")
                    return None

                content_type = resp.headers.get("Content-Type", "")
                if "application/json" in content_type:
                    data = await resp.json()
                    b64_img = data.get("result", {}).get("image")
                    if b64_img:
                        img_bytes = base64.b64decode(b64_img)
                        logger.info(f"✅ تصویر Base64 از کلودفلر دریافت و دیکود شد ({len(img_bytes)} bytes).")
                        return img_bytes
                    logger.error(f"❌ کلید image در JSON کلودفلر نبود: {data}")
                    return None
                else:
                    raw_bytes = await resp.read()
                    if raw_bytes and len(raw_bytes) > 500:
                        try:
                            import json
                            parsed = json.loads(raw_bytes.decode("utf-8"))
                            b64_img = parsed.get("result", {}).get("image")
                            if b64_img:
                                return base64.b64decode(b64_img)
                        except Exception:
                            pass
                        logger.info(f"✅ تصویر باینری کلودفلر دریافت شد ({len(raw_bytes)} bytes).")
                        return raw_bytes
                    return None
    except Exception as e:
        logger.error(f"❌ استثنا در ارتباط با کلودفلر: {e}")
        return None
