"""
QueryForge - Application Configuration
Uses pydantic-settings to load from .env file
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # App
    APP_NAME: str = "QueryForge"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # AI - Google Gemini (Free Tier)
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-flash"  # Free tier model

    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

    # File Upload
    MAX_UPLOAD_SIZE_MB: int = 50

    # Query Limits
    MAX_QUERY_ROWS: int = 5000
    QUERY_TIMEOUT_SECONDS: int = 30

    # History & Snapshots
    SNAPSHOT_LIMIT: int = 20
    HISTORY_LIMIT: int = 100

    # Storage Paths
    DATABASE_DIR: str = "./databases"
    SNAPSHOT_DIR: str = "./snapshots"
    UPLOAD_DIR: str = "./uploads"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
