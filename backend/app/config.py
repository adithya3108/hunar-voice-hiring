from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    hunar_api_key: str = ""
    hunar_api_base_url: str = "https://api.voice.hunar.ai"
    hunar_webhook_secret: str = ""
    hunar_from_phone_number: str = ""

    pdl_api_key: str = ""
    openrouter_api_key: str = ""
    openrouter_model: str = "anthropic/claude-sonnet-4.5"

    public_base_url: str = "http://localhost:8000"
    database_url: str = "sqlite:///./hunar.db"
    frontend_origin: str = "http://localhost:3000"


@lru_cache
def get_settings() -> Settings:
    return Settings()
