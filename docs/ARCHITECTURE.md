# 🏗️ System Architecture

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                           EXTERNAL CLIENTS                          │
│                    (Web Browsers, Mobile Apps, APIs)                │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 │ HTTPS (TLS 1.2+)
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         NGINX REVERSE PROXY                         │
│  ┌────────────────┐  ┌─────────────────┐  ┌────────────────────┐  │
│  │ SSL Termination│  │  Rate Limiting  │  │  Load Balancing    │  │
│  │   (Let's       │  │  (10 req/s)     │  │  (Round Robin)     │  │
│  │   Encrypt)     │  │                 │  │                    │  │
│  └────────────────┘  └─────────────────┘  └────────────────────┘  │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      KUBERNETES INGRESS (Optional)                  │
│              cert-manager | External DNS | Path Routing             │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         KUBERNETES SERVICE                          │
│                    (ClusterIP - Internal Load Balancer)             │
└─────────┬───────────────────────┬───────────────────────┬───────────┘
          │                       │                       │
          ▼                       ▼                       ▼
┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐
│   APP POD 1      │   │   APP POD 2      │   │   APP POD 3      │
│  ┌────────────┐  │   │  ┌────────────┐  │   │  ┌────────────┐  │
│  │  Gunicorn  │  │   │  │  Gunicorn  │  │   │  │  Gunicorn  │  │
│  │  (4 workers)│ │   │  │  (4 workers)│ │   │  │  (4 workers)│ │
│  └─────┬──────┘  │   │  └─────┬──────┘  │   │  └─────┬──────┘  │
│        │         │   │        │         │   │        │         │
│  ┌─────▼──────┐  │   │  ┌─────▼──────┐  │   │  ┌─────▼──────┐  │
│  │  FASTAPI   │  │   │  │  FASTAPI   │  │   │  │  FASTAPI   │  │
│  │APPLICATION │  │   │  │APPLICATION │  │   │  │APPLICATION │  │
│  └────────────┘  │   │  └────────────┘  │   │  └────────────┘  │
└──────────────────┘   └──────────────────┘   └──────────────────┘
          │                       │                       │
          └───────────────────────┼───────────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
                    ▼                           ▼
         ┌──────────────────┐        ┌──────────────────┐
         │   PostgreSQL     │        │      Redis       │
         │   (Managed DB)   │        │   (Cache Layer)  │
         │                  │        │                  │
         │ - Logs Storage   │        │ - Session Cache  │
         │ - User Data      │        │ - Rate Limit     │
         │ - Analytics      │        │ - Threat Intel   │
         └──────────────────┘        └──────────────────┘
