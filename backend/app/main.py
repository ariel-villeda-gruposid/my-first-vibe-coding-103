"""
Fleet Management API - Main Application Entry Point.

This module configures and creates the FastAPI application instance.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from app.api.responses import ErrorBody, ErrorDetail, ErrorResponse, Meta
from app.api.v1.router import router as api_v1_router
from app.core.config import get_settings
from app.core.exceptions import AppException
from app.core.logging import get_logger, set_request_context, setup_logging
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.

    Handles startup and shutdown events.

    Args:
        app: The FastAPI application instance.

    Yields:
        None
    """
    # Startup
    settings = get_settings()
    setup_logging(settings.LOG_LEVEL)
    logger.info("Fleet Management API starting up")

    yield

    # Shutdown
    logger.info("Fleet Management API shutting down")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance.
    """
    settings = get_settings()

    app = FastAPI(
        title="Fleet Management API",
        description="RESTful API for managing fleet vehicles, drivers, and assignments.",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request context middleware
    @app.middleware("http")
    async def request_context_middleware(request: Request, call_next):
        """Add request_id and correlation_id to each request context."""
        # Get correlation_id from header or generate new one
        correlation_id = request.headers.get("X-Correlation-ID")
        set_request_context(correlation_id=correlation_id)

        response = await call_next(request)

        # Add tracking headers to response
        from app.core.logging import get_correlation_id, get_request_id

        response.headers["X-Request-ID"] = get_request_id() or ""
        response.headers["X-Correlation-ID"] = get_correlation_id() or ""

        return response

    # Exception handlers
    @app.exception_handler(AppException)
    async def app_exception_handler(
        request: Request, exc: AppException
    ) -> JSONResponse:
        """Handle custom application exceptions."""
        logger.warning(f"AppException: {exc.code} - {exc.message}")

        error_response = ErrorResponse(
            error=ErrorBody(
                code=exc.code,
                message=exc.message,
                details=exc.details,
            ),
            meta=Meta(),
        )

        return JSONResponse(
            status_code=exc.status_code,
            content=error_response.model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Handle Pydantic validation errors."""
        details = {}

        for error in exc.errors():
            field = ".".join(str(loc) for loc in error["loc"] if loc != "body")
            if field not in details:
                details[field] = []
            details[field].append(
                ErrorDetail(
                    code=error["type"].upper().replace(".", "_"),
                    message=error["msg"],
                ).model_dump()
            )

        error_response = ErrorResponse(
            error=ErrorBody(
                code="VALIDATION_ERROR",
                message="Request validation failed.",
                details=details if details else None,
            ),
            meta=Meta(),
        )

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_response.model_dump(),
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Handle unexpected exceptions."""
        logger.exception(f"Unhandled exception: {exc}")

        error_response = ErrorResponse(
            error=ErrorBody(
                code="INTERNAL_SERVER_ERROR",
                message="An unexpected error occurred.",
            ),
            meta=Meta(),
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response.model_dump(),
        )

    # Include routers
    app.include_router(api_v1_router)

    return app


# Create application instance
app = create_app()
