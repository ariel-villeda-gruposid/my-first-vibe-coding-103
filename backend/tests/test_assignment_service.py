"""
Unit tests for Assignment service.

Tests AssignmentService business logic with mocked repositories.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest
from app.api.v1.schemas.assignment import AssignmentCreate, AssignmentUpdate
from app.domain.models.assignment import Assignment
from app.domain.models.driver import Driver, DriverStatus
from app.domain.models.vehicle import FuelType, Vehicle, VehicleStatus, VehicleType
from app.domain.services.assignment_service import (
    AssignmentNotFoundError,
    AssignmentService,
    AssignmentUpdateError,
    DriverAlreadyAssignedError,
    DriverNotActiveError,
    DriverNotFoundError,
    ETagMismatchError,
    OverlappingAssignmentError,
    VehicleAlreadyAssignedError,
    VehicleNotAvailableError,
    VehicleNotFoundError,
)


@pytest.fixture
def mock_assignment_repo():
    """Create a mock assignment repository."""
    return MagicMock()


@pytest.fixture
def mock_driver_repo():
    """Create a mock driver repository."""
    return MagicMock()


@pytest.fixture
def mock_vehicle_repo():
    """Create a mock vehicle repository."""
    return MagicMock()


@pytest.fixture
def service(mock_assignment_repo, mock_driver_repo, mock_vehicle_repo):
    """Create an AssignmentService with mocked dependencies."""
    return AssignmentService(mock_assignment_repo, mock_driver_repo, mock_vehicle_repo)


@pytest.fixture
def sample_assignment():
    """Create a sample assignment for testing."""
    now = datetime.now(timezone.utc)
    return Assignment(
        id="assign-123",
        driver_id="driver-456",
        vehicle_id="vehicle-789",
        start_datetime=now,
        end_datetime=None,
        notes="Test assignment",
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def sample_driver():
    """Create a sample driver for testing."""
    now = datetime.now(timezone.utc)
    return Driver(
        id="driver-456",
        name="John Doe",
        license_number="ABC123456",
        contact_number="+1-555-123-4567",
        status=DriverStatus.ACTIVE,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def sample_vehicle():
    """Create a sample vehicle for testing."""
    now = datetime.now(timezone.utc)
    return Vehicle(
        id="vehicle-789",
        plate_number="ABC-1234",
        model="Camry",
        year=2022,
        vehicle_type=VehicleType.SEDAN,
        fuel_type=FuelType.GASOLINE,
        status=VehicleStatus.ACTIVE,
        created_at=now,
        updated_at=now,
    )


class TestGetAssignment:
    """Test get_assignment method."""

    def test_get_assignment_success(
        self, service, mock_assignment_repo, sample_assignment
    ):
        """Should return assignment and etag when found."""
        mock_assignment_repo.find_by_id.return_value = sample_assignment
        mock_assignment_repo.generate_etag.return_value = "etag-123"

        assignment, etag = service.get_assignment("assign-123")

        assert assignment == sample_assignment
        assert etag == "etag-123"
        mock_assignment_repo.find_by_id.assert_called_once_with("assign-123")

    def test_get_assignment_not_found(self, service, mock_assignment_repo):
        """Should raise AssignmentNotFoundError when not found."""
        mock_assignment_repo.find_by_id.return_value = None

        with pytest.raises(AssignmentNotFoundError) as exc_info:
            service.get_assignment("nonexistent")

        assert "nonexistent" in str(exc_info.value)


class TestListAssignments:
    """Test list_assignments method."""

    def test_list_assignments_default(
        self, service, mock_assignment_repo, sample_assignment
    ):
        """Should return list with default parameters."""
        mock_assignment_repo.find_all.return_value = ([sample_assignment], 1)

        assignments, total = service.list_assignments()

        assert assignments == [sample_assignment]
        assert total == 1
        mock_assignment_repo.find_all.assert_called_once()

    def test_list_assignments_with_filters(
        self, service, mock_assignment_repo, sample_assignment
    ):
        """Should pass filters to repository."""
        mock_assignment_repo.find_all.return_value = ([sample_assignment], 1)

        service.list_assignments(
            driver_id="driver-123",
            vehicle_id="vehicle-456",
            active_only=True,
            limit=10,
            skip=5,
        )

        mock_assignment_repo.find_all.assert_called_once_with(
            driver_id="driver-123",
            vehicle_id="vehicle-456",
            active_only=True,
            limit=10,
            skip=5,
            sort_by="start_datetime",
            sort_order="desc",
        )


class TestCreateAssignment:
    """Test create_assignment method."""

    def test_create_assignment_success(
        self,
        service,
        mock_assignment_repo,
        mock_driver_repo,
        mock_vehicle_repo,
        sample_driver,
        sample_vehicle,
    ):
        """Should create assignment when all validations pass."""
        now = datetime.now(timezone.utc)
        mock_driver_repo.find_by_id.return_value = sample_driver
        mock_vehicle_repo.find_by_id.return_value = sample_vehicle
        mock_assignment_repo.has_overlapping_assignment.return_value = False
        mock_assignment_repo.create.side_effect = lambda a: a
        mock_assignment_repo.generate_etag.return_value = "etag-new"

        data = AssignmentCreate(
            driver_id=sample_driver.id,
            vehicle_id=sample_vehicle.id,
            start_datetime=now,
            end_datetime=now + timedelta(hours=8),
            notes="Test notes",
        )

        assignment, etag = service.create_assignment(data)

        assert assignment.driver_id == sample_driver.id
        assert assignment.vehicle_id == sample_vehicle.id
        assert assignment.notes == "Test notes"
        assert etag == "etag-new"
        mock_assignment_repo.create.assert_called_once()

    def test_create_assignment_driver_not_found(self, service, mock_driver_repo):
        """Should raise DriverNotFoundError when driver doesn't exist."""
        mock_driver_repo.find_by_id.return_value = None
        now = datetime.now(timezone.utc)

        data = AssignmentCreate(
            driver_id="nonexistent",
            vehicle_id="vehicle-789",
            start_datetime=now,
        )

        with pytest.raises(DriverNotFoundError):
            service.create_assignment(data)

    def test_create_assignment_driver_not_active(
        self, service, mock_driver_repo, sample_driver
    ):
        """Should raise DriverNotActiveError when driver is suspended."""
        sample_driver.status = DriverStatus.SUSPENDED
        mock_driver_repo.find_by_id.return_value = sample_driver
        now = datetime.now(timezone.utc)

        data = AssignmentCreate(
            driver_id=sample_driver.id,
            vehicle_id="vehicle-789",
            start_datetime=now,
        )

        with pytest.raises(DriverNotActiveError):
            service.create_assignment(data)

    def test_create_assignment_vehicle_not_found(
        self, service, mock_driver_repo, mock_vehicle_repo, sample_driver
    ):
        """Should raise VehicleNotFoundError when vehicle doesn't exist."""
        mock_driver_repo.find_by_id.return_value = sample_driver
        mock_vehicle_repo.find_by_id.return_value = None
        now = datetime.now(timezone.utc)

        data = AssignmentCreate(
            driver_id=sample_driver.id,
            vehicle_id="nonexistent",
            start_datetime=now,
        )

        with pytest.raises(VehicleNotFoundError):
            service.create_assignment(data)

    def test_create_assignment_vehicle_not_available(
        self,
        service,
        mock_driver_repo,
        mock_vehicle_repo,
        sample_driver,
        sample_vehicle,
    ):
        """Should raise VehicleNotAvailableError when vehicle is in maintenance."""
        sample_vehicle.status = VehicleStatus.MAINTENANCE
        mock_driver_repo.find_by_id.return_value = sample_driver
        mock_vehicle_repo.find_by_id.return_value = sample_vehicle
        now = datetime.now(timezone.utc)

        data = AssignmentCreate(
            driver_id=sample_driver.id,
            vehicle_id=sample_vehicle.id,
            start_datetime=now,
        )

        with pytest.raises(VehicleNotAvailableError):
            service.create_assignment(data)

    def test_create_assignment_driver_already_assigned(
        self,
        service,
        mock_driver_repo,
        mock_vehicle_repo,
        mock_assignment_repo,
        sample_driver,
        sample_vehicle,
    ):
        """Should raise DriverAlreadyAssignedError when driver has overlapping assignment."""
        mock_driver_repo.find_by_id.return_value = sample_driver
        mock_vehicle_repo.find_by_id.return_value = sample_vehicle
        # First call for driver check returns True (overlap)
        mock_assignment_repo.has_overlapping_assignment.side_effect = [True]
        now = datetime.now(timezone.utc)

        data = AssignmentCreate(
            driver_id=sample_driver.id,
            vehicle_id=sample_vehicle.id,
            start_datetime=now,
        )

        with pytest.raises(DriverAlreadyAssignedError):
            service.create_assignment(data)

    def test_create_assignment_vehicle_already_assigned(
        self,
        service,
        mock_driver_repo,
        mock_vehicle_repo,
        mock_assignment_repo,
        sample_driver,
        sample_vehicle,
    ):
        """Should raise VehicleAlreadyAssignedError when vehicle has overlapping assignment."""
        mock_driver_repo.find_by_id.return_value = sample_driver
        mock_vehicle_repo.find_by_id.return_value = sample_vehicle
        # First call for driver check returns False, second for vehicle returns True
        mock_assignment_repo.has_overlapping_assignment.side_effect = [False, True]
        now = datetime.now(timezone.utc)

        data = AssignmentCreate(
            driver_id=sample_driver.id,
            vehicle_id=sample_vehicle.id,
            start_datetime=now,
        )

        with pytest.raises(VehicleAlreadyAssignedError):
            service.create_assignment(data)


class TestUpdateAssignment:
    """Test update_assignment method."""

    def test_update_assignment_notes_success(
        self, service, mock_assignment_repo, sample_assignment
    ):
        """Should update notes successfully."""
        mock_assignment_repo.find_by_id.return_value = sample_assignment
        mock_assignment_repo.generate_etag.return_value = "etag-123"
        mock_assignment_repo.has_overlapping_assignment.return_value = False
        mock_assignment_repo.update.side_effect = lambda a: a

        data = AssignmentUpdate(notes="Updated notes")

        assignment, etag = service.update_assignment("assign-123", data)

        assert assignment.notes == "Updated notes"
        mock_assignment_repo.update.assert_called_once()

    def test_update_assignment_not_found(self, service, mock_assignment_repo):
        """Should raise AssignmentNotFoundError when not found."""
        mock_assignment_repo.find_by_id.return_value = None

        data = AssignmentUpdate(notes="Updated")

        with pytest.raises(AssignmentNotFoundError):
            service.update_assignment("nonexistent", data)

    def test_update_assignment_etag_mismatch(
        self, service, mock_assignment_repo, sample_assignment
    ):
        """Should raise ETagMismatchError when ETag doesn't match."""
        mock_assignment_repo.find_by_id.return_value = sample_assignment
        mock_assignment_repo.generate_etag.return_value = "current-etag"

        data = AssignmentUpdate(notes="Updated")

        with pytest.raises(ETagMismatchError):
            service.update_assignment("assign-123", data, if_match="wrong-etag")

    def test_update_assignment_start_datetime_after_started_fails(
        self, service, mock_assignment_repo
    ):
        """Should raise error when changing start_datetime after assignment started."""
        now = datetime.now(timezone.utc)
        started_assignment = Assignment(
            id="assign-123",
            driver_id="driver-456",
            vehicle_id="vehicle-789",
            start_datetime=now - timedelta(hours=1),  # Started 1 hour ago
            end_datetime=None,
            notes=None,
            created_at=now - timedelta(hours=2),
            updated_at=now - timedelta(hours=2),
        )
        mock_assignment_repo.find_by_id.return_value = started_assignment
        mock_assignment_repo.generate_etag.return_value = "etag"

        data = AssignmentUpdate(start_datetime=now + timedelta(hours=1))

        with pytest.raises(AssignmentUpdateError) as exc_info:
            service.update_assignment("assign-123", data)

        assert "started" in str(exc_info.value).lower()

    def test_update_assignment_end_before_start_fails(
        self, service, mock_assignment_repo, sample_assignment
    ):
        """Should raise error when end_datetime < start_datetime."""
        mock_assignment_repo.find_by_id.return_value = sample_assignment
        mock_assignment_repo.generate_etag.return_value = "etag"

        data = AssignmentUpdate(
            end_datetime=sample_assignment.start_datetime - timedelta(hours=1)
        )

        with pytest.raises(AssignmentUpdateError) as exc_info:
            service.update_assignment("assign-123", data)

        assert "end_datetime" in str(exc_info.value).lower()


class TestCloseAssignment:
    """Test close_assignment method."""

    def test_close_assignment_success(
        self, service, mock_assignment_repo, sample_assignment
    ):
        """Should close an active assignment."""
        mock_assignment_repo.find_by_id.return_value = sample_assignment
        mock_assignment_repo.generate_etag.return_value = "etag"
        mock_assignment_repo.update.side_effect = lambda a: a

        assignment, etag = service.close_assignment("assign-123")

        assert assignment.end_datetime is not None
        mock_assignment_repo.update.assert_called_once()

    def test_close_assignment_not_found(self, service, mock_assignment_repo):
        """Should raise AssignmentNotFoundError when not found."""
        mock_assignment_repo.find_by_id.return_value = None

        with pytest.raises(AssignmentNotFoundError):
            service.close_assignment("nonexistent")

    def test_close_assignment_etag_mismatch(
        self, service, mock_assignment_repo, sample_assignment
    ):
        """Should raise ETagMismatchError when ETag doesn't match."""
        mock_assignment_repo.find_by_id.return_value = sample_assignment
        mock_assignment_repo.generate_etag.return_value = "current-etag"

        with pytest.raises(ETagMismatchError):
            service.close_assignment("assign-123", if_match="wrong-etag")


class TestDeleteAssignment:
    """Test delete_assignment method."""

    def test_delete_active_assignment_closes_it(
        self, service, mock_assignment_repo, sample_assignment
    ):
        """Should close an active assignment instead of deleting."""
        mock_assignment_repo.find_by_id.return_value = sample_assignment
        mock_assignment_repo.generate_etag.return_value = "etag"
        mock_assignment_repo.update.side_effect = lambda a: a

        result = service.delete_assignment("assign-123")

        assert result is True
        mock_assignment_repo.delete.assert_not_called()
        mock_assignment_repo.update.assert_called()

    def test_delete_inactive_assignment_deletes_it(self, service, mock_assignment_repo):
        """Should delete an inactive assignment."""
        now = datetime.now(timezone.utc)
        inactive_assignment = Assignment(
            id="assign-123",
            driver_id="driver-456",
            vehicle_id="vehicle-789",
            start_datetime=now - timedelta(hours=8),
            end_datetime=now - timedelta(hours=1),  # Ended 1 hour ago
            notes=None,
            created_at=now - timedelta(hours=8),
            updated_at=now - timedelta(hours=1),
        )
        mock_assignment_repo.find_by_id.return_value = inactive_assignment
        mock_assignment_repo.generate_etag.return_value = "etag"
        mock_assignment_repo.delete.return_value = True

        result = service.delete_assignment("assign-123")

        assert result is True
        mock_assignment_repo.delete.assert_called_once_with("assign-123")

    def test_delete_assignment_not_found(self, service, mock_assignment_repo):
        """Should raise AssignmentNotFoundError when not found."""
        mock_assignment_repo.find_by_id.return_value = None

        with pytest.raises(AssignmentNotFoundError):
            service.delete_assignment("nonexistent")


