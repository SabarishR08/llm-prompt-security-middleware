"""
Error Handling and Custom Exceptions
Centralized error management for better debugging and user experience.
"""
from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class BaseAPIException(HTTPException):
    """Base exception for all API errors."""
    
    def __init__(
        self,
        detail: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        headers: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class AuthenticationError(BaseAPIException):
    """Raised when authentication fails."""
    
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Bearer"},
        )


class AuthorizationError(BaseAPIException):
    """Raised when user lacks required permissions."""
    
    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_403_FORBIDDEN,
        )


class ValidationError(BaseAPIException):
    """Raised when input validation fails."""
    
    def __init__(self, detail: str = "Validation error"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


class ResourceNotFoundError(BaseAPIException):
    """Raised when requested resource is not found."""
    
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_404_NOT_FOUND,
        )


class RateLimitError(BaseAPIException):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, detail: str = "Rate limit exceeded"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            headers={"Retry-After": "60"},
        )


class SecurityError(BaseAPIException):
    """Raised when security violation is detected."""
    
    def __init__(self, detail: str = "Security violation detected"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_403_FORBIDDEN,
        )


class ServiceUnavailableError(BaseAPIException):
    """Raised when external service is unavailable."""
    
    def __init__(self, detail: str = "Service temporarily unavailable"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


class DatabaseError(BaseAPIException):
    """Raised when database operation fails."""
    
    def __init__(self, detail: str = "Database error occurred"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class ConfigurationError(Exception):
    """Raised when configuration is invalid."""
    pass


# Error response builder
def build_error_response(
    error: Exception,
    request_id: Optional[str] = None,
    include_stack_trace: bool = False,
) -> Dict[str, Any]:
    """
    Build standardized error response.
    
    Args:
        error: Exception instance
        request_id: Request identifier for tracking
        include_stack_trace: Include stack trace in response (dev only)
    
    Returns:
        Standardized error response dictionary
    """
    import traceback
    
    response = {
        "error": {
            "type": type(error).__name__,
            "message": str(error),
        }
    }
    
    if request_id:
        response["request_id"] = request_id
    
    if include_stack_trace:
        response["error"]["stack_trace"] = traceback.format_exc()
    
    return response
