from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    DATABASE_URL: str
    ENVIRONMENT: str = "local"
    CORS_ORIGINS: list[str] = ["*"]
    API_V1_PREFIX: str = "/api/v1"


settings = Settings()  # ty: ignore[missing-argument]

SHOW_DOCS_IN = {"local", "staging"}
