from datetime import timedelta

from pydantic_settings import BaseSettings, SettingsConfigDict


class AuthConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="AUTH_", extra="ignore")

    JWT_ALG: str = "HS256"
    JWT_SECRET: str
    JWT_EXP_MINUTES: int = 60
    REFRESH_TOKEN_KEY: str
    REFRESH_TOKEN_EXP: timedelta = timedelta(days=30)
    SECURE_COOKIES: bool = False


auth_settings = AuthConfig()  # ty: ignore[missing-argument]