```

---

## Application Layer Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          FASTAPI APPLICATION                        │
├─────────────────────────────────────────────────────────────────────┤
│                         MIDDLEWARE STACK                            │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ 1. RequestIDMiddleware      → UUID tracking                  │  │
│  │ 2. PerformanceMiddleware    → Latency monitoring             │  │
│  │ 3. SecurityHeadersMiddleware → CSP, HSTS, X-Frame-Options    │  │
│  │ 4. RateLimitMiddleware      → 100 req/60s per IP             │  │
│  │ 5. CORSMiddleware           → Cross-origin control           │  │
│  └──────────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────────┤
│                            API ROUTES                               │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────────┐   │
│  │ Health Router  │  │  Auth Router   │  │ Analysis Router    │   │
│  │ /health/*      │  │  /api/auth/*   │  │ /api/analyze       │   │
│  │                │  │                │  │                    │   │
│  │ - /live        │  │ - /login       │  │ - Prompt analysis  │   │
│  │ - /ready       │  │ - /register    │  │ - PII detection    │   │
│  │ - /metrics     │  │ - /refresh     │  │ - Toxicity check   │   │
│  │ - /info        │  │ - /logout      │  │                    │   │
│  └────────────────┘  └────────────────┘  └────────────────────┘   │
│                                                                     │
│  ┌────────────────┐  ┌────────────────┐                           │
│  │  Logs Router   │  │Dashboard Router│                           │
│  │  /api/logs/*   │  │  /api/stats/*  │                           │
│  │                │  │                │                           │
│  │ - GET /logs    │  │ - /overview    │                           │
│  │ - POST /logs   │  │ - /timeseries  │                           │
│  │ - GET /logs/id │  │ - /pii-trends  │                           │
│  └────────────────┘  └────────────────┘                           │
├─────────────────────────────────────────────────────────────────────┤
│                          INPUT VALIDATION                           │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Pydantic Models:                                             │  │
│  │ - PromptRequest    → Prompt analysis validation              │  │
│  │ - LoginRequest     → Authentication validation               │  │
│  │ - PaginationParams → Query parameter validation              │  │
│  │ - DateRangeFilter  → Time filtering validation               │  │
│  └──────────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────────┤
│                          BUSINESS LOGIC                             │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────────┐   │
│  │ Gemini Service │  │ Prompt Inject. │  │  Threat Intel      │   │
│  │                │  │   Detector     │  │  Service           │   │
│  │ - AI Analysis  │  │                │  │                    │   │
│  │ - PII Detection│  │ - 6 Attack     │  │ - VirusTotal       │   │
│  │ - Toxicity     │  │   Patterns     │  │ - Safe Browsing    │   │
│  │                │  │ - Severity     │  │ - AbuseIPDB        │   │
│  └────────────────┘  └────────────────┘  └────────────────────┘   │
│                                                                     │
│  ┌────────────────┐  ┌────────────────┐                           │
│  │ Alerts Service │  │   Auth Utils   │                           │
│  │                │  │                │                           │
│  │ - Email (SMTP) │  │ - JWT Manager  │                           │
│  │ - Email (Grid) │  │ - bcrypt Hash  │                           │
│  │ - SMS (Twilio) │  │ - RBAC         │                           │
│  └────────────────┘  └────────────────┘                           │
├─────────────────────────────────────────────────────────────────────┤
│                        EXCEPTION HANDLING                           │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Custom Exceptions:                                           │  │
│  │ AuthenticationError (401) | AuthorizationError (403)         │  │
│  │ ValidationError (422)     | ResourceNotFoundError (404)      │  │
│  │ RateLimitError (429)      | SecurityError (400)              │  │
│  │ ServiceUnavailableError (503) | DatabaseError (500)          │  │
│  └──────────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────────┤
│                        CONFIGURATION LAYER                          │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Environment-Based Config:                                    │  │
│  │ - DevelopmentConfig → Debug mode, verbose logging            │  │
│  │ - ProductionConfig  → Optimized, secure defaults             │  │
│  │ - TestingConfig     → Isolated test environment              │  │
│  └──────────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────────┤
│                           LOGGING SYSTEM                            │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Structured JSON Logging:                                     │  │
│  │ - Request ID tracking                                        │  │
│  │ - User context (user_id, role)                               │  │
│  │ - Endpoint + method                                          │  │
│  │ - Log rotation (100MB max, 10 backups)                       │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Request Flow Diagram

```
┌─────────────┐
│   CLIENT    │
│  (Browser)  │
└──────┬──────┘
       │
       │ 1. HTTPS Request
       │    POST /api/analyze
       │    {"prompt": "Test with SSN: 123-45-6789"}
       ▼
┌──────────────────┐
│  NGINX/INGRESS   │
│                  │
│ ✓ SSL Termination│
│ ✓ Rate Check     │ ─────► [Rate Limit Exceeded?] ─────► 429 Response
│ ✓ Load Balance   │
└────────┬─────────┘
         │
         │ 2. Forward to Pod
         ▼
