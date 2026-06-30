from pydantic_settings import BaseSettings, SettingsConfigDict


class NotificationSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="NOTIFICATIONS_")

    RESEND_API_KEY: str = ""
    EMAIL_FROM_ADDRESS: str = "store@example.com"
    EMAIL_FROM_NAME: str = "Store"
    EMAIL_ENABLED: bool = False
    FRONTEND_URL: str = "http://localhost:4321"


notification_settings = NotificationSettings()
