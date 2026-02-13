"""
Integration tests for Assignment API endpoints.

Tests the Assignment REST API using TestClient with mocked service.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest
from app.api.v1.endpoints.assignments import get_assignment_service
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
    VehicleAlreadyAssignedError,
    VehicleNotAvailableError,
    VehicleNotFoundError,
)
from app.main import app
from fastapi.testclient import TestClient


@pytest.fixture
def mock_service():
    """Create a mock assignment service."""
    return MagicMock(spec=AssignmentService)


@pytest.fixture
def client(mock_service):
    """Create a test client with service override."""
    app.dependency_overrides[get_assignment_service] = lambda: mock_service
    yield TestClient(app)
    app.dependency_overrides.clear()


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


class TestListAssignments:
    """Tests for GET /api/v1/assignments."""

    def test_list_assignments_empty(self, client, mock_service):
        """Should return empty list when no assignments exist."""
        mock_service.list_assignments.return_value = ([], 0)

        response = client.get("/api/v1/assignments")

        assert response.status_code == 200
        data = response.json()
        assert data["data"] == []
        assert data["pagination"]["total"] == 0

    def test_list_assignments_with_results(
        self, client, mock_service, sample_assignment
    ):
        """Should return list of assignments."""
        mock_service.list_assignments.return_value = ([sample_assignment], 1)

        response = client.get("/api/v1/assignments")

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1
        assert data["data"][0]["id"] == sample_assignment.id
        assert data["pagination"]["total"] == 1

    def test_list_assignments_with_driver_filter(self, client, mock_service):
        """Should filter assignments by driver_id."""
        mock_service.list_assignments.return_value = ([], 0)

        response = client.get("/api/v1/assignments?driver_id=driver-123")

        assert response.status_code == 200
        mock_service.list_assignments.assert_called_once()
        call_kwargs = mock_service.list_assignments.call_args[1]
        assert call_kwargs["driver_id"] == "driver-123"

    def test_list_assignments_with_vehicle_filter(self, client, mock_service):
        """Should filter assignments by vehicle_id."""
        mock_service.list_assignments.return_value = ([], 0)

        response = client.get("/api/v1/assignments?vehicle_id=vehicle-456")

        assert response.status_code == 200
        call_kwargs = mock_service.list_assignments.call_args[1]
        assert call_kwargs["vehicle_id"] == "vehicle-456"

    def test_list_assignments_with_active_only(self, client, mock_service):
        """Should filter to active only when requested."""
        mock_service.list_assignments.return_value = ([], 0)

        response = client.get("/api/v1/assignments?active_only=true")

        assert response.status_code == 200
        call_kwargs = mock_service.list_assignments.call_args[1]
        assert call_kwargs["active_only"] is True


class TestListActiveAssignments:
    """Tests for GET /api/v1/assignments/active."""

    def test_list_active_assignments(self, client, mock_service, sample_assignment):
        """Should return only active assignments."""
        mock_service.list_assignments.return_value = ([sample_assignment], 1)

        response = client.get("/api/v1/assignments/active")

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1
        mock_service.list_assignments.assert_called_once()
        call_kwargs = mock_service.list_assignments.call_args[1]
        assert call_kwargs["active_only"] is True


class TestGetAssignment:
    """Tests for GET /api/v1/assignments/{id}."""

    def test_get_assignment_success(self, client, mock_service, sample_assignment):
        """Should return assignment when found."""
        mock_service.get_assignment.return_value = (sample_assignment, "etag-123")

        response = client.get(f"/api/v1/assignments/{sample_assignment.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_assignment.id
        assert data["driver_id"] == sample_assignment.driver_id
        assert data["vehicle_id"] == sample_assignment.vehicle_id
        assert response.headers["ETag"] == "etag-123"

    def test_get_assignment_not_found(self, client, mock_service):
        """Should return 404 when assignment not found."""
        mock_service.get_assignment.side_effect = AssignmentNotFoundError("Not found")

        response = client.get("/api/v1/assignments/nonexistent")

        assert response.status_code == 404


class TestGetAssignmentStats:
    """Tests for GET /api/v1/assignments/stats."""

    def test_get_assignment_stats(self, client, mock_service):
        """Should return assignment statistics."""
        mock_service.get_stats.return_value = {"total": 100, "active": 30, "closed": 70}

        response = client.get("/api/v1/assignments/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 100
        assert data["active"] == 30
        assert data["closed"] == 70


class TestCreateAssignment:
    """Tests for POST /api/v1/assignments."""

    def test_create_assignment_success(self, client, mock_service, sample_assignment):
        """Should create assignment when all validations pass."""
        mock_service.create_assignment.return_value = (sample_assignment, "etag-new")

        now = datetime.now(timezone.utc)
        payload = {
            "driver_id": sample_assignment.driver_id,
            "vehicle_id": sample_assignment.vehicle_id,
            "start_datetime": now.isoformat(),
            "notes": "Test notes",
        }

        response = client.post("/api/v1/assignments", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["id"] == sample_assignment.id
        assert response.headers["ETag"] == "etag-new"

    def test_create_assignment_driver_not_found(self, client, mock_service):
        """Should return 400 when driver not found."""
        mock_service.create_assignment.side_effect = DriverNotFoundError(
            "Driver not found"
        )

        now = datetime.now(timezone.utc)
        payload = {
            "driver_id": "nonexistent",
            "vehicle_id": "vehicle-789",
            "start_datetime": now.isoformat(),
        }

        response = client.post("/api/v1/assignments", json=payload)

        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["error"] == "driver_not_found"

    def test_create_assignment_vehicle_not_found(self, client, mock_service):
        """Should return 400 when vehicle not found."""
        mock_service.create_assignment.side_effect = VehicleNotFoundError(
            "Vehicle not found"
        )

        now = datetime.now(timezone.utc)
        payload = {
            "driver_id": "driver-456",
            "vehicle_id": "nonexistent",
            "start_datetime": now.isoformat(),
        }

        response = client.post("/api/v1/assignments", json=payload)

        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["error"] == "vehicle_not_found"

    def test_create_assignment_driver_not_active(self, client, mock_service):
        """Should return 400 when driver is not active."""
        mock_service.create_assignment.side_effect = DriverNotActiveError(
            "Driver suspended"
        )

        now = datetime.now(timezone.utc)
        payload = {
            "driver_id": "driver-456",
            "vehicle_id": "vehicle-789",
            "start_datetime": now.isoformat(),
        }

        response = client.post("/api/v1/assignments", json=payload)

        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["error"] == "driver_not_active"

    def test_create_assignment_vehicle_not_available(self, client, mock_service):
        """Should return 400 when vehicle is not available."""
        mock_service.create_assignment.side_effect = VehicleNotAvailableError(
            "In maintenance"
        )

        now = datetime.now(timezone.utc)
        payload = {
            "driver_id": "driver-456",
            "vehicle_id": "vehicle-789",
            "start_datetime": now.isoformat(),
        }

        response = client.post("/api/v1/assignments", json=payload)

        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["error"] == "vehicle_not_available"

    def test_create_assignment_driver_already_assigned(self, client, mock_service):
        """Should return 409 when driver already has active assignment."""
        mock_service.create_assignment.side_effect = DriverAlreadyAssignedError(
            "Already assigned"
        )

        now = datetime.now(timezone.utc)
        payload = {
            "driver_id": "driver-456",
            "vehicle_id": "vehicle-789",
            "start_datetime": now.isoformat(),
        }

        response = client.post("/api/v1/assignments", json=payload)

        assert response.status_code == 409
        data = response.json()
        assert data["detail"]["error"] == "driver_already_assigned"

    def test_create_assignment_vehicle_already_assigned(self, client, mock_service):
        """Should return 409 when vehicle already has active assignment."""
        mock_service.create_assignment.side_effect = VehicleAlreadyAssignedError(
            "Already assigned"
        )

        now = datetime.now(timezone.utc)
        payload = {
            "driver_id": "driver-456",
            "vehicle_id": "vehicle-789",
            "start_datetime": now.isoformat(),
        }

        response = client.post("/api/v1/assignments", json=payload)

        assert response.status_code == 409
        data = response.json()
        assert data["detail"]["error"] == "vehicle_already_assigned"


class TestUpdateAssignment:
    """Tests for PATCH /api/v1/assignments/{id}."""

    def test_update_assignment_notes(self, client, mock_service, sample_assignment):
        """Should update assignment notes."""
        updated = Assignment(
            id=sample_assignment.id,
            driver_id=sample_assignment.driver_id,
            vehicle_id=sample_assignment.vehicle_id,
            start_datetime=sample_assignment.start_datetime,
            end_datetime=sample_assignment.end_datetime,
            notes="Updated notes",
            created_at=sample_assignment.created_at,
            updated_at=datetime.now(timezone.utc),
        )
        mock_service.update_assignment.return_value = (updated, "etag-new")

        response = client.patch(
            f"/api/v1/assignments/{sample_assignment.id}",
            json={"notes": "Updated notes"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["notes"] == "Updated notes"

    def test_update_assignment_not_found(self, client, mock_service):
        """Should return 404 when assignment not found."""
        mock_service.update_assignment.side_effect = AssignmentNotFoundError(
            "Not found"
        )

        response = client.patch("/api/v1/assignments/nonexistent", json={"notes": "X"})

        assert response.status_code == 404

    def test_update_assignment_etag_mismatch(self, client, mock_service):
        """Should return 412 when ETag doesn't match."""
        mock_service.update_assignment.side_effect = ETagMismatchError("Mismatch")

        response = client.patch(
            "/api/v1/assignments/assign-123",
            json={"notes": "Updated"},
            headers={"If-Match": "wrong-etag"},
        )

        assert response.status_code == 412

    def test_update_assignment_update_error(self, client, mock_service):
        """Should return 400 for update errors."""
        mock_service.update_assignment.side_effect = AssignmentUpdateError(
            "Cannot update"
        )

        response = client.patch(
            "/api/v1/assignments/assign-123",
            json={"start_datetime": datetime.now(timezone.utc).isoformat()},
        )

        assert response.status_code == 400


