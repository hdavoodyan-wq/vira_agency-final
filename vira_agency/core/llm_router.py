"""
لایه ارتباطی هوش مصنوعی (LLM Router) با مدل ۱۰۰٪ پایدار و بدون خطای گوگل
"""
import asyncio
import json
import logging
import urllib.error
import urllib.request
from typing import Any

from vira_agency.core.config import AgencyConfig
from vira_agency.core.database import AgencyDatabase

log = logging.getLogger(__name__)


class LLMRouter:
    def __init__(self, cfg: AgencyConfig, db: AgencyDatabase):
        self.cfg = cfg
        self.db = db

    async def generate_text(self, prompt: str, system_prompt: str = "", department: str = "CEO", temperature: float = 0.7) -> str:
        full_prompt = f"{system_prompt}\n\n{prompt}".strip() if system_prompt else prompt

        api_key = self.cfg.gemini_api_key
        if not api_key:
            import os
            for k in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "BOT_TOKEN"):
                val = os.getenv(k, "").strip()
                if val.startswith("AIza"):
                    api_key = val
                    break

        if not api_key:
            return "⚠️ خطا: کلید GEMINI_API_KEY در پنل رندر تنظیم نشده است."

        # استفاده از مدل کاملاً آزاد و پایدار gemini-1.5-flash روی اندپوینت رسمی v1
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": full_prompt}]}],
            "generationConfig": {"temperature": temperature},
        }

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            
            def _send():
                with urllib.request.urlopen(req, timeout=45) as resp:
                    return json.loads(resp.read().decode("utf-8"))

            data = await asyncio.to_thread(_send)
            candidates = data.get("candidates") or []
            if candidates:
                parts = candidates[0].get("content", {}).get("parts") or []
                if parts:
                    ans = parts[0].get("text", "").strip()
                    if ans:
                        self.db.log_ai_usage(department, "gemini", "gemini-1.5-flash", len(full_prompt) // 4)
                        return ans
            return "⚠️ پاسخ معتبری از هوش مصنوعی دریافت نشد."
        except Exception as e:
            log.exception("Gemini API connection error")
            return f"⚠️ خطای ارتباط با جمینای: {str(e)[:150]}"
