from enum import StrEnum


class DocumentType(StrEnum):
    INVOICE = "INVOICE"
    RECEIPT = "RECEIPT"
    CREDIT_NOTE = "CREDIT_NOTE"
    PACKING_SLIP = "PACKING_SLIP"


class DocumentStatus(StrEnum):
    DRAFT = "DRAFT"
    SENT = "SENT"
    PAID = "PAID"
    CANCELLED = "CANCELLED"
    VOID = "VOID"


class DocsErrorCode:
    DOCUMENT_NOT_FOUND = "DOCUMENT_NOT_FOUND"
