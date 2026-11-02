import json
import os
import sqlite3
import time
from typing import Any, Optional


class AgencyDatabase:
    def __init__(self, db_path: str):
        self.db_path = db_path
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        self._init_schema()
        self._seed_default_departments()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self):
        schema = """
        CREATE TABLE IF NOT EXISTS brand_pages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            department TEXT NOT NULL,
            niche TEXT NOT NULL,
            handle TEXT DEFAULT '',
            tone TEXT NOT NULL,
            visual_identity TEXT DEFAULT '{}',
            is_active INTEGER DEFAULT 1,
            created_at INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS page_contents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            page_id INTEGER NOT NULL,
            content_type TEXT NOT NULL,
            category TEXT DEFAULT '',
            topic TEXT NOT NULL,
            payload TEXT DEFAULT '{}',
            status TEXT DEFAULT 'draft',
            created_at INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS ai_usage_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            department TEXT NOT NULL,
            provider TEXT NOT NULL,
            model TEXT NOT NULL,
            tokens_used INTEGER DEFAULT 0,
            created_at INTEGER NOT NULL
        );
        """
        with self._conn() as conn:
            conn.executescript(schema)

    def _seed_default_departments(self):
        with self._conn() as conn:
            cur = conn.execute("SELECT COUNT(*) as cnt FROM brand_pages")
            if cur.fetchone()["cnt"] > 0:
                return
            now = int(time.time())
            default_pages = [
                ("trading", "📈 ترید و بازارهای مالی", "Trading Dept", "ترید، کریپتو و فارکس", "@tradebazehn", "حرفه‌ای، تحلیلی و قاطع", "{}", now),
                ("dark_psych", "🖤 روانشناسی تاریک", "Dark Psych Dept", "روانشناسی تاریک و کاریزما", "@tradebazehn", "عمیق، مرموز و فلسفی", "{}", now),
                ("papermache", "🎨 هنر و مجسمه‌سازی پاپیه‌ماشه", "Art Dept", "ساخت و فروش مجسمه‌های دست‌ساز پاپیه‌ماشه", "@papermache_art", "گرم، صمیمی، شاعرانه و هنرمندانه", "{}", now),
            ]
            conn.executemany(
                "INSERT INTO brand_pages (slug, title, department, niche, handle, tone, visual_identity, created_at) VALUES (?,?,?,?,?,?,?,?)",
                default_pages,
            )

    def get_pages(self, active_only: bool = True) -> list[dict[str, Any]]:
        q = "SELECT * FROM brand_pages" + (" WHERE is_active=1" if active_only else "") + " ORDER BY id ASC"
        with self._conn() as conn:
            return [dict(r) for r in conn.execute(q).fetchall()]

    def get_page_by_slug(self, slug: str) -> Optional[dict[str, Any]]:
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM brand_pages WHERE slug=?", (slug,)).fetchone()
            return dict(row) if row else None

    def save_content(self, page_id: int, content_type: str, topic: str, payload: dict, category: str = "") -> int:
        with self._conn() as conn:
            cur = conn.execute(
                "INSERT INTO page_contents (page_id, content_type, category, topic, payload, created_at) VALUES (?,?,?,?,?,?)",
                (page_id, content_type, category, topic, json.dumps(payload, ensure_ascii=False), int(time.time())),
            )
            return cur.lastrowid

    def log_ai_usage(self, department: str, provider: str, model: str, tokens: int = 0):
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO ai_usage_logs (department, provider, model, tokens_used, created_at) VALUES (?,?,?,?,?)",
                (department, provider, model, tokens, int(time.time())),
            )
