"""
Assignment service for business logic.

Implements business rules and orchestrates operations for assignments.
"""

from datetime import datetime, timezone
from typing import List, Optional, Tuple
from uuid import uuid4

from app.api.v1.schemas.assignment import AssignmentCreate, AssignmentUpdate
from app.domain.models.assignment import Assignment
from app.domain.models.driver import DriverStatus
from app.domain.models.vehicle import VehicleStatus
from app.infrastructure.repositories.assignment_repository import AssignmentRepository
from app.infrastructure.repositories.driver_repository import DriverRepository
from app.infrastructure.repositories.vehicle_repository import VehicleRepository


class AssignmentServiceError(Exception):
    """Base exception for assignment service errors."""

    pass


class AssignmentNotFoundError(AssignmentServiceError):
    """Raised when an assignment is not found."""

    pass


class DriverNotFoundError(AssignmentServiceError):
    """Raised when a driver is not found."""

    pass


class VehicleNotFoundError(AssignmentServiceError):
    """Raised when a vehicle is not found."""

    pass


class DriverNotActiveError(AssignmentServiceError):
    """Raised when driver is not active."""

    pass


class VehicleNotAvailableError(AssignmentServiceError):
    """Raised when vehicle is not available."""

    pass


class DriverAlreadyAssignedError(AssignmentServiceError):
    """Raised when driver already has an active assignment."""

    pass


class VehicleAlreadyAssignedError(AssignmentServiceError):
    """Raised when vehicle already has an active assignment."""

    pass


class OverlappingAssignmentError(AssignmentServiceError):
    """Raised when assignment would overlap with existing one."""

    pass


class AssignmentUpdateError(AssignmentServiceError):
    """Raised when assignment cannot be updated."""

    pass


class ETagMismatchError(AssignmentServiceError):
    """Raised when ETag doesn't match (optimistic concurrency)."""

    pass


