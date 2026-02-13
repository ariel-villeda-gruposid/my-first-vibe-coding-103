"""
Health check endpoint for the Fleet Management API.

Provides system health status for monitoring and load balancers.
"""

from app.api.responses import HealthResponse, SuccessResponse
from app.core.config import get_settings
from app.core.logging import get_logger
from fastapi import APIRouter, status
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

router = APIRouter()
logger = get_logger(__name__)


@router.get(
    "/health",
    response_model=SuccessResponse[HealthResponse],
    status_code=status.HTTP_200_OK,
    summary="Health Check",
    description="Check the health status of the API and its dependencies.",
)
def health_check() -> SuccessResponse[HealthResponse]:
    """
    Perform a health check of the API.

    Returns:
        SuccessResponse containing health status information.
    """
    settings = get_settings()
    db_status = "healthy"

    # Check MongoDB connection
    try:
        client = MongoClient(settings.MONGODB_URI, serverSelectionTimeoutMS=2000)
        client.admin.command("ping")
        client.close()
    except ConnectionFailure:
        db_status = "unhealthy"
        logger.warning("MongoDB connection failed during health check")

    health_data = HealthResponse(
        status="healthy" if db_status == "healthy" else "degraded",
        version="1.0.0",
        database=db_status,
    )

    return SuccessResponse(data=health_data)
