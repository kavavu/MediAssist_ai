"""
Application configuration for different environments (development, testing, production).

Uses environment variables when set; otherwise falls back to safe defaults.
Database can be switched to PostgreSQL by setting DATABASE_URL.
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

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-me")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        # Use absolute path to backend/instance for SQLite
        "sqlite:///../instance/mediassist.db",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret-key-change-me")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB file upload limit


class DevelopmentConfig(BaseConfig):
    """Development configuration."""

    DEBUG = True


class TestingConfig(BaseConfig):
    """Testing configuration."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


class ProductionConfig(BaseConfig):
    """Production configuration (to be refined later)."""

    DEBUG = False


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

