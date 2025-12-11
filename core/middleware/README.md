# HTTP Middleware

FastAPI middleware for security, monitoring, and request handling.

## Middleware Stack

Middleware is applied in this order (top to bottom):

```
1. RequestIDMiddleware      → UUID tracking
2. PerformanceMiddleware    → Latency monitoring
3. SecurityHeadersMiddleware → Security headers
4. RateLimitMiddleware      → Rate limiting
5. CORSMiddleware           → Cross-origin control
```

---

## Rate Limit Middleware (`rate_limit.py`)

**Purpose:** Prevent abuse by limiting requests per IP

**Configuration:**
- **Limit:** 100 requests per 60 seconds per IP
- **Storage:** In-memory (Redis in production)
- **Response:** HTTP 429 Too Many Requests

**Features:**
- Per-IP tracking
- Sliding window algorithm
- Configurable limits per endpoint

**Response on limit:**
```json
{
  "error": "Rate limit exceeded",
  "retry_after": 45,
  "limit": 100,
  "window": 60
}
```

**Usage:**
```python
from core.middleware.rate_limit import RateLimitMiddleware

app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=100
)
```

---

## Request ID Middleware (`request_id.py`)

**Purpose:** Distributed tracing and request correlation

**Features:**
- Generates UUID for each request
- Adds `X-Request-ID` header to response
- Logs request ID with all events
- Useful for debugging and tracing

**Header:** `X-Request-ID: 550e8400-e29b-41d4-a716-446655440000`

**Usage in logs:**
```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Request processed",
  "duration_ms": 45
}
```

---

## Security Headers Middleware (`security_headers.py`)

**Purpose:** Add security headers to all responses

**Headers Added:**
- `Strict-Transport-Security` (HSTS): Forces HTTPS
- `Content-Security-Policy` (CSP): Prevents XSS
- `X-Frame-Options`: Prevents clickjacking
- `X-Content-Type-Options`: Prevents MIME sniffing
- `X-XSS-Protection`: Browser XSS filter
- `Referrer-Policy`: Controls referrer information

**Example Headers:**
```
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'self'
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
```

---

## Performance Middleware (`performance.py`)

**Purpose:** Monitor request performance and export metrics

**Metrics Tracked:**
- Request duration (milliseconds)
- Status codes (2xx, 4xx, 5xx)
- Endpoint performance
- Throughput (req/s)

**Metrics Export:**
- Prometheus format (`/metrics` endpoint)
- JSON logs
- Console output (dev mode)

**Example Metrics:**
```
http_request_duration_ms{method="POST",endpoint="/api/analyze",status="200"} 45.2
http_requests_total{method="POST",endpoint="/api/analyze",status="200"} 1234
```

**Usage:**
```python
from core.middleware.performance import PerformanceMiddleware

app.add_middleware(PerformanceMiddleware)
```

---

## Middleware Configuration

In `main.py`:

```python
from fastapi import FastAPI
from core.middleware.rate_limit import RateLimitMiddleware
from core.middleware.request_id import RequestIDMiddleware
from core.middleware.security_headers import SecurityHeadersMiddleware
from core.middleware.performance import PerformanceMiddleware

app = FastAPI()

# Add middleware (order matters!)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(PerformanceMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware, requests_per_minute=100)
```
