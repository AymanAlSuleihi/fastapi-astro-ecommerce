from pydantic_settings import BaseSettings, SettingsConfigDict


class StorageSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="R2_")

    R2_ACCESS_KEY_ID: str = ""
    R2_SECRET_ACCESS_KEY: str = ""
    R2_ENDPOINT_URL: str = ""
    R2_BUCKET_NAME: str = ""
    R2_PUBLIC_URL: str = ""

    @property
    def configured(self) -> bool:
        return bool(self.R2_ACCESS_KEY_ID and self.R2_BUCKET_NAME)


storage_settings = StorageSettings()
