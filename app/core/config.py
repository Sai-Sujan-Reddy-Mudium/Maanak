from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Application Settings loaded from environment variables or .env file.
    """
    SUPABASE_URL: str
    SUPABASE_KEY: str
    OPENROUTER_KEYS: List[str]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
