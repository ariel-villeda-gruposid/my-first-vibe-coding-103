"""
Driver Pydantic schemas for API request/response validation.

Defines schemas for creating, updating, and returning driver data.
"""

import re
from datetime import datetime
from typing import Optional

from app.domain.models.driver import DriverStatus
from pydantic import BaseModel, ConfigDict, Field, field_validator

# Validation constants
LICENSE_PATTERN = re.compile(r"^[A-Za-z0-9]+$")
# Flexible phone pattern: allows + prefix, digits, spaces, hyphens, parentheses
PHONE_PATTERN = re.compile(r"^\+?[\d\s\-\(\)]{7,20}$")


class DriverBase(BaseModel):
    """Base schema with shared driver attributes."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Driver's full name",
    )
    license_number: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Unique alphanumeric license number",
    )
    contact_number: str = Field(
        ...,
        min_length=7,
        max_length=20,
        description="Driver's phone number",
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Trim whitespace from name."""
        return v.strip()

    @field_validator("license_number")
    @classmethod
    def validate_license_number(cls, v: str) -> str:
        """Validate and normalize license number."""
        v = v.strip().upper()
        if not v:
            raise ValueError("License number cannot be empty")
        if not LICENSE_PATTERN.match(v):
            raise ValueError("License number must be alphanumeric with no whitespace")
        return v

    @field_validator("contact_number")
    @classmethod
    def validate_contact_number(cls, v: str) -> str:
        """Validate and normalize contact number."""
        v = v.strip()
        if not v:
            raise ValueError("Contact number cannot be empty")
        if not PHONE_PATTERN.match(v):
            raise ValueError(
                "Contact number must be a valid phone format "
                "(digits, spaces, hyphens, parentheses allowed, 7-20 chars)"
            )
        return v


class DriverCreate(DriverBase):
    """Schema for creating a new driver."""

    status: DriverStatus = Field(
        default=DriverStatus.ACTIVE,
        description="Initial driver status",
    )


class DriverUpdate(BaseModel):
    """Schema for full driver update (PUT)."""

    name: str = Field(..., min_length=1, max_length=100)
    license_number: str = Field(..., min_length=1, max_length=20)
    contact_number: str = Field(..., min_length=7, max_length=20)
    status: DriverStatus

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Trim whitespace from name."""
        return v.strip()

    @field_validator("license_number")
    @classmethod
    def validate_license_number(cls, v: str) -> str:
        """Validate and normalize license number."""
        v = v.strip().upper()
        if not v:
            raise ValueError("License number cannot be empty")
        if not LICENSE_PATTERN.match(v):
            raise ValueError("License number must be alphanumeric with no whitespace")
        return v

    @field_validator("contact_number")
    @classmethod
    def validate_contact_number(cls, v: str) -> str:
        """Validate and normalize contact number."""
        v = v.strip()
        if not v:
            raise ValueError("Contact number cannot be empty")
        if not PHONE_PATTERN.match(v):
            raise ValueError(
                "Contact number must be a valid phone format "
                "(digits, spaces, hyphens, parentheses allowed, 7-20 chars)"
            )
        return v


class DriverPatch(BaseModel):
    """Schema for partial driver update (PATCH)."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    license_number: Optional[str] = Field(default=None, min_length=1, max_length=20)
    contact_number: Optional[str] = Field(default=None, min_length=7, max_length=20)
    status: Optional[DriverStatus] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Trim whitespace from name if provided."""
        if v is None:
            return None
        return v.strip()

    @field_validator("license_number")
    @classmethod
    def validate_license_number(cls, v: Optional[str]) -> Optional[str]:
        """Validate and normalize license number if provided."""
        if v is None:
            return None
        v = v.strip().upper()
        if not v:
            raise ValueError("License number cannot be empty")
        if not LICENSE_PATTERN.match(v):
            raise ValueError("License number must be alphanumeric with no whitespace")
        return v

    @field_validator("contact_number")
    @classmethod
    def validate_contact_number(cls, v: Optional[str]) -> Optional[str]:
        """Validate and normalize contact number if provided."""
        if v is None:
            return None
        v = v.strip()
        if not v:
            raise ValueError("Contact number cannot be empty")
        if not PHONE_PATTERN.match(v):
            raise ValueError(
                "Contact number must be a valid phone format "
                "(digits, spaces, hyphens, parentheses allowed, 7-20 chars)"
            )
        return v


class DriverResponse(BaseModel):
    """Schema for driver in API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Unique driver identifier (UUID)")
    name: str
    license_number: str
    contact_number: str
    status: DriverStatus
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(cls, driver) -> "DriverResponse":
        """
        Create a response schema from a domain Driver.

        Args:
            driver: Driver domain object.

        Returns:
            DriverResponse instance.
        """
        return cls(
            id=driver.id,
            name=driver.name,
            license_number=driver.license_number,
            contact_number=driver.contact_number,
            status=driver.status,
            created_at=driver.created_at,
            updated_at=driver.updated_at,
        )


class DriverListParams(BaseModel):
    """Query parameters for listing drivers."""

    status: Optional[DriverStatus] = Field(default=None, description="Filter by status")
    include_deleted: bool = Field(
        default=False, description="Include soft-deleted drivers"
    )
    limit: int = Field(
        default=50, ge=1, le=500, description="Maximum results to return"
    )
    skip: int = Field(default=0, ge=0, description="Number of results to skip")
    sort_by: str = Field(default="updated_at", description="Field to sort by")
    sort_order: str = Field(
        default="desc", pattern="^(asc|desc)$", description="Sort direction"
    )
