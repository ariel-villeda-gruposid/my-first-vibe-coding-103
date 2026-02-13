"""
Tests for the StatisticsService.

Verifies dashboard statistics aggregation logic.
"""

from unittest.mock import MagicMock

import pytest
from app.domain.services.statistics_service import StatisticsService


@pytest.fixture
def mock_vehicle_repository():
    """Create a mock vehicle repository."""
    return MagicMock()


@pytest.fixture
def mock_driver_repository():
    """Create a mock driver repository."""
    return MagicMock()


@pytest.fixture
def mock_assignment_repository():
    """Create a mock assignment repository."""
    return MagicMock()


@pytest.fixture
def statistics_service(
    mock_vehicle_repository,
    mock_driver_repository,
    mock_assignment_repository,
):
    """Create a StatisticsService with mocked dependencies."""
    return StatisticsService(
        vehicle_repository=mock_vehicle_repository,
        driver_repository=mock_driver_repository,
        assignment_repository=mock_assignment_repository,
    )


class TestGetDashboardStats:
    """Tests for get_dashboard_stats method."""

    def test_returns_all_statistics(
        self,
        statistics_service,
        mock_vehicle_repository,
        mock_driver_repository,
        mock_assignment_repository,
    ):
        """Returns combined statistics from all repositories."""
        # Arrange
        mock_vehicle_repository.count_by_status.return_value = {
            "active": 10,
            "inactive": 5,
            "maintenance": 2,
        }
        mock_driver_repository.count_by_status.return_value = {
            "active": 15,
            "suspended": 3,
        }
        mock_assignment_repository.count_active.return_value = 8
        mock_assignment_repository.count_all.return_value = 100

        # Act
        result = statistics_service.get_dashboard_stats()

        # Assert
        assert result["vehicle_count_by_status"] == {
            "active": 10,
            "inactive": 5,
            "maintenance": 2,
        }
        assert result["driver_count_by_status"] == {
            "active": 15,
            "suspended": 3,
        }
        assert result["active_assignments_count"] == 8
        assert result["total_assignments_count"] == 100

    def test_calls_all_repositories(
        self,
        statistics_service,
        mock_vehicle_repository,
        mock_driver_repository,
        mock_assignment_repository,
    ):
        """Calls all repository methods."""
        # Arrange
        mock_vehicle_repository.count_by_status.return_value = {}
        mock_driver_repository.count_by_status.return_value = {}
        mock_assignment_repository.count_active.return_value = 0
        mock_assignment_repository.count_all.return_value = 0

        # Act
        statistics_service.get_dashboard_stats()

        # Assert
        mock_vehicle_repository.count_by_status.assert_called_once()
        mock_driver_repository.count_by_status.assert_called_once()
        mock_assignment_repository.count_active.assert_called_once()
        mock_assignment_repository.count_all.assert_called_once()

    def test_handles_empty_counts(
        self,
        statistics_service,
        mock_vehicle_repository,
        mock_driver_repository,
        mock_assignment_repository,
    ):
        """Handles empty/zero counts gracefully."""
        # Arrange
        mock_vehicle_repository.count_by_status.return_value = {}
        mock_driver_repository.count_by_status.return_value = {}
        mock_assignment_repository.count_active.return_value = 0
        mock_assignment_repository.count_all.return_value = 0

        # Act
        result = statistics_service.get_dashboard_stats()

        # Assert
        assert result["vehicle_count_by_status"] == {}
        assert result["driver_count_by_status"] == {}
        assert result["active_assignments_count"] == 0
        assert result["total_assignments_count"] == 0


class TestGetVehicleStats:
    """Tests for get_vehicle_stats method."""

    def test_returns_vehicle_counts(
        self,
        statistics_service,
        mock_vehicle_repository,
    ):
        """Returns vehicle counts by status."""
        # Arrange
        expected = {"active": 5, "inactive": 3}
        mock_vehicle_repository.count_by_status.return_value = expected

        # Act
        result = statistics_service.get_vehicle_stats()

        # Assert
        assert result == expected


class TestGetDriverStats:
    """Tests for get_driver_stats method."""

    def test_returns_driver_counts(
        self,
        statistics_service,
        mock_driver_repository,
    ):
        """Returns driver counts by status."""
        # Arrange
        expected = {"active": 10, "suspended": 2}
        mock_driver_repository.count_by_status.return_value = expected

        # Act
        result = statistics_service.get_driver_stats()

        # Assert
        assert result == expected


class TestGetAssignmentStats:
    """Tests for get_assignment_stats method."""

    def test_returns_assignment_counts(
        self,
        statistics_service,
        mock_assignment_repository,
    ):
        """Returns assignment active and total counts."""
        # Arrange
        mock_assignment_repository.count_active.return_value = 5
        mock_assignment_repository.count_all.return_value = 50

        # Act
        result = statistics_service.get_assignment_stats()

        # Assert
        assert result == {"active": 5, "total": 50}
