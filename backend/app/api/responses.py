"""
Response models for standardized API responses.

All API responses follow the format defined in the constitution.
"""

from datetime import datetime, timezone
from typing import Dict, Generic, List, Optional, TypeVar

from app.core.logging import get_correlation_id, get_request_id
from pydantic import BaseModel, Field

T = TypeVar("T")


class Meta(BaseModel):
    """Metadata included in all API responses."""

    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc)
        .isoformat()
        .replace("+00:00", "Z")
    )
    request_id: Optional[str] = Field(default_factory=get_request_id)
    correlation_id: Optional[str] = Field(default_factory=get_correlation_id)


class Pagination(BaseModel):
    """Pagination information for list responses."""

    total: int
    limit: int
    skip: int
    has_more: bool


class SuccessResponse(BaseModel, Generic[T]):
    """Standard success response wrapper."""

    success: bool = True
    data: T
    meta: Meta = Field(default_factory=Meta)


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated list response wrapper."""

    success: bool = True
    data: List[T]
    pagination: Pagination
    meta: Meta = Field(default_factory=Meta)


class ErrorDetail(BaseModel):
    """Individual error detail for a specific field."""

    code: str
    message: str


class ErrorBody(BaseModel):
    """Error information in error responses."""

    code: str
    message: str
    details: Optional[Dict[str, List[ErrorDetail]]] = None


class ErrorResponse(BaseModel):
    """Standard error response wrapper."""

    success: bool = False
    error: ErrorBody
    meta: Meta = Field(default_factory=Meta)


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str = "1.0.0"
    database: str
