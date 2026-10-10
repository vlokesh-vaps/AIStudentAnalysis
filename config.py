import os
import logging
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Central configuration for AI Student Performance Analyzer.
    
    Supports local development, LAN access, production HTTP/HTTPS,
    Docker, and reverse-proxy deployments with URL prefixes.
    """
    # Environment
    FLASK_ENV = os.getenv("FLASK_ENV", "development").strip().lower()
    ENV = FLASK_ENV
    DEBUG = FLASK_ENV == "development"
    TESTING = False

    # Server Bind Settings
    HOST = os.getenv("HOST", "0.0.0.0").strip()
    PORT = int(os.getenv("PORT", "8051"))

    # Security & Secrets
    SECRET_KEY = os.getenv("SECRET_KEY", "ai-student-analysis-secret-key")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()

    # Application Base Path / URL Prefix (e.g., '/student-analysis' or empty for domain root)
    APPLICATION_ROOT = (
        os.getenv("APPLICATION_ROOT")
        or os.getenv("URL_PREFIX")
        or os.getenv("APP_BASE_PATH")
        or ""
    ).strip().rstrip("/")
    if APPLICATION_ROOT and not APPLICATION_ROOT.startswith("/"):
        APPLICATION_ROOT = f"/{APPLICATION_ROOT}"
    URL_PREFIX = APPLICATION_ROOT

    # API Prefix (defaults to /api)
    API_PREFIX = os.getenv("API_PREFIX", "/api").strip().rstrip("/")
    if not API_PREFIX.startswith("/"):
        API_PREFIX = f"/{API_PREFIX}"

    # Public Origin (when absolute external URLs are explicitly needed)
    PUBLIC_ORIGIN = os.getenv("PUBLIC_ORIGIN", "").strip().rstrip("/")
    PREFERRED_URL_SCHEME = os.getenv(
        "PREFERRED_URL_SCHEME",
        "https" if os.getenv("PUBLIC_ORIGIN", "").startswith("https://") else "http"
    ).strip().lower()

    # Reverse Proxy / Forwarded Headers
    # Number of trusted proxies in front of this application (defaults to 1)
    _trust_env = os.getenv("TRUST_PROXY_HEADERS", "").strip().lower()
    if _trust_env in ("true", "1", "yes"):
        TRUSTED_PROXIES = int(os.getenv("TRUSTED_PROXIES", "1"))
    elif _trust_env in ("false", "0", "no"):
        TRUSTED_PROXIES = 0
    else:
        TRUSTED_PROXIES = int(os.getenv("TRUSTED_PROXIES", "1"))

    # CORS & Allowed Hosts
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").strip()
    ALLOWED_HOSTS = [h.strip() for h in os.getenv("ALLOWED_HOSTS", "*").split(",") if h.strip()]

    # Uploads (in MB)
    MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "25"))
    MAX_CONTENT_LENGTH = MAX_UPLOAD_SIZE_MB * 1024 * 1024

    # API Documentation
    ENABLE_DOCS = os.getenv("ENABLE_DOCS", "true").strip().lower() in ("true", "1", "yes")

    # Logging Level
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").strip().upper()

    # Flask Settings
    JSON_SORT_KEYS = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = (
        os.getenv("SESSION_COOKIE_SECURE", "false").strip().lower() in ("true", "1", "yes")
        or PREFERRED_URL_SCHEME == "https"
    )

    @classmethod
    def validate(cls):
        """Validate critical configuration settings at startup."""
        errors = []
        if cls.PORT < 1 or cls.PORT > 65535:
            errors.append(f"Invalid PORT: {cls.PORT}. Must be between 1 and 65535.")
        if cls.MAX_UPLOAD_SIZE_MB <= 0:
            errors.append(f"Invalid MAX_UPLOAD_SIZE_MB: {cls.MAX_UPLOAD_SIZE_MB}. Must be positive.")
        if cls.TRUSTED_PROXIES < 0:
            errors.append(f"Invalid TRUSTED_PROXIES: {cls.TRUSTED_PROXIES}. Must be non-negative.")
        if cls.FLASK_ENV == "production" and not cls.GROQ_API_KEY:
            logging.getLogger(__name__).warning(
                "GROQ_API_KEY is not configured in production. AI narrative analysis endpoints will return 503."
            )
        if errors:
            raise ValueError("Configuration validation failed:\n" + "\n".join(f"- {e}" for e in errors))
