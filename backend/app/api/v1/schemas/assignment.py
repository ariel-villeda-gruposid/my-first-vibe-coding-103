"""
Assignment Pydantic schemas for API request/response validation.

Defines schemas for creating, updating, and returning assignment data.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# Validation constants
MAX_NOTES_LENGTH = 127


class AssignmentBase(BaseModel):
    """Base schema with shared assignment attributes."""

    driver_id: str = Field(
        ...,
        description="UUID of the driver being assigned",
    )
    vehicle_id: str = Field(
        ...,
        description="UUID of the vehicle being assigned",
    )
    start_datetime: datetime = Field(
        ...,
        description="Start datetime of the assignment (UTC)",
    )


class AssignmentCreate(AssignmentBase):
    """Schema for creating a new assignment."""

    end_datetime: Optional[datetime] = Field(
        default=None,
        description="End datetime (null for ongoing assignments)",
    )
    notes: Optional[str] = Field(
        default=None,
        max_length=MAX_NOTES_LENGTH,
        description=f"Optional notes (max {MAX_NOTES_LENGTH} chars)",
    )

    @field_validator("notes")
    @classmethod
    def validate_notes(cls, v: Optional[str]) -> Optional[str]:
        """Trim trailing whitespace from notes."""
        if v is None:
            return None
        v = v.rstrip()
        if not v:
            return None
        if len(v) > MAX_NOTES_LENGTH:
            raise ValueError(f"Notes must be at most {MAX_NOTES_LENGTH} characters")
        return v

    @model_validator(mode="after")
    def validate_dates(self) -> "AssignmentCreate":
        """Validate that start_datetime <= end_datetime if end_datetime is provided."""
        if self.end_datetime is not None:
            if self.start_datetime > self.end_datetime:
                raise ValueError("start_datetime must be <= end_datetime")
        return self


class AssignmentUpdate(BaseModel):
    """Schema for updating an assignment (PATCH operation).

    Only notes and end_datetime may be modified.
    start_datetime can be modified only if new value <= now.
    """

    notes: Optional[str] = Field(
        default=None,
        max_length=MAX_NOTES_LENGTH,
        description=f"Updated notes (max {MAX_NOTES_LENGTH} chars)",
    )
    end_datetime: Optional[datetime] = Field(
        default=None,
        description="End datetime to close the assignment",
    )
    start_datetime: Optional[datetime] = Field(
        default=None,
        description="Updated start datetime (must be <= now)",
    )

    @field_validator("notes")
    @classmethod
    def validate_notes(cls, v: Optional[str]) -> Optional[str]:
        """Trim trailing whitespace from notes."""
        if v is None:
            return None
        v = v.rstrip()
        if not v:
            return None
        if len(v) > MAX_NOTES_LENGTH:
            raise ValueError(f"Notes must be at most {MAX_NOTES_LENGTH} characters")
        return v


class AssignmentResponse(BaseModel):
    """Schema for assignment in API responses."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Unique assignment identifier (UUID)")
    driver_id: str
    vehicle_id: str
    start_datetime: datetime
    end_datetime: Optional[datetime]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    # Optional: Include driver and vehicle names for convenience
    driver_name: Optional[str] = Field(
        default=None, description="Driver name from join"
    )
    vehicle_plate: Optional[str] = Field(
        default=None, description="Vehicle plate from join"
    )

    @classmethod
    def from_domain(
        cls,
        assignment,
        driver_name: Optional[str] = None,
        vehicle_plate: Optional[str] = None,
    ) -> "AssignmentResponse":
        """
        Create a response schema from a domain Assignment.

        Args:
            assignment: Assignment domain object.
            driver_name: Optional driver name for display.
            vehicle_plate: Optional vehicle plate for display.

        Returns:
            AssignmentResponse instance.
        """
        return cls(
            id=assignment.id,
            driver_id=assignment.driver_id,
            vehicle_id=assignment.vehicle_id,
            start_datetime=assignment.start_datetime,
            end_datetime=assignment.end_datetime,
            notes=assignment.notes,
            created_at=assignment.created_at,
            updated_at=assignment.updated_at,
            driver_name=driver_name,
            vehicle_plate=vehicle_plate,
        )


class AssignmentListParams(BaseModel):
    """Query parameters for listing assignments."""

    driver_id: Optional[str] = Field(default=None, description="Filter by driver ID")
    vehicle_id: Optional[str] = Field(default=None, description="Filter by vehicle ID")
    active_only: bool = Field(default=False, description="Show only active assignments")
    limit: int = Field(
        default=50, ge=1, le=500, description="Maximum results to return"
    )
    skip: int = Field(default=0, ge=0, description="Number of results to skip")
    sort_by: str = Field(default="start_datetime", description="Field to sort by")
    sort_order: str = Field(
        default="desc", pattern="^(asc|desc)$", description="Sort direction"
    )


class AssignmentListResponse(BaseModel):
    """Response schema for paginated assignment list."""

    items: list[AssignmentResponse] = Field(..., description="List of assignments")
    total: int = Field(..., description="Total number of matching assignments")
    limit: int = Field(..., description="Maximum results requested")
    skip: int = Field(..., description="Number of results skipped")
