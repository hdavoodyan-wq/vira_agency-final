```python
"""
مسیریاب هوشمند چندموتوره (Multi-Provider LLM Router)
۱. کشف خودکار مدل‌های فعال Gemini از سرور گوگل (بدون خطای 404)
۲. پشتیبان خودکار با NVIDIA NIM API (کلید NVIDIA_API_KEY شما در رندر)
۳. پشتیبان خودکار با Cloudflare Workers AI (کلید CLOUDFLARE_API_TOKEN شما در رندر)
۴. پشتیبان خودکار با HuggingFace (کلید HF_TOKEN شما در رندر)
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
        self._cached_gemini_model: str | None = None

    async def generate_text(self, prompt: str, system_prompt: str = "", department: str = "CEO", temperature: float = 0.7) -> str:
        full_prompt = f"{system_prompt}\n\n{prompt}".strip() if system_prompt else prompt
        errors = []

        # ۱. تلاش با Google Gemini (با کشف خودکار مدل فعال اکانت شما)
        gemini_key = self.cfg.gemini_api_key or os.getenv("GEMINI_API_KEY", "").strip()
        if gemini_key:
            try:
                res, used_model = await asyncio.to_thread(self._try_gemini_smart, full_prompt, temperature, gemini_key)
                if res:
                    self.db.log_ai_usage(department, "gemini", used_model, len(full_prompt) // 4)
                    return res
            except Exception as e:
                err_msg = f"Gemini: {e}"
                log.warning(err_msg)
                errors.append(err_msg)

        # ۲. تلاش خودکار با NVIDIA API (موجود در پنل رندر شما)
        nvidia_key = self.cfg.nvidia_api_key or os.getenv("NVIDIA_API_KEY", "").strip()
        if nvidia_key:
            try:
                res = await asyncio.to_thread(self._call_nvidia, prompt, system_prompt, temperature, nvidia_key)
                if res:
                    self.db.log_ai_usage(department, "nvidia", "llama-3.1-70b", len(full_prompt) // 4)
                    return res
            except Exception as e:
                err_msg = f"NVIDIA: {e}"
                log.warning(err_msg)
                errors.append(err_msg)

        # ۳. تلاش خودکار با Cloudflare Workers AI (موجود در پنل رندر شما)
        cf_id = self.cfg.cf_account_id or os.getenv("CLOUDFLARE_ACCOUNT_ID", "").strip()
        cf_token = self.cfg.cf_api_token or os.getenv("CLOUDFLARE_API_TOKEN", "").strip()
        if cf_id and cf_token:
            try:
                res = await asyncio.to_thread(self._call_cloudflare, prompt, system_prompt, cf_id, cf_token)
                if res:
                    self.db.log_ai_usage(department, "cloudflare", "llama-3.1-8b", len(full_prompt) // 4)
                    return res
            except Exception as e:
                err_msg = f"Cloudflare: {e}"
                log.warning(err_msg)
                errors.append(err_msg)

        # ۴. تلاش خودکار با HuggingFace (موجود در پنل رندر شما)
        hf_key = self.cfg.hf_token or os.getenv("HF_TOKEN", "").strip()
        if hf_key:
            try:
                res = await asyncio.to_thread(self._call_huggingface, full_prompt, hf_key)
                if res:
                    self.db.log_ai_usage(department, "huggingface", "qwen-2.5-72b", len(full_prompt) // 4)
                    return res
            except Exception as e:
                err_msg = f"HF: {e}"
                log.warning(err_msg)
                errors.append(err_msg)

        detail = " | ".join(errors) if errors else "هیچ کلیدی در Environment پیدا نشد"
        return f"⚠️ خطای دقیق سرویس‌ها:\n{detail[:350]}"

    def _discover_gemini_models(self, api_key: str) -> list[str]:
        """استعلام مستقیم لیست مدل‌های مجاز برای کلید شما از سرور گوگل"""
        url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        available = []
        for m in data.get("models", []):
            methods = m.get("supportedGenerationMethods", [])
            name = m.get("name", "")  # e.g., models/gemini-2.0-flash
            if "generateContent" in methods and "gemini" in name:
                short_name = name.replace("models/", "")
                if "vision" not in short_name and "embedding" not in short_name and "tts" not in short_name:
                    available.append(short_name)

        # اولویت‌بندی بهترین مدل‌های موجود در اکانت
        preferred_order = [
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-2.0-flash-exp",
            "gemini-1.5-flash",
            "gemini-1.5-flash-latest",
            "gemini-1.5-pro",
            "gemini-pro",
        ]
        sorted_models = [p for p in preferred_order if p in available]
        for a in available:
            if a not in sorted_models:
                sorted_models.append(a)
        return sorted_models or preferred_order

    def _try_gemini_smart(self, text: str, temperature: float, api_key: str) -> tuple[str, str]:
        models_to_try = []
        if self._cached_gemini_model:
            models_to_try.append(self._cached_gemini_model)

        try:
            discovered = self._discover_gemini_models(api_key)
            for m in discovered:
                if m not in models_to_try:
                    models_to_try.append(m)
        except urllib.error.HTTPError as he:
            err_body = he.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"HTTP {he.code}: {err_body[:120]}")
        except Exception:
            models_to_try.extend(["gemini-2.0-flash", "gemini-2.5-flash", "gemini-1.5-flash"])

        last_err = ""
        for model_name in models_to_try[:5]:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
            payload = {
                "contents": [{"parts": [{"text": text}]}],
                "generationConfig": {"temperature": temperature},
            }
            try:
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=35) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                candidates = data.get("candidates") or []
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts") or []
                    if parts and parts[0].get("text"):
                        self._cached_gemini_model = model_name
                        return parts[0]["text"].strip(), model_name
            except urllib.error.HTTPError as he:
                err_body = he.read().decode("utf-8", errors="ignore")
                last_err = f"{model_name} -> HTTP {he.code}: {err_body[:100]}"
                continue
            except Exception as e:
                last_err = f"{model_name} -> {e}"
                continue

        raise RuntimeError(last_err or "No Gemini model responded")

    def _call_nvidia(self, prompt: str, system_prompt: str, temperature: float, api_key: str) -> str:
        url = "https://integrate.api.nvidia.com/v1/chat/completions"
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        for model in ("meta/llama-3.1-70b-instruct", "meta/llama-3.1-8b-instruct", "google/gemma-2-27b-it"):
            try:
                payload = {
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": 1024,
                }
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {api_key}",
                    },
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=35) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                ans = data["choices"][0]["message"]["content"].strip()
                if ans:
                    return ans
            except Exception:
                continue
        raise RuntimeError("NVIDIA API failed")

    def _call_cloudflare(self, prompt: str, system_prompt: str, account_id: str, api_token: str) -> str:
        model = "@cf/meta/llama-3.1-8b-instruct"
        url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/{model}"
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        req = urllib.request.Request(
            url,
            data=json.dumps({"messages": messages}).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_token}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=35) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        res = (data.get("result") or {}).get("response", "").strip()
        if res:
            return res
        raise RuntimeError("Cloudflare returned empty response")

    def _call_huggingface(self, full_prompt: str, hf_token: str) -> str:
        url = "https://router.huggingface.co/hf-inference/models/Qwen/Qwen2.5-72B-Instruct/v1/chat/completions"
        payload = {
            "model": "Qwen/Qwen2.5-72B-Instruct",
            "messages": [{"role": "user", "content": full_prompt}],
            "max_tokens": 900,
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {hf_token}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=35) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip()
```