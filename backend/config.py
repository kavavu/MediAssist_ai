"""
Application configuration for different environments (development, testing, production).

Uses environment variables when set; otherwise falls back to safe defaults.
Database can be switched to PostgreSQL by setting DATABASE_URL.

SECURITY NOTE:
- SECRET_KEY and JWT_SECRET_KEY MUST be set via environment variables in production.
- The app will refuse to start in production without strong secrets.
- CORS origins should be restricted to your frontend domain in production.
"""
import os
from datetime import timedelta
from pathlib import Path

# Auto-load .env file from backend/ or project root
from dotenv import load_dotenv
_env_paths = [
    Path(__file__).parent / ".env",
    Path(__file__).parent.parent / ".env",
]
for _p in _env_paths:
    if _p.exists():
        load_dotenv(dotenv_path=_p)
        break


# --- Base settings used in all environments ---
class BaseConfig:
    """Base configuration shared across environments."""

    # SECURITY: In production, these MUST come from environment variables.
    # The app checks this at startup and refuses to run with weak secrets.
    SECRET_KEY = os.getenv("SECRET_KEY", "")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        # Use absolute path to backend/instance for SQLite
        "sqlite:///../instance/mediassist.db",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB file upload limit
    
    # CORS: In production, restrict to your frontend origin.
    # Format: ["https://yourdomain.com", "https://app.yourdomain.com"]
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*")
    
    # Socket.IO CORS origins (should match HTTP CORS)
    SOCKET_CORS_ORIGINS = os.getenv("SOCKET_CORS_ORIGINS", "*")


class DevelopmentConfig(BaseConfig):
    """Development configuration."""

    DEBUG = True


class TestingConfig(BaseConfig):
    """Testing configuration."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


class ProductionConfig(BaseConfig):
    """Production configuration with strict security checks."""

    DEBUG = False
    
    def __init__(self):
        # SECURITY: Refuse to start in production without strong secrets
        if not self.SECRET_KEY or len(self.SECRET_KEY) < 32:
            raise RuntimeError(
                "FATAL: SECRET_KEY must be set to a strong secret (32+ chars) in production. "
                "Set the SECRET_KEY environment variable."
            )
        if not self.JWT_SECRET_KEY or len(self.JWT_SECRET_KEY) < 32:
            raise RuntimeError(
                "FATAL: JWT_SECRET_KEY must be set to a strong secret (32+ chars) in production. "
                "Set the JWT_SECRET_KEY environment variable."
            )


# Map environment names to config classes
config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config():
    """Pick which config to use (e.g. APP_ENV=development uses DevelopmentConfig)."""
    env = os.getenv("APP_ENV", "development").lower()
    return config_by_name.get(env, DevelopmentConfig)