┌──────────────────────────────────────────────────────┐
│              FASTAPI POD (Middleware Stack)          │
│                                                      │
│  ┌────────────────────────────────────────────────┐ │
│  │ RequestIDMiddleware                            │ │
│  │ → Generates UUID: "req-abc123"                 │ │
│  │ → Adds to request context                      │ │
│  └──────────────────────┬─────────────────────────┘ │
│                         │                            │
│  ┌──────────────────────▼─────────────────────────┐ │
│  │ PerformanceMiddleware                          │ │
│  │ → Start timer                                  │ │
│  └──────────────────────┬─────────────────────────┘ │
│                         │                            │
│  ┌──────────────────────▼─────────────────────────┐ │
│  │ SecurityHeadersMiddleware                      │ │
│  │ → Queue security headers for response          │ │
│  └──────────────────────┬─────────────────────────┘ │
│                         │                            │
│  ┌──────────────────────▼─────────────────────────┐ │
│  │ RateLimitMiddleware                            │ │
│  │ → Check client IP request count                │ │
│  │ → Update sliding window                        │ │
│  └──────────────────────┬─────────────────────────┘ │
│                         │                            │
│  ┌──────────────────────▼─────────────────────────┐ │
│  │ CORSMiddleware                                 │ │
│  │ → Validate origin                              │ │
│  └──────────────────────┬─────────────────────────┘ │
└─────────────────────────┼──────────────────────────┘
                          │
                          │ 3. Route to Endpoint
                          ▼
                  ┌───────────────┐
                  │AnalysisRouter │
                  │ /api/analyze  │
                  └───────┬───────┘
                          │
                          │ 4. Validate Input
                          ▼
                  ┌───────────────┐
                  │ PromptRequest │
                  │  Pydantic     │
                  └───────┬───────┘
                          │
                          │ 5. Business Logic
                          ▼
         ┌────────────────────────────────┐
         │                                │
         ▼                                ▼
  ┌────────────┐                  ┌────────────────┐
  │  Gemini    │                  │ Prompt Inject. │
  │  Service   │                  │   Detector     │
  │            │                  │                │
  │ - PII      │                  │ - SQL Inject.  │
  │ - Toxicity │                  │ - XSS          │
  │ - Policy   │                  │ - Cmd Inject.  │
  └─────┬──────┘                  └────────┬───────┘
        │                                  │
        │ 6. Check Cache                   │
        ▼                                  │
  ┌────────────┐                           │
  │   Redis    │                           │
  │   Cache    │                           │
  └─────┬──────┘                           │
        │                                  │
        │ 7. Aggregate Results             │
        └──────────────┬───────────────────┘
                       │
                       │ 8. Store Log
                       ▼
                ┌──────────────┐
                │  PostgreSQL  │
                │              │
                │ - Insert log │
                │ - Analytics  │
                └──────┬───────┘
                       │
                       │ 9. Check Severity
                       ▼
                ┌──────────────┐
                │Alerts Service│ ─────► [High Severity?] ─────► Send Email/SMS
                └──────┬───────┘
                       │
                       │ 10. Build Response
                       ▼
         ┌─────────────────────────────┐
         │      JSON Response          │
         │ {                           │
         │   "is_injection": true,     │
         │   "severity": "high",       │
         │   "pii_detected": ["SSN"],  │
         │   "toxicity_score": 0.2,    │
         │   "timestamp": "..."        │
         │ }                           │
         └──────────────┬──────────────┘
                        │
         ┌──────────────▼──────────────┐
         │  PerformanceMiddleware      │
         │  → Calculate duration: 245ms│
         │  → Add X-Process-Time header│
         └──────────────┬──────────────┘
                        │
         ┌──────────────▼──────────────┐
         │  SecurityHeadersMiddleware  │
         │  → Add CSP, HSTS, X-Frame   │
         └──────────────┬──────────────┘
                        │
         ┌──────────────▼──────────────┐
         │   RequestIDMiddleware       │
         │   → Add X-Request-ID header │
         └──────────────┬──────────────┘
                        │
                        │ 11. Log Request
                        ▼
                 ┌─────────────┐
                 │ JSON Logger │
                 │ → logs/app.log
                 └──────┬──────┘
                        │
                        │ 12. Return Response
                        ▼
                   ┌─────────┐
                   │ CLIENT  │
                   └─────────┘
```

---

## Data Flow

```
┌────────────────────────────────────────────────────────┐
│                    EXTERNAL DATA SOURCES               │
├───────────────┬────────────────┬──────────────────────┤
│ Google Gemini │  VirusTotal    │  AbuseIPDB/Safe     │
│  AI API       │   Threat Intel │  Browsing           │
└───────┬───────┴────────┬───────┴──────────┬───────────┘
        │                │                  │
        │ API Calls      │ API Calls        │ API Calls
        ▼                ▼                  ▼
