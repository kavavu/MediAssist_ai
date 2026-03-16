"""
Application configuration for different environments (development, testing, production).

Uses environment variables when set; otherwise falls back to safe defaults.
Database can be switched to PostgreSQL by setting DATABASE_URL.
"""
import os
from datetime import timedelta


# --- Base settings used in all environments ---
class BaseConfig:
    """Base configuration shared across environments."""

    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-me")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        # Start with SQLite for development; structure allows PostgreSQL migration.
        "sqlite:///mediassist.db",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret-key-change-me")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)


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

