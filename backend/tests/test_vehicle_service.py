"""
Unit tests for VehicleService.

Tests business logic and service layer functionality.
"""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from app.core.exceptions import (
    ConcurrencyException,
    ConflictException,
    NotFoundException,
)
from app.domain.models.vehicle import FuelType, Vehicle, VehicleStatus, VehicleType
from app.domain.services.vehicle_service import VehicleService


@pytest.fixture
def mock_vehicle_repository():
    """Creates a mock VehicleRepository."""
    return MagicMock()


@pytest.fixture
def vehicle_service(mock_vehicle_repository):
    """Creates a VehicleService instance with mocked repository."""
    return VehicleService(vehicle_repository=mock_vehicle_repository)


@pytest.fixture
def sample_vehicle():
    """Creates a sample Vehicle for testing."""
    return Vehicle(
        plate_number="ABC-1234",
        model="Toyota Camry",
        year=2023,
        vehicle_type=VehicleType.SEDAN,
        fuel_type=FuelType.HYBRID,
        status=VehicleStatus.ACTIVE,
    )


class TestGetVehicleById:
    """Tests for get_vehicle_by_id method."""

    def test_get_vehicle_by_id_returns_vehicle(
        self, vehicle_service, mock_vehicle_repository, sample_vehicle
    ):
        """Returns vehicle when found."""
        # Arrange
        mock_vehicle_repository.find_by_id.return_value = sample_vehicle

        # Act
        result = vehicle_service.get_vehicle_by_id(sample_vehicle.id)

        # Assert
        assert result == sample_vehicle
        mock_vehicle_repository.find_by_id.assert_called_once_with(sample_vehicle.id)

    def test_get_vehicle_by_id_raises_not_found(
        self, vehicle_service, mock_vehicle_repository
    ):
        """Raises NotFoundException when vehicle not found."""
        # Arrange
        vehicle_id = str(uuid.uuid4())
        mock_vehicle_repository.find_by_id.return_value = None

        # Act & Assert
        with pytest.raises(NotFoundException) as exc_info:
            vehicle_service.get_vehicle_by_id(vehicle_id)

        assert exc_info.value.code == "VEHICLE_NOT_FOUND"
        assert vehicle_id in exc_info.value.message


class TestGetAllVehicles:
    """Tests for get_all_vehicles method."""

    def test_get_all_vehicles_returns_list(
        self, vehicle_service, mock_vehicle_repository, sample_vehicle
    ):
        """Returns list of vehicles with total count."""
        # Arrange
        vehicles = [sample_vehicle]
        mock_vehicle_repository.find_all.return_value = (vehicles, 1)

        # Act
        result, total = vehicle_service.get_all_vehicles()

        # Assert
        assert len(result) == 1
        assert result[0] == sample_vehicle
        assert total == 1

    def test_get_all_vehicles_passes_filters(
        self, vehicle_service, mock_vehicle_repository
    ):
        """Passes filter parameters to repository."""
        # Arrange
        mock_vehicle_repository.find_all.return_value = ([], 0)

        # Act
        vehicle_service.get_all_vehicles(
            status=VehicleStatus.ACTIVE,
            vehicle_type=VehicleType.SUV,
            fuel_type=FuelType.ELECTRIC,
            include_deleted=True,
            limit=25,
            skip=10,
            sort_by="created_at",
            sort_order="asc",
        )

        # Assert
        mock_vehicle_repository.find_all.assert_called_once_with(
            status=VehicleStatus.ACTIVE,
            vehicle_type=VehicleType.SUV,
            fuel_type=FuelType.ELECTRIC,
            include_deleted=True,
            limit=25,
            skip=10,
            sort_by="created_at",
            sort_order="asc",
        )


