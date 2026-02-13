"""
Unit tests for custom exceptions.
"""

import pytest
from app.core.exceptions import (
    AppException,
    ConcurrencyException,
    ConflictException,
    NotFoundException,
    ValidationException,
)


class TestAppException:
    """Tests for the base AppException class."""

    def test_app_exception_initializes_with_all_fields(self):
        """Test that AppException initializes with all provided fields."""
        # Arrange
        details = {"field": [{"code": "ERROR", "message": "test"}]}

        # Act
        exc = AppException(
            code="TEST_ERROR",
            message="Test message",
            status_code=400,
            details=details,
        )

        # Assert
        assert exc.code == "TEST_ERROR"
        assert exc.message == "Test message"
        assert exc.status_code == 400
        assert exc.details == details

    def test_app_exception_default_status_code_is_500(self):
        """Test that AppException defaults to status code 500."""
        # Arrange & Act
        exc = AppException(code="TEST", message="Test")

        # Assert
        assert exc.status_code == 500

    def test_app_exception_to_dict_without_details(self):
        """Test to_dict method without details."""
        # Arrange
        exc = AppException(code="TEST_ERROR", message="Test message")

        # Act
        result = exc.to_dict()

        # Assert
        assert result == {"code": "TEST_ERROR", "message": "Test message"}

    def test_app_exception_to_dict_with_details(self):
        """Test to_dict method with details."""
        # Arrange
        details = {"field": [{"code": "REQUIRED", "message": "Field is required"}]}
        exc = AppException(
            code="VALIDATION", message="Validation failed", details=details
        )

        # Act
        result = exc.to_dict()

        # Assert
        assert result["code"] == "VALIDATION"
        assert result["message"] == "Validation failed"
        assert result["details"] == details


class TestNotFoundException:
    """Tests for the NotFoundException class."""

    def test_not_found_exception_default_values(self):
        """Test NotFoundException with default values."""
        # Arrange & Act
        exc = NotFoundException()

        # Assert
        assert exc.code == "RESOURCE_NOT_FOUND"
        assert exc.message == "The requested resource was not found."
        assert exc.status_code == 404

    def test_not_found_exception_custom_values(self):
        """Test NotFoundException with custom values."""
        # Arrange & Act
        exc = NotFoundException(code="VEHICLE_NOT_FOUND", message="Vehicle not found")

        # Assert
        assert exc.code == "VEHICLE_NOT_FOUND"
        assert exc.message == "Vehicle not found"
        assert exc.status_code == 404


class TestConflictException:
    """Tests for the ConflictException class."""

    def test_conflict_exception_default_values(self):
        """Test ConflictException with default values."""
        # Arrange & Act
        exc = ConflictException()

        # Assert
        assert exc.code == "CONFLICT"
        assert exc.status_code == 409

    def test_conflict_exception_custom_values(self):
        """Test ConflictException with custom values."""
        # Arrange & Act
        exc = ConflictException(
            code="DUPLICATE_PLATE",
            message="Plate number already exists",
        )

        # Assert
        assert exc.code == "DUPLICATE_PLATE"
        assert exc.message == "Plate number already exists"
        assert exc.status_code == 409


class TestValidationException:
    """Tests for the ValidationException class."""

    def test_validation_exception_default_values(self):
        """Test ValidationException with default values."""
        # Arrange & Act
        exc = ValidationException()

        # Assert
        assert exc.code == "VALIDATION_ERROR"
        assert exc.message == "Validation failed."
        assert exc.status_code == 422
        assert exc.details is None

    def test_validation_exception_with_field_details(self):
        """Test ValidationException with field-level details."""
        # Arrange
        details = {
            "plate_number": [
                {"code": "REQUIRED", "message": "Plate number is required"}
            ],
            "year": [{"code": "MIN_VALUE", "message": "Year must be >= 1996"}],
        }

        # Act
        exc = ValidationException(
            message="Validation failed for vehicle",
            details=details,
        )

        # Assert
        assert exc.status_code == 422
        assert exc.details == details


class TestConcurrencyException:
    """Tests for the ConcurrencyException class."""

    def test_concurrency_exception_default_values(self):
        """Test ConcurrencyException with default values."""
        # Arrange & Act
        exc = ConcurrencyException()

        # Assert
        assert exc.code == "CONCURRENCY_CONFLICT"
        assert exc.status_code == 412  # 412 Precondition Failed per RFC 7232
        assert "modified" in exc.message.lower()
