"""
Structured JSON logging module with request_id and correlation_id support.

Provides consistent logging format across the application.
"""

import json
import logging
import sys
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, Dict, Optional

# Context variables for request tracking
request_id_ctx: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
correlation_id_ctx: ContextVar[Optional[str]] = ContextVar(
    "correlation_id", default=None
)


def generate_request_id() -> str:
    """
    Generate a unique request ID.

    Returns:
        A unique request ID string prefixed with 'req_'.
    """
    return f"req_{uuid.uuid4().hex[:12]}"


def generate_correlation_id() -> str:
    """
    Generate a unique correlation ID.

    Returns:
        A unique correlation ID string prefixed with 'corr_'.
    """
    return f"corr_{uuid.uuid4().hex[:12]}"


def get_request_id() -> Optional[str]:
    """
    Get the current request ID from context.

    Returns:
        The current request ID or None.
    """
    return request_id_ctx.get()


def get_correlation_id() -> Optional[str]:
    """
    Get the current correlation ID from context.

    Returns:
        The current correlation ID or None.
    """
    return correlation_id_ctx.get()


def set_request_context(
    request_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
) -> None:
    """
    Set request context variables.

    Args:
        request_id: The request ID to set (generates new if None).
        correlation_id: The correlation ID to set (generates new if None).
    """
    request_id_ctx.set(request_id or generate_request_id())
    correlation_id_ctx.set(correlation_id or generate_correlation_id())


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """
        Format the log record as JSON.

        Args:
            record: The log record to format.

        Returns:
            JSON-formatted log string.
        """
        log_data: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": get_request_id(),
            "correlation_id": get_correlation_id(),
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)

        return json.dumps(log_data)


def setup_logging(log_level: str = "INFO") -> None:
    """
    Configure application logging with JSON format.

    Args:
        log_level: The logging level (DEBUG, INFO, WARNING, ERROR).
    """
    # Remove existing handlers
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create console handler with JSON formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(JSONFormatter())

    # Configure root logger
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    root_logger.addHandler(console_handler)

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.

    Args:
        name: The logger name (typically __name__).

    Returns:
        A configured logger instance.
    """
    return logging.getLogger(name)