class AssignmentService:
    """
    Service for assignment business logic.

    Handles validation, business rules, and orchestration for assignments.
    """

    def __init__(
        self,
        assignment_repository: AssignmentRepository,
        driver_repository: DriverRepository,
        vehicle_repository: VehicleRepository,
    ) -> None:
        """
        Initialize the service with repositories.

        Args:
            assignment_repository: Repository for assignment data access.
            driver_repository: Repository for driver data access.
            vehicle_repository: Repository for vehicle data access.
        """
        self._assignment_repo = assignment_repository
        self._driver_repo = driver_repository
        self._vehicle_repo = vehicle_repository

    def get_assignment(self, assignment_id: str) -> Tuple[Assignment, str]:
        """
        Get an assignment by ID.

        Args:
            assignment_id: Assignment UUID.

        Returns:
            Tuple of (assignment, etag).

        Raises:
            AssignmentNotFoundError: If assignment not found.
        """
        assignment = self._assignment_repo.find_by_id(assignment_id)
        if assignment is None:
            raise AssignmentNotFoundError(
                f"Assignment with ID {assignment_id} not found"
            )
        etag = self._assignment_repo.generate_etag(assignment)
        return assignment, etag

    def list_assignments(
        self,
        driver_id: Optional[str] = None,
        vehicle_id: Optional[str] = None,
        active_only: bool = False,
        limit: int = 50,
        skip: int = 0,
        sort_by: str = "start_datetime",
        sort_order: str = "desc",
    ) -> Tuple[List[Assignment], int]:
        """
        List assignments with optional filtering.

        Args:
            driver_id: Filter by driver.
            vehicle_id: Filter by vehicle.
            active_only: Only return active assignments.
            limit: Maximum results to return.
            skip: Results to skip for pagination.
            sort_by: Field to sort by.
            sort_order: 'asc' or 'desc'.

        Returns:
            Tuple of (list of assignments, total count).
        """
        return self._assignment_repo.find_all(
            driver_id=driver_id,
            vehicle_id=vehicle_id,
            active_only=active_only,
            limit=limit,
            skip=skip,
            sort_by=sort_by,
            sort_order=sort_order,
        )

    def create_assignment(self, data: AssignmentCreate) -> Tuple[Assignment, str]:
        """
        Create a new assignment.

        Validates:
        - Driver exists and is active
        - Vehicle exists and is available
        - Driver doesn't have active assignment
        - Vehicle doesn't have active assignment
        - No overlapping assignments

        Args:
            data: Assignment creation data.

        Returns:
            Tuple of (created assignment, etag).

        Raises:
            DriverNotFoundError: Driver doesn't exist.
            VehicleNotFoundError: Vehicle doesn't exist.
            DriverNotActiveError: Driver is not active.
            VehicleNotAvailableError: Vehicle is not available.
            DriverAlreadyAssignedError: Driver has active assignment.
            VehicleAlreadyAssignedError: Vehicle has active assignment.
            OverlappingAssignmentError: Assignment would overlap.
        """
        # Validate driver exists and is active
        driver = self._driver_repo.find_by_id(data.driver_id)
        if driver is None:
            raise DriverNotFoundError(f"Driver with ID {data.driver_id} not found")
        if not driver.can_receive_assignments():
            raise DriverNotActiveError(
                f"Driver {data.driver_id} is not active (status: {driver.status.value})"
            )

        # Validate vehicle exists and is available
        vehicle = self._vehicle_repo.find_by_id(data.vehicle_id)
        if vehicle is None:
            raise VehicleNotFoundError(f"Vehicle with ID {data.vehicle_id} not found")
        if vehicle.status != VehicleStatus.ACTIVE:
            raise VehicleNotAvailableError(
                f"Vehicle {data.vehicle_id} is not available (status: {vehicle.status.value})"
            )

        # Check for overlapping assignments
        start_dt = data.start_datetime
        end_dt = data.end_datetime

        if self._assignment_repo.has_overlapping_assignment(
            driver_id=data.driver_id,
            vehicle_id=None,
            start_datetime=start_dt,
            end_datetime=end_dt,
        ):
            raise DriverAlreadyAssignedError(
                f"Driver {data.driver_id} already has an overlapping assignment"
            )

        if self._assignment_repo.has_overlapping_assignment(
            driver_id=None,
            vehicle_id=data.vehicle_id,
            start_datetime=start_dt,
            end_datetime=end_dt,
        ):
            raise VehicleAlreadyAssignedError(
                f"Vehicle {data.vehicle_id} already has an overlapping assignment"
            )

        # Create the assignment
        now = datetime.now(timezone.utc)
        assignment = Assignment(
            id=str(uuid4()),
            driver_id=data.driver_id,
            vehicle_id=data.vehicle_id,
            start_datetime=start_dt,
            end_datetime=end_dt,
            notes=data.notes,
            created_at=now,
            updated_at=now,
        )

        created = self._assignment_repo.create(assignment)
        etag = self._assignment_repo.generate_etag(created)
        return created, etag

    def update_assignment(
        self,
        assignment_id: str,
        data: AssignmentUpdate,
        if_match: Optional[str] = None,
    ) -> Tuple[Assignment, str]:
        """
        Update an assignment (PATCH semantics).

        Can only update: notes, end_datetime, start_datetime (if not started yet).

        Args:
            assignment_id: Assignment to update.
            data: Update data.
            if_match: ETag for optimistic concurrency.

        Returns:
            Tuple of (updated assignment, new etag).

        Raises:
            AssignmentNotFoundError: Assignment not found.
            ETagMismatchError: ETag doesn't match.
            AssignmentUpdateError: Invalid update.
        """
        assignment = self._assignment_repo.find_by_id(assignment_id)
        if assignment is None:
            raise AssignmentNotFoundError(
                f"Assignment with ID {assignment_id} not found"
            )

        # Check ETag if provided
        if if_match is not None:
            current_etag = self._assignment_repo.generate_etag(assignment)
            if if_match != current_etag:
                raise ETagMismatchError(
                    f"ETag mismatch: expected {current_etag}, got {if_match}"
                )

        now = datetime.now(timezone.utc)

        # Update start_datetime only if assignment hasn't started
        if data.start_datetime is not None:
            if assignment.start_datetime <= now:
                raise AssignmentUpdateError(
                    "Cannot change start_datetime after assignment has started"
                )
            # Check for overlaps with new start time
            if self._assignment_repo.has_overlapping_assignment(
                driver_id=assignment.driver_id,
                vehicle_id=assignment.vehicle_id,
                start_datetime=data.start_datetime,
                end_datetime=data.end_datetime or assignment.end_datetime,
                exclude_id=assignment_id,
            ):
                raise OverlappingAssignmentError(
                    "Updated assignment would overlap with existing assignment"
                )
            assignment.start_datetime = data.start_datetime

        # Update end_datetime
        if data.end_datetime is not None:
            if data.end_datetime < assignment.start_datetime:
                raise AssignmentUpdateError(
                    "end_datetime cannot be before start_datetime"
                )
            # Check for overlaps with new end time
            if self._assignment_repo.has_overlapping_assignment(
                driver_id=assignment.driver_id,
                vehicle_id=assignment.vehicle_id,
                start_datetime=data.start_datetime or assignment.start_datetime,
                end_datetime=data.end_datetime,
                exclude_id=assignment_id,
            ):
                raise OverlappingAssignmentError(
                    "Updated assignment would overlap with existing assignment"
                )
            assignment.end_datetime = data.end_datetime

        # Update notes (can always be updated)
        if data.notes is not None:
            assignment.update(notes=data.notes)
        else:
            assignment.updated_at = now

        updated = self._assignment_repo.update(assignment)
        etag = self._assignment_repo.generate_etag(updated)
        return updated, etag

    def close_assignment(
        self,
        assignment_id: str,
        if_match: Optional[str] = None,
    ) -> Tuple[Assignment, str]:
        """
        Close an assignment (set end_datetime to now).

        Args:
            assignment_id: Assignment to close.
            if_match: ETag for optimistic concurrency.

        Returns:
            Tuple of (closed assignment, new etag).

        Raises:
            AssignmentNotFoundError: Assignment not found.
            ETagMismatchError: ETag doesn't match.
        """
        assignment = self._assignment_repo.find_by_id(assignment_id)
        if assignment is None:
            raise AssignmentNotFoundError(
                f"Assignment with ID {assignment_id} not found"
            )

        # Check ETag if provided
        if if_match is not None:
            current_etag = self._assignment_repo.generate_etag(assignment)
            if if_match != current_etag:
                raise ETagMismatchError(
                    f"ETag mismatch: expected {current_etag}, got {if_match}"
                )

        assignment.close()
        updated = self._assignment_repo.update(assignment)
        etag = self._assignment_repo.generate_etag(updated)
        return updated, etag

    def delete_assignment(
        self,
        assignment_id: str,
        if_match: Optional[str] = None,
    ) -> bool:
        """
        Delete an assignment (hard delete, or close if active).

        For active assignments, this closes them instead of deleting.

        Args:
            assignment_id: Assignment to delete.
            if_match: ETag for optimistic concurrency.

        Returns:
            True if deleted/closed.

        Raises:
            AssignmentNotFoundError: Assignment not found.
            ETagMismatchError: ETag doesn't match.
        """
        assignment, current_etag = self.get_assignment(assignment_id)

        # Check ETag if provided
        if if_match is not None and if_match != current_etag:
            raise ETagMismatchError(
                f"ETag mismatch: expected {current_etag}, got {if_match}"
            )

        # If active, close it instead of deleting
        if assignment.is_active():
            self.close_assignment(assignment_id)
            return True

        # Delete inactive assignments
        return self._assignment_repo.delete(assignment_id)

    def close_assignments_for_driver(self, driver_id: str) -> int:
        """
        Close all active assignments for a driver.

        Called when driver status changes to non-active.

        Args:
            driver_id: Driver UUID.

        Returns:
            Number of assignments closed.
        """
        return self._assignment_repo.close_active_assignments_for_driver(driver_id)

    def close_assignments_for_vehicle(self, vehicle_id: str) -> int:
        """
        Close all active assignments for a vehicle.

        Called when vehicle status changes to non-available.

        Args:
            vehicle_id: Vehicle UUID.

        Returns:
            Number of assignments closed.
        """
        return self._assignment_repo.close_active_assignments_for_vehicle(vehicle_id)

    def get_active_assignment_for_driver(self, driver_id: str) -> Optional[Assignment]:
        """
        Get the active assignment for a driver.

        Args:
            driver_id: Driver UUID.

        Returns:
            Active assignment or None.
        """
        return self._assignment_repo.find_active_assignment_for_driver(driver_id)

    def get_active_assignment_for_vehicle(
        self, vehicle_id: str
    ) -> Optional[Assignment]:
        """
        Get the active assignment for a vehicle.

        Args:
            vehicle_id: Vehicle UUID.

        Returns:
            Active assignment or None.
        """
        return self._assignment_repo.find_active_assignment_for_vehicle(vehicle_id)

    def get_stats(self) -> dict:
        """
        Get assignment statistics.

        Returns:
            Dictionary with stats.
        """
        _, total = self._assignment_repo.find_all(limit=1)
        active = self._assignment_repo.count_active()
        return {
            "total": total,
            "active": active,
            "closed": total - active,
        }
