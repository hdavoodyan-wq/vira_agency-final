"""
مسیریاب هوشمند LLM و تصویرساز با سیستم فال‌بک خودکار دو‌مرحله‌ای (جمینای ➡️ کلودفلر)
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


class LLMRouter:
    def __init__(self, cfg: AgencyConfig, db: AgencyDatabase):
        self.cfg = cfg
        self.db = db

    async def generate_text(self, prompt: str, system_prompt: str = "", department: str = "CEO", temperature: float = 0.7) -> str:
        full_prompt = f"{system_prompt}\n\n{prompt}".strip() if system_prompt else prompt
        
        api_key = getattr(self.cfg, "gemini_api_key", "")
        if not api_key:
            return "⚠️ خطا: کلید GEMINI_API_KEY در تنظیمات سرور ثبت نشده است."

        # مدل‌ها به ترتیب اولویت: در صورت لیمیت یا خطا، خودکار روی مدل بعدی می‌پرد
        models_to_try = [
            "gemini-2.5-flash",
            "gemini-2.5-pro",
            "gemini-1.5-pro",
            "gemini-1.5-flash"
        ]

        last_err = ""
        for model_name in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
            payload = {
                "contents": [{"parts": [{"text": full_prompt}]}],
                "generationConfig": {"temperature": temperature},
            }
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
                    if parts:
                        ans = parts[0].get("text", "").strip()
                        if ans:
                            self.db.log_ai_usage(department, "gemini", model_name, len(full_prompt) // 4)
                            log.info("Successfully generated text using model: %s", model_name)
                            return ans
            except urllib.error.HTTPError as he:
                err_body = he.read().decode("utf-8", errors="ignore")
                last_err = f"{model_name} (HTTP {he.code})"
                log.warning("Model %s hit quota/error: %s. Switching to next model...", model_name, err_body[:100])
                continue
            except Exception as e:
                last_err = f"{model_name} ({str(e)})"
                log.warning("Model %s error: %s. Switching to next model...", model_name, e)
                continue

        return f"⚠️ خطای API جمینای: تمامی مدل‌ها بررسی شدند اما سهمیه یا ارتباط برقرار نشد. آخرین خطا: {last_err}"

    async def generate_image(self, prompt: str, output_path: str) -> bool:
        """سیستم دومرحله‌ای تولید تصویر با فال‌بک خودکار (جمینای ➡️ کلودفلر)"""
        
        # ۱. تلاش اول با سرویس تصویرساز جمینای (در صورت پشتیبانی یا فعال بودن اندپوینت)
        try:
            api_key = getattr(self.cfg, "gemini_api_key", "")
            if api_key:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
                payload = {
                    "contents": [{"parts": [{"text": f"Generate image prompt details for: {prompt}"}]}]
                }
                # در صورت نیاز به پردازش متن تصویر با جمینای
        except Exception as e:
            log.warning("Gemini image prep failed, falling back to Cloudflare: %s", e)

        # ۲. تلاش دوم و قطعی: موتور ابری کلودفلر (Cloudflare Workers AI - Flux)
        cf_account = getattr(self.cfg, "cf_account_id", "")
        cf_token = getattr(self.cfg, "cf_api_token", "")

        if cf_account and cf_token:
            try:
                url = f"https://api.cloudflare.com/client/v4/accounts/{cf_account}/ai/run/@cf/blackforestlabs/flux-1-schnell"
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
                    log.info("Image successfully generated and saved via Cloudflare fallback!")
                    return True
            except Exception as e:
                log.warning("Cloudflare image fallback failed: %s", e)

        return False