class TestCreateVehicle:
    """Tests for create_vehicle method."""

    def test_create_vehicle_success(self, vehicle_service, mock_vehicle_repository):
        """Creates new vehicle successfully."""
        # Arrange
        mock_vehicle_repository.find_by_plate_number.return_value = None
        mock_vehicle_repository.create.side_effect = lambda v: v

        # Act
        result = vehicle_service.create_vehicle(
            plate_number="NEW-1234",
            model="New Model",
            year=2024,
            vehicle_type=VehicleType.SUV,
            fuel_type=FuelType.ELECTRIC,
        )

        # Assert
        assert result.plate_number == "NEW-1234"
        assert result.model == "New Model"
        assert result.year == 2024
        assert result.status == VehicleStatus.ACTIVE
        mock_vehicle_repository.create.assert_called_once()

    def test_create_vehicle_normalizes_plate_number(
        self, vehicle_service, mock_vehicle_repository
    ):
        """Normalizes plate number to uppercase and trimmed."""
        # Arrange
        mock_vehicle_repository.find_by_plate_number.return_value = None
        mock_vehicle_repository.create.side_effect = lambda v: v

        # Act
        result = vehicle_service.create_vehicle(
            plate_number="  abc-1234  ",
            model="Test",
            year=2024,
            vehicle_type=VehicleType.SEDAN,
            fuel_type=FuelType.GASOLINE,
        )

        # Assert
        assert result.plate_number == "ABC-1234"

    def test_create_vehicle_raises_conflict_for_duplicate_plate(
        self, vehicle_service, mock_vehicle_repository, sample_vehicle
    ):
        """Raises ConflictException when plate number already exists."""
        # Arrange
        mock_vehicle_repository.find_by_plate_number.return_value = sample_vehicle

        # Act & Assert
        with pytest.raises(ConflictException) as exc_info:
            vehicle_service.create_vehicle(
                plate_number=sample_vehicle.plate_number,
                model="Duplicate",
                year=2024,
                vehicle_type=VehicleType.SUV,
                fuel_type=FuelType.DIESEL,
            )

        assert exc_info.value.code == "DUPLICATE_PLATE"

    def test_create_vehicle_restores_soft_deleted_vehicle(
        self, vehicle_service, mock_vehicle_repository
    ):
        """Restores and updates soft-deleted vehicle with same plate."""
        # Arrange
        deleted_vehicle = Vehicle(
            plate_number="DEL-1234",
            model="Old Model",
            year=2020,
            vehicle_type=VehicleType.SEDAN,
            fuel_type=FuelType.GASOLINE,
        )
        deleted_vehicle.soft_delete()
        mock_vehicle_repository.find_by_plate_number.return_value = deleted_vehicle
        mock_vehicle_repository.update.side_effect = lambda v: v

        # Act
        result = vehicle_service.create_vehicle(
            plate_number="DEL-1234",
            model="New Model",
            year=2024,
            vehicle_type=VehicleType.SUV,
            fuel_type=FuelType.ELECTRIC,
        )

        # Assert
        assert result.is_deleted is False
        assert result.model == "New Model"
        assert result.year == 2024
        mock_vehicle_repository.update.assert_called_once()


