"""
Driver domain model and enums.

Defines the Driver entity and related enumerations for the fleet management system.
"""

import re
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


class DriverStatus(str, Enum):
    """Driver operational status."""

    ACTIVE = "active"
    SUSPENDED = "suspended"


class Driver:
    """
    Driver domain entity.

    Represents a fleet driver with all their attributes and business rules.

    Attributes:
        id: Unique identifier (UUID string).
        name: Driver's full name.
        license_number: Unique license number (normalized to uppercase, alphanumeric).
        contact_number: Driver's phone number.
        status: Current operational status.
        created_at: Timestamp when the driver was created.
        updated_at: Timestamp when the driver was last updated.
        deleted_at: Timestamp when the driver was soft-deleted (None if active).
    """

    # Validation constants
    LICENSE_PATTERN = re.compile(r"^[A-Za-z0-9]+$")
    # Flexible phone pattern: allows + prefix, digits, spaces, hyphens, parentheses
    PHONE_PATTERN = re.compile(r"^\+?[\d\s\-\(\)]{7,20}$")

    def __init__(
        self,
        name: str,
        license_number: str,
        contact_number: str,
        status: DriverStatus = DriverStatus.ACTIVE,
        id: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        deleted_at: Optional[datetime] = None,
    ) -> None:
        """
        Initialize a Driver instance.

        Args:
            name: Driver's full name.
            license_number: Unique license number (will be normalized).
            contact_number: Driver's phone number.
            status: Operational status (default: ACTIVE).
            id: Optional UUID (generated if not provided).
            created_at: Optional creation timestamp.
            updated_at: Optional update timestamp.
            deleted_at: Optional soft-delete timestamp.
        """
        now = datetime.now(timezone.utc)

        self.id = id or str(uuid.uuid4())
        self.name = name.strip()
        self.license_number = self._normalize_license_number(license_number)
        self.contact_number = self._normalize_contact_number(contact_number)
        self.status = status
        self.created_at = created_at or now
        self.updated_at = updated_at or now
        self.deleted_at = deleted_at

    @staticmethod
    def _normalize_license_number(license_number: str) -> str:
        """
        Normalize license number to uppercase, trimmed.

        Args:
            license_number: Raw license number.

        Returns:
            Normalized license number.
        """
        return license_number.strip().upper()

    @staticmethod
    def _normalize_contact_number(contact_number: str) -> str:
        """
        Normalize contact number by trimming whitespace.

        Args:
            contact_number: Raw contact number.

        Returns:
            Normalized contact number.
        """
        return contact_number.strip()

    @classmethod
    def validate_license_number(cls, license_number: str) -> bool:
        """
        Validate that license number is alphanumeric.

        Args:
            license_number: License number to validate.

        Returns:
            True if valid, False otherwise.
        """
        normalized = cls._normalize_license_number(license_number)
        return bool(normalized and cls.LICENSE_PATTERN.match(normalized))

    @classmethod
    def validate_contact_number(cls, contact_number: str) -> bool:
        """
        Validate that contact number matches phone format.

        Args:
            contact_number: Contact number to validate.

        Returns:
            True if valid, False otherwise.
        """
        normalized = cls._normalize_contact_number(contact_number)
        return bool(normalized and cls.PHONE_PATTERN.match(normalized))

    def is_active(self) -> bool:
        """Check if the driver is active (not deleted and status is ACTIVE)."""
        return self.deleted_at is None and self.status == DriverStatus.ACTIVE

    def is_deleted(self) -> bool:
        """Check if the driver has been soft-deleted."""
        return self.deleted_at is not None

    def can_receive_assignments(self) -> bool:
        """Check if the driver can receive new assignments."""
        return self.is_active()

    def soft_delete(self) -> None:
        """Mark the driver as soft-deleted."""
        now = datetime.now(timezone.utc)
        self.deleted_at = now
        self.updated_at = now

    def update(
        self,
        name: Optional[str] = None,
        license_number: Optional[str] = None,
        contact_number: Optional[str] = None,
        status: Optional[DriverStatus] = None,
    ) -> None:
        """
        Update driver attributes.

        Only updates provided (non-None) values.

        Args:
            name: New name (optional).
            license_number: New license number (optional).
            contact_number: New contact number (optional).
            status: New status (optional).
        """
        if name is not None:
            self.name = name.strip()
        if license_number is not None:
            self.license_number = self._normalize_license_number(license_number)
        if contact_number is not None:
            self.contact_number = self._normalize_contact_number(contact_number)
        if status is not None:
            self.status = status

        self.updated_at = datetime.now(timezone.utc)

    def to_dict(self) -> dict:
        """
        Convert the driver to a dictionary.

        Returns:
            Dictionary representation of the driver.
        """
        return {
            "id": self.id,
            "name": self.name,
            "license_number": self.license_number,
            "contact_number": self.contact_number,
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "deleted_at": self.deleted_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Driver":
        """
        Create a Driver instance from a dictionary.

        Args:
            data: Dictionary containing driver data.

        Returns:
            Driver instance.
        """
        status = data.get("status")
        if isinstance(status, str):
            status = DriverStatus(status)

        return cls(
            id=data.get("id"),
            name=data["name"],
            license_number=data["license_number"],
            contact_number=data["contact_number"],
            status=status or DriverStatus.ACTIVE,
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            deleted_at=data.get("deleted_at"),
        )

    def __eq__(self, other: object) -> bool:
        """Check equality based on ID."""
        if not isinstance(other, Driver):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        """Hash based on ID."""
        return hash(self.id)

    def __repr__(self) -> str:
        """Return string representation."""
        return (
            f"Driver(id={self.id!r}, name={self.name!r}, "
            f"license_number={self.license_number!r}, status={self.status.value!r})"
        )
