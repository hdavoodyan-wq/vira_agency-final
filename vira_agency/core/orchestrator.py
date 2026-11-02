from typing import Any
from vira_agency.core.config import VIRA_SYSTEM_IDENTITY, AgencyConfig
from vira_agency.core.database import AgencyDatabase
from vira_agency.core.llm_router import LLMRouter


class ViraOrchestrator:
    def __init__(self, cfg: AgencyConfig, db: AgencyDatabase, llm: LLMRouter):
        self.cfg = cfg
        self.db = db
        self.llm = llm

    async def detect_intent(self, user_message: str) -> dict[str, Any]:
        msg = user_message.strip()
        lower = msg.lower()
        target_slug = "unknown"
        if any(w in lower for w in ("ترید", "بیت‌کوین", "بیتکوین", "چارت", "کندل", "فارکس", "کریپتو", "بازار")):
            target_slug = "trading"
        elif any(w in lower for w in ("تاریک", "دراکولا", "سمی", "روانشناسی", "زبان بدن", "رابطه")):
            target_slug = "dark_psych"
        elif any(w in lower for w in ("پاپیه", "پاپیه‌ماشه", "پاپیا", "مجسمه", "خمیر", "چسب چوب", "هنر", "دکور")):
            target_slug = "papermache"

        if any(w in lower for w in ("استوری", "story")):
            return {"intent": "create_story", "target_page_slug": target_slug, "topic": msg}
        if any(w in lower for w in ("کاروسل", "پست", "اسلاید", "carousel")):
            return {"intent": "create_carousel", "target_page_slug": target_slug, "topic": msg}
        if any(w in lower for w in ("ریلز", "ویدیو", "reel", "کلیپ")):
            return {"intent": "create_reel", "target_page_slug": target_slug, "topic": msg}
        return {"intent": "chat", "target_page_slug": target_slug, "topic": msg}

    async def chat_with_vira(self, user_message: str) -> str:
        prompt = f"کاربر می‌گوید: «{user_message}»\nبه عنوان دستیار ویرا با لحنی بامزه، دوستانه و باهوش پاسخ بده."
        return await self.llm.generate_text(prompt=prompt, system_prompt=VIRA_SYSTEM_IDENTITY, department="CEO_Chat")
