import uuid
from io import BytesIO

from PIL import Image as PILImage
from sqlalchemy import select

from src.images.models import Image
from src.storage.service import StorageService
from src.worker.settings import broker

THUMBNAIL_SIZES = [
    (150, 150),
    (300, 300),
    (600, 600),
]


@broker.task(task_name="generate_thumbnails")
async def generate_thumbnails(
    image_id: str, entity_type: str, entity_id: str, base_key: str
) -> None:
    """Generate thumbnail variants for an uploaded image."""
    import os

    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://ecommerce:ecommerce@db:5432/ecommerce",
    )
    engine = create_async_engine(database_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as db:
        original = await db.scalar(
            select(Image).where(Image.id == uuid.UUID(image_id))
        )
        if not original:
            return

        storage = StorageService()
        if not storage.configured:
            return

        client = storage.client
        if not client:
            return

        from src.storage.config import storage_settings

        try:
            obj = client.get_object(
                Bucket=storage_settings.R2_BUCKET_NAME,
                Key=base_key,
            )
            content = obj["Body"].read()
        except Exception:
            return

        base = base_key.rsplit(".", 1)[0]
        ext = base_key.rsplit(".", 1)[-1] if "." in base_key else "jpg"

        for w, h in THUMBNAIL_SIZES:
            try:
                thumb_bytes = _resize(content, w, h)
                thumb_key = f"{base}_{w}x{h}.{ext}"
                thumb_url = storage.upload(thumb_bytes, thumb_key, "image/jpeg")

                thumb = Image(
                    entity_type=entity_type,
                    entity_id=uuid.UUID(entity_id),
                    url=thumb_url,
                    storage_key=thumb_key,
                    width=w,
                    height=h,
                    file_size=len(thumb_bytes),
                    parent_id=original.id,
                )
                db.add(thumb)
            except Exception:
                continue

        await db.commit()

    await engine.dispose()


def _resize(data: bytes, width: int, height: int) -> bytes:
    with PILImage.open(BytesIO(data)) as img:
        img = img.convert("RGB")
        img.thumbnail((width, height), PILImage.LANCZOS)
        out = BytesIO()
        img.save(out, format="JPEG", quality=85, optimize=True)
        return out.getvalue()
