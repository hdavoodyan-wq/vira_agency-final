"""
ماژول تنظیمات مرکزی آژانس هوشمند دستیار ویرا
توسعه‌دهنده: حسین داودیان
"""
import os
from dataclasses import dataclass, field
from zoneinfo import ZoneInfo

@dataclass
class AgencyConfig:
    bot_name: str = "دستیار ویرا"
    creator_name: str = "حسین داودیان"
    
    # خواندن مستقیم توکن تلگرام از رندر
    telegram_token: str = field(default_factory=lambda: (
        os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("BOT_TOKEN") or ""
    ).strip())
    
    # خواندن آیدی ادمین
    owner_id: int = field(default_factory=lambda: int(
        (os.getenv("TELEGRAM_OWNER_ID") or os.getenv("OWNER_ID") or "0").strip() or "0"
    ))
    
    db_path: str = field(default_factory=lambda: os.getenv("VIRA_DB_PATH", "data/vira_agency.db"))
    
    # خواندن مستقیم و بدون واسطه کلید جمینای از پنل رندر
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

VIRA_SYSTEM_IDENTITY = "تو دستیار ویرا هستی؛ مدیرعامل هوشمند آژانس دیجیتال مارکتینگ."
