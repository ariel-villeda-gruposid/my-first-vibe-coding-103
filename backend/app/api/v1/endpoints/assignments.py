"""
Assignment API endpoints.

REST API endpoints for managing assignments.
"""

from typing import Annotated, Optional

from app.api.v1.schemas.assignment import (
    AssignmentCreate,
    AssignmentListResponse,
    AssignmentResponse,
    AssignmentUpdate,
)
from app.core.dependencies import DatabaseDep
from app.core.logging import get_logger
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
from app.infrastructure.repositories.assignment_repository import AssignmentRepository
from app.infrastructure.repositories.driver_repository import DriverRepository
from app.infrastructure.repositories.vehicle_repository import VehicleRepository
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/assignments", tags=["Assignments"])
logger = get_logger(__name__)


def get_assignment_service(db: DatabaseDep) -> AssignmentService:
    """
    Dependency to get assignment service.

    Args:
        db: MongoDB database instance.

    Returns:
        AssignmentService instance with repositories.
    """
    assignment_repo = AssignmentRepository(db)
    driver_repo = DriverRepository(db)
    vehicle_repo = VehicleRepository(db)
    return AssignmentService(assignment_repo, driver_repo, vehicle_repo)


AssignmentServiceDep = Annotated[AssignmentService, Depends(get_assignment_service)]


@router.get("", response_model=AssignmentListResponse)
def list_assignments(
    driver_id: Optional[str] = Query(None, description="Filter by driver ID"),
    vehicle_id: Optional[str] = Query(None, description="Filter by vehicle ID"),
    active_only: bool = Query(False, description="Only return active assignments"),
    limit: int = Query(50, ge=1, le=100, description="Maximum results"),
    skip: int = Query(0, ge=0, description="Results to skip"),
    sort_by: str = Query("start_datetime", description="Field to sort by"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order"),
    service: AssignmentService = Depends(get_assignment_service),
) -> AssignmentListResponse:
    """
    List all assignments with optional filtering.

    - **driver_id**: Filter by driver
    - **vehicle_id**: Filter by vehicle
    - **active_only**: Only return active assignments
    - **limit**: Maximum results (1-100)
    - **skip**: Pagination offset
    - **sort_by**: Field to sort by
    - **sort_order**: 'asc' or 'desc'
    """
    assignments, total = service.list_assignments(
        driver_id=driver_id,
        vehicle_id=vehicle_id,
        active_only=active_only,
        limit=limit,
        skip=skip,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    return AssignmentListResponse(
        items=[AssignmentResponse.model_validate(a.__dict__) for a in assignments],
        total=total,
        limit=limit,
        skip=skip,
    )


@router.get("/active", response_model=AssignmentListResponse)
def list_active_assignments(
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0),
    service: AssignmentService = Depends(get_assignment_service),
) -> AssignmentListResponse:
    """List only active assignments."""
    assignments, total = service.list_assignments(
        active_only=True,
        limit=limit,
        skip=skip,
    )

    return AssignmentListResponse(
        items=[AssignmentResponse.model_validate(a.__dict__) for a in assignments],
        total=total,
        limit=limit,
        skip=skip,
    )


@router.get("/stats")
def get_assignment_stats(
    service: AssignmentService = Depends(get_assignment_service),
) -> dict:
    """Get assignment statistics."""
    return service.get_stats()


@router.get("/{assignment_id}", response_model=AssignmentResponse)
def get_assignment(
    assignment_id: str,
    service: AssignmentService = Depends(get_assignment_service),
) -> JSONResponse:
    """
    Get an assignment by ID.

    Returns the assignment with ETag header for concurrency control.
    """
    try:
        assignment, etag = service.get_assignment(assignment_id)
        response_data = AssignmentResponse.model_validate(assignment.__dict__)
        return JSONResponse(
            content=response_data.model_dump(mode="json"),
            headers={"ETag": etag},
        )
    except AssignmentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/driver/{driver_id}/active", response_model=Optional[AssignmentResponse])
def get_active_assignment_for_driver(
    driver_id: str,
    service: AssignmentService = Depends(get_assignment_service),
) -> Optional[AssignmentResponse]:
    """Get the active assignment for a specific driver."""
    assignment = service.get_active_assignment_for_driver(driver_id)
    if assignment is None:
        return None
    return AssignmentResponse.model_validate(assignment.__dict__)


@router.get("/vehicle/{vehicle_id}/active", response_model=Optional[AssignmentResponse])
def get_active_assignment_for_vehicle(
    vehicle_id: str,
    service: AssignmentService = Depends(get_assignment_service),
) -> Optional[AssignmentResponse]:
    """Get the active assignment for a specific vehicle."""
    assignment = service.get_active_assignment_for_vehicle(vehicle_id)
    if assignment is None:
        return None
    return AssignmentResponse.model_validate(assignment.__dict__)


@router.post("", response_model=AssignmentResponse, status_code=status.HTTP_201_CREATED)
def create_assignment(
    data: AssignmentCreate,
    service: AssignmentService = Depends(get_assignment_service),
) -> JSONResponse:
    """
    Create a new assignment.

    Validates:
    - Driver exists and is active
    - Vehicle exists and is available
    - No overlapping assignments for driver or vehicle
    """
    try:
        assignment, etag = service.create_assignment(data)
        response_data = AssignmentResponse.model_validate(assignment.__dict__)
        return JSONResponse(
            content=response_data.model_dump(mode="json"),
            status_code=status.HTTP_201_CREATED,
            headers={"ETag": etag},
        )
    except DriverNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "driver_not_found", "message": str(e)},
        )
    except VehicleNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "vehicle_not_found", "message": str(e)},
        )
    except DriverNotActiveError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "driver_not_active", "message": str(e)},
        )
    except VehicleNotAvailableError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "vehicle_not_available", "message": str(e)},
        )
    except DriverAlreadyAssignedError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "driver_already_assigned", "message": str(e)},
        )
    except VehicleAlreadyAssignedError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "vehicle_already_assigned", "message": str(e)},
        )
    except OverlappingAssignmentError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "overlapping_assignment", "message": str(e)},
        )


