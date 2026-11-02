"""
لایه آداپتور هوش مصنوعی (Model Provider Adapter) با مدل پایدار و بدون خطای ۴۰۴
"""
import asyncio
import json
import logging
import re
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
        # لیست مدل‌های پیش‌فرض به ترتیب اولویت (از جدیدترین به پایدارترین)
        self.candidate_models = [
            "gemini-2.5-flash",
            "gemini-1.5-flash",
            "gemini-2.0-flash",
            "gemini-pro"
        ]

    async def generate_text(self, prompt: str, system_prompt: str = "", department: str = "CEO", temperature: float = 0.7) -> str:
        full_prompt = f"{system_prompt}\n\n{prompt}".strip() if system_prompt else prompt

        if self.cfg.gemini_api_key:
            for model_name in self.candidate_models:
                try:
                    res = await asyncio.to_thread(self._call_gemini, full_prompt, temperature, model_name)
                    if res:
                        self.db.log_ai_usage(department, "gemini", model_name, len(full_prompt) // 4)
                        return res
                except Exception as e:
                    log.warning("Model %s failed (%s), trying next...", model_name, e)
                    continue

        return "⚠️ ارتباط با هوش مصنوعی برقرار نشد. لطفاً کلید GEMINI_API_KEY را بررسی کن."

    def _call_gemini(self, text: str, temperature: float, model_name: str) -> str:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={self.cfg.gemini_api_key}"
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
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        candidates = data.get("candidates") or []
        if candidates:
            parts = candidates[0].get("content", {}).get("parts") or []
            if parts:
                return parts[0].get("text", "").strip()
        return ""
