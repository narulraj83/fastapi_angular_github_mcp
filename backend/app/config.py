from functools import lru_cache
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict, NoDecode
from typing import Annotated


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "GitHub Repository Assistant"
    environment: str = "development"
    database_url: str = "sqlite:///./github_assistant.db"
    secret_key: str = "change-this-development-secret"
    encryption_key: str = ""
    github_client_id: str = ""
    github_client_secret: str = ""
    github_callback_url: str = "http://localhost:8000/api/v1/github/callback"
    openai_api_key: str = ""
    ai_provider: str = "openai"
    ai_model: str = "gpt-4o-mini"
    frontend_url: str = "http://localhost:4200"
    mcp_server_url: str = "http://localhost:8001/mcp"
    github_api_url: str = "https://api.github.com"
    access_token_minutes: int = 30
    refresh_token_days: int = 14
    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:4200", "http://127.0.0.1:4200"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value):
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