@router.patch("/{assignment_id}", response_model=AssignmentResponse)
def update_assignment(
    assignment_id: str,
    data: AssignmentUpdate,
    if_match: Optional[str] = Header(None, alias="If-Match"),
    service: AssignmentService = Depends(get_assignment_service),
) -> JSONResponse:
    """
    Update an assignment (partial update).

    Can update: notes, end_datetime, start_datetime (if not started).
    Uses ETag for optimistic concurrency (If-Match header).
    """
    try:
        assignment, etag = service.update_assignment(assignment_id, data, if_match)
        response_data = AssignmentResponse.model_validate(assignment.__dict__)
        return JSONResponse(
            content=response_data.model_dump(mode="json"),
            headers={"ETag": etag},
        )
    except AssignmentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ETagMismatchError:
        raise HTTPException(
            status_code=status.HTTP_412_PRECONDITION_FAILED,
            detail="Resource has been modified. Please refresh and try again.",
        )
    except AssignmentUpdateError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "update_error", "message": str(e)},
        )
    except OverlappingAssignmentError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"error": "overlapping_assignment", "message": str(e)},
        )


@router.post("/{assignment_id}/close", response_model=AssignmentResponse)
def close_assignment(
    assignment_id: str,
    if_match: Optional[str] = Header(None, alias="If-Match"),
    service: AssignmentService = Depends(get_assignment_service),
) -> JSONResponse:
    """
    Close an assignment (set end_datetime to now).

    Uses ETag for optimistic concurrency.
    """
    try:
        assignment, etag = service.close_assignment(assignment_id, if_match)
        response_data = AssignmentResponse.model_validate(assignment.__dict__)
        return JSONResponse(
            content=response_data.model_dump(mode="json"),
            headers={"ETag": etag},
        )
    except AssignmentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ETagMismatchError:
        raise HTTPException(
            status_code=status.HTTP_412_PRECONDITION_FAILED,
            detail="Resource has been modified. Please refresh and try again.",
        )


@router.delete("/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_assignment(
    assignment_id: str,
    if_match: Optional[str] = Header(None, alias="If-Match"),
    service: AssignmentService = Depends(get_assignment_service),
) -> None:
    """
    Delete an assignment.

    For active assignments, this closes them (sets end_datetime).
    For inactive assignments, performs hard delete.
    Uses ETag for optimistic concurrency.
    """
    try:
        service.delete_assignment(assignment_id, if_match)
    except AssignmentNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ETagMismatchError:
        raise HTTPException(
            status_code=status.HTTP_412_PRECONDITION_FAILED,
            detail="Resource has been modified. Please refresh and try again.",
        )
