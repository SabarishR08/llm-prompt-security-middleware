# 🏗️ System Architecture

## High-Level Architecture

```mermaid
flowchart TD
       A[User Prompt] --> B[JWT Auth]
       B --> C[Compliance Checks<br/>PII, Toxicity, Injection, Profanity]
       C --> D[Threat Intel APIs<br/>VirusTotal, GSB, OTX]
       D --> E{Decision}
       E -->|Pass| F[Gemini API<br/>Safe Response]
       E -->|Block| G[Return 403<br/>+ reason]
       E -->|Flag| H[Review Queue]
       F --> I[Audit Log]
       G --> I
       H --> I
```

```mermaid
flowchart TD
    Clients[External Clients<br/>Web, Mobile, APIs] --> Nginx[NGINX Reverse Proxy<br/>TLS, rate limit, load balance]
    Nginx --> Ingress[Kubernetes Ingress<br/>cert-manager, path routing]
    Ingress --> Svc[Kubernetes Service<br/>ClusterIP LB]
    Svc --> Pod1[App Pod 1<br/>Gunicorn workers]
    Svc --> Pod2[App Pod 2<br/>Gunicorn workers]
    Svc --> Pod3[App Pod 3<br/>Gunicorn workers]
    Pod1 --> PG[PostgreSQL<br/>Logs, Users, Analytics]
    Pod2 --> Redis[Redis Cache<br/>Rate limit, threat intel cache]
    Pod3 --> PG
```

---

## Application Layer Architecture

```mermaid
flowchart TD
    A[FastAPI Application] --> B[Middleware Stack<br/>RequestID, Performance, SecurityHeaders, RateLimit, CORS]
    B --> C[API Routes<br/>Health, Auth, Analysis, Logs, Dashboard]
    C --> D[Input Validation<br/>Pydantic Models]
    D --> E[Business Logic<br/>Gemini Service, Prompt Detector, Threat Intel]
    E --> F[Support Services<br/>Alerts, Auth Utils]
    F --> G[Exception Handling]
    G --> H[Configuration Layer]
    H --> I[Logging System]
```

---

## Request Flow Diagram

```mermaid
sequenceDiagram
    participant C as Client
    participant N as Nginx/Ingress
    participant M as Middleware
    participant R as Analysis Router
    participant S as Services
    participant DB as Redis/DB
    participant A as Alerts

    C->>N: HTTPS POST /api/analyze
    N->>M: Forward request
    M->>M: RequestID, Performance, SecurityHeaders, RateLimit, CORS
    M->>R: Route to /api/analyze
    R->>S: Validate request + run detectors
    S->>DB: Cache lookup (Redis)
    S->>DB: Log + analytics (PostgreSQL)
    S->>A: Alert on high severity
    S-->>C: JSON response
```

---

## Data Flow

```mermaid
flowchart LR
    A[External Data Sources<br/>Gemini, VirusTotal, Safe Browsing] --> B[FastAPI Application Layer]
    B --> C[Service Orchestration<br/>Gemini Service, Threat Intel, Prompt Detector]
    C --> D[Response Builder]
    C --> E[Redis Cache]
    C --> F[PostgreSQL<br/>Logs, Users, Alerts]
    E --> D
    F --> G[Analytics & Dashboard]
    D --> H[API Response]
```

---

## Security Layers

```mermaid
flowchart TD
    L1[Network Security<br/>Firewall, TLS 1.2+, DDoS protection, IP allowlist] --> L2
    L2[Application Gateway<br/>Nginx rate limits, request size caps, TLS termination, headers] --> L3
    L3[Middleware Security<br/>RateLimit, SecurityHeaders, CORS, Request ID] --> L4
    L4[Auth & Authz<br/>JWT validation, bcrypt, RBAC, token expiry] --> L5
    L5[Input Validation<br/>Pydantic schemas, SQLi prevention, XSS escape, prompt detection] --> L6
    L6[Business Logic Security<br/>AI safety checks, threat intel, PII masking, toxicity filtering] --> L7
    L7[Data Security<br/>Encryption at rest/in transit, secrets management, audit logging] --> L8
    L8[Monitoring & Alerting<br/>Threat detection, logs, multi-channel alerts, anomaly detection]
```

---

## Deployment Architecture

### Docker Compose (Development/Small Production)

```mermaid
flowchart TB
    Host[Docker Host] --> Net[Docker Network<br/>ai-security-network]
    Net --> Nginx[nginx container<br/>ports 80, 443]
    Net --> App[FastAPI app container<br/>Gunicorn x4, health checks]
    Net --> PG[PostgreSQL container<br/>port 5432, volume postgres_data]
    Net --> Redis[Redis container<br/>port 6379, volume redis_data]
    App -. logs bind .-> Logs[Host ./logs]
    PG --> V1[postgres_data volume]
    Redis --> V2[redis_data volume]
```

### Kubernetes (Enterprise Production)

```mermaid
flowchart TB
    Ingress[Ingress Controller<br/>cert-manager, rate limits, path routing] --> Svc[Service: ai-security-service<br/>ClusterIP LB]
    Svc --> P1[Pod 1<br/>App, 512Mi, 250m]
    Svc --> P2[Pod 2<br/>App, 512Mi, 250m]
    Svc --> P3[Pod 3<br/>App, 512Mi, 250m]
    Svc --> HPA[HPA<br/>min 3, max 10, CPU 70%, Mem 80%]
    Svc --> CM[ConfigMap<br/>env + config]
    Svc --> Secret[Secret<br/>DB creds, API keys, JWT]
    P1 --> PG[Managed PostgreSQL]
    P2 --> Redis[Managed Redis]
    P3 --> PG
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