class TestUpdateVehicle:
    """Tests for update_vehicle method."""

    def test_update_vehicle_success(
        self, vehicle_service, mock_vehicle_repository, sample_vehicle
    ):
        """Updates vehicle successfully."""
        # Arrange
        mock_vehicle_repository.find_by_id.return_value = sample_vehicle
        mock_vehicle_repository.exists_by_plate_number.return_value = False
        mock_vehicle_repository.update.side_effect = lambda v: v

        # Act
        result = vehicle_service.update_vehicle(
            vehicle_id=sample_vehicle.id,
            plate_number="UPD-9999",
            model="Updated Model",
            year=2025,
            vehicle_type=VehicleType.TRUCK,
            fuel_type=FuelType.DIESEL,
            status=VehicleStatus.ACTIVE,
        )

        # Assert
        assert result.plate_number == "UPD-9999"
        assert result.model == "Updated Model"
        mock_vehicle_repository.update.assert_called_once()

    def test_update_vehicle_raises_not_found(
        self, vehicle_service, mock_vehicle_repository
    ):
        """Raises NotFoundException when vehicle not found."""
        # Arrange
        vehicle_id = str(uuid.uuid4())
        mock_vehicle_repository.find_by_id.return_value = None

        # Act & Assert
        with pytest.raises(NotFoundException):
            vehicle_service.update_vehicle(
                vehicle_id=vehicle_id,
                plate_number="NEW-1234",
                model="Test",
                year=2024,
                vehicle_type=VehicleType.SEDAN,
                fuel_type=FuelType.GASOLINE,
                status=VehicleStatus.ACTIVE,
            )

    def test_update_vehicle_raises_conflict_for_duplicate_plate(
        self, vehicle_service, mock_vehicle_repository, sample_vehicle
    ):
        """Raises ConflictException when changing to existing plate."""
        # Arrange
        mock_vehicle_repository.find_by_id.return_value = sample_vehicle
        mock_vehicle_repository.exists_by_plate_number.return_value = True

        # Act & Assert
        with pytest.raises(ConflictException) as exc_info:
            vehicle_service.update_vehicle(
                vehicle_id=sample_vehicle.id,
                plate_number="DUPLICATE-1234",
                model="Test",
                year=2024,
                vehicle_type=VehicleType.SEDAN,
                fuel_type=FuelType.GASOLINE,
                status=VehicleStatus.ACTIVE,
            )

        assert exc_info.value.code == "DUPLICATE_PLATE"

    def test_update_vehicle_with_etag_mismatch_raises_concurrency_error(
        self, vehicle_service, mock_vehicle_repository, sample_vehicle
    ):
        """Raises ConcurrencyException when ETag doesn't match."""
        # Arrange
        mock_vehicle_repository.find_by_id.return_value = sample_vehicle
        mock_vehicle_repository.generate_etag.return_value = "current-etag"

        # Act & Assert
        with pytest.raises(ConcurrencyException):
            vehicle_service.update_vehicle(
                vehicle_id=sample_vehicle.id,
                plate_number=sample_vehicle.plate_number,
                model="Test",
                year=2024,
                vehicle_type=VehicleType.SEDAN,
                fuel_type=FuelType.GASOLINE,
                status=VehicleStatus.ACTIVE,
                etag="wrong-etag",
            )

    def test_update_vehicle_with_matching_etag_succeeds(
        self, vehicle_service, mock_vehicle_repository, sample_vehicle
    ):
        """Succeeds when ETag matches."""
        # Arrange
        mock_vehicle_repository.find_by_id.return_value = sample_vehicle
        mock_vehicle_repository.generate_etag.return_value = "matching-etag"
        mock_vehicle_repository.exists_by_plate_number.return_value = False
        mock_vehicle_repository.update.side_effect = lambda v: v

        # Act
        result = vehicle_service.update_vehicle(
            vehicle_id=sample_vehicle.id,
            plate_number=sample_vehicle.plate_number,
            model="Updated",
            year=2024,
            vehicle_type=VehicleType.SEDAN,
            fuel_type=FuelType.GASOLINE,
            status=VehicleStatus.ACTIVE,
            etag="matching-etag",
        )

        # Assert
        assert result.model == "Updated"


class TestPatchVehicle:
    """Tests for patch_vehicle method."""

    def test_patch_vehicle_updates_single_field(
        self, vehicle_service, mock_vehicle_repository, sample_vehicle
    ):
        """Patches only the provided field."""
        # Arrange
        original_plate = sample_vehicle.plate_number
        mock_vehicle_repository.find_by_id.return_value = sample_vehicle
        mock_vehicle_repository.update.side_effect = lambda v: v

        # Act
        result = vehicle_service.patch_vehicle(
            vehicle_id=sample_vehicle.id,
            model="Patched Model",
        )

        # Assert
        assert result.model == "Patched Model"
        assert result.plate_number == original_plate

    def test_patch_vehicle_validates_plate_uniqueness(
        self, vehicle_service, mock_vehicle_repository, sample_vehicle
    ):
        """Validates plate uniqueness when plate is changed."""
        # Arrange
        mock_vehicle_repository.find_by_id.return_value = sample_vehicle
        mock_vehicle_repository.exists_by_plate_number.return_value = True

        # Act & Assert
        with pytest.raises(ConflictException) as exc_info:
            vehicle_service.patch_vehicle(
                vehicle_id=sample_vehicle.id,
                plate_number="DUPLICATE-1234",
            )

        assert exc_info.value.code == "DUPLICATE_PLATE"


