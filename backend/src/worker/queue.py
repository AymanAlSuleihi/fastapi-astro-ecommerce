import uuid


async def enqueue_thumbnails(
    image_id: uuid.UUID, entity_type: str, entity_id: uuid.UUID, storage_key: str
) -> None:
    """Enqueue thumbnail generation via Taskiq. Fails silently if broker unavailable."""
    try:
        from src.worker.tasks import generate_thumbnails

        await generate_thumbnails.kiq(
            str(image_id), entity_type, str(entity_id), storage_key
        )
    except Exception:
        pass  # Valkey unavailable or broker not started — no thumbnails
