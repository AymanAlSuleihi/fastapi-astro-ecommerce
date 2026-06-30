import uuid
from io import BytesIO

from PIL import Image as PILImage
from sqlalchemy import select

from src.database import DbDep
from src.images.config import THUMBNAIL_SIZES
from src.images.exceptions import ImageNotFound
from src.images.models import Image
from src.images.schemas import ImageUpdate
from src.storage.service import StorageService


class ImageService:
    def __init__(self, db: DbDep):
        self.db = db

    async def list_images(
        self, entity_type: str, entity_id: uuid.UUID
    ) -> list[Image]:
        result = await self.db.execute(
            select(Image)
            .where(
                Image.entity_type == entity_type,
                Image.entity_id == entity_id,
                Image.parent_id.is_(None),
            )
            .order_by(Image.sort_order, Image.created_at)
        )
        return list(result.scalars().all())

    async def get_image(self, image_id: uuid.UUID) -> Image:
        img = await self.db.scalar(select(Image).where(Image.id == image_id))
        if not img:
            raise ImageNotFound()
        return img

    async def upload(
        self,
        entity_type: str,
        entity_id: uuid.UUID,
        filename: str,
        content: bytes,
        content_type: str,
        alt_text: str | None = None,
    ) -> Image:
        storage = StorageService()
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "jpg"
        key = storage.build_key(entity_type, entity_id, f"{uuid.uuid4()}.{ext}")

        if storage.configured:
            url = storage.upload(content, key, content_type)
        else:
            url = f"/storage/{key}"  # placeholder for dev

        # Get dimensions
        width = height = None
        try:
            with PILImage.open(BytesIO(content)) as img:
                width, height = img.size
        except Exception:
            pass

        image = Image(
            entity_type=entity_type,
            entity_id=entity_id,
            url=url,
            storage_key=key,
            alt_text=alt_text,
            width=width,
            height=height,
            file_size=len(content),
        )
        self.db.add(image)
        await self.db.commit()
        await self.db.refresh(image)

        # Enqueue thumbnail generation
        from src.worker.tasks import generate_thumbnails

        await generate_thumbnails.kiq(
            str(image.id), entity_type, str(entity_id), key
        )

        return image

    async def update(self, image_id: uuid.UUID, data: ImageUpdate) -> Image:
        img = await self.get_image(image_id)
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(img, key, value)
        await self.db.commit()
        await self.db.refresh(img)
        return img

    async def delete(self, image_id: uuid.UUID) -> None:
        img = await self.get_image(image_id)
        storage = StorageService()
        if storage.configured:
            storage.delete(img.storage_key)
        # Delete thumbnails
        from sqlalchemy import delete as sqla_delete

        await self.db.execute(
            sqla_delete(Image).where(Image.parent_id == image_id)
        )
        await self.db.delete(img)
        await self.db.commit()

    async def generate_thumbnails(
        self,
        image_id: str,
        entity_type: str,
        entity_id: str,
        base_key: str,
    ) -> None:
        """Generate thumbnail variants for an uploaded image. Called from the task queue."""
        original = await self.get_image(uuid.UUID(image_id))

        storage = StorageService()
        if not storage.configured:
            return

        content = storage.download(base_key)
        if not content:
            return

        base = base_key.rsplit(".", 1)[0]
        ext = base_key.rsplit(".", 1)[-1] if "." in base_key else "jpg"

        for w, h in THUMBNAIL_SIZES:
            try:
                thumb_bytes = resize_image(content, w, h)
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
                self.db.add(thumb)
            except Exception:
                continue

        await self.db.commit()


def resize_image(data: bytes, width: int, height: int) -> bytes:
    """Resize image data to fit within width×height, preserving aspect ratio."""
    with PILImage.open(BytesIO(data)) as img:
        img = img.convert("RGB")
        img.thumbnail((width, height), PILImage.LANCZOS)
        out = BytesIO()
        img.save(out, format="JPEG", quality=85, optimize=True)
        return out.getvalue()
