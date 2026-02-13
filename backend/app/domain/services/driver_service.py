"""
Driver service for business logic.

Implements business rules and orchestrates driver operations.
"""

from typing import Dict, List, Optional, Tuple

from app.core.exceptions import (
    ConcurrencyException,
    ConflictException,
    NotFoundException,
)
from app.domain.models.driver import Driver, DriverStatus
from app.infrastructure.repositories.driver_repository import DriverRepository


class DriverService:
    """
    Service class for driver business logic.

    Handles all driver-related business rules and operations.
    """

    def __init__(
        self,
        driver_repository: DriverRepository,
        assignment_repository: Optional[object] = None,
    ) -> None:
        """
        Initialize the service with required repositories.

        Args:
            driver_repository: Repository for driver data access.
            assignment_repository: Repository for assignment data access (optional).
        """
        self._driver_repository = driver_repository
        self._assignment_repository = assignment_repository

    def get_all_drivers(
        self,
        status: Optional[DriverStatus] = None,
        include_deleted: bool = False,
        limit: int = 50,
        skip: int = 0,
        sort_by: str = "updated_at",
        sort_order: str = "desc",
    ) -> Tuple[List[Driver], int]:
        """
        Get all drivers with optional filtering and pagination.

        Args:
            status: Filter by driver status.
            include_deleted: Whether to include soft-deleted drivers.
            limit: Maximum number of results.
            skip: Number of results to skip.
            sort_by: Field to sort by.
            sort_order: Sort direction.

        Returns:
            Tuple of (list of drivers, total count).
        """
        return self._driver_repository.find_all(
            status=status,
            include_deleted=include_deleted,
            limit=limit,
            skip=skip,
            sort_by=sort_by,
            sort_order=sort_order,
        )

    def get_driver_by_id(self, driver_id: str) -> Driver:
        """
        Get a driver by their ID.

        Args:
            driver_id: Driver UUID string.

        Returns:
            Driver domain object.

        Raises:
            NotFoundException: If driver is not found.
        """
        driver = self._driver_repository.find_by_id(driver_id)
        if driver is None:
            raise NotFoundException(
                code="DRIVER_NOT_FOUND",
                message=f"Driver with ID '{driver_id}' not found.",
            )
        return driver

    def create_driver(
        self,
        name: str,
        license_number: str,
        contact_number: str,
        status: DriverStatus = DriverStatus.ACTIVE,
    ) -> Driver:
        """
        Create a new driver.

        If a soft-deleted driver with the same license number exists,
        it will be restored and updated instead of creating a new one.

        Args:
            name: Driver's full name.
            license_number: Unique license number.
            contact_number: Contact phone number.
            status: Initial status (default: ACTIVE).

        Returns:
            Created or restored driver.

        Raises:
            ConflictException: If license number is already in use.
        """
        normalized_license = license_number.strip().upper()

        # Check for existing driver with same license (including soft-deleted)
        existing = self._driver_repository.find_by_license_number(
            normalized_license, include_deleted=True
        )

        if existing is not None:
            if existing.is_deleted():
                # Restore and update the soft-deleted driver
                existing.deleted_at = None
                existing.update(
                    name=name,
                    license_number=normalized_license,
                    contact_number=contact_number,
                    status=status,
                )
                return self._driver_repository.update(existing)
            else:
                # Active driver with same license exists
                raise ConflictException(
                    code="DUPLICATE_LICENSE",
                    message=(
                        f"A driver with license number '{normalized_license}' "
                        "already exists."
                    ),
                )

        # Create new driver
        driver = Driver(
            name=name,
            license_number=normalized_license,
            contact_number=contact_number,
            status=status,
        )
        return self._driver_repository.create(driver)

    def update_driver(
        self,
        driver_id: str,
        name: str,
        license_number: str,
        contact_number: str,
        status: DriverStatus,
        etag: Optional[str] = None,
    ) -> Driver:
        """
        Fully update a driver (PUT operation).

        Args:
            driver_id: Driver UUID to update.
            name: New name.
            license_number: New license number.
            contact_number: New contact number.
            status: New status.
            etag: Optional ETag for concurrency control.

        Returns:
            Updated driver.

        Raises:
            NotFoundException: If driver is not found.
            ConflictException: If license number conflicts or status change is invalid.
            ConcurrencyException: If ETag doesn't match.
        """
        driver = self.get_driver_by_id(driver_id)

        # Check if driver is deleted
        if driver.is_deleted():
            raise NotFoundException(
                code="DRIVER_NOT_FOUND",
                message=f"Driver with ID '{driver_id}' not found.",
            )

        # Check ETag for concurrency
        if etag is not None:
            current_etag = self._driver_repository.generate_etag(driver)
            if etag != current_etag:
                raise ConcurrencyException()

        # Validate license number uniqueness
        normalized_license = license_number.strip().upper()
        if normalized_license != driver.license_number:
            if self._driver_repository.exists_by_license_number(
                normalized_license, exclude_id=driver_id
            ):
                raise ConflictException(
                    code="DUPLICATE_LICENSE",
                    message=(
                        f"A driver with license number '{normalized_license}' "
                        "already exists."
                    ),
                )

        # Validate status transition
        self._validate_status_transition(driver, status)

        # Update driver
        driver.update(
            name=name,
            license_number=normalized_license,
            contact_number=contact_number,
            status=status,
        )

        return self._driver_repository.update(driver)

    def patch_driver(
        self,
        driver_id: str,
        name: Optional[str] = None,
        license_number: Optional[str] = None,
        contact_number: Optional[str] = None,
        status: Optional[DriverStatus] = None,
        etag: Optional[str] = None,
    ) -> Driver:
        """
        Partially update a driver (PATCH operation).

        Args:
            driver_id: Driver UUID to update.
            name: New name (optional).
            license_number: New license number (optional).
            contact_number: New contact number (optional).
            status: New status (optional).
            etag: Optional ETag for concurrency control.

        Returns:
            Updated driver.

        Raises:
            NotFoundException: If driver is not found.
            ConflictException: If license number conflicts or status change is invalid.
            ConcurrencyException: If ETag doesn't match.
        """
        driver = self.get_driver_by_id(driver_id)

        # Check if driver is deleted
        if driver.is_deleted():
            raise NotFoundException(
                code="DRIVER_NOT_FOUND",
                message=f"Driver with ID '{driver_id}' not found.",
            )

        # Check ETag for concurrency
        if etag is not None:
            current_etag = self._driver_repository.generate_etag(driver)
            if etag != current_etag:
                raise ConcurrencyException()

        # Validate license number uniqueness if changing
        if license_number is not None:
            normalized_license = license_number.strip().upper()
            if normalized_license != driver.license_number:
                if self._driver_repository.exists_by_license_number(
                    normalized_license, exclude_id=driver_id
                ):
                    raise ConflictException(
                        code="DUPLICATE_LICENSE",
                        message=(
                            f"A driver with license number '{normalized_license}' "
                            "already exists."
                        ),
                    )

        # Validate status transition if changing
        if status is not None:
            self._validate_status_transition(driver, status)

        # Update only provided fields
        driver.update(
            name=name,
            license_number=license_number,
            contact_number=contact_number,
            status=status,
        )

        return self._driver_repository.update(driver)

    def delete_driver(self, driver_id: str) -> None:
        """
        Soft delete a driver.

        Args:
            driver_id: Driver UUID to delete.

        Raises:
            NotFoundException: If driver is not found.
            ConflictException: If driver has active assignments.
        """
        driver = self.get_driver_by_id(driver_id)

        if driver.is_deleted():
            raise NotFoundException(
                code="DRIVER_NOT_FOUND",
                message=f"Driver with ID '{driver_id}' not found.",
            )

        # Check for active assignments
        if self._has_active_assignments(driver_id):
            raise ConflictException(
                code="DRIVER_HAS_ACTIVE_ASSIGNMENTS",
                message="Cannot delete driver with active assignments. Close assignments first.",
            )

        self._driver_repository.soft_delete(driver_id)

    def get_driver_etag(self, driver: Driver) -> str:
        """
        Get the ETag for a driver.

        Args:
            driver: Driver domain object.

        Returns:
            ETag string.
        """
        return self._driver_repository.generate_etag(driver)

    def get_driver_counts_by_status(self) -> Dict[str, int]:
        """
        Get driver counts grouped by status.

        Returns:
            Dictionary mapping status to count.
        """
        return self._driver_repository.count_by_status()

    def get_active_drivers(
        self, limit: int = 100, skip: int = 0
    ) -> Tuple[List[Driver], int]:
        """
        Get all active drivers (for assignment dropdowns).

        Args:
            limit: Maximum number of results.
            skip: Number of results to skip.

        Returns:
            Tuple of (list of active drivers, total count).
        """
        return self._driver_repository.find_active_drivers(limit=limit, skip=skip)

    def _validate_status_transition(
        self, driver: Driver, new_status: DriverStatus
    ) -> None:
        """
        Validate that a status transition is allowed.

        SUSPENDED drivers cannot receive assignments.
        Changing to SUSPENDED requires no active assignments.

        Args:
            driver: Current driver state.
            new_status: Desired new status.

        Raises:
            ConflictException: If the transition is not allowed.
        """
        # If status isn't changing, no validation needed
        if driver.status == new_status:
            return

        # Moving to SUSPENDED requires no active assignments
        if new_status == DriverStatus.SUSPENDED:
            if self._has_active_assignments(driver.id):
                raise ConflictException(
                    code="DRIVER_HAS_ACTIVE_ASSIGNMENTS",
                    message=(
                        "Cannot change status to suspended while driver "
                        "has active assignments. Close assignments first."
                    ),
                )

    def _has_active_assignments(self, driver_id: str) -> bool:
        """
        Check if a driver has active assignments.

        Args:
            driver_id: Driver UUID to check.

        Returns:
            True if the driver has active assignments.
        """
        # TODO: Implement when AssignmentRepository is available
        if self._assignment_repository is None:
            return False

        # This will be implemented in Phase 4
        # return self._assignment_repository.has_active_assignment_for_driver(driver_id)
        return False
