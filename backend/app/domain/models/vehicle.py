"""
Vehicle domain model and enums.

Defines the Vehicle entity and related enumerations for the fleet management system.
"""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class VehicleStatus(str, Enum):
    """Vehicle operational status."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"


class VehicleType(str, Enum):
    """Vehicle type classification."""

    SEDAN = "sedan"
    SUV = "suv"
    TRUCK = "truck"
    VAN = "van"
    MOTORCYCLE = "motorcycle"


class FuelType(str, Enum):
    """Vehicle fuel type."""

    GASOLINE = "gasoline"
    DIESEL = "diesel"
    ELECTRIC = "electric"
    HYBRID = "hybrid"


class Vehicle:
    """
    Vehicle domain entity.

    Represents a fleet vehicle with all its attributes and business rules.

    Attributes:
        id: Unique identifier (UUID string).
        plate_number: Unique vehicle plate number (normalized to uppercase).
        model: Vehicle model name.
        year: Manufacturing year (>= 1996).
        type: Vehicle type classification.
        fuel_type: Type of fuel the vehicle uses.
        status: Current operational status.
        created_at: Timestamp when the vehicle was created.
        updated_at: Timestamp when the vehicle was last updated.
        deleted_at: Timestamp when the vehicle was soft-deleted (None if active).
    """

    def __init__(
        self,
        plate_number: str,
        model: str,
        year: int,
        vehicle_type: VehicleType,
        fuel_type: FuelType,
        status: VehicleStatus = VehicleStatus.ACTIVE,
        id: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        deleted_at: Optional[datetime] = None,
    ) -> None:
        """
        Initialize a Vehicle instance.

        Args:
            plate_number: Vehicle plate number (will be normalized).
            model: Vehicle model name.
            year: Manufacturing year.
            vehicle_type: Type of vehicle.
            fuel_type: Type of fuel.
            status: Operational status (default: ACTIVE).
            id: Optional UUID (generated if not provided).
            created_at: Optional creation timestamp.
            updated_at: Optional update timestamp.
            deleted_at: Optional soft-delete timestamp.
        """
        now = datetime.now(timezone.utc)

        self.id = id or str(uuid.uuid4())
        self.plate_number = self._normalize_plate_number(plate_number)
        self.model = model.strip()
        self.year = year
        self.type = vehicle_type
        self.fuel_type = fuel_type
        self.status = status
        self.created_at = created_at or now
        self.updated_at = updated_at or now
        self.deleted_at = deleted_at

    @staticmethod
    def _normalize_plate_number(plate_number: str) -> str:
        """
        Normalize plate number to uppercase with trimmed whitespace.

        Args:
            plate_number: Raw plate number input.

        Returns:
            Normalized plate number string.
        """
        return plate_number.strip().upper()

    @property
    def is_deleted(self) -> bool:
        """Check if the vehicle is soft-deleted."""
        return self.deleted_at is not None

    @property
    def vehicle_type(self) -> VehicleType:
        """Get the vehicle type."""
        return self.type

    @property
    def can_be_assigned(self) -> bool:
        """Check if the vehicle can receive assignments."""
        return self.status == VehicleStatus.ACTIVE and not self.is_deleted

    def soft_delete(self) -> None:
        """Mark the vehicle as soft-deleted."""
        now = datetime.now(timezone.utc)
        self.deleted_at = now
        self.updated_at = now

    def restore(self) -> None:
        """Restore a soft-deleted vehicle."""
        self.deleted_at = None
        self.updated_at = datetime.now(timezone.utc)

    def update(
        self,
        plate_number: Optional[str] = None,
        model: Optional[str] = None,
        year: Optional[int] = None,
        vehicle_type: Optional[VehicleType] = None,
        fuel_type: Optional[FuelType] = None,
        status: Optional[VehicleStatus] = None,
    ) -> None:
        """
        Update vehicle attributes.

        Args:
            plate_number: New plate number (optional).
            model: New model name (optional).
            year: New year (optional).
            vehicle_type: New vehicle type (optional).
            fuel_type: New fuel type (optional).
            status: New status (optional).
        """
        if plate_number is not None:
            self.plate_number = self._normalize_plate_number(plate_number)
        if model is not None:
            self.model = model.strip()
        if year is not None:
            self.year = year
        if vehicle_type is not None:
            self.type = vehicle_type
        if fuel_type is not None:
            self.fuel_type = fuel_type
        if status is not None:
            self.status = status

        self.updated_at = datetime.now(timezone.utc)

    def to_dict(self) -> dict:
        """
        Convert vehicle to dictionary representation.

        Returns:
            Dictionary with all vehicle attributes.
        """
        return {
            "id": self.id,
            "plate_number": self.plate_number,
            "model": self.model,
            "year": self.year,
            "vehicle_type": self.type.value,
            "fuel_type": self.fuel_type.value,
            "status": self.status.value,
            "is_deleted": self.is_deleted,
            "created_at": self.created_at.isoformat().replace("+00:00", "Z"),
            "updated_at": self.updated_at.isoformat().replace("+00:00", "Z"),
            "deleted_at": (
                self.deleted_at.isoformat().replace("+00:00", "Z")
                if self.deleted_at
                else None
            ),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Vehicle":
        """
        Create a Vehicle from a dictionary.

        Args:
            data: Dictionary with vehicle attributes.

        Returns:
            Vehicle instance.
        """
        return cls(
            id=data.get("id"),
            plate_number=data["plate_number"],
            model=data["model"],
            year=data["year"],
            vehicle_type=VehicleType(data["vehicle_type"]),
            fuel_type=FuelType(data["fuel_type"]),
            status=VehicleStatus(data.get("status", "active")),
            created_at=cls._parse_datetime(data.get("created_at")),
            updated_at=cls._parse_datetime(data.get("updated_at")),
            deleted_at=cls._parse_datetime(data.get("deleted_at")),
        )

    @staticmethod
    def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
        """Parse ISO datetime string to datetime object."""
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        # Handle both Z suffix and +00:00
        value = value.replace("Z", "+00:00")
        return datetime.fromisoformat(value)

    def __repr__(self) -> str:
        """String representation of the vehicle."""
        return (
            f"Vehicle(id={self.id!r}, plate_number={self.plate_number!r}, "
            f"model={self.model!r}, status={self.status.value!r})"
        )

    def __eq__(self, other: object) -> bool:
        """Check equality based on ID."""
        if not isinstance(other, Vehicle):
            return False
        return self.id == other.id
