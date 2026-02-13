"""API v1 schemas module initialization."""

from app.api.v1.schemas.vehicle import (
    VehicleCreate,
    VehicleListParams,
    VehiclePatch,
    VehicleResponse,
    VehicleUpdate,
)

__all__ = [
    "VehicleCreate",
    "VehicleUpdate",
    "VehiclePatch",
    "VehicleResponse",
    "VehicleListParams",
]
