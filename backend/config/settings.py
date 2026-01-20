from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Any
from pydantic import field_validator

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"


class OpenAiSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="OPENAI_", env_file=ENV_FILE, env_file_encoding='utf-8',
                                      extra='ignore')
    api_key: str = ''

class GeminiAiSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="GEMINI_", env_file=ENV_FILE, env_file_encoding='utf-8',
                                      extra='ignore')
    api_key: str = ''
    base_url: str = 'https://generativelanguage.googleapis.com/v1beta/openai/'

class SesSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SES_", env_file=ENV_FILE, env_file_encoding='utf-8', extra='ignore')
    secret: str = ''
    secret_id: str = ''
    secret_key: str = ''
    template_id: int = 0
    region:str = 'ap-hongkong'


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "Just Chat A Moment API"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./data.db"

    # Auth
    SECRET_KEY: str = "change-this-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30

    # CORS
    CORS_ALLOW_ORIGINS: List[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]

    @field_validator("CORS_ALLOW_ORIGINS", "CORS_ALLOW_METHODS", "CORS_ALLOW_HEADERS", mode="before")
    @classmethod
    def parse_csv_or_json_list(cls, v: Any) -> Any:
        if isinstance(v, str):
            # Allow comma-separated string
            items = [item.strip() for item in v.split(",") if item.strip() != ""]
            if items:
                return items
        return v

    openai: OpenAiSettings = OpenAiSettings()
    gemini: GeminiAiSettings = GeminiAiSettings()
    ses: SesSettings = SesSettings()


settings = Settings()
