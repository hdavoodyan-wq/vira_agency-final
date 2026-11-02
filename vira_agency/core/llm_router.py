"""
لایه ارتباطی هوشمند و ضدقطعی با سیستم هوش مصنوعی و تصویرساز (Gemini با پشتیبان Cloudflare)
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
        
        api_key = getattr(self.cfg, "gemini_api_key", "") or os.getenv("GEMINI_API_KEY", "").strip()
        if not api_key:
            for k in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "GENAI_API_KEY"):
                val = os.getenv(k, "").strip()
                if val.startswith("AIza"):
                    api_key = val
                    break

        if not api_key:
            return "⚠️ خطا: کلید GEMINI_API_KEY در پنل رندر تنظیم نشده است."

        models_to_try = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"]
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
            except Exception as e:
                last_err = str(e)
                continue

        return f"⚠️ خطای ارتباط با جمینای: {last_err[:100]}"

    async def generate_image(self, prompt: str, output_path: str) -> bool:
        """سیستم دومرحله‌ای تولید تصویر: اول تلاش با جمینای، در صورت خطا سوئیچ خودکار روی کلودفلر (Cloudflare AI)"""
        # ۱. تلاش اول با جمینای (یا سرویس‌های کمکی)
        try:
            # اگر در آینده مدل تصویرساز جمینای فعال شود در اینجا قرار می‌گیرد
            pass
        except Exception:
            pass

        # ۲. تلاش دوم و پشتیبان: موتور ابری کلودفلر (Cloudflare Workers AI)
        cf_account = getattr(self.cfg, "cf_account_id", "") or os.getenv("CF_ACCOUNT_ID", "").strip()
        cf_token = getattr(self.cfg, "cf_api_token", "") or os.getenv("CF_API_TOKEN", "").strip()

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
                    # اگر پاسخ به صورت JSON بود (تصویر بیس‌۶۴) یا باینری مستقیم
                    try:
                        res_json = json.loads(img_bytes.decode("utf-8"))
                        if "result" in res_json and "image" in res_json["result"]:
                            import base64
                            img_bytes = base64.b64decode(res_json["result"]["image"])
                    except Exception:
                        pass

                    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
                    with open(output_path, "wb") as f:
                        f.write(img_bytes)
                    return os.path.exists(output_path) and os.path.getsize(output_path) > 500
            except Exception as e:
                log.warning("Cloudflare image fallback failed: %s", e)

        return False