┌─────────────────────────────────────────────────────────┐
│               FASTAPI APPLICATION LAYER                 │
│  ┌──────────────────────────────────────────────────┐  │
│  │          SERVICE ORCHESTRATION                   │  │
│  │                                                  │  │
│  │  Gemini Service ─────┐                          │  │
│  │                      │                          │  │
│  │  Threat Intel ───────┼───► Response Builder     │  │
│  │                      │                          │  │
│  │  Prompt Detector ────┘                          │  │
│  └──────────────────────────────────────────────────┘  │
└───────────────┬────────────────────────────────────────┘
                │
                │ Write Operations
                ▼
┌─────────────────────────────────────────────────────────┐
│               DATA PERSISTENCE LAYER                    │
│                                                         │
│  ┌───────────────────┐        ┌───────────────────┐    │
│  │   PostgreSQL      │        │      Redis        │    │
│  │                   │        │                   │    │
│  │ TABLES:           │        │ KEYS:             │    │
│  │ - logs            │        │ - session:*       │    │
│  │ - users           │        │ - cache:*         │    │
│  │ - alerts          │        │ - ratelimit:*     │    │
│  │ - threat_intel    │        │ - threat:*        │    │
│  │                   │        │                   │    │
│  │ INDEXES:          │        │ EXPIRY:           │    │
│  │ - timestamp       │        │ - 3600s (default) │    │
│  │ - severity        │        │ - 60s (rate limit)│    │
│  │ - user_id         │        │                   │    │
│  └───────────────────┘        └───────────────────┘    │
└─────────────────────────────────────────────────────────┘
                │
                │ Read Operations (Analytics)
                ▼
