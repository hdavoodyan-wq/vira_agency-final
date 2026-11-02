```python
"""
مسیریاب هوشمند LLM با پشتیبانی از تولید JSON استوری/ریلز و ساخت تصویر با کلودفلر (Flux)
"""
import asyncio
import base64
import json
import logging
import os
import re
import urllib.request
import urllib.error

from vira_agency.core.config import AgencyConfig
from vira_agency.core.database import AgencyDatabase

log = logging.getLogger(__name__)

DEFAULT_GEMINI_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemma-4-26b-a4b-it",
]

API_ROOT = "https://generativelanguage.googleapis.com/v1beta"
ERROR_PREFIX = "⚠️"


class LLMRouter:
    def __init__(self, cfg: AgencyConfig, db: AgencyDatabase):
        self.cfg = cfg
        self.db = db

    def _get_models(self) -> list:
        raw = getattr(self.cfg, "gemini_models", None) or os.environ.get("GEMINI_MODELS", "")
        if isinstance(raw, (list, tuple)):
            models = [str(m).strip() for m in raw if str(m).strip()]
        else:
            models = [m.strip() for m in str(raw).split(",") if m.strip()]
        return models or DEFAULT_GEMINI_MODELS

    async def _try_models(self, models, prompt, system_prompt, department, temperature, api_key):
        issues = []
        for model_name in models:
            url = f"{API_ROOT}/models/{model_name}:generateContent?key={api_key}"
            
            # برای مدل‌های خانواده gemma که systemInstruction جداگانه قبول نمی‌کنند، ترکیب در متن انجام می‌شود
            if "gemma" in model_name.lower() and system_prompt:
                combined_text = f"{system_prompt}\n\nدرخواست کاربر:\n{prompt}"
                payload = {
                    "contents": [{"role": "user", "parts": [{"text": combined_text}]}],
                    "generationConfig": {"temperature": temperature},
                }
            else:
                payload = {
                    "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": temperature},
                }
                if system_prompt:
                    payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}

            try:
                def _call():
                    req = urllib.request.Request(
                        url,
                        data=json.dumps(payload).encode("utf-8"),
                        headers={"Content-Type": "application/json"},
                        method="POST",
                    )
                    with urllib.request.urlopen(req, timeout=45) as resp:
                        return json.loads(resp.read().decode("utf-8"))

                data = await asyncio.to_thread(_call)
                candidates = data.get("candidates") or []
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts") or []
                    ans = "".join(p.get("text", "") for p in parts).strip()
                    if ans:
                        self.db.log_ai_usage(department, "gemini", model_name, (len(system_prompt) + len(prompt)) // 4)
                        log.info("Successfully generated text using model: %s", model_name)
                        return ans, issues
            except urllib.error.HTTPError as he:
                body = he.read().decode("utf-8", errors="ignore")
                issues.append({"model": model_name, "code": he.code, "detail": body[:150]})
                log.warning("Model %s HTTP %s: %s", model_name, he.code, body[:200])
                continue
            except Exception as e:
                issues.append({"model": model_name, "code": 0, "detail": str(e)[:150]})
                log.warning("Model %s error: %s", model_name, e)
                continue
        return None, issues

    async def generate_text(self, prompt: str, system_prompt: str = "", department: str = "CEO", temperature: float = 0.7) -> str:
        api_key = (getattr(self.cfg, "gemini_api_key", "") or "").strip().strip('"').strip("'")
        if not api_key:
            return f"{ERROR_PREFIX} خطا: کلید GEMINI_API_KEY در تنظیمات سرور ثبت نشده است."

        enforced_system = (
            f"{system_prompt}\n"
            "قانون مهم: فقط و فقط متن نهایی فارسی را برگردان. هرگز دستورالعمل‌ها، Persona یا توضیحات انگلیسی را در خروجی ننویس."
        ).strip()

        models = self._get_models()
        ans, issues = await self._try_models(models, prompt, enforced_system, department, temperature, api_key)
        if ans:
            return ans

        return f"{ERROR_PREFIX} خطای ارتباط با جمینای: {issues}"

    async def json(self, prompt: str, quality: str = "best", temperature: float = 0.7) -> dict:
        """دریافت خروجی JSON استاندارد (برای استوری، کاروسل و ریلز دقیقاً مثل ربات قبلی)"""
        sys_json = (
            "You are a professional Persian content generator. "
            "Output ONLY a valid JSON object. Do not include markdown fences or extra explanations."
        )
        api_key = (getattr(self.cfg, "gemini_api_key", "") or "").strip().strip('"').strip("'")
        models = self._get_models()
        raw, _ = await self._try_models(models, prompt, sys_json, "JSON_Gen", temperature, api_key)
        if not raw:
            return {}

        try:
            # استخراج اولین بلوک JSON از پاسخ مدل
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            cleaned = match.group(0) if match else raw.strip()
            return json.loads(cleaned)
        except Exception as e:
            log.warning("JSON parse failed, building fallback dict: %s", e)
            return {"heading": "نکته تخصصی روز", "body": raw[:220]}

    async def text(self, prompt: str, temperature: float = 0.7) -> str:
        return await self.generate_text(prompt, temperature=temperature)

    async def generate_image(self, prompt: str, output_path: str) -> bool:
        """تولید تصویر با موتور ابری کلودفلر (Flux-1-Schnell) دقیقاً مثل ربات قبلی"""
        cf_account = getattr(self.cfg, "cf_account_id", "")
        cf_token = getattr(self.cfg, "cf_api_token", "")

        if cf_account and cf_token:
            try:
                url = f"https://api.cloudflare.com/client/v4/accounts/{cf_account}/ai/run/@cf/black-forest-labs/flux-1-schnell"
                payload = {"prompt": prompt}
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={
                        "Authorization": f"Bearer {cf_token}",
                        "Content-Type": "application/json",
                    },
                    method="POST",
                )

                def _call_cf():
                    with urllib.request.urlopen(req, timeout=60) as resp:
                        return resp.read()

                img_bytes = await asyncio.to_thread(_call_cf)
                if img_bytes and len(img_bytes) > 500:
                    try:
                        res_json = json.loads(img_bytes.decode("utf-8"))
                        if "result" in res_json and "image" in res_json["result"]:
                            img_bytes = base64.b64decode(res_json["result"]["image"])
                    except Exception:
                        pass

                    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
                    with open(output_path, "wb") as f:
                        f.write(img_bytes)
                    log.info("Image successfully generated via Cloudflare!")
                    return True
            except Exception as e:
                log.warning("Cloudflare image generation failed: %s", e)

        return False
```