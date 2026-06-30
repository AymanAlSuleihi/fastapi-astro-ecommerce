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
    from src.database import SessionFactory
    from src.images.exceptions import ImageNotFound
    from src.images.service import ImageService

    async with SessionFactory() as session:
        try:
            await ImageService(session).generate_thumbnails(
                image_id, entity_type, entity_id, base_key
            )
        except ImageNotFound:
            pass  # Image deleted before task ran