┌─────────────────────────────────────────────────────────┐
│                 DASHBOARD & REPORTING                   │
│                                                         │
│  ┌──────────────────┐  ┌─────────────────────────┐     │
│  │ Analytics Engine │  │   Chart Generation      │     │
│  │                  │  │                         │     │
│  │ - Time series    │  │ - Trend charts          │     │
│  │ - Aggregations   │  │ - Pie charts            │     │
│  │ - Filtering      │  │ - Bar graphs            │     │
│  └──────────────────┘  └─────────────────────────┘     │
└─────────────────────────────────────────────────────────┘
```

---

## Security Layers

```
┌────────────────────────────────────────────────────────────┐
│               DEFENSE IN DEPTH ARCHITECTURE                │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  LAYER 1: NETWORK SECURITY                                 │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ - Firewall (UFW/iptables)                            │ │
│  │ - HTTPS Only (TLS 1.2+)                              │ │
│  │ - DDoS Protection (Cloudflare/AWS Shield)            │ │
│  │ - IP Whitelisting (Optional)                         │ │
│  └──────────────────────────────────────────────────────┘ │
│                         ▼                                  │
│  LAYER 2: APPLICATION GATEWAY                              │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ - Nginx Rate Limiting (10 req/s)                     │ │
│  │ - Request Size Limits (10MB)                         │ │
│  │ - SSL/TLS Termination                                │ │
│  │ - Header Security (CSP, HSTS)                        │ │
│  └──────────────────────────────────────────────────────┘ │
│                         ▼                                  │
│  LAYER 3: MIDDLEWARE SECURITY                              │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ - Rate Limiting (100 req/60s per IP)                 │ │
│  │ - Security Headers (X-Frame-Options, CSP)            │ │
│  │ - CORS Validation                                    │ │
│  │ - Request ID Tracking                                │ │
│  └──────────────────────────────────────────────────────┘ │
│                         ▼                                  │
│  LAYER 4: AUTHENTICATION & AUTHORIZATION                   │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ - JWT Token Validation                               │ │
│  │ - bcrypt Password Hashing (cost factor 12)           │ │
│  │ - Role-Based Access Control (RBAC)                   │ │
│  │ - Token Expiration (15 min access, 7 day refresh)    │ │
│  └──────────────────────────────────────────────────────┘ │
│                         ▼                                  │
│  LAYER 5: INPUT VALIDATION                                 │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ - Pydantic Schema Validation                         │ │
│  │ - SQL Injection Prevention (ORM)                     │ │
│  │ - XSS Prevention (HTML Escaping)                     │ │
│  │ - Prompt Injection Detection                         │ │
│  └──────────────────────────────────────────────────────┘ │
│                         ▼                                  │
│  LAYER 6: BUSINESS LOGIC SECURITY                          │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ - AI Safety Checks (Gemini)                          │ │
│  │ - Threat Intelligence Validation                     │ │
│  │ - PII Detection & Masking                            │ │
│  │ - Toxicity Filtering                                 │ │
│  └──────────────────────────────────────────────────────┘ │
│                         ▼                                  │
│  LAYER 7: DATA SECURITY                                    │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ - Encryption at Rest (Database)                      │ │
│  │ - Encryption in Transit (TLS)                        │ │
│  │ - Secrets Management (.env, K8s Secrets)             │ │
│  │ - Audit Logging (All transactions)                   │ │
│  └──────────────────────────────────────────────────────┘ │
│                         ▼                                  │
│  LAYER 8: MONITORING & ALERTING                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ - Real-time Threat Detection                         │ │
│  │ - Security Event Logging                             │ │
│  │ - Multi-channel Alerts (Email, SMS)                  │ │
│  │ - Anomaly Detection                                  │ │
│  └──────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────┘
```

---

## Deployment Architecture

### Docker Compose (Development/Small Production)

```
┌──────────────────────────────────────────────────┐
│              DOCKER HOST SERVER                  │
│                                                  │
│  ┌────────────────────────────────────────────┐ │
│  │        Docker Network: ai-security-network │ │
│  │                                            │ │
│  │  ┌──────────────┐    ┌─────────────────┐  │ │
│  │  │   Nginx      │    │   FastAPI App   │  │ │
│  │  │ Container    │◄───│   Container     │  │ │
│  │  │              │    │                 │  │ │
│  │  │ Port: 80,443 │    │  - 4 Gunicorn   │  │ │
│  │  │              │    │    workers      │  │ │
│  │  └──────┬───────┘    │  - Health       │  │ │
│  │         │            │    checks       │  │ │
│  │         │            └────┬────────────┘  │ │
│  │         │                 │               │ │
│  │         │                 │               │ │
│  │    ┌────▼─────┐     ┌────▼──────┐        │ │
│  │    │PostgreSQL│     │   Redis   │        │ │
│  │    │Container │     │ Container │        │ │
│  │    │          │     │           │        │ │
│  │    │Port: 5432│     │Port: 6379 │        │ │
│  │    └──────────┘     └───────────┘        │ │
│  │                                           │ │
│  │  Volumes:                                 │ │
│  │  - postgres_data (persistent)             │ │
│  │  - redis_data (persistent)                │ │
│  │  - ./logs (host mounted)                  │ │
│  └───────────────────────────────────────────┘ │
└──────────────────────────────────────────────────┘
```

### Kubernetes (Enterprise Production)

```
┌─────────────────────────────────────────────────────────────────┐
│                    KUBERNETES CLUSTER                           │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │              NAMESPACE: ai-security                       │ │
│  │                                                           │ │
│  │  ┌─────────────────────────────────────────────────────┐ │ │
│  │  │               INGRESS CONTROLLER                    │ │ │
│  │  │  - cert-manager (Let's Encrypt)                     │ │ │
│  │  │  - Rate limiting annotations                        │ │ │
│  │  │  - Path-based routing                               │ │ │
│  │  └────────────────────┬────────────────────────────────┘ │ │
│  │                       │                                   │ │
│  │                       ▼                                   │ │
│  │  ┌─────────────────────────────────────────────────────┐ │ │
│  │  │            SERVICE: ai-security-service             │ │ │
│  │  │            (ClusterIP - Load Balancer)              │ │ │
│  │  └────────┬──────────────┬──────────────┬──────────────┘ │ │
│  │           │              │              │                │ │
│  │           ▼              ▼              ▼                │ │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────┐        │ │
│  │  │  POD 1     │  │  POD 2     │  │  POD 3     │        │ │
│  │  │            │  │            │  │            │        │ │
│  │  │ - App      │  │ - App      │  │ - App      │        │ │
│  │  │ - 512Mi    │  │ - 512Mi    │  │ - 512Mi    │        │ │
│  │  │ - 250m CPU │  │ - 250m CPU │  │ - 250m CPU │        │ │
│  │  │ - Liveness │  │ - Liveness │  │ - Liveness │        │ │
│  │  │ - Readiness│  │ - Readiness│  │ - Readiness│        │ │
│  │  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘        │ │
│  │        │               │               │               │ │
│  │        └───────────────┴───────────────┘               │ │
│  │                        │                               │ │
│  │  ┌─────────────────────▼──────────────────────┐        │ │
│  │  │        ConfigMap: ai-security-config       │        │ │
│  │  │  - Environment variables                   │        │ │
│  │  │  - Non-sensitive configuration             │        │ │
│  │  └────────────────────────────────────────────┘        │ │
│  │                                                         │ │
│  │  ┌────────────────────────────────────────────┐        │ │
│  │  │        Secret: ai-security-secrets         │        │ │
│  │  │  - Database credentials                    │        │ │
│  │  │  - API keys                                │        │ │
│  │  │  - JWT secrets                             │        │ │
│  │  └────────────────────────────────────────────┘        │ │
│  │                                                         │ │
│  │  ┌────────────────────────────────────────────┐        │ │
│  │  │     HorizontalPodAutoscaler (HPA)          │        │ │
│  │  │  - Min: 3 pods                             │        │ │
│  │  │  - Max: 10 pods                            │        │ │
│  │  │  - CPU: 70% threshold                      │        │ │
│  │  │  - Memory: 80% threshold                   │        │ │
│  │  └────────────────────────────────────────────┘        │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐ │
│  │           EXTERNAL MANAGED SERVICES                   │ │
│  │                                                       │ │
│  │  ┌──────────────────┐       ┌──────────────────┐    │ │
│  │  │   PostgreSQL     │       │      Redis       │    │ │
│  │  │  (Cloud Managed) │       │  (Cloud Managed) │    │ │
│  │  │                  │       │                  │    │ │
│  │  │  - Auto backups  │       │  - High avail.   │    │ │
│  │  │  - Replication   │       │  - Clustering    │    │ │
│  │  │  - Monitoring    │       │  - Persistence   │    │ │
│  │  └──────────────────┘       └──────────────────┘    │ │
│  └───────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## Technology Stack Summary

**Backend:**
- FastAPI 0.115.0 (Modern async web framework)
- Gunicorn 23.0.0 (WSGI server)
- Uvicorn 0.32.1 (ASGI server)
- Pydantic 2.10.3 (Data validation)

**Database:**
- PostgreSQL 15+ (Relational database)
- SQLAlchemy 2.0.36 (ORM)
- Alembic 1.14.0 (Migrations)

**Caching:**
- Redis 7+ (In-memory cache)
- hiredis 3.0.0 (Performance optimization)

**Security:**
- PyJWT 2.10.1 (Token management)
- bcrypt 5.0.0 (Password hashing)
- python-jose 3.3.0 (Cryptography)

**AI & NLP:**
- Google Generative AI 0.8.3 (Gemini API)
- tiktoken 0.8.0 (Token counting)

**Monitoring:**
- psutil 6.1.0 (System metrics)
- python-json-logger 3.2.1 (Structured logging)
- Sentry SDK 2.19.2 (Error tracking)

**Infrastructure:**
- Docker (Containerization)
- Kubernetes (Orchestration)
- Nginx (Reverse proxy)

**CI/CD:**
- GitHub Actions (Automation)
- Trivy (Vulnerability scanning)
- Bandit (Security analysis)

---

**Architecture Version:** 2.0.0  
**Last Updated:** 2024  
**Designed For:** Enterprise Production Deployment
