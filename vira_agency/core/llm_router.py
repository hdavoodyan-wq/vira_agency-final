"""
لایه آداپتور هوش مصنوعی (LLM Router) با سیستم Fallback هوشمند برای گوگل جمینای
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

        # لیست مدل‌های معتبر به ترتیب اولویت برای جلوگیری از خطای ۴۰۴ یا دسترسی
        models = [
            "gemini-1.5-flash",
            "gemini-1.5-pro",
            "gemini-pro"
        ]

        for model_name in models:
            try:
                res = await asyncio.to_thread(self._call_gemini, full_prompt, temperature, model_name, api_key)
                if res:
                    self.db.log_ai_usage(department, "gemini", model_name, len(full_prompt) // 4)
                    return res
            except Exception as e:
                log.warning("Model %s failed: %s", model_name, e)
                continue

        return "⚠️ خطا در ارتباط با هوش مصنوعی. لطفاً کلید API را بررسی کنید."

    def _call_gemini(self, text: str, temperature: float, model_name: str, api_key: str) -> str:
        url = f"https://generativelanguage.googleapis.com/v1/models/{model_name}:generateContent?key={api_key}"
        payload = {
            "contents": [{"parts": [{"text": text}]}],
            "generationConfig": {"temperature": temperature},
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=45) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        candidates = data.get("candidates") or []
        if candidates:
            parts = candidates[0].get("content", {}).get("parts") or []
            if parts:
                return parts[0].get("text", "").strip()
        return ""
