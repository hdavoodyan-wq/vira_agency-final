"""
مدیرعامل مرکزی آژانس ویرا (CEO Orchestrator)
وظایف:
۱. مدیریت تعاملات و هدایت درخواست‌ها به ۳ دپارتمان تخصصی
۲. ارائه متد get_department_agent جهت دریافت ایجنت‌های تخصصی
"""
import logging
from vira_agency.core.config import VIRA_SYSTEM_IDENTITY, AgencyConfig
from vira_agency.core.database import AgencyDatabase
from vira_agency.core.llm_router import LLMRouter
from vira_agency.agents.department_agents import TradingAgent, DarkPsychAgent, ArtAgent

log = logging.getLogger(__name__)


class ViraOrchestrator:
    def __init__(self, cfg: AgencyConfig, db: AgencyDatabase, llm: LLMRouter):
        self.cfg = cfg
        self.db = db
        self.llm = llm

        self.trading_dept = TradingAgent(llm)
        self.dark_dept = DarkPsychAgent(llm)
        self.art_dept = ArtAgent(llm)

    def get_department_agent(self, slug: str):
        """ارجاع مستقیم به ایجنت دپارتمان مربوطه بر اساس اسلاگ پیج"""
        s = (slug or "").lower()
        if "trade" in s or s == "trading":
            return self.trading_dept
        elif "dark" in s or "psych" in s:
            return self.dark_dept
        elif "art" in s or "paper" in s or "mache" in s:
            return self.art_dept
        return self.trading_dept

    async def chat_with_vira(self, user_message: str) -> str:
        prompt = (
            f"کاربر می‌گوید: «{user_message}»\n"
            "به عنوان «دستیار ویرا»، مدیر ارشد آژانس دیجیتال مارکتینگ، با لحنی صمیمی، باهوش و حرفه‌ای به زبان فارسی پاسخ بده."
        )
        return await self.llm.generate_text(prompt=prompt, system_prompt=VIRA_SYSTEM_IDENTITY, department="CEO_Chat")
