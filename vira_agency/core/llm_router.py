"""
مسیریاب هوشمند LLM با اولویت مطلق روی قدرتمندترین مدل‌های نسل جدید (Gemini 3.8 Flash و Gemini 3.1 Pro)
"""
import asyncio
import json
import logging
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

        # اولویت‌بندی دقیق براساس جدیدترین مدل‌های رسمی API گوگل
        models_to_try = [
            "gemini-3.8-flash",
            "gemini-3.1-pro-preview",
            "gemini-3.5-flash-lite",
            "gemini-1.5-pro"
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
                            return ans
            except urllib.error.HTTPError as he:
                err_body = he.read().decode("utf-8", errors="ignore")
                last_err = f"{model_name} (HTTP {he.code})"
                log.warning("Model %s failed: %s", model_name, err_body[:150])
                continue
            except Exception as e:
                last_err = f"{model_name} ({str(e)})"
                log.warning("Model %s error: %s", model_name, e)
                continue

        return f"⚠️ خطای API جمینای: آخرین خطا: {last_err}"

    async def generate_image(self, prompt: str, output_path: str) -> bool:
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
                            import base64
                            img_bytes = base64.b64decode(res_json["result"]["image"])
                    except Exception:
                        pass

                    import os
                    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
                    with open(output_path, "wb") as f:
                        f.write(img_bytes)
                    return True
            except Exception as e:
                log.warning("Cloudflare image generation failed: %s", e)

        return False
