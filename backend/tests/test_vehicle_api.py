"""
API endpoint tests for Vehicle endpoints.

Tests the REST API behavior for vehicle operations using FastAPI dependency overrides.
"""

import uuid
from unittest.mock import MagicMock

import pytest
from app.api.v1.endpoints.vehicles import get_vehicle_service
from app.core.exceptions import (
    ConcurrencyException,
    ConflictException,
    NotFoundException,
)
from app.domain.models.vehicle import FuelType, Vehicle, VehicleStatus, VehicleType
from app.main import app
from fastapi.testclient import TestClient


@pytest.fixture
def sample_vehicle():
    """Creates a sample Vehicle for testing."""
    return Vehicle(
        plate_number="ABC1234",
        model="Toyota Camry",
        year=2023,
        vehicle_type=VehicleType.SEDAN,
        fuel_type=FuelType.HYBRID,
        status=VehicleStatus.ACTIVE,
    )


@pytest.fixture
def mock_service():
    """Creates a mock VehicleService."""
    return MagicMock()


@pytest.fixture
def client_with_mock(mock_service):
    """
    Creates a test client with mocked vehicle service.

    Yields the client and mock service for test assertions.
    """
    app.dependency_overrides[get_vehicle_service] = lambda: mock_service
    yield TestClient(app), mock_service
    app.dependency_overrides.clear()


class TestListVehicles:
    """Tests for GET /api/v1/vehicles endpoint."""

    def test_list_vehicles_returns_empty_list(self, client_with_mock):
        """Returns empty list when no vehicles exist."""
        # Arrange
        client, mock_service = client_with_mock
        mock_service.get_all_vehicles.return_value = ([], 0)

        # Act
        response = client.get("/api/v1/vehicles")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"] == []
        assert data["pagination"]["total"] == 0

    def test_list_vehicles_returns_vehicles(self, client_with_mock, sample_vehicle):
        """Returns list of vehicles."""
        # Arrange
        client, mock_service = client_with_mock
        mock_service.get_all_vehicles.return_value = ([sample_vehicle], 1)

        # Act
        response = client.get("/api/v1/vehicles")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 1
        assert data["data"][0]["plate_number"] == "ABC1234"
        assert data["pagination"]["total"] == 1

    def test_list_vehicles_with_filters(self, client_with_mock):
        """Passes filter parameters to service."""
        # Arrange
        client, mock_service = client_with_mock
        mock_service.get_all_vehicles.return_value = ([], 0)

        # Act
        response = client.get(
            "/api/v1/vehicles",
            params={
                "status": "active",
                "type": "suv",
                "fuel": "electric",
                "limit": 25,
                "skip": 10,
            },
        )

        # Assert
        assert response.status_code == 200
        mock_service.get_all_vehicles.assert_called_once_with(
            status=VehicleStatus.ACTIVE,
            vehicle_type=VehicleType.SUV,
            fuel_type=FuelType.ELECTRIC,
            include_deleted=False,
            limit=25,
            skip=10,
            sort_by="updated_at",
            sort_order="desc",
        )


