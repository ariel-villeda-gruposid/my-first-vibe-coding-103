"""
Statistics Pydantic schemas for API serialization.

Defines response schemas for the statistics endpoint.
"""

from typing import Dict

from pydantic import BaseModel, Field


class VehicleStats(BaseModel):
    """Vehicle statistics by status."""

    active: int = Field(default=0, description="Number of active vehicles")
    inactive: int = Field(default=0, description="Number of inactive vehicles")
    maintenance: int = Field(default=0, description="Number of vehicles in maintenance")


class DriverStats(BaseModel):
    """Driver statistics by status."""

    active: int = Field(default=0, description="Number of active drivers")
    suspended: int = Field(default=0, description="Number of suspended drivers")


class AssignmentStats(BaseModel):
    """Assignment statistics."""

    active: int = Field(default=0, description="Number of active assignments")
    total: int = Field(default=0, description="Total number of assignments")


class DashboardStats(BaseModel):
    """Complete dashboard statistics response."""

    vehicle_count_by_status: Dict[str, int] = Field(
        default_factory=dict,
        description="Vehicle counts grouped by status",
    )
    driver_count_by_status: Dict[str, int] = Field(
        default_factory=dict,
        description="Driver counts grouped by status",
    )
    active_assignments_count: int = Field(
        default=0,
        description="Number of currently active assignments",
    )
    total_assignments_count: int = Field(
        default=0,
        description="Total number of assignments",
    )

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "vehicle_count_by_status": {
                    "active": 15,
                    "inactive": 5,
                    "maintenance": 3,
                },
                "driver_count_by_status": {
                    "active": 20,
                    "suspended": 2,
                },
                "active_assignments_count": 12,
                "total_assignments_count": 150,
            }
        }
