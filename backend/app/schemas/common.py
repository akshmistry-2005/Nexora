from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Standard pagination query parameters."""

    page: int = Field(default=1, ge=1, description="Page number, 1-indexed")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page (max 100)")


class PaginationMeta(BaseModel):
    """Metadata describing a paginated collection."""

    page: int
    page_size: int
    total_items: int
    total_pages: int
    has_next: bool
    has_prev: bool


class ErrorDetail(BaseModel):
    """Structured error information."""

    code: str
    message: str
    details: list[dict[str, str]] | None = None


class StandardResponse(BaseModel, Generic[T]):
    """Consistent envelope for single-resource and scalar responses."""

    success: bool = True
    data: T
    error: ErrorDetail | None = None


class PaginatedResponse(BaseModel, Generic[T]):
    """Consistent envelope for paginated resource lists."""

    success: bool = True
    data: list[T]
    meta: PaginationMeta
    error: ErrorDetail | None = None
