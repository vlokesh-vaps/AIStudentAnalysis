import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    PORT = int(os.getenv("PORT", "8051"))
    DEBUG = FLASK_ENV == "development"
    MAX_CONTENT_LENGTH = 25 * 1024 * 1024
    JSON_SORT_KEYS = False
