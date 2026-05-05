import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
    DB_NAME = os.getenv("DB_NAME", "postal_db")
    SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret-key")
    GEMINI_API_KEYS = [
    os.environ.get("GEMINI_API_KEY_1"),
    os.environ.get("GEMINI_API_KEY_2"),
    os.environ.get("GEMINI_API_KEY_3"),
    ]
    GEMINI_API_KEYS = [k for k in GEMINI_API_KEYS if k]
    USE_GEMINI = os.getenv("USE_GEMINI", "false").lower() == "true"
    DEBUG = True