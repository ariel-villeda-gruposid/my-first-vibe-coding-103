"""
Unit tests for Vehicle domain model.

Tests the Vehicle class, enums, and domain logic.
"""

import uuid
from datetime import datetime, timezone

import pytest
from app.domain.models.vehicle import FuelType, Vehicle, VehicleStatus, VehicleType


class TestVehicleStatus:
    """Tests for VehicleStatus enum."""

    def test_status_values(self):
        """Verify all expected status values exist."""
        # Arrange & Act & Assert
        assert VehicleStatus.ACTIVE.value == "active"
        assert VehicleStatus.INACTIVE.value == "inactive"
        assert VehicleStatus.MAINTENANCE.value == "maintenance"

    def test_status_from_string(self):
        """Can create status from string value."""
        # Arrange & Act & Assert
        assert VehicleStatus("active") == VehicleStatus.ACTIVE
        assert VehicleStatus("inactive") == VehicleStatus.INACTIVE
        assert VehicleStatus("maintenance") == VehicleStatus.MAINTENANCE


class TestVehicleType:
    """Tests for VehicleType enum."""

    def test_type_values(self):
        """Verify all expected type values exist."""
        # Arrange & Act & Assert
        assert VehicleType.SEDAN.value == "sedan"
        assert VehicleType.SUV.value == "suv"
        assert VehicleType.TRUCK.value == "truck"
        assert VehicleType.VAN.value == "van"
        assert VehicleType.MOTORCYCLE.value == "motorcycle"


class TestFuelType:
    """Tests for FuelType enum."""

    def test_fuel_type_values(self):
        """Verify all expected fuel type values exist."""
        # Arrange & Act & Assert
        assert FuelType.GASOLINE.value == "gasoline"
        assert FuelType.DIESEL.value == "diesel"
        assert FuelType.ELECTRIC.value == "electric"
        assert FuelType.HYBRID.value == "hybrid"


class TestVehicleCreation:
    """Tests for Vehicle creation."""

    def test_create_vehicle_with_all_fields(self):
        """Vehicle can be created with all fields."""
        # Arrange
        plate_number = "ABC-1234"
        model = "Toyota Camry"
        year = 2023
        vehicle_type = VehicleType.SEDAN
        fuel_type = FuelType.HYBRID
        status = VehicleStatus.ACTIVE

        # Act
        vehicle = Vehicle(
            plate_number=plate_number,
            model=model,
            year=year,
            vehicle_type=vehicle_type,
            fuel_type=fuel_type,
            status=status,
        )

        # Assert
        assert vehicle.plate_number == plate_number
        assert vehicle.model == model
        assert vehicle.year == year
        assert vehicle.vehicle_type == vehicle_type
        assert vehicle.fuel_type == fuel_type
        assert vehicle.status == status
        assert vehicle.is_deleted is False
        assert vehicle.deleted_at is None

    def test_create_vehicle_generates_uuid_id(self):
        """New vehicle gets a valid UUID string as ID."""
        # Arrange & Act
        vehicle = Vehicle(
            plate_number="XYZ-9999",
            model="Honda Civic",
            year=2022,
            vehicle_type=VehicleType.SEDAN,
            fuel_type=FuelType.GASOLINE,
        )

        # Assert
        assert vehicle.id is not None
        # Verify it's a valid UUID
        uuid.UUID(vehicle.id)

    def test_create_vehicle_sets_timestamps(self):
        """New vehicle gets created_at and updated_at timestamps."""
        # Arrange
        before_creation = datetime.now(timezone.utc)

        # Act
        vehicle = Vehicle(
            plate_number="TMP-0001",
            model="Test Model",
            year=2024,
            vehicle_type=VehicleType.SUV,
            fuel_type=FuelType.DIESEL,
        )
        after_creation = datetime.now(timezone.utc)

        # Assert
        assert vehicle.created_at >= before_creation
        assert vehicle.created_at <= after_creation
        assert vehicle.updated_at >= before_creation
        assert vehicle.updated_at <= after_creation

    def test_create_vehicle_default_status_is_active(self):
        """Vehicle defaults to ACTIVE status when not specified."""
        # Arrange & Act
        vehicle = Vehicle(
            plate_number="DEF-5678",
            model="Ford F-150",
            year=2021,
            vehicle_type=VehicleType.TRUCK,
            fuel_type=FuelType.DIESEL,
        )

        # Assert
        assert vehicle.status == VehicleStatus.ACTIVE


class TestVehicleUpdate:
    """Tests for Vehicle update functionality."""

    def test_update_vehicle_changes_fields(self):
        """Update method changes provided fields."""
        # Arrange
        vehicle = Vehicle(
            plate_number="OLD-1234",
            model="Old Model",
            year=2020,
            vehicle_type=VehicleType.SEDAN,
            fuel_type=FuelType.GASOLINE,
        )
        original_created_at = vehicle.created_at

        # Act
        vehicle.update(
            plate_number="NEW-5678",
            model="New Model",
            year=2024,
        )

        # Assert
        assert vehicle.plate_number == "NEW-5678"
        assert vehicle.model == "New Model"
        assert vehicle.year == 2024
        assert vehicle.created_at == original_created_at  # Should not change

    def test_update_vehicle_only_changes_provided_fields(self):
        """Update method only changes fields that are provided."""
        # Arrange
        vehicle = Vehicle(
            plate_number="ABC-1234",
            model="Test Model",
            year=2023,
            vehicle_type=VehicleType.SUV,
            fuel_type=FuelType.HYBRID,
        )
        original_model = vehicle.model
        original_year = vehicle.year

        # Act
        vehicle.update(plate_number="NEW-9999")

        # Assert
        assert vehicle.plate_number == "NEW-9999"
        assert vehicle.model == original_model
        assert vehicle.year == original_year

    def test_update_vehicle_updates_timestamp(self):
        """Update method updates the updated_at timestamp."""
        # Arrange
        vehicle = Vehicle(
            plate_number="TST-0001",
            model="Timestamp Test",
            year=2023,
            vehicle_type=VehicleType.VAN,
            fuel_type=FuelType.ELECTRIC,
        )
        original_updated_at = vehicle.updated_at

        # Act
        vehicle.update(model="Updated Model")

        # Assert
        assert vehicle.updated_at >= original_updated_at


class TestVehicleSoftDelete:
    """Tests for Vehicle soft delete functionality."""

    def test_soft_delete_sets_is_deleted(self):
        """Soft delete sets is_deleted to True."""
        # Arrange
        vehicle = Vehicle(
            plate_number="DEL-0001",
            model="Delete Test",
            year=2023,
            vehicle_type=VehicleType.SEDAN,
            fuel_type=FuelType.GASOLINE,
        )

        # Act
        vehicle.soft_delete()

        # Assert
        assert vehicle.is_deleted is True

    def test_soft_delete_sets_deleted_at(self):
        """Soft delete sets deleted_at timestamp."""
        # Arrange
        vehicle = Vehicle(
            plate_number="DEL-0002",
            model="Delete Test 2",
            year=2023,
            vehicle_type=VehicleType.SUV,
            fuel_type=FuelType.DIESEL,
        )
        before_deletion = datetime.now(timezone.utc)

        # Act
        vehicle.soft_delete()
        after_deletion = datetime.now(timezone.utc)

        # Assert
        assert vehicle.deleted_at is not None
        assert vehicle.deleted_at >= before_deletion
        assert vehicle.deleted_at <= after_deletion

    def test_soft_delete_updates_updated_at(self):
        """Soft delete updates the updated_at timestamp."""
        # Arrange
        vehicle = Vehicle(
            plate_number="DEL-0003",
            model="Delete Test 3",
            year=2023,
            vehicle_type=VehicleType.TRUCK,
            fuel_type=FuelType.HYBRID,
        )
        original_updated_at = vehicle.updated_at

        # Act
        vehicle.soft_delete()

        # Assert
        assert vehicle.updated_at >= original_updated_at


class TestVehicleRestore:
    """Tests for Vehicle restore functionality."""

    def test_restore_clears_is_deleted(self):
        """Restore clears is_deleted flag."""
        # Arrange
        vehicle = Vehicle(
            plate_number="RST-0001",
            model="Restore Test",
            year=2023,
            vehicle_type=VehicleType.SEDAN,
            fuel_type=FuelType.GASOLINE,
        )
        vehicle.soft_delete()

        # Act
        vehicle.restore()

        # Assert
        assert vehicle.is_deleted is False

    def test_restore_clears_deleted_at(self):
        """Restore clears deleted_at timestamp."""
        # Arrange
        vehicle = Vehicle(
            plate_number="RST-0002",
            model="Restore Test 2",
            year=2023,
            vehicle_type=VehicleType.SUV,
            fuel_type=FuelType.DIESEL,
        )
        vehicle.soft_delete()

        # Act
        vehicle.restore()

        # Assert
        assert vehicle.deleted_at is None


class TestVehicleToDict:
    """Tests for Vehicle serialization to dictionary."""

    def test_to_dict_includes_all_fields(self):
        """to_dict returns all vehicle fields."""
        # Arrange
        vehicle = Vehicle(
            plate_number="DCT-0001",
            model="Dict Test",
            year=2023,
            vehicle_type=VehicleType.SEDAN,
            fuel_type=FuelType.GASOLINE,
            status=VehicleStatus.ACTIVE,
        )

        # Act
        result = vehicle.to_dict()

        # Assert
        assert result["id"] == vehicle.id
        assert result["plate_number"] == "DCT-0001"
        assert result["model"] == "Dict Test"
        assert result["year"] == 2023
        assert result["vehicle_type"] == "sedan"
        assert result["fuel_type"] == "gasoline"
        assert result["status"] == "active"
        assert result["is_deleted"] is False
        assert result["deleted_at"] is None
        assert "created_at" in result
        assert "updated_at" in result

    def test_to_dict_serializes_deleted_vehicle(self):
        """to_dict properly serializes deleted vehicle."""
        # Arrange
        vehicle = Vehicle(
            plate_number="DCT-0002",
            model="Deleted Dict Test",
            year=2023,
            vehicle_type=VehicleType.VAN,
            fuel_type=FuelType.ELECTRIC,
        )
        vehicle.soft_delete()

        # Act
        result = vehicle.to_dict()

        # Assert
        assert result["is_deleted"] is True
        assert result["deleted_at"] is not None


class TestVehicleFromDict:
    """Tests for Vehicle deserialization from dictionary."""

    def test_from_dict_creates_vehicle(self):
        """from_dict creates vehicle from dictionary."""
        # Arrange
        data = {
            "id": str(uuid.uuid4()),
            "plate_number": "FRD-0001",
            "model": "From Dict Test",
            "year": 2024,
            "vehicle_type": "suv",
            "fuel_type": "hybrid",
            "status": "active",
            "is_deleted": False,
            "deleted_at": None,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }

        # Act
        vehicle = Vehicle.from_dict(data)

        # Assert
        assert vehicle.id == data["id"]
        assert vehicle.plate_number == "FRD-0001"
        assert vehicle.model == "From Dict Test"
        assert vehicle.year == 2024
        assert vehicle.vehicle_type == VehicleType.SUV
        assert vehicle.fuel_type == FuelType.HYBRID
        assert vehicle.status == VehicleStatus.ACTIVE

    def test_from_dict_handles_deleted_vehicle(self):
        """from_dict properly deserializes deleted vehicle."""
        # Arrange
        deleted_at = datetime.now(timezone.utc)
        data = {
            "id": str(uuid.uuid4()),
            "plate_number": "FRD-0002",
            "model": "Deleted From Dict",
            "year": 2023,
            "vehicle_type": "truck",
            "fuel_type": "diesel",
            "status": "inactive",
            "is_deleted": True,
            "deleted_at": deleted_at,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }

        # Act
        vehicle = Vehicle.from_dict(data)

        # Assert
        assert vehicle.is_deleted is True
        assert vehicle.deleted_at == deleted_at
