"""
مسیریاب هوشمند LLM با اتصال پایدار به اندپوینت v1beta و مدل‌های فعال گوگل
+ تشخیص خودکار علت خطا (تموم شدن سهمیه/توکن رایگان، کلید، محدودیت منطقه، اسم مدل، شبکه)
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

# برای تغییر بدون دست زدن به کد، تو .env بذار: GEMINI_MODELS=gemini-2.5-flash,gemini-2.5-pro
DEFAULT_GEMINI_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.5-pro",
]

API_ROOT = "https://generativelanguage.googleapis.com/v1beta"
ERROR_PREFIX = "⚠️"

# انواع خطا (kind)
QUOTA, KEY, REGION, MODEL, SERVER, NETWORK, EMPTY, OTHER = (
    "quota", "key", "region", "model", "server", "network", "empty", "other",
)

KIND_TITLES = {
    QUOTA: "🔴 احتمالاً سهمیه/توکن رایگان تموم شده",
    KEY: "🔑 مشکل از کلید API",
    REGION: "🌍 محدودیت منطقه (IP سرور)",
    MODEL: "🤖 اسم مدل پیدا نشد",
    SERVER: "🛠 سرور گوگل مشکل داره/شلوغه",
    NETWORK: "📡 اتصال به گوگل برقرار نشد",
    EMPTY: "📭 مدل جواب خالی داد",
    OTHER: "❓ خطای نامشخص",
}

KIND_ADVICE = {
    QUOTA: (
        "سهمیه‌ی رایگان (در دقیقه یا در روز) پر شده. چند دقیقه صبر کن یا فردا امتحان کن. "
        "برای حل دائمی: تو aistudio.google.com سهمیه رو چک کن، یه کلید/پروژه‌ی جدید بساز، "
        "یا billing رو فعال کن. (گوگل مقدار دقیق باقی‌مونده رو از طریق API نمیده؛ "
        "فقط از ارور ۴۲۹ میشه فهمید.)"
    ),
    KEY: "کلید نامعتبره، غیرفعال شده یا Generative Language API روی پروژه‌اش روشن نیست. یه کلید جدید از aistudio.google.com بگیر.",
    REGION: "گوگل از کشور/IP این سرور درخواست قبول نمی‌کنه. سرور یا پروکسی خارج از ایران لازمه.",
    MODEL: "اسم مدل اشتباهه یا مسیر API وسط راه (پروکسی) درست نیست.",
    SERVER: "ارور سمت گوگله (۵۰۰/۵۰۳). چند دقیقه بعد دوباره امتحان کن.",
    NETWORK: "timeout، DNS، فایروال یا VPN. اینترنت/پروکسی سرور رو چک کن.",
    EMPTY: "ممکنه پرامپت توسط فیلتر ایمنی بلاک شده باشه. پرامپت رو عوض کن.",
    OTHER: "متن خطا رو تو لاگ سرور ببین.",
}


def is_error_text(text: str) -> bool:
    """اگه خروجی generate_text خطا بود True (برای جلوگیری از ساخت استوری با متن خطا)"""
    return (text or "").strip().startswith(ERROR_PREFIX)


def _parse_google_error(body: str):
    """status و message رو از بدنه‌ی خطای گوگل درمیاره"""
    try:
        err = json.loads(body).get("error", {})
        return err.get("status", ""), err.get("message", "")
    except Exception:
        return "", (body or "")[:200]


def _classify_http(code: int, status: str, message: str) -> str:
    low = (message or "").lower()
    if code == 429 or status == "RESOURCE_EXHAUSTED" or "quota" in low:
        return QUOTA
    if "location" in low and ("not supported" in low or "unsupported" in low):
        return REGION
    if code in (401, 403) or "api key" in low or status in ("UNAUTHENTICATED", "PERMISSION_DENIED"):
        return KEY
    if code == 400 and "api_key" in low.replace(" ", "_"):
        return KEY
    if code == 404 or status == "NOT_FOUND":
        return MODEL
    if code >= 500:
        return SERVER
    return OTHER


class LLMRouter:
    def __init__(self, cfg: AgencyConfig, db: AgencyDatabase):
        self.cfg = cfg
        self.db = db

    # ---------- کمکی‌ها ----------
    def _get_models(self) -> list:
        raw = getattr(self.cfg, "gemini_models", None) or os.environ.get("GEMINI_MODELS", "")
        if isinstance(raw, (list, tuple)):
            models = [str(m).strip() for m in raw if str(m).strip()]
        else:
            models = [m.strip() for m in str(raw).split(",") if m.strip()]
        return models or DEFAULT_GEMINI_MODELS

    def _http_json(self, url: str, api_key: str, payload=None, timeout: int = 45):
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8") if payload is not None else None,
            headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
            method="POST" if payload is not None else "GET",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

    async def _list_available_models(self, api_key: str):
        """مدل‌های واقعاً در دسترس کلید رو می‌گیره. خروجی: (ok, models_or_error)"""
        try:
            data = await asyncio.to_thread(self._http_json, f"{API_ROOT}/models", api_key, None, 20)
            names = []
            for m in data.get("models", []):
                if "generateContent" in (m.get("supportedGenerationMethods") or []):
                    names.append(m.get("name", "").replace("models/", ""))
            return True, [n for n in names if n]
        except urllib.error.HTTPError as he:
            body = he.read().decode("utf-8", errors="ignore")
            status, msg = _parse_google_error(body)
            return False, f"HTTP {he.code} {status}: {msg[:120]}"
        except Exception as e:
            return False, str(e)

    async def _try_models(self, models, prompt, system_prompt, department, temperature, api_key):
        """مدل‌ها رو به‌ترتیب امتحان می‌کنه. خروجی: (متن یا None, لیست مشکلات)"""
        issues = []
        for model_name in models:
            url = f"{API_ROOT}/models/{model_name}:generateContent"
            payload = {
                "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": temperature},
            }
            if system_prompt:
                payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}

            try:
                data = await asyncio.to_thread(self._http_json, url, api_key, payload, 45)
                candidates = data.get("candidates") or []
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts") or []
                    ans = "".join(p.get("text", "") for p in parts).strip()
                    if ans:
                        self.db.log_ai_usage(department, "gemini", model_name,
                                             (len(system_prompt) + len(prompt)) // 4)
                        log.info("Successfully generated text using model: %s", model_name)
                        return ans, issues

                reason = ""
                if candidates:
                    reason = candidates[0].get("finishReason", "")
                elif data.get("promptFeedback"):
                    reason = str(data["promptFeedback"].get("blockReason", ""))
                issues.append({"model": model_name, "kind": EMPTY, "code": 200, "detail": reason})
                log.warning("Model %s returned empty response (%s)", model_name, reason)

            except urllib.error.HTTPError as he:
                body = he.read().decode("utf-8", errors="ignore")
                status, msg = _parse_google_error(body)
                kind = _classify_http(he.code, status, msg)
                issues.append({"model": model_name, "kind": kind, "code": he.code, "detail": msg[:150]})
                log.warning("Model %s HTTP %s [%s]: %s", model_name, he.code, kind, body[:1000])
                # کلید یا منطقه مشکل داره: امتحان مدل‌های دیگه بی‌فایده‌ست
                if kind in (KEY, REGION):
                    break
            except Exception as e:
                issues.append({"model": model_name, "kind": NETWORK, "code": 0, "detail": str(e)[:150]})
                log.warning("Model %s network error: %s", model_name, e)
        return None, issues

    def _build_error_message(self, issues, extra: str = "") -> str:
        """پیام خطای خلاصه و قابل فهم با علت احتمالی"""
        kinds = [i["kind"] for i in issues]
        # اولویت نمایش علت اصلی
        main = next((k for k in (QUOTA, KEY, REGION, NETWORK, SERVER, MODEL, EMPTY, OTHER) if k in kinds), OTHER)

        lines = [f"{ERROR_PREFIX} خطای API جمینای", KIND_TITLES[main], KIND_ADVICE[main], ""]
        lines.append("جزئیات هر مدل:")
        for i in issues:
            code = f"HTTP {i['code']}" if i["code"] else "no-response"
            lines.append(f"• {i['model']}: {code} ({KIND_TITLES[i['kind']].split(' ', 1)[1]})")
        if extra:
            lines += ["", extra]
        return "\n".join(lines)

    # ---------- API اصلی ----------
    async def generate_text(self, prompt: str, system_prompt: str = "", department: str = "CEO", temperature: float = 0.7) -> str:
        api_key = getattr(self.cfg, "gemini_api_key", "")
        if not api_key:
            return f"{ERROR_PREFIX} خطا: کلید GEMINI_API_KEY در تنظیمات سرور ثبت نشده است."

        models = self._get_models()
        ans, issues = await self._try_models(models, prompt, system_prompt, department, temperature, api_key)
        if ans:
            return ans

        extra = ""
        # اگه همه‌ی خطاها ۴۰۴ بودن: ببین کلید چه مدل‌هایی واقعاً داره و با اونا دوباره تلاش کن
        if issues and all(i["kind"] == MODEL for i in issues):
            ok, result = await self._list_available_models(api_key)
            if ok:
                tried = set(models)
                fallback = [m for m in result if m not in tried and "flash" in m][:2] or \
                           [m for m in result if m not in tried][:2]
                if fallback:
                    log.info("Retrying with models available for this key: %s", fallback)
                    ans, issues2 = await self._try_models(fallback, prompt, system_prompt, department, temperature, api_key)
                    if ans:
                        log.warning("Models %s don't exist for this key. Working ones: %s. Update GEMINI_MODELS.", models, result[:10])
                        return ans
                    issues += issues2
                extra = "✅ کلید سالمه. مدل‌های موجود برای کلید تو: " + ", ".join(result[:6])
            else:
                extra = f"❌ لیست مدل‌ها هم گرفته نشد → {result}\nاحتمالاً پروکسی/IP/کلید مشکل داره."

        return self._build_error_message(issues, extra)

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