class TestCloseAssignment:
    """Tests for POST /api/v1/assignments/{id}/close."""

    def test_close_assignment_success(self, client, mock_service, sample_assignment):
        """Should close an active assignment."""
        closed = Assignment(
            id=sample_assignment.id,
            driver_id=sample_assignment.driver_id,
            vehicle_id=sample_assignment.vehicle_id,
            start_datetime=sample_assignment.start_datetime,
            end_datetime=datetime.now(timezone.utc),
            notes=sample_assignment.notes,
            created_at=sample_assignment.created_at,
            updated_at=datetime.now(timezone.utc),
        )
        mock_service.close_assignment.return_value = (closed, "etag-new")

        response = client.post(f"/api/v1/assignments/{sample_assignment.id}/close")

        assert response.status_code == 200
        data = response.json()
        assert data["end_datetime"] is not None

    def test_close_assignment_not_found(self, client, mock_service):
        """Should return 404 when assignment not found."""
        mock_service.close_assignment.side_effect = AssignmentNotFoundError("Not found")

        response = client.post("/api/v1/assignments/nonexistent/close")

        assert response.status_code == 404

    def test_close_assignment_etag_mismatch(self, client, mock_service):
        """Should return 412 when ETag doesn't match."""
        mock_service.close_assignment.side_effect = ETagMismatchError("Mismatch")

        response = client.post(
            "/api/v1/assignments/assign-123/close",
            headers={"If-Match": "wrong-etag"},
        )

        assert response.status_code == 412


