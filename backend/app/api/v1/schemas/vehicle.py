"""
Vehicle Pydantic schemas for API request/response validation.

Defines schemas for creating, updating, and returning vehicle data.
"""

import re
from datetime import datetime
from typing import Optional

from app.domain.models.vehicle import FuelType, VehicleStatus, VehicleType
from pydantic import BaseModel, ConfigDict, Field, field_validator

# Validation constants
MIN_YEAR = 1996
MAX_YEAR = 2030
MAX_PLATE_LENGTH = 10
PLATE_PATTERN = re.compile(r"^[A-Za-z0-9]+$")


class VehicleBase(BaseModel):
    """Base schema with shared vehicle attributes."""

    plate_number: str = Field(
        ...,
        min_length=1,
        max_length=MAX_PLATE_LENGTH,
        description="Unique alphanumeric plate number (max 10 chars)",
    )
    model: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Vehicle model name",
    )
    year: int = Field(
        ...,
        ge=MIN_YEAR,
        le=MAX_YEAR,
        description=f"Manufacturing year ({MIN_YEAR}-{MAX_YEAR})",
    )
    type: VehicleType = Field(..., description="Vehicle type classification")
    fuel_type: FuelType = Field(..., description="Fuel type")

    @field_validator("plate_number")
    @classmethod
    def validate_plate_number(cls, v: str) -> str:
        """Validate and normalize plate number."""
        v = v.strip().upper()
        if not v:
            raise ValueError("Plate number cannot be empty")
        if not PLATE_PATTERN.match(v):
            raise ValueError("Plate number must be alphanumeric with no whitespace")
        if len(v) > MAX_PLATE_LENGTH:
            raise ValueError(
                f"Plate number must be at most {MAX_PLATE_LENGTH} characters"
            )
        return v

    @field_validator("model")
    @classmethod
    def validate_model(cls, v: str) -> str:
        """Trim whitespace from model name."""
        return v.strip()


class VehicleCreate(VehicleBase):
    """Schema for creating a new vehicle."""

    status: VehicleStatus = Field(
        default=VehicleStatus.ACTIVE,
        description="Initial vehicle status",
    )


class VehicleUpdate(BaseModel):
    """Schema for full vehicle update (PUT)."""

    plate_number: str = Field(
        ...,
        min_length=1,
        max_length=MAX_PLATE_LENGTH,
        description="Unique alphanumeric plate number",
    )
    model: str = Field(..., min_length=1, max_length=100)
    year: int = Field(..., ge=MIN_YEAR, le=MAX_YEAR)
    type: VehicleType
    fuel_type: FuelType
    status: VehicleStatus

    @field_validator("plate_number")
    @classmethod
    def validate_plate_number(cls, v: str) -> str:
        """Validate and normalize plate number."""
        v = v.strip().upper()
        if not v:
            raise ValueError("Plate number cannot be empty")
        if not PLATE_PATTERN.match(v):
            raise ValueError("Plate number must be alphanumeric with no whitespace")
        return v

    @field_validator("model")
    @classmethod
    def validate_model(cls, v: str) -> str:
        """Trim whitespace from model name."""
        return v.strip()


class VehiclePatch(BaseModel):
    """Schema for partial vehicle update (PATCH)."""

    plate_number: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=MAX_PLATE_LENGTH,
    )
    model: Optional[str] = Field(default=None, min_length=1, max_length=100)
    year: Optional[int] = Field(default=None, ge=MIN_YEAR, le=MAX_YEAR)
    type: Optional[VehicleType] = None
    fuel_type: Optional[FuelType] = None
    status: Optional[VehicleStatus] = None

    @field_validator("plate_number")
    @classmethod
    def validate_plate_number(cls, v: Optional[str]) -> Optional[str]:
        """Validate and normalize plate number if provided."""
        if v is None:
            return None
        v = v.strip().upper()
        if not v:
            raise ValueError("Plate number cannot be empty")
        if not PLATE_PATTERN.match(v):
            raise ValueError("Plate number must be alphanumeric with no whitespace")
        return v

    @field_validator("model")
    @classmethod
    def validate_model(cls, v: Optional[str]) -> Optional[str]:
        """Trim whitespace from model name if provided."""
        if v is None:
            return None
        return v.strip()


class VehicleResponse(BaseModel):
    """Schema for vehicle in API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Unique vehicle identifier (UUID)")
    plate_number: str
    model: str
    year: int
    type: VehicleType
    fuel_type: FuelType
    status: VehicleStatus
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_domain(cls, vehicle) -> "VehicleResponse":
        """
        Create a response schema from a domain Vehicle.

        Args:
            vehicle: Vehicle domain object.

        Returns:
            VehicleResponse instance.
        """
        return cls(
            id=vehicle.id,
            plate_number=vehicle.plate_number,
            model=vehicle.model,
            year=vehicle.year,
            type=vehicle.type,
            fuel_type=vehicle.fuel_type,
            status=vehicle.status,
            created_at=vehicle.created_at,
            updated_at=vehicle.updated_at,
        )


class VehicleListParams(BaseModel):
    """Query parameters for listing vehicles."""

    status: Optional[VehicleStatus] = Field(
        default=None, description="Filter by status"
    )
    type: Optional[VehicleType] = Field(
        default=None, description="Filter by vehicle type"
    )
    fuel_type: Optional[FuelType] = Field(
        default=None, description="Filter by fuel type"
    )
    include_deleted: bool = Field(
        default=False, description="Include soft-deleted vehicles"
    )
    limit: int = Field(
        default=50, ge=1, le=500, description="Maximum results to return"
    )
    skip: int = Field(default=0, ge=0, description="Number of results to skip")
    sort_by: str = Field(default="updated_at", description="Field to sort by")
    sort_order: str = Field(
        default="desc", pattern="^(asc|desc)$", description="Sort direction"
    )
