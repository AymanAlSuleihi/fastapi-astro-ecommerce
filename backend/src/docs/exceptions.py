from src.docs.constants import DocsErrorCode
from src.exceptions import NotFoundException


class DocumentNotFound(NotFoundException):
    def __init__(self):
        super().__init__(detail="Document not found", code=DocsErrorCode.DOCUMENT_NOT_FOUND)
