"""
ماژول تنظیمات مرکزی آژانس هوشمند دستیار ویرا (AI Marketing & Digital Business Agency)
توسعه‌دهنده: حسین داودیان
"""
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
    telegram_token: str = field(default_factory=lambda: (
        os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("BOT_TOKEN") or ""
    ).strip())
    owner_id: int = field(default_factory=lambda: int(
        (os.getenv("TELEGRAM_OWNER_ID") or os.getenv("OWNER_ID") or "0").strip() or "0"
    ))
    db_path: str = field(default_factory=lambda: os.getenv("VIRA_DB_PATH", "data/vira_agency.db"))
    
    # خواندن مطمئن و جامع کلید جمینای مستقیماً از متغیرهای رندر
    gemini_api_key: str = field(default_factory=lambda: (
        os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("GENAI_API_KEY") or ""
    ).strip())
    
    tz_name: str = field(default_factory=lambda: os.getenv("TZ", "Asia/Tehran"))

    @property
    def tz(self) -> ZoneInfo:
        try:
            return ZoneInfo(self.tz_name)
        except Exception:
            return ZoneInfo("UTC")


VIRA_SYSTEM_IDENTITY = """تو «دستیار ویرا» (Vira) هستی؛ مدیرعامل هوشمند آژانس دیجیتال مارکتینگ.
- نام سازنده‌ات «حسین داودیان» است، اما فقط در صورت پرسش مستقیم آن را اعلام می‌کنی.
- لحن صحبت تو صمیمی، بامزه و باهوش است.
"""
"""
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
    telegram_token: str = field(default_factory=lambda: (
        os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("BOT_TOKEN") or ""
    ).strip())
    owner_id: int = field(default_factory=lambda: int(
        (os.getenv("TELEGRAM_OWNER_ID") or os.getenv("OWNER_ID") or "0").strip() or "0"
    ))
    db_path: str = field(default_factory=lambda: os.getenv("VIRA_DB_PATH", "data/vira_agency.db"))
    
    gemini_api_key: str = field(default_factory=lambda: (
        os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or os.getenv("GENAI_API_KEY") or ""
    ).strip())
    
    tz_name: str = field(default_factory=lambda: os.getenv("TZ", "Asia/Tehran"))

    @property
    def tz(self) -> ZoneInfo:
        try:
            return ZoneInfo(self.tz_name)
        except Exception:
            return ZoneInfo("UTC")


VIRA_SYSTEM_IDENTITY = """تو «دستیار ویرا» (Vira) هستی؛ مدیرعامل هوشمند آژانس دیجیتال مارکتینگ.
- نام سازنده‌ات «حسین داودیان» است، اما فقط در صورت پرسش مستقیم آن را اعلام می‌کنی.
- لحن صحبت تو صمیمی، بامزه و باهوش است.
"""
