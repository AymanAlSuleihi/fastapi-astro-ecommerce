import uuid

import boto3

from src.storage.config import storage_settings


class StorageService:
    def __init__(self):
        self._client = None

    @property
    def client(self):
        if self._client is None and storage_settings.configured:
            self._client = boto3.client(
                "s3",
                endpoint_url=storage_settings.R2_ENDPOINT_URL,
                aws_access_key_id=storage_settings.R2_ACCESS_KEY_ID,
                aws_secret_access_key=storage_settings.R2_SECRET_ACCESS_KEY,
            )
        return self._client

    @property
    def configured(self) -> bool:
        return storage_settings.configured

    def build_key(self, entity_type: str, entity_id: uuid.UUID, filename: str) -> str:
        return f"{entity_type}/{entity_id}/{filename}"

    def build_url(self, key: str) -> str:
        return f"{storage_settings.R2_PUBLIC_URL}/{key}"

    def upload(self, data: bytes, key: str, content_type: str = "image/jpeg") -> str:
        if not self.client:
            raise RuntimeError("Storage is not configured")
        self.client.put_object(
            Bucket=storage_settings.R2_BUCKET_NAME,
            Key=key,
            Body=data,
            ContentType=content_type,
        )
        return self.build_url(key)

    def delete(self, key: str) -> None:
        if not self.client:
            return
        self.client.delete_object(
            Bucket=storage_settings.R2_BUCKET_NAME,
            Key=key,
        )
