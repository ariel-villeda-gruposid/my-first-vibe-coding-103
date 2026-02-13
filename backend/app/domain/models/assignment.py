"""
Assignment domain model.

Defines the Assignment entity for linking drivers to vehicles.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional


class Assignment:
    """
    Assignment domain entity.

    Represents a relationship between a driver and a vehicle for a time period.

    Attributes:
        id: Unique identifier (UUID string).
        driver_id: UUID of the assigned driver.
        vehicle_id: UUID of the assigned vehicle.
        start_datetime: When the assignment started (UTC).
        end_datetime: When the assignment ended (UTC), None if active.
        notes: Optional notes about the assignment (max 127 chars).
        created_at: Timestamp when the assignment was created.
        updated_at: Timestamp when the assignment was last updated.
    """

    MAX_NOTES_LENGTH = 127

    def __init__(
        self,
        driver_id: str,
        vehicle_id: str,
        start_datetime: datetime,
        end_datetime: Optional[datetime] = None,
        notes: Optional[str] = None,
        id: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ) -> None:
        """
        Initialize an Assignment instance.

        Args:
            driver_id: UUID of the driver.
            vehicle_id: UUID of the vehicle.
            start_datetime: Start of the assignment.
            end_datetime: End of the assignment (None for active).
            notes: Optional notes (max 127 chars, will be trimmed).
            id: Optional UUID (generated if not provided).
            created_at: Optional creation timestamp.
            updated_at: Optional update timestamp.
        """
        now = datetime.now(timezone.utc)

        self.id = id or str(uuid.uuid4())
        self.driver_id = driver_id
        self.vehicle_id = vehicle_id
        self.start_datetime = start_datetime
        self.end_datetime = end_datetime
        self.notes = self._normalize_notes(notes)
        self.created_at = created_at or now
        self.updated_at = updated_at or now

    @staticmethod
    def _normalize_notes(notes: Optional[str]) -> Optional[str]:
        """
        Normalize notes by trimming trailing whitespace.

        Args:
            notes: Raw notes string.

        Returns:
            Normalized notes or None.
        """
        if notes is None:
            return None
        normalized = notes.rstrip()
        if not normalized:
            return None
        return normalized

    @classmethod
    def validate_notes(cls, notes: Optional[str]) -> bool:
        """
        Validate that notes are within length limit.

        Args:
            notes: Notes to validate.

        Returns:
            True if valid, False otherwise.
        """
        if notes is None:
            return True
        normalized = notes.rstrip()
        return len(normalized) <= cls.MAX_NOTES_LENGTH

    def is_active(self) -> bool:
        """
        Check if the assignment is currently active.

        An assignment is active if end_datetime is None or in the future.

        Returns:
            True if assignment is active.
        """
        if self.end_datetime is None:
            return True
        return self.end_datetime > datetime.now(timezone.utc)

    def close(self, end_time: Optional[datetime] = None) -> None:
        """
        Close the assignment by setting end_datetime.

        Args:
            end_time: End time (defaults to now).
        """
        now = datetime.now(timezone.utc)
        self.end_datetime = end_time or now
        self.updated_at = now

    def update(
        self,
        notes: Optional[str] = ...,
        end_datetime: Optional[datetime] = ...,
        start_datetime: Optional[datetime] = ...,
    ) -> None:
        """
        Update assignment attributes.

        Only updates provided (not ...) values.

        Args:
            notes: New notes (optional).
            end_datetime: New end datetime (optional).
            start_datetime: New start datetime (optional).

        Raises:
            ValueError: If notes exceed MAX_NOTES_LENGTH.
        """
        if notes is not ...:
            if notes is not None and not self.validate_notes(notes):
                raise ValueError(
                    f"Notes must be at most {self.MAX_NOTES_LENGTH} characters"
                )
            self.notes = self._normalize_notes(notes)
        if end_datetime is not ...:
            self.end_datetime = end_datetime
        if start_datetime is not ...:
            self.start_datetime = start_datetime

        self.updated_at = datetime.now(timezone.utc)

    def to_dict(self) -> dict:
        """
        Convert the assignment to a dictionary.

        Returns:
            Dictionary representation of the assignment.
        """
        return {
            "id": self.id,
            "driver_id": self.driver_id,
            "vehicle_id": self.vehicle_id,
            "start_datetime": self.start_datetime,
            "end_datetime": self.end_datetime,
            "notes": self.notes,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Assignment":
        """
        Create an Assignment instance from a dictionary.

        Args:
            data: Dictionary containing assignment data.

        Returns:
            Assignment instance.
        """
        return cls(
            id=data.get("id"),
            driver_id=data["driver_id"],
            vehicle_id=data["vehicle_id"],
            start_datetime=data["start_datetime"],
            end_datetime=data.get("end_datetime"),
            notes=data.get("notes"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )

    def __eq__(self, other: object) -> bool:
        """Check equality based on ID."""
        if not isinstance(other, Assignment):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        """Hash based on ID."""
        return hash(self.id)

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"Assignment(id={self.id!r}, driver_id={self.driver_id!r}, "
            f"vehicle_id={self.vehicle_id!r}, active={self.is_active()})"
        )
