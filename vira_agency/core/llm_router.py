"""
مسیریاب هوشمند LLM با اتصال پایدار به اندپوینت v1beta و مدل‌های فعال گوگل
"""
import asyncio
import base64
import json
import logging
import os
import urllib.request
import urllib.error

from vira_agency.core.config import AgencyConfig
from vira_agency.core.database import AgencyDatabase

log = logging.getLogger(__name__)

# مدل‌های پیش‌فرض (فعال). برای تغییر بدون دست زدن به کد:
# تو .env بذار: GEMINI_MODELS=gemini-2.5-flash,gemini-2.5-pro
DEFAULT_GEMINI_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.5-pro",
]

# پیشوند پیام‌های خطا؛ بقیه‌ی کد می‌تونه با is_error_text() چک کنه
ERROR_PREFIX = "⚠️"


def is_error_text(text: str) -> bool:
    """اگه خروجی generate_text خطا بود True برمی‌گردونه (برای جلوگیری از ساخت استوری با متن خطا)"""
    return (text or "").strip().startswith(ERROR_PREFIX)


class LLMRouter:
    def __init__(self, cfg: AgencyConfig, db: AgencyDatabase):
        self.cfg = cfg
        self.db = db

    def _get_models(self) -> list:
        """لیست مدل‌ها: اول از config، بعد از env، بعد پیش‌فرض"""
        raw = getattr(self.cfg, "gemini_models", None) or os.environ.get("GEMINI_MODELS", "")
        if isinstance(raw, (list, tuple)):
            models = [str(m).strip() for m in raw if str(m).strip()]
        else:
            models = [m.strip() for m in str(raw).split(",") if m.strip()]
        return models or DEFAULT_GEMINI_MODELS

    async def generate_text(self, prompt: str, system_prompt: str = "", department: str = "CEO", temperature: float = 0.7) -> str:
        api_key = getattr(self.cfg, "gemini_api_key", "")
        if not api_key:
            return f"{ERROR_PREFIX} خطا: کلید GEMINI_API_KEY در تنظیمات سرور ثبت نشده است."

        models_to_try = self._get_models()
        errors = []  # همه‌ی خطاها جمع می‌شن، نه فقط آخری

        for model_name in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
            payload = {
                "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": temperature},
            }
            # system prompt جدا و به شکل استاندارد فرستاده می‌شه
            if system_prompt:
                payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}

            try:
                def _call():
                    req = urllib.request.Request(
                        url,
                        data=json.dumps(payload).encode("utf-8"),
                        headers={
                            "Content-Type": "application/json",
                            # کلید تو هدر، تا تو لاگ و URL لو نره
                            "x-goog-api-key": api_key,
                        },
                        method="POST",
                    )
                    with urllib.request.urlopen(req, timeout=45) as resp:
                        return json.loads(resp.read().decode("utf-8"))

                data = await asyncio.to_thread(_call)
                candidates = data.get("candidates") or []
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts") or []
                    # مدل‌های 2.5 ممکنه چند part بدن؛ همه‌ی متن‌ها رو بچسبون
                    ans = "".join(p.get("text", "") for p in parts).strip()
                    if ans:
                        self.db.log_ai_usage(
                            department, "gemini", model_name,
                            (len(system_prompt) + len(prompt)) // 4,
                        )
                        log.info("Successfully generated text using model: %s", model_name)
                        return ans

                # جواب خالی (مثلاً بلاک شدن توسط safety)
                reason = ""
                if candidates:
                    reason = candidates[0].get("finishReason", "")
                elif data.get("promptFeedback"):
                    reason = str(data["promptFeedback"].get("blockReason", ""))
                errors.append(f"{model_name} (empty{': ' + reason if reason else ''})")
                log.warning("Model %s returned empty response (%s). Trying next...", model_name, reason)

            except urllib.error.HTTPError as he:
                err_body = he.read().decode("utf-8", errors="ignore")
                errors.append(f"{model_name} (HTTP {he.code})")
                # پیام کامل خطا لاگ می‌شه (نه فقط ۱۰۰ کاراکتر)
                log.warning("Model %s failed with HTTP %s: %s. Trying next...", model_name, he.code, err_body[:1000])
                # کلید اشتباه/ممنوع: امتحان مدل‌های دیگه فایده نداره
                if he.code in (401, 403):
                    break
                continue
            except Exception as e:
                errors.append(f"{model_name} ({e})")
                log.warning("Model %s error: %s. Trying next...", model_name, e)
                continue

        return f"{ERROR_PREFIX} خطای API جمینای. نتیجه‌ی مدل‌ها: " + " | ".join(errors)

    async def generate_image(self, prompt: str, output_path: str) -> bool:
        """تولید تصویر با موتور ابری کلودفلر (فال‌بک خودکار)"""
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