class TestDeleteAssignment:
    """Tests for DELETE /api/v1/assignments/{id}."""

    def test_delete_assignment_success(self, client, mock_service):
        """Should delete/close an assignment."""
        mock_service.delete_assignment.return_value = True

        response = client.delete("/api/v1/assignments/assign-123")

        assert response.status_code == 204

    def test_delete_assignment_not_found(self, client, mock_service):
        """Should return 404 when assignment not found."""
        mock_service.delete_assignment.side_effect = AssignmentNotFoundError(
            "Not found"
        )

        response = client.delete("/api/v1/assignments/nonexistent")

        assert response.status_code == 404

    def test_delete_assignment_etag_mismatch(self, client, mock_service):
        """Should return 412 when ETag doesn't match."""
        mock_service.delete_assignment.side_effect = ETagMismatchError("Mismatch")

        response = client.delete(
            "/api/v1/assignments/assign-123",
            headers={"If-Match": "wrong-etag"},
        )

        assert response.status_code == 412


class TestGetActiveAssignmentForDriver:
    """Tests for GET /api/v1/assignments/driver/{id}/active."""

    def test_get_active_assignment_for_driver_found(
        self, client, mock_service, sample_assignment
    ):
        """Should return active assignment when found."""
        mock_service.get_active_assignment_for_driver.return_value = sample_assignment

        response = client.get("/api/v1/assignments/driver/driver-456/active")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_assignment.id

    def test_get_active_assignment_for_driver_not_found(self, client, mock_service):
        """Should return null when no active assignment."""
        mock_service.get_active_assignment_for_driver.return_value = None

        response = client.get("/api/v1/assignments/driver/driver-456/active")

        assert response.status_code == 200
        assert response.json() is None


class TestGetActiveAssignmentForVehicle:
    """Tests for GET /api/v1/assignments/vehicle/{id}/active."""

    def test_get_active_assignment_for_vehicle_found(
        self, client, mock_service, sample_assignment
    ):
        """Should return active assignment when found."""
        mock_service.get_active_assignment_for_vehicle.return_value = sample_assignment

        response = client.get("/api/v1/assignments/vehicle/vehicle-789/active")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_assignment.id

    def test_get_active_assignment_for_vehicle_not_found(self, client, mock_service):
        """Should return null when no active assignment."""
        mock_service.get_active_assignment_for_vehicle.return_value = None

        response = client.get("/api/v1/assignments/vehicle/vehicle-789/active")

        assert response.status_code == 200
        assert response.json() is None
