"""
Custom exception classes for the Fleet Management API.

All custom exceptions inherit from AppException to enable consistent error handling.
"""

from typing import Any, Dict, List, Optional


class AppException(Exception):
    """
    Base exception for all application errors.

    Attributes:
        code: Error code in UPPER_SNAKE_CASE format.
        message: Human-readable error message.
        status_code: HTTP status code to return.
        details: Optional field-level error details.
    """

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, List[Dict[str, str]]]] = None,
    ) -> None:
        """
        Initialize the AppException.

        Args:
            code: Error code in UPPER_SNAKE_CASE format.
            message: Human-readable error message.
            status_code: HTTP status code to return.
            details: Optional field-level error details for validation errors.
        """
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert exception to dictionary for JSON response.

        Returns:
            Dictionary representation of the error.
        """
        error_dict: Dict[str, Any] = {
            "code": self.code,
            "message": self.message,
        }
        if self.details:
            error_dict["details"] = self.details
        return error_dict


class NotFoundException(AppException):
    """Exception raised when a requested resource is not found."""

    def __init__(
        self,
        code: str = "RESOURCE_NOT_FOUND",
        message: str = "The requested resource was not found.",
    ) -> None:
        """
        Initialize NotFoundException.

        Args:
            code: Error code (default: RESOURCE_NOT_FOUND).
            message: Human-readable error message.
        """
        super().__init__(code=code, message=message, status_code=404)


class ConflictException(AppException):
    """Exception raised when a business rule conflict occurs."""

    def __init__(
        self,
        code: str = "CONFLICT",
        message: str = "A conflict occurred with the current state.",
    ) -> None:
        """
        Initialize ConflictException.

        Args:
            code: Error code (default: CONFLICT).
            message: Human-readable error message.
        """
        super().__init__(code=code, message=message, status_code=409)


class ValidationException(AppException):
    """Exception raised when request validation fails."""

    def __init__(
        self,
        code: str = "VALIDATION_ERROR",
        message: str = "Validation failed.",
        details: Optional[Dict[str, List[Dict[str, str]]]] = None,
    ) -> None:
        """
        Initialize ValidationException.

        Args:
            code: Error code (default: VALIDATION_ERROR).
            message: Human-readable error message.
            details: Field-level validation error details.
        """
        super().__init__(code=code, message=message, status_code=422, details=details)


class ConcurrencyException(AppException):
    """Exception raised when an ETag/If-Match concurrency conflict occurs."""

    def __init__(
        self,
        code: str = "CONCURRENCY_CONFLICT",
        message: str = "The resource has been modified. Please refresh and try again.",
    ) -> None:
        """
        Initialize ConcurrencyException.

        Args:
            code: Error code (default: CONCURRENCY_CONFLICT).
            message: Human-readable error message.
        """
        super().__init__(code=code, message=message, status_code=412)
