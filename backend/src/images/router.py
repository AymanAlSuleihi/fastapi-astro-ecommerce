import uuid
from typing import Annotated

from fastapi import APIRouter, Form, Query, UploadFile, status

from src.admin.dependencies import CurrentAdminDep
from src.database import DbDep
from src.images.schemas import ImageRead, ImageUpdate
from src.images.service import ImageService

router = APIRouter(prefix="/images", tags=["images"])


@router.get("/", response_model=list[ImageRead])
async def list_images(
    db: DbDep,
    entity_type: Annotated[str, Query()],
    entity_id: Annotated[uuid.UUID, Query()],
):
    service = ImageService(db)
    return await service.list_images(entity_type, entity_id)


@router.post(
    "/upload",
    response_model=ImageRead,
    status_code=status.HTTP_201_CREATED,
)
async def upload_image(
    db: DbDep,
    _admin: CurrentAdminDep,
    file: UploadFile,
    entity_type: Annotated[str, Form()],
    entity_id: Annotated[uuid.UUID, Form()],
    alt_text: Annotated[str | None, Form()] = None,
):
    content = await file.read()
    service = ImageService(db)
    return await service.upload(
        entity_type=entity_type,
        entity_id=entity_id,
        filename=file.filename or "image.jpg",
        content=content,
        content_type=file.content_type or "image/jpeg",
        alt_text=alt_text,
    )


@router.patch("/{image_id}", response_model=ImageRead)
async def update_image(
    image_id: uuid.UUID,
    data: ImageUpdate,
    db: DbDep,
    _admin: CurrentAdminDep,
):
    service = ImageService(db)
    return await service.update(image_id, data)


@router.delete("/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_image(
    image_id: uuid.UUID,
    db: DbDep,
    _admin: CurrentAdminDep,
):
    service = ImageService(db)
    await service.delete(image_id)