class TestGetVehicle:
    """Tests for GET /api/v1/vehicles/{vehicle_id} endpoint."""

    def test_get_vehicle_returns_vehicle(self, client_with_mock, sample_vehicle):
        """Returns vehicle when found."""
        # Arrange
        client, mock_service = client_with_mock
        mock_service.get_vehicle_by_id.return_value = sample_vehicle
        mock_service.get_vehicle_etag.return_value = "test-etag"

        # Act
        response = client.get(f"/api/v1/vehicles/{sample_vehicle.id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["id"] == sample_vehicle.id
        assert data["data"]["plate_number"] == "ABC1234"
        assert response.headers.get("ETag") == "test-etag"

    def test_get_vehicle_not_found(self, client_with_mock):
        """Returns 404 when vehicle not found."""
        # Arrange
        client, mock_service = client_with_mock
        vehicle_id = str(uuid.uuid4())
        mock_service.get_vehicle_by_id.side_effect = NotFoundException(
            code="VEHICLE_NOT_FOUND",
            message=f"Vehicle with ID '{vehicle_id}' not found.",
        )

        # Act
        response = client.get(f"/api/v1/vehicles/{vehicle_id}")

        # Assert
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "VEHICLE_NOT_FOUND"


class TestCreateVehicle:
    """Tests for POST /api/v1/vehicles endpoint."""

    def test_create_vehicle_success(self, client_with_mock, sample_vehicle):
        """Creates vehicle and returns 201."""
        # Arrange
        client, mock_service = client_with_mock
        mock_service.create_vehicle.return_value = sample_vehicle
        mock_service.get_vehicle_etag.return_value = "new-etag"

        # Act
        response = client.post(
            "/api/v1/vehicles",
            json={
                "plate_number": "ABC1234",
                "model": "Toyota Camry",
                "year": 2023,
                "type": "sedan",
                "fuel_type": "hybrid",
            },
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["data"]["plate_number"] == "ABC1234"
        assert response.headers.get("ETag") == "new-etag"
        assert f"/api/v1/vehicles/{sample_vehicle.id}" in response.headers.get(
            "Location", ""
        )

    def test_create_vehicle_duplicate_plate(self, client_with_mock):
        """Returns 409 for duplicate plate number."""
        # Arrange
        client, mock_service = client_with_mock
        mock_service.create_vehicle.side_effect = ConflictException(
            code="DUPLICATE_PLATE",
            message="A vehicle with plate number 'ABC1234' already exists.",
        )

        # Act
        response = client.post(
            "/api/v1/vehicles",
            json={
                "plate_number": "ABC1234",
                "model": "Test",
                "year": 2024,
                "type": "sedan",
                "fuel_type": "gasoline",
            },
        )

        # Assert
        assert response.status_code == 409
        data = response.json()
        assert data["success"] is False
        assert data["error"]["code"] == "DUPLICATE_PLATE"

    def test_create_vehicle_validation_error(self, client_with_mock):
        """Returns 422 for invalid input data."""
        # Arrange
        client, _ = client_with_mock

        # Act
        response = client.post(
            "/api/v1/vehicles",
            json={
                "plate_number": "",  # Invalid empty plate
                "model": "Test",
                "year": 1800,  # Invalid year
                "type": "invalid_type",
                "fuel_type": "gasoline",
            },
        )

        # Assert
        assert response.status_code == 422


class TestUpdateVehicle:
    """Tests for PUT /api/v1/vehicles/{vehicle_id} endpoint."""

    def test_update_vehicle_success(self, client_with_mock, sample_vehicle):
        """Updates vehicle and returns 200."""
        # Arrange
        client, mock_service = client_with_mock
        updated_vehicle = Vehicle(
            plate_number="UPD9999",
            model="Updated Model",
            year=2025,
            vehicle_type=VehicleType.TRUCK,
            fuel_type=FuelType.DIESEL,
            status=VehicleStatus.ACTIVE,
        )
        mock_service.update_vehicle.return_value = updated_vehicle
        mock_service.get_vehicle_etag.return_value = "updated-etag"

        # Act
        response = client.put(
            f"/api/v1/vehicles/{sample_vehicle.id}",
            json={
                "plate_number": "UPD9999",
                "model": "Updated Model",
                "year": 2025,
                "type": "truck",
                "fuel_type": "diesel",
                "status": "active",
            },
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["plate_number"] == "UPD9999"
        assert response.headers.get("ETag") == "updated-etag"

    def test_update_vehicle_with_if_match_header(
        self, client_with_mock, sample_vehicle
    ):
        """Passes If-Match header to service."""
        # Arrange
        client, mock_service = client_with_mock
        mock_service.update_vehicle.return_value = sample_vehicle
        mock_service.get_vehicle_etag.return_value = "new-etag"

        # Act
        response = client.put(
            f"/api/v1/vehicles/{sample_vehicle.id}",
            json={
                "plate_number": "ABC1234",
                "model": "Test",
                "year": 2024,
                "type": "sedan",
                "fuel_type": "gasoline",
                "status": "active",
            },
            headers={"If-Match": "test-etag"},
        )

        # Assert
        assert response.status_code == 200
        mock_service.update_vehicle.assert_called_once()
        call_kwargs = mock_service.update_vehicle.call_args.kwargs
        assert call_kwargs["etag"] == "test-etag"

    def test_update_vehicle_concurrency_error(self, client_with_mock, sample_vehicle):
        """Returns 412 for ETag mismatch."""
        # Arrange
        client, mock_service = client_with_mock
        mock_service.update_vehicle.side_effect = ConcurrencyException()

        # Act
        response = client.put(
            f"/api/v1/vehicles/{sample_vehicle.id}",
            json={
                "plate_number": "ABC1234",
                "model": "Test",
                "year": 2024,
                "type": "sedan",
                "fuel_type": "gasoline",
                "status": "active",
            },
            headers={"If-Match": "wrong-etag"},
        )

        # Assert
        assert response.status_code == 412


class TestPatchVehicle:
    """Tests for PATCH /api/v1/vehicles/{vehicle_id} endpoint."""

    def test_patch_vehicle_success(self, client_with_mock, sample_vehicle):
        """Patches vehicle and returns 200."""
        # Arrange
        client, mock_service = client_with_mock
        patched_vehicle = Vehicle(
            plate_number="ABC1234",
            model="Patched Model",
            year=2023,
            vehicle_type=VehicleType.SEDAN,
            fuel_type=FuelType.HYBRID,
            status=VehicleStatus.ACTIVE,
        )
        mock_service.patch_vehicle.return_value = patched_vehicle
        mock_service.get_vehicle_etag.return_value = "patched-etag"

        # Act
        response = client.patch(
            f"/api/v1/vehicles/{sample_vehicle.id}",
            json={"model": "Patched Model"},
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["model"] == "Patched Model"


class TestDeleteVehicle:
    """Tests for DELETE /api/v1/vehicles/{vehicle_id} endpoint."""

    def test_delete_vehicle_success(self, client_with_mock, sample_vehicle):
        """Deletes vehicle and returns 204."""
        # Arrange
        client, mock_service = client_with_mock
        mock_service.delete_vehicle.return_value = None

        # Act
        response = client.delete(f"/api/v1/vehicles/{sample_vehicle.id}")

        # Assert
        assert response.status_code == 204
        mock_service.delete_vehicle.assert_called_once_with(sample_vehicle.id)

    def test_delete_vehicle_not_found(self, client_with_mock):
        """Returns 404 when vehicle not found."""
        # Arrange
        client, mock_service = client_with_mock
        vehicle_id = str(uuid.uuid4())
        mock_service.delete_vehicle.side_effect = NotFoundException(
            code="VEHICLE_NOT_FOUND",
            message=f"Vehicle with ID '{vehicle_id}' not found.",
        )

        # Act
        response = client.delete(f"/api/v1/vehicles/{vehicle_id}")

        # Assert
        assert response.status_code == 404

    def test_delete_vehicle_with_active_assignments(
        self, client_with_mock, sample_vehicle
    ):
        """Returns 409 when vehicle has active assignments."""
        # Arrange
        client, mock_service = client_with_mock
        mock_service.delete_vehicle.side_effect = ConflictException(
            code="VEHICLE_HAS_ACTIVE_ASSIGNMENTS",
            message="Cannot delete vehicle with active assignments.",
        )

        # Act
        response = client.delete(f"/api/v1/vehicles/{sample_vehicle.id}")

        # Assert
        assert response.status_code == 409
        data = response.json()
        assert data["error"]["code"] == "VEHICLE_HAS_ACTIVE_ASSIGNMENTS"


class TestVehicleStats:
    """Tests for GET /api/v1/vehicles/stats/by-status endpoint."""

    def test_get_vehicle_stats(self, client_with_mock):
        """Returns vehicle stats by status."""
        # Arrange
        client, mock_service = client_with_mock
        mock_service.get_vehicle_counts_by_status.return_value = {
            "active": 5,
            "inactive": 2,
            "maintenance": 1,
        }

        # Act
        response = client.get("/api/v1/vehicles/stats/by-status")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["active"] == 5
        assert data["data"]["inactive"] == 2
        assert data["data"]["maintenance"] == 1
