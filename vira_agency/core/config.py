import os
from dataclasses import dataclass, field
from zoneinfo import ZoneInfo

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


@dataclass
class AgencyConfig:
    bot_name: str = "دستیار ویرا"
    creator_name: str = "حسین داودیان"
    telegram_token: str = field(default_factory=lambda: os.getenv("TELEGRAM_BOT_TOKEN", "").strip())
    owner_id: int = field(default_factory=lambda: int(os.getenv("TELEGRAM_OWNER_ID", "0").strip() or "0"))
    db_path: str = field(default_factory=lambda: os.getenv("VIRA_DB_PATH", "data/vira_agency.db"))
    assets_root: str = field(default_factory=lambda: os.getenv("VIRA_ASSETS_DIR", "data/assets"))
    cf_account_id: str = field(default_factory=lambda: os.getenv("CF_ACCOUNT_ID", "").strip())
    cf_api_token: str = field(default_factory=lambda: os.getenv("CF_API_TOKEN", "").strip())
    gemini_api_key: str = field(default_factory=lambda: os.getenv("GEMINI_API_KEY", "").strip())
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", "").strip())
    openai_base_url: str = field(default_factory=lambda: os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1").strip())
    tz_name: str = field(default_factory=lambda: os.getenv("TZ", "Asia/Tehran"))

    @property
    def tz(self) -> ZoneInfo:
        try:
            return ZoneInfo(self.tz_name)
        except Exception:
            return ZoneInfo("UTC")


VIRA_SYSTEM_IDENTITY = """تو «دستیار ویرا» (Vira) هستی؛ مدیرعامل هوشمند آژانس دیجیتال مارکتینگ.
قوانین هویت و پاسخگویی تو:
- در مکالمات عادی خودت را فقط با نام «دستیار ویرا» معرفی می‌کنی.
- نام سازنده‌ات «حسین داودیان» است، اما فقط و فقط اگر کاربر مستقیماً پرسید «چه کسی تو را ساخته؟» یا «سازنده‌ات کیست؟» آن را می‌گویی.
- لحن صحبت تو: صمیمی، بامزه، باهوش و حرفه‌ای است.
"""
