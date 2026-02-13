"""
Statistics endpoint for the Fleet Management API.

Provides aggregated statistics across all domains.
"""

from app.api.responses import SuccessResponse
from app.api.v1.schemas.statistics import DashboardStats
from app.core.dependencies import DatabaseDep
from app.core.logging import get_logger
from app.domain.services.statistics_service import StatisticsService
from app.infrastructure.repositories.assignment_repository import AssignmentRepository
from app.infrastructure.repositories.driver_repository import DriverRepository
from app.infrastructure.repositories.vehicle_repository import VehicleRepository
from fastapi import APIRouter, status

router = APIRouter()
logger = get_logger(__name__)


def get_statistics_service(db: DatabaseDep) -> StatisticsService:
    """
    Create a StatisticsService instance with all required repositories.

    Args:
        db: Database dependency.

    Returns:
        StatisticsService instance.
    """
    vehicle_repo = VehicleRepository(db)
    driver_repo = DriverRepository(db)
    assignment_repo = AssignmentRepository(db)
    return StatisticsService(vehicle_repo, driver_repo, assignment_repo)


@router.get(
    "/stats",
    response_model=SuccessResponse[DashboardStats],
    status_code=status.HTTP_200_OK,
    summary="Get Dashboard Statistics",
    description="Get aggregated statistics for the dashboard.",
)
def get_dashboard_stats(db: DatabaseDep) -> SuccessResponse[DashboardStats]:
    """
    Get aggregated dashboard statistics.

    Returns statistics including:
    - Vehicle counts by status
    - Driver counts by status
    - Active assignments count
    - Total assignments count

    Args:
        db: Database connection.

    Returns:
        SuccessResponse containing dashboard statistics.
    """
    service = get_statistics_service(db)
    stats = service.get_dashboard_stats()

    logger.info(
        "Dashboard stats retrieved",
        extra={
            "active_vehicles": stats["vehicle_count_by_status"].get("active", 0),
            "active_drivers": stats["driver_count_by_status"].get("active", 0),
            "active_assignments": stats["active_assignments_count"],
        },
    )

    return SuccessResponse(data=DashboardStats(**stats))
