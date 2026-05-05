import os
from dotenv import load_dotenv

load_dotenv()


def _parse_keys(raw):
    """Split comma-separated keys, strip whitespace, drop empties"""
    if not raw:
        return []
    return [k.strip() for k in raw.split(",") if k.strip()]


class Config:
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
    DB_NAME = os.getenv("DB_NAME", "postal_db")
    SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret-key")
    GROQ_API_KEYS = _parse_keys(os.getenv("GROQ_API_KEY"))
    USE_GROQ = os.getenv("USE_GROQ", "false").lower() == "true"
    DEBUG = True
