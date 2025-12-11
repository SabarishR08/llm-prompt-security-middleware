"""
Performance Monitoring Middleware
Tracks request latency and performance metrics.
"""
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)


class PerformanceMiddleware(BaseHTTPMiddleware):
    """Middleware to monitor request performance."""
    
    def __init__(self, app, slow_request_threshold: float = 1.0):
        """
        Initialize performance middleware.
        
        Args:
            app: FastAPI application
            slow_request_threshold: Log warning if request takes longer (seconds)
        """
        super().__init__(app)
        self.slow_request_threshold = slow_request_threshold
    
    async def dispatch(self, request: Request, call_next):
        """Track request timing and log slow requests."""
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Add performance headers
        response.headers["X-Process-Time"] = f"{duration:.3f}"
        
        # Log slow requests
        if duration > self.slow_request_threshold:
            logger.warning(
                f"Slow request detected: {request.method} {request.url.path} "
                f"took {duration:.3f}s"
            )
        
        # Log all requests in debug mode
        logger.debug(
            f"{request.method} {request.url.path} "
            f"completed in {duration:.3f}s - {response.status_code}"
        )
        
        return response
