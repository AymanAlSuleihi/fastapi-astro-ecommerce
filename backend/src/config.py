from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    DATABASE_URL: str
    ENVIRONMENT: str = "local"
    CORS_ORIGINS: list[str] = ["*"]


settings = Settings()  # ty: ignore[missing-argument]

SHOW_DOCS_IN = {"local", "staging"}
