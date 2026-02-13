"""
Vehicle service for business logic.

Implements business rules and orchestrates vehicle operations.
"""

from typing import Dict, List, Optional, Tuple

from app.core.exceptions import (
    ConcurrencyException,
    ConflictException,
    NotFoundException,
)
from app.domain.models.vehicle import FuelType, Vehicle, VehicleStatus, VehicleType
from app.infrastructure.repositories.vehicle_repository import VehicleRepository


class VehicleService:
    """
    Service class for vehicle business logic.

    Handles all vehicle-related business rules and operations.
    """

    def __init__(
        self,
        vehicle_repository: VehicleRepository,
        assignment_repository: Optional[object] = None,
    ) -> None:
        """
        Initialize the service with required repositories.

        Args:
            vehicle_repository: Repository for vehicle data access.
            assignment_repository: Repository for assignment data access (optional).
        """
        self._vehicle_repository = vehicle_repository
        self._assignment_repository = assignment_repository

    def get_all_vehicles(
        self,
        status: Optional[VehicleStatus] = None,
        vehicle_type: Optional[VehicleType] = None,
        fuel_type: Optional[FuelType] = None,
        include_deleted: bool = False,
        limit: int = 50,
        skip: int = 0,
        sort_by: str = "updated_at",
        sort_order: str = "desc",
    ) -> Tuple[List[Vehicle], int]:
        """
        Get all vehicles with optional filtering and pagination.

        Args:
            status: Filter by vehicle status.
            vehicle_type: Filter by vehicle type.
            fuel_type: Filter by fuel type.
            include_deleted: Whether to include soft-deleted vehicles.
            limit: Maximum number of results.
            skip: Number of results to skip.
            sort_by: Field to sort by.
            sort_order: Sort direction.

        Returns:
            Tuple of (list of vehicles, total count).
        """
        return self._vehicle_repository.find_all(
            status=status,
            vehicle_type=vehicle_type,
            fuel_type=fuel_type,
            include_deleted=include_deleted,
            limit=limit,
            skip=skip,
            sort_by=sort_by,
            sort_order=sort_order,
        )

    def get_vehicle_by_id(self, vehicle_id: str) -> Vehicle:
        """
        Get a vehicle by its ID.

        Args:
            vehicle_id: Vehicle UUID string.

        Returns:
            Vehicle domain object.

        Raises:
            NotFoundException: If vehicle is not found.
        """
        vehicle = self._vehicle_repository.find_by_id(vehicle_id)
        if vehicle is None:
            raise NotFoundException(
                code="VEHICLE_NOT_FOUND",
                message=f"Vehicle with ID '{vehicle_id}' not found.",
            )
        return vehicle

    def create_vehicle(
        self,
        plate_number: str,
        model: str,
        year: int,
        vehicle_type: VehicleType,
        fuel_type: FuelType,
        status: VehicleStatus = VehicleStatus.ACTIVE,
    ) -> Vehicle:
        """
        Create a new vehicle.

        If a soft-deleted vehicle with the same plate number exists,
        it will be restored and updated instead of creating a new one.

        Args:
            plate_number: Vehicle plate number.
            model: Vehicle model name.
            year: Manufacturing year.
            vehicle_type: Type of vehicle.
            fuel_type: Fuel type.
            status: Initial status (default: ACTIVE).

        Returns:
            Created or restored vehicle.

        Raises:
            ConflictException: If plate number is already in use.
        """
        normalized_plate = plate_number.strip().upper()

        # Check for existing vehicle with same plate (including soft-deleted)
        existing = self._vehicle_repository.find_by_plate_number(
            normalized_plate, include_deleted=True
        )

        if existing is not None:
            if existing.is_deleted:
                # Restore and update the soft-deleted vehicle
                existing.restore()
                existing.update(
                    plate_number=normalized_plate,
                    model=model,
                    year=year,
                    vehicle_type=vehicle_type,
                    fuel_type=fuel_type,
                    status=status,
                )
                return self._vehicle_repository.update(existing)
            else:
                # Active vehicle with same plate exists
                raise ConflictException(
                    code="DUPLICATE_PLATE",
                    message=(
                        f"A vehicle with plate number '{normalized_plate}' "
                        "already exists."
                    ),
                )

        # Create new vehicle
        vehicle = Vehicle(
            plate_number=normalized_plate,
            model=model,
            year=year,
            vehicle_type=vehicle_type,
            fuel_type=fuel_type,
            status=status,
        )
        return self._vehicle_repository.create(vehicle)

    def update_vehicle(
        self,
        vehicle_id: str,
        plate_number: str,
        model: str,
        year: int,
        vehicle_type: VehicleType,
        fuel_type: FuelType,
        status: VehicleStatus,
        etag: Optional[str] = None,
    ) -> Vehicle:
        """
        Fully update a vehicle (PUT operation).

        Args:
            vehicle_id: Vehicle UUID to update.
            plate_number: New plate number.
            model: New model name.
            year: New year.
            vehicle_type: New vehicle type.
            fuel_type: New fuel type.
            status: New status.
            etag: Optional ETag for concurrency control.

        Returns:
            Updated vehicle.

        Raises:
            NotFoundException: If vehicle is not found.
            ConflictException: If plate number conflicts or status change is invalid.
            ConcurrencyException: If ETag doesn't match.
        """
        vehicle = self.get_vehicle_by_id(vehicle_id)

        # Check ETag for concurrency
        if etag is not None:
            current_etag = self._vehicle_repository.generate_etag(vehicle)
            if etag != current_etag:
                raise ConcurrencyException()

        # Validate plate number uniqueness
        normalized_plate = plate_number.strip().upper()
        if normalized_plate != vehicle.plate_number:
            if self._vehicle_repository.exists_by_plate_number(
                normalized_plate, exclude_id=vehicle_id
            ):
                raise ConflictException(
                    code="DUPLICATE_PLATE",
                    message=(
                        f"A vehicle with plate number '{normalized_plate}' "
                        "already exists."
                    ),
                )

        # Validate status transition
        self._validate_status_transition(vehicle, status)

        # Update vehicle
        vehicle.update(
            plate_number=normalized_plate,
            model=model,
            year=year,
            vehicle_type=vehicle_type,
            fuel_type=fuel_type,
            status=status,
        )

        return self._vehicle_repository.update(vehicle)

    def patch_vehicle(
        self,
        vehicle_id: str,
        plate_number: Optional[str] = None,
        model: Optional[str] = None,
        year: Optional[int] = None,
        vehicle_type: Optional[VehicleType] = None,
        fuel_type: Optional[FuelType] = None,
        status: Optional[VehicleStatus] = None,
        etag: Optional[str] = None,
    ) -> Vehicle:
        """
        Partially update a vehicle (PATCH operation).

        Args:
            vehicle_id: Vehicle UUID to update.
            plate_number: New plate number (optional).
            model: New model name (optional).
            year: New year (optional).
            vehicle_type: New vehicle type (optional).
            fuel_type: New fuel type (optional).
            status: New status (optional).
            etag: Optional ETag for concurrency control.

        Returns:
            Updated vehicle.

        Raises:
            NotFoundException: If vehicle is not found.
            ConflictException: If plate number conflicts or status change is invalid.
            ConcurrencyException: If ETag doesn't match.
        """
        vehicle = self.get_vehicle_by_id(vehicle_id)

        # Check ETag for concurrency
        if etag is not None:
            current_etag = self._vehicle_repository.generate_etag(vehicle)
            if etag != current_etag:
                raise ConcurrencyException()

        # Validate plate number uniqueness if changing
        if plate_number is not None:
            normalized_plate = plate_number.strip().upper()
            if normalized_plate != vehicle.plate_number:
                if self._vehicle_repository.exists_by_plate_number(
                    normalized_plate, exclude_id=vehicle_id
                ):
                    raise ConflictException(
                        code="DUPLICATE_PLATE",
                        message=(
                            f"A vehicle with plate number '{normalized_plate}' "
                            "already exists."
                        ),
                    )

        # Validate status transition if changing
        if status is not None:
            self._validate_status_transition(vehicle, status)

        # Update only provided fields
        vehicle.update(
            plate_number=plate_number,
            model=model,
            year=year,
            vehicle_type=vehicle_type,
            fuel_type=fuel_type,
            status=status,
        )

        return self._vehicle_repository.update(vehicle)

    def delete_vehicle(self, vehicle_id: str) -> None:
        """
        Soft delete a vehicle.

        Args:
            vehicle_id: Vehicle UUID to delete.

        Raises:
            NotFoundException: If vehicle is not found.
            ConflictException: If vehicle has active assignments.
        """
        vehicle = self.get_vehicle_by_id(vehicle_id)

        if vehicle.is_deleted:
            raise NotFoundException(
                code="VEHICLE_NOT_FOUND",
                message=f"Vehicle with ID '{vehicle_id}' not found.",
            )

        # Check for active assignments
        if self._has_active_assignments(vehicle_id):
            raise ConflictException(
                code="VEHICLE_HAS_ACTIVE_ASSIGNMENTS",
                message="Cannot delete vehicle with active assignments. Close assignments first.",
            )

        self._vehicle_repository.soft_delete(vehicle_id)

    def get_vehicle_etag(self, vehicle: Vehicle) -> str:
        """
        Get the ETag for a vehicle.

        Args:
            vehicle: Vehicle domain object.

        Returns:
            ETag string.
        """
        return self._vehicle_repository.generate_etag(vehicle)

    def get_vehicle_counts_by_status(self) -> Dict[str, int]:
        """
        Get vehicle counts grouped by status.

        Returns:
            Dictionary mapping status to count.
        """
        return self._vehicle_repository.count_by_status()

    def _validate_status_transition(
        self, vehicle: Vehicle, new_status: VehicleStatus
    ) -> None:
        """
        Validate that a status transition is allowed.

        INACTIVE or MAINTENANCE vehicles cannot be assigned.
        Changing to INACTIVE or MAINTENANCE requires no active assignments.

        Args:
            vehicle: Current vehicle state.
            new_status: Desired new status.

        Raises:
            ConflictException: If the transition is not allowed.
        """
        # If status isn't changing, no validation needed
        if vehicle.status == new_status:
            return

        # Moving to INACTIVE or MAINTENANCE requires no active assignments
        if new_status in (VehicleStatus.INACTIVE, VehicleStatus.MAINTENANCE):
            if self._has_active_assignments(vehicle.id):
                raise ConflictException(
                    code="VEHICLE_HAS_ACTIVE_ASSIGNMENTS",
                    message=(
                        f"Cannot change status to {new_status.value} while vehicle "
                        "has active assignments. Close assignments first."
                    ),
                )

    def _has_active_assignments(self, vehicle_id: str) -> bool:
        """
        Check if a vehicle has active assignments.

        Args:
            vehicle_id: Vehicle UUID to check.

        Returns:
            True if the vehicle has active assignments.
        """
        # TODO: Implement when AssignmentRepository is available
        if self._assignment_repository is None:
            return False

        # This will be implemented in Phase 4
        # return self._assignment_repository.has_active_assignment_for_vehicle(vehicle_id)
        return False
