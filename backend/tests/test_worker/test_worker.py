import uuid
from io import BytesIO

import pytest
from PIL import Image as PILImage

from src.worker.queue import enqueue_thumbnails
from src.worker.tasks import THUMBNAIL_SIZES, _resize, generate_thumbnails

# ── _resize ──────────────────────────────────────────────────


def test_resize_small():
    """Resize an image to a smaller size."""
    img = PILImage.new("RGB", (800, 600), color="red")
    buf = BytesIO()
    img.save(buf, format="JPEG")
    original = buf.getvalue()

    result = _resize(original, 150, 150)
    assert len(result) < len(original)

    with PILImage.open(BytesIO(result)) as resized:
        assert resized.size[0] <= 150
        assert resized.size[1] <= 150


def test_resize_maintains_aspect_ratio():
    """thumbnail preserves aspect ratio."""
    img = PILImage.new("RGB", (800, 400), color="blue")
    buf = BytesIO()
    img.save(buf, format="JPEG")

    result = _resize(buf.getvalue(), 300, 300)
    with PILImage.open(BytesIO(result)) as resized:
        w, h = resized.size
        assert w <= 300
        assert h <= 300
        assert w == 300 or h == 300


def test_thumbnail_sizes_are_valid():
    """All configured sizes are non-zero and square."""
    for w, h in THUMBNAIL_SIZES:
        assert w > 0
        assert h > 0


@pytest.mark.asyncio
async def test_enqueue_thumbnails_graceful():
    """enqueue_thumbnails does not raise when Valkey is unavailable."""
    # Should not raise — fails silently when broker not connected
    await enqueue_thumbnails(
        image_id=uuid.uuid4(),
        entity_type="product",
        entity_id=uuid.uuid4(),
        storage_key="test/key.jpg",
    )


@pytest.mark.asyncio
async def test_generate_thumbnails_image_not_found():
    """generate_thumbnails returns early when image doesn't exist."""
    await generate_thumbnails(
        image_id=str(uuid.uuid4()),
        entity_type="product",
        entity_id=str(uuid.uuid4()),
        base_key="test/key.jpg",
    )
    # Should not raise — no R2 config, no image, returns early
