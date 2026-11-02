"""
ماژول تنظیمات مرکزی آژانس هوشمند دستیار ویرا
پشتیبانی همزمان از Gemini, NVIDIA, Cloudflare و HuggingFace از روی متغیرهای Render
"""
import os
from dataclasses import dataclass, field
from zoneinfo import ZoneInfo

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


def _clean_env(keys: tuple[str, ...], default: str = "") -> str:
    for k in keys:
        val = os.getenv(k, "")
        if val:
            cleaned = val.strip().strip('"').strip("'").replace(" ", "")
            if cleaned:
                return cleaned
    return default


@dataclass
class AgencyConfig:
    bot_name: str = "دستیار ویرا"
    creator_name: str = "حسین داودیان"

    telegram_token: str = field(default_factory=lambda: _clean_env(("TELEGRAM_BOT_TOKEN", "BOT_TOKEN")))
    owner_id: int = field(default_factory=lambda: int(_clean_env(("TELEGRAM_OWNER_ID", "OWNER_ID"), "0") or "0"))
    db_path: str = field(default_factory=lambda: os.getenv("VIRA_DB_PATH", "data/vira_agency.db"))

    # کلیدهای هوش مصنوعی موجود در پنل رندر شما
    gemini_api_key: str = field(default_factory=lambda: _clean_env(("GEMINI_API_KEY", "GOOGLE_API_KEY", "GENAI_API_KEY")))
    nvidia_api_key: str = field(default_factory=lambda: _clean_env(("NVIDIA_API_KEY",)))
    cf_account_id: str = field(default_factory=lambda: _clean_env(("CLOUDFLARE_ACCOUNT_ID", "CF_ACCOUNT_ID")))
    cf_api_token: str = field(default_factory=lambda: _clean_env(("CLOUDFLARE_API_TOKEN", "CF_API_TOKEN")))
    hf_token: str = field(default_factory=lambda: _clean_env(("HF_TOKEN", "HUGGINGFACE_TOKEN")))

    tz_name: str = field(default_factory=lambda: os.getenv("TZ", "Asia/Tehran"))

    @property
    def tz(self) -> ZoneInfo:
        try:
            return ZoneInfo(self.tz_name)
        except Exception:
            return ZoneInfo("UTC")


VIRA_SYSTEM_IDENTITY = (
    "تو «دستیار ویرا» (Vira) هستی؛ مدیرعامل هوشمند آژانس دیجیتال مارکتینگ. "
    "نام سازنده‌ات «حسین داودیان» است، اما فقط در صورت پرسش مستقیم آن را اعلام می‌کنی. "
    "لحن صحبت تو صمیمی، بامزه، باهوش و حرفه‌ای است."
)