class TestCloseAssignmentsForDriver:
    """Test close_assignments_for_driver method."""

    def test_close_assignments_for_driver(self, service, mock_assignment_repo):
        """Should close all active assignments for a driver."""
        mock_assignment_repo.close_active_assignments_for_driver.return_value = 2

        count = service.close_assignments_for_driver("driver-123")

        assert count == 2
        mock_assignment_repo.close_active_assignments_for_driver.assert_called_once_with(
            "driver-123"
        )


class TestCloseAssignmentsForVehicle:
    """Test close_assignments_for_vehicle method."""

    def test_close_assignments_for_vehicle(self, service, mock_assignment_repo):
        """Should close all active assignments for a vehicle."""
        mock_assignment_repo.close_active_assignments_for_vehicle.return_value = 1

        count = service.close_assignments_for_vehicle("vehicle-456")

        assert count == 1
        mock_assignment_repo.close_active_assignments_for_vehicle.assert_called_once_with(
            "vehicle-456"
        )


class TestGetActiveAssignments:
    """Test get_active_assignment methods."""

    def test_get_active_assignment_for_driver(
        self, service, mock_assignment_repo, sample_assignment
    ):
        """Should return active assignment for driver."""
        mock_assignment_repo.find_active_assignment_for_driver.return_value = (
            sample_assignment
        )

        result = service.get_active_assignment_for_driver("driver-123")

        assert result == sample_assignment

    def test_get_active_assignment_for_driver_none(self, service, mock_assignment_repo):
        """Should return None when no active assignment for driver."""
        mock_assignment_repo.find_active_assignment_for_driver.return_value = None

        result = service.get_active_assignment_for_driver("driver-123")

        assert result is None

    def test_get_active_assignment_for_vehicle(
        self, service, mock_assignment_repo, sample_assignment
    ):
        """Should return active assignment for vehicle."""
        mock_assignment_repo.find_active_assignment_for_vehicle.return_value = (
            sample_assignment
        )

        result = service.get_active_assignment_for_vehicle("vehicle-456")

        assert result == sample_assignment


class TestGetStats:
    """Test get_stats method."""

    def test_get_stats(self, service, mock_assignment_repo):
        """Should return assignment statistics."""
        mock_assignment_repo.find_all.return_value = ([], 100)
        mock_assignment_repo.count_active.return_value = 30

        stats = service.get_stats()

        assert stats["total"] == 100
        assert stats["active"] == 30
        assert stats["closed"] == 70
