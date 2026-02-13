"""
API v1 router aggregation.

Combines all endpoint routers for API version 1.
"""

from app.api.v1.endpoints import assignments, drivers, health, statistics, vehicles
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1")

# Include endpoint routers
router.include_router(health.router, tags=["Health"])
router.include_router(vehicles.router)
router.include_router(drivers.router)
router.include_router(assignments.router)
router.include_router(statistics.router, tags=["Statistics"])
