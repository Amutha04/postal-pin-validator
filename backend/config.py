import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
    DB_NAME = os.getenv("DB_NAME", "postal_db")
    TESSERACT_PATH = os.getenv("TESSERACT_PATH", r"C:\Program Files\Tesseract-OCR\tesseract.exe")
    SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret-key")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    USE_GEMINI = os.getenv("USE_GEMINI", "false").lower() == "true"
    DEBUG = True