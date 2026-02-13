"""
Statistics service for aggregated dashboard data.

Provides combined statistics from all domains.
"""

from typing import Dict

from app.infrastructure.repositories.assignment_repository import AssignmentRepository
from app.infrastructure.repositories.driver_repository import DriverRepository
from app.infrastructure.repositories.vehicle_repository import VehicleRepository


class StatisticsService:
    """
    Service for gathering aggregated statistics across domains.

    Combines data from vehicle, driver, and assignment repositories.
    """

    def __init__(
        self,
        vehicle_repository: VehicleRepository,
        driver_repository: DriverRepository,
        assignment_repository: AssignmentRepository,
    ) -> None:
        """
        Initialize the service with required repositories.

        Args:
            vehicle_repository: Repository for vehicle data access.
            driver_repository: Repository for driver data access.
            assignment_repository: Repository for assignment data access.
        """
        self._vehicle_repository = vehicle_repository
        self._driver_repository = driver_repository
        self._assignment_repository = assignment_repository

    def get_dashboard_stats(self) -> Dict:
        """
        Get all dashboard statistics.

        Returns:
            Dictionary containing all statistics:
            - vehicle_count_by_status: Dict of status -> count
            - driver_count_by_status: Dict of status -> count
            - active_assignments_count: Number of active assignments
            - total_assignments_count: Total number of assignments
        """
        vehicle_counts = self._vehicle_repository.count_by_status()
        driver_counts = self._driver_repository.count_by_status()
        active_assignments = self._assignment_repository.count_active()
        total_assignments = self._assignment_repository.count_all()

        return {
            "vehicle_count_by_status": vehicle_counts,
            "driver_count_by_status": driver_counts,
            "active_assignments_count": active_assignments,
            "total_assignments_count": total_assignments,
        }

    def get_vehicle_stats(self) -> Dict[str, int]:
        """
        Get vehicle statistics by status.

        Returns:
            Dictionary of status -> count.
        """
        return self._vehicle_repository.count_by_status()

    def get_driver_stats(self) -> Dict[str, int]:
        """
        Get driver statistics by status.

        Returns:
            Dictionary of status -> count.
        """
        return self._driver_repository.count_by_status()

    def get_assignment_stats(self) -> Dict[str, int]:
        """
        Get assignment statistics.

        Returns:
            Dictionary with 'active' and 'total' counts.
        """
        return {
            "active": self._assignment_repository.count_active(),
            "total": self._assignment_repository.count_all(),
        }
