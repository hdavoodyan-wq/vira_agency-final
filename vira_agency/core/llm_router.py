"""
مسیریاب هوشمند چندموتوره (Multi-Provider LLM Router) با اتصال پایدار به Google Gemini
"""
import asyncio
import json
import logging
import os
import urllib.error
import urllib.request

from vira_agency.core.config import AgencyConfig
from vira_agency.core.database import AgencyDatabase

log = logging.getLogger(__name__)


class LLMRouter:
    def __init__(self, cfg: AgencyConfig, db: AgencyDatabase):
        self.cfg = cfg
        self.db = db

    async def generate_text(self, prompt: str, system_prompt: str = "", department: str = "CEO", temperature: float = 0.7) -> str:
        full_prompt = f"{system_prompt}\n\n{prompt}".strip() if system_prompt else prompt

        # خواندن مستقیم کلید از کانفیگ یا به صورت مستقیم از متغیرهای محیطی رندر
        api_key = getattr(self.cfg, "gemini_api_key", "") or os.getenv("GEMINI_API_KEY", "").strip()
        if not api_key:
            for k in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "GENAI_API_KEY"):
                val = os.getenv(k, "").strip()
                if val.startswith("AIza"):
                    api_key = val
                    break

        if not api_key:
            return "⚠️ خطا: کلید GEMINI_API_KEY در پنل رندر تنظیم نشده است."

        # لیست مدل‌های معتبر و پایدار گوگل به ترتیب اولویت
        models_to_try = [
            "gemini-1.5-flash",
            "gemini-1.5-pro",
            "gemini-pro"
        ]

        last_err = ""
        for model_name in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1/models/{model_name}:generateContent?key={api_key}"
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
                            self.db.log_ai_usage(department, "gemini", model_name, len(full_prompt) // 4)
                            return ans
            except urllib.error.HTTPError as he:
                err_body = he.read().decode("utf-8", errors="ignore")
                last_err = f"{model_name}:{he.code}"
                log.warning("Model %s failed with HTTP %d: %s", model_name, he.code, err_body[:100])
                continue
            except Exception as e:
                last_err = f"{model_name}:{e}"
                log.warning("Model %s failed: %s", model_name, e)
                continue

        return f"⚠️ خطای ارتباط با جمینای (آخرین خطا: {last_err}). لطفاً کلید API را بررسی کنید."
