"""Configuration management for PRAudit."""

from typing import Set
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application setting model loaded from environment or defaults."""

    APP_NAME: str = "PRAudit"
    ENVIRONMENT: str = "production"
    LOG_LEVEL: str = "INFO"

    # Repository Discovery Defaults
    DEFAULT_IGNORE_PATTERNS: Set[str] = Field(
        default_factory=lambda: {
            ".git",
            ".git/**",
            ".venv",
            ".venv/**",
            "venv",
            "venv/**",
            "env",
            "env/**",
            "__pycache__",
            "__pycache__/**",
            "*.pyc",
            ".pytest_cache",
            ".pytest_cache/**",
            ".mypy_cache",
            ".mypy_cache/**",
            "node_modules",
            "node_modules/**",
            "dist",
            "dist/**",
            "build",
            "build/**",
            ".DS_Store",
            "*.egg-info",
            "*.egg-info/**",
            ".gemini",
            ".gemini/**",
        }
    )

    MAX_FILE_SIZE_BYTES: int = 5 * 1024 * 1024  # 5 MB safety limit per file

    model_config = SettingsConfigDict(
        env_prefix="PRAUDIT_",
        case_sensitive=False,
    )


settings = Settings()
