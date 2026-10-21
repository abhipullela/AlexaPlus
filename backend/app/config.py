"""Central place for app settings, read from environment variables / .env file."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str = "sqlite:///./data/alexaplus.db"

    # Tell pydantic to also look inside a file called ".env"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
