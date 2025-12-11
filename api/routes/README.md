# API Routes Documentation

## Analysis Router (`analysis_router.py`)

**Endpoint:** `POST /api/analysis/analyze`

**Purpose:** Main analysis endpoint accepting user prompts

**Responsibility:**
- Validates incoming prompt with `PromptAnalysisRequest` schema
- Authenticates user via JWT token
- Orchestrates compliance engine (PII → Toxicity → Injection → Profanity)
- Calls threat intelligence services in parallel
- Makes decision (PASS/FAIL/FLAG)
- Sends safe prompts to Gemini for response
- Logs everything to SQLite with audit trail
- Returns `AnalysisResponse` with result and metadata

**Request Example:**
```json
{
  "prompt": "What is the weather today?"
}
```

**Response Example:**
```json
{
  "status": "PASS",
  "pii_detected": false,
  "toxicity_score": 0.02,
  "injection_detected": false,
  "gemini_response": "The current weather is...",
  "analysis_id": "uuid-here"
}
```

---

## Authentication Router (`auth_router.py`)

**Endpoint:** `POST /api/auth/login`

**Purpose:** User authentication and token generation

**Responsibility:**
- Validates username/password against user database
- Generates JWT token with role claim
- Returns access token (expires in 24 hours)
- Logs authentication attempts

**Request Example:**
```json
{
  "username": "admin",
  "password": "secure_password"
}
```

**Response Example:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 86400,
  "role": "admin"
}
```

---

## Logs Router (`logs_router.py`)

**Endpoint:** `GET /api/logs`

**Purpose:** Retrieve audit logs with RBAC protection

**Responsibility:**
- Checks user role (Admin/Moderator only)
- Filters logs by: `user_id`, `severity`, `date_range`, `threat_type`
- Returns paginated results
- Exports to CSV/JSON format
- Compliance-ready for regulatory audits

**Query Parameters:**
- `user_id` (optional): Filter by user
- `severity` (optional): low, medium, high, critical
- `start_date` (optional): ISO 8601 date
- `end_date` (optional): ISO 8601 date
- `limit` (optional): Default 50, max 1000
- `offset` (optional): For pagination

**Response Example:**
```json
{
  "total": 1234,
  "logs": [
    {
      "id": 1,
      "timestamp": "2025-12-11T10:30:00Z",
      "user_id": "user123",
      "prompt": "...",
      "status": "BLOCKED",
      "reason": "PII detected"
    }
  ]
}
```

---

## Dashboard Router (`dashboard_router.py`)

**Purpose:** Real-time security metrics and analytics

### Endpoints:

#### `GET /api/dashboard/metrics`
Overall statistics (total requests, blocked, flagged, etc.)

**Response Example:**
```json
{
  "total_requests": 10000,
  "blocked": 250,
  "flagged": 75,
  "passed": 9675,
  "block_rate": 2.5
}
```

#### `GET /api/dashboard/threats`
Threat breakdown by type

**Response Example:**
```json
{
  "pii_detections": 120,
  "toxicity_blocks": 80,
  "injection_attempts": 30,
  "profanity": 20
}
```

#### `GET /api/dashboard/trends`
Time-series data

---

## Health Router (`health_router.py`)

**Purpose:** Health check and liveness probes

### Endpoints:

#### `GET /api/health`
Full health check (database, services, dependencies)

**Response Example:**
```json
{
  "status": "healthy",
  "timestamp": "2025-12-11T10:30:00Z",
  "checks": {
    "database": "ok",
    "gemini_api": "ok",
    "threat_intel": "ok"
  }
}
```

#### `GET /api/liveness`
Kubernetes liveness probe (simple ping)

**Response:** `200 OK` with `{"status": "alive"}`

#### `GET /api/readiness`
Kubernetes readiness probe (checks if ready to serve traffic)

**Response:** `200 OK` if ready, `503` if not ready
