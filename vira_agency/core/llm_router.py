"""
لایه آداپتور هوش مصنوعی (LLM Router) با اتصال رسمی و صددرصد پایدار به Google Generative AI
"""
import asyncio
import logging
import os
from vira_agency.core.config import AgencyConfig
from vira_agency.core.database import AgencyDatabase

log = logging.getLogger(__name__)


class LLMRouter:
    def __init__(self, cfg: AgencyConfig, db: AgencyDatabase):
        self.cfg = cfg
        self.db = db

    async def generate_text(self, prompt: str, system_prompt: str = "", department: str = "CEO", temperature: float = 0.7) -> str:
        full_prompt = f"{system_prompt}\n\n{prompt}".strip() if system_prompt else prompt

        # پیدا کردن کلید API از راه‌های مختلف برای جلوگیری از خالی بودن
        api_key = self.cfg.gemini_api_key
        if not api_key:
            for k in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "BOT_TOKEN"):
                val = os.getenv(k, "").strip()
                if val.startswith("AIza"):
                    api_key = val
                    break

        if not api_key:
            return "⚠️ خطا: کلید GEMINI_API_KEY در پنل رندر تنظیم نشده است."

        try:
            import google.generativeai as genai

            # تنظیم رسمی کلید API
            genai.configure(api_key=api_key)

            # استفاده از مدل استاندارد و پایدار جمینای
            model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                generation_config={"temperature": temperature}
            )

            # اجرای درخواست به صورت ناهمگام (Async)
            response = await asyncio.to_thread(model.generate_content, full_prompt)
            
            if response and response.text:
                ans = response.text.strip()
                self.db.log_ai_usage(department, "google-genai", "gemini-1.5-flash", len(full_prompt) // 4)
                return ans

            return "⚠️ پاسخ معتبری از هوش مصنوعی دریافت نشد."

        except Exception as e:
            log.exception("Google GenAI official SDK error")
            return f"⚠️ خطای ارتباط با هوش مصنوعی: {str(e)[:180]}"
