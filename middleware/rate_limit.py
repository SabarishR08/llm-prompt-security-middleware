"""
Rate Limiting Middleware
Protects API endpoints from abuse and DDoS attacks.
"""
import time
from typing import Dict, Optional
from collections import defaultdict
from threading import Lock
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """Thread-safe rate limiter using sliding window algorithm."""
    
    def __init__(self, requests: int = 100, window: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            requests: Maximum requests allowed per window
            window: Time window in seconds
        """
        self.requests = requests
        self.window = window
        self.clients: Dict[str, list] = defaultdict(list)
        self.lock = Lock()
    
    def is_allowed(self, client_id: str) -> tuple[bool, Optional[int]]:
        """
        Check if request is allowed.
        
        Args:
            client_id: Unique client identifier (IP address)
        
        Returns:
            Tuple of (allowed, retry_after_seconds)
        """
        now = time.time()
        
        with self.lock:
            # Remove expired timestamps
            self.clients[client_id] = [
                ts for ts in self.clients[client_id]
                if now - ts < self.window
            ]
            
            # Check if limit exceeded
            if len(self.clients[client_id]) >= self.requests:
                oldest = self.clients[client_id][0]
                retry_after = int(self.window - (now - oldest)) + 1
                return False, retry_after
            
            # Add current timestamp
            self.clients[client_id].append(now)
            return True, None
    
    def cleanup(self):
        """Remove expired entries to free memory."""
        now = time.time()
        
        with self.lock:
            expired_clients = []
            for client_id, timestamps in self.clients.items():
                # Remove old timestamps
                valid_timestamps = [
                    ts for ts in timestamps
                    if now - ts < self.window
                ]
                
                if not valid_timestamps:
                    expired_clients.append(client_id)
                else:
                    self.clients[client_id] = valid_timestamps
            
            # Remove completely expired clients
            for client_id in expired_clients:
                del self.clients[client_id]


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting API requests."""
    
    def __init__(
        self,
        app,
        requests: int = 100,
        window: int = 60,
        enabled: bool = True,
    ):
        """
        Initialize rate limit middleware.
        
        Args:
            app: FastAPI application
            requests: Max requests per window
            window: Time window in seconds
            enabled: Enable/disable rate limiting
        """
        super().__init__(app)
        self.limiter = RateLimiter(requests=requests, window=window)
        self.enabled = enabled
        self.excluded_paths = {"/health", "/docs", "/redoc", "/openapi.json"}
    
    async def dispatch(self, request: Request, call_next):
        """Process request through rate limiter."""
        # Skip if disabled or excluded path
        if not self.enabled or request.url.path in self.excluded_paths:
            return await call_next(request)
        
        # Get client identifier (IP address)
        client_ip = request.client.host if request.client else "unknown"
        
        # Check rate limit
        allowed, retry_after = self.limiter.is_allowed(client_ip)
        
        if not allowed:
            logger.warning(
                f"Rate limit exceeded for {client_ip} - "
                f"retry after {retry_after}s"
            )
            
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "retry_after": retry_after,
                },
                headers={"Retry-After": str(retry_after)},
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.limiter.requests)
        response.headers["X-RateLimit-Window"] = str(self.limiter.window)
        
        return response