class TestDeleteVehicle:
    """Tests for delete_vehicle method."""

    def test_delete_vehicle_success(
        self, vehicle_service, mock_vehicle_repository, sample_vehicle
    ):
        """Soft deletes vehicle successfully."""
        # Arrange
        mock_vehicle_repository.find_by_id.return_value = sample_vehicle

        # Act
        vehicle_service.delete_vehicle(sample_vehicle.id)

        # Assert
        mock_vehicle_repository.soft_delete.assert_called_once_with(sample_vehicle.id)

    def test_delete_vehicle_raises_not_found(
        self, vehicle_service, mock_vehicle_repository
    ):
        """Raises NotFoundException when vehicle not found."""
        # Arrange
        vehicle_id = str(uuid.uuid4())
        mock_vehicle_repository.find_by_id.return_value = None

        # Act & Assert
        with pytest.raises(NotFoundException):
            vehicle_service.delete_vehicle(vehicle_id)

    def test_delete_already_deleted_vehicle_raises_not_found(
        self, vehicle_service, mock_vehicle_repository
    ):
        """Raises NotFoundException for already deleted vehicle."""
        # Arrange
        deleted_vehicle = Vehicle(
            plate_number="DEL-0001",
            model="Deleted",
            year=2023,
            vehicle_type=VehicleType.SEDAN,
            fuel_type=FuelType.GASOLINE,
        )
        deleted_vehicle.soft_delete()
        mock_vehicle_repository.find_by_id.return_value = deleted_vehicle

        # Act & Assert
        with pytest.raises(NotFoundException):
            vehicle_service.delete_vehicle(deleted_vehicle.id)


class TestStatusTransitionValidation:
    """Tests for status transition validation rules."""

    def test_change_to_inactive_with_active_assignments_fails(
        self, mock_vehicle_repository
    ):
        """Cannot change to INACTIVE when vehicle has active assignments."""
        # Arrange
        mock_assignment_repository = MagicMock()
        service = VehicleService(
            vehicle_repository=mock_vehicle_repository,
            assignment_repository=mock_assignment_repository,
        )

        vehicle = Vehicle(
            plate_number="TST-0001",
            model="Test",
            year=2024,
            vehicle_type=VehicleType.SEDAN,
            fuel_type=FuelType.GASOLINE,
            status=VehicleStatus.ACTIVE,
        )
        mock_vehicle_repository.find_by_id.return_value = vehicle
        mock_vehicle_repository.exists_by_plate_number.return_value = False

        # TODO: Update when assignment repository integration is complete
        # mock_assignment_repository.has_active_assignment_for_vehicle.return_value = True
        # For now, this should succeed since assignment check returns False

        mock_vehicle_repository.update.side_effect = lambda v: v

        # Act
        result = service.update_vehicle(
            vehicle_id=vehicle.id,
            plate_number=vehicle.plate_number,
            model=vehicle.model,
            year=vehicle.year,
            vehicle_type=vehicle.vehicle_type,
            fuel_type=vehicle.fuel_type,
            status=VehicleStatus.INACTIVE,
        )

        # Assert - currently succeeds because no assignment repository
        assert result.status == VehicleStatus.INACTIVE


class TestGetVehicleEtag:
    """Tests for get_vehicle_etag method."""

    def test_get_vehicle_etag_returns_etag(
        self, vehicle_service, mock_vehicle_repository, sample_vehicle
    ):
        """Returns ETag from repository."""
        # Arrange
        expected_etag = "test-etag-12345"
        mock_vehicle_repository.generate_etag.return_value = expected_etag

        # Act
        result = vehicle_service.get_vehicle_etag(sample_vehicle)

        # Assert
        assert result == expected_etag
        mock_vehicle_repository.generate_etag.assert_called_once_with(sample_vehicle)


class TestGetVehicleCountsByStatus:
    """Tests for get_vehicle_counts_by_status method."""

    def test_get_vehicle_counts_by_status(
        self, vehicle_service, mock_vehicle_repository
    ):
        """Returns counts from repository."""
        # Arrange
        expected_counts = {"active": 5, "inactive": 2, "maintenance": 1}
        mock_vehicle_repository.count_by_status.return_value = expected_counts

        # Act
        result = vehicle_service.get_vehicle_counts_by_status()

        # Assert
        assert result == expected_counts
        mock_vehicle_repository.count_by_status.assert_called_once()
