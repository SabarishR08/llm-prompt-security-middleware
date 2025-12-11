"""
Request ID Middleware
Adds unique request ID for tracing and debugging.
"""
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add unique request ID to all requests."""
    
    async def dispatch(self, request: Request, call_next):
        """Add request ID to request and response."""
        # Generate or retrieve request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        
        # Add to request state
        request.state.request_id = request_id
        
        # Process request
        response = await call_next(request)
        
        # Add to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response
