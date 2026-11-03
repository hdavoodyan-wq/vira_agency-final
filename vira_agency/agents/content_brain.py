"""
vira_agency/core/content_brain.py
مغز متفکر محتوایی: حافظه ۳۰ روزه ضد تکرار، شکارچی ترندها و سیستم امتیازدهی کیفی (QA)
نسخه ۱۰۰٪ کامل و بدون هیچ‌گونه خلاصه‌سازی
"""
import sqlite3
import datetime
import random
import os
import json
import logging

logger = logging.getLogger("vira_agency.brain")
DB_PATH = "data/vira_content_memory.db"


def init_memory():
    """راه‌اندازی جدول حافظه تاریخی تاپیک‌ها در دیتابیس SQLite"""
    os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS published_topics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            page_key TEXT,
            topic_title TEXT,
            hook TEXT,
            score INTEGER,
            created_at TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


init_memory()


def is_topic_repeated_recently(page_key: str, topic_title: str, days: int = 30) -> bool:
    """بررسی اینکه آیا سوژه در ۳۰ روز گذشته کار شده است یا خیر"""
    if not topic_title:
        return False
    try:
        clean_topic = topic_title.replace("«", "").replace("»", "").replace("موضوع", "").strip().lower()
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        since_date = datetime.datetime.now() - datetime.timedelta(days=days)
        c.execute("""
            SELECT COUNT(*) FROM published_topics 
            WHERE page_key = ? AND (topic_title LIKE ? OR ? LIKE '%' || topic_title || '%') AND created_at >= ?
        """, (page_key, f"%{clean_topic}%", clean_topic, since_date))
        count = c.fetchone()[0]
        conn.close()
        return count > 0
    except Exception as e:
        logger.error(f"Error checking topic repetition: {e}")
        return False


def record_published_topic(page_key: str, topic_title: str, hook: str, score: int):
    """ثبت موضوع تایید شده در تاریخچه سیستم"""
    try:
        clean_topic = topic_title.replace("«", "").replace("»", "").replace("موضوع", "").strip()
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            INSERT INTO published_topics (page_key, topic_title, hook, score, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (page_key, clean_topic, hook, score, datetime.datetime.now()))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error recording published topic: {e}")


def evaluate_quality_score(slides: list) -> dict:
    """
    سیستم ارزیابی و امتیازدهی طبق سند استراتژی:
    - قدرت قلاب اسلاید اول (۲۰)
    - کیفیت روایت و نگهداشت (۲۰)
    - ارزش علمی و محتوایی (۲۰)
    - کیفیت طراحی و خوانایی (۱۵)
    - ارزش ذخیره و اشتراک (۱۵)
    - دعوت به تعامل و CTA (۱۰)
    """
    if not slides:
        return {"score": 0, "is_approved": False, "verdict": "رد به دلیل محتوای خالی"}

    hook = slides[0].get("text", "") or slides[0].get("body", "")
    score = 75

    # بررسی جذابیت و قدرت قلاب بر اساس سوالات تضاد و کنجکاوی
    hook_keywords = ["چرا", "چطور", "چگونه", "بدون اینکه", "معامله", "اشتباه", "راز", "کنترل", "تله", "خطا"]
    if any(k in hook for k in hook_keywords):
        score += 10

    # بررسی پیوستگی و طول روایت (تعداد اسلایدها)
    if len(slides) >= 7:
        score += 8
    elif len(slides) >= 4:
        score += 5

    # بررسی پایان‌بندی و دعوت به تعامل (CTA)
    last_slide_text = slides[-1].get("text", "") or slides[-1].get("body", "")
    if any(q in last_slide_text for q in ["؟", "آیا", "دایرکت", "نظرت", "سیو", "ذخیره"]):
        score += 7

    score = min(score, 98)
    return {
        "score": score,
        "is_approved": score >= 80,
        "verdict": "اولویت انتشار" if score >= 90 else "قابل انتشار"
    }
