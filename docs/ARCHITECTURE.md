# 🏗️ System Architecture

This document describes the **design, data flow, and security architecture** of the **LLM Prompt Security Middleware**. The architecture is designed with a **defense-in-depth** approach and reflects the **actual implementation and reference deployment patterns** used in this project.

---

## High-Level Architecture

```mermaid
flowchart TD
       A[User Prompt] --> B[JWT Authentication]
       B --> C[Compliance Checks<br/>PII, Toxicity, Injection, Profanity]
       C --> D[Threat Intelligence APIs<br/>VirusTotal, GSB, OTX]
       D --> E{Decision Engine}
       E -->|Pass| F[Gemini API<br/>Safety-filtered Response]
       E -->|Block| G[403 Response<br/>With Reason]
       E -->|Flag| H[Manual Review / Audit]
       F --> I[Audit Log]
       G --> I
       H --> I
```

```mermaid
flowchart TD
    Clients[External Clients<br/>Web, Mobile, APIs] --> Nginx[NGINX Reverse Proxy<br/>TLS, Rate Limiting]
    Nginx --> Ingress[Kubernetes Ingress<br/>Path Routing]
    Ingress --> Svc[Kubernetes Service]
    Svc --> Pod1[App Pod]
    Svc --> Pod2[App Pod]
    Svc --> Pod3[App Pod]
    Pod1 --> PG[PostgreSQL<br/>Audit Logs, Users]
    Pod2 --> Redis[Redis Cache<br/>Rate Limits, Intel Cache]
    Pod3 --> PG
```

---

## Application Layer Architecture

```mermaid
flowchart TD
    A[FastAPI Application] --> B[Middleware Stack<br/>Request ID, Security Headers, Rate Limiting, CORS]
    B --> C[API Routes<br/>Health, Auth, Analysis, Logs]
    C --> D[Input Validation<br/>Pydantic Schemas]
    D --> E[Business Logic<br/>Prompt Detector, Threat Intel, Gemini Service]
    E --> F[Authentication Utilities]
    F --> G[Centralized Exception Handling]
    G --> H[Configuration Layer]
    H --> I[Structured Logging System]
```

---

## Request Flow Diagram

```mermaid
sequenceDiagram
    participant C as Client
    participant N as Nginx/Ingress
    participant M as Middleware
    participant R as Analysis Router
    participant S as Core Services
    participant DB as Redis / PostgreSQL

    C->>N: HTTPS POST /api/analyze
    N->>M: Forward request
    M->>M: Request ID, Rate Limit, Headers
    M->>R: Route to analysis endpoint
    R->>S: Validate input & run detectors
    S->>DB: Cache lookup / audit log
    S-->>C: JSON response
```

---

## Data Flow

```mermaid
flowchart LR
    A[External Services<br/>Gemini, VirusTotal, Safe Browsing] --> B[FastAPI Application]
    B --> C[Service Orchestration Layer]
    C --> D[Response Builder]
    C --> E[Redis Cache]
    C --> F[PostgreSQL<br/>Audit Logs]
    E --> D
    D --> G[API Response]
```

---

## Security Layers (Defense in Depth)

```mermaid
flowchart TD
    L1[Network Layer<br/>TLS Termination, Reverse Proxy Protections] --> L2
    L2[Gateway Layer<br/>NGINX Rate Limits, Request Size Caps] --> L3
    L3[Middleware Security<br/>Security Headers, CORS, Request ID] --> L4
    L4[Authentication & Authorization<br/>JWT, RBAC, Token Expiry] --> L5
    L5[Input Validation<br/>Pydantic Schemas, Injection Detection] --> L6
    L6[Business Logic Security<br/>PII Masking, Toxicity Filtering, Threat Intel] --> L7
    L7[Data Protection<br/>Secrets Management, Audit Logging]
```

---

## Deployment Architecture

### Docker Compose (Development / Small-Scale Deployment)

```mermaid
flowchart TB
    Host[Docker Host] --> Net[Docker Network]
    Net --> Nginx[nginx Container]
    Net --> App[FastAPI App Container<br/>Gunicorn Workers]
    Net --> PG[PostgreSQL Container]
    Net --> Redis[Redis Container]
    App -. logs .-> Logs[Host Logs Directory]
```

### Kubernetes (Scalable Production Reference)

```mermaid
flowchart TB
    Ingress[Ingress Controller] --> Svc[Application Service]
    Svc --> P1[Application Pod]
    Svc --> P2[Application Pod]
    Svc --> P3[Application Pod]
    Svc --> HPA[Horizontal Pod Autoscaler]
    Svc --> CM[ConfigMap]
    Svc --> Secret[Secrets]
    P1 --> PG[Managed PostgreSQL]
    P2 --> Redis[Managed Redis]
    P3 --> PG
```

> **Note:** Kubernetes deployment is provided as a **reference architecture** demonstrating scalability and security best practices.

---

## Technology Stack Summary

### Backend

* FastAPI (Async API framework)
* Gunicorn + Uvicorn (ASGI/WSGI servers)
* Pydantic (Request & response validation)

### Database & Storage

* PostgreSQL (Audit logs, user data)
* SQLAlchemy (ORM)
* Alembic (Schema migrations)

### Caching

* Redis (Rate limiting, threat intel caching)

### Security

* JWT (Authentication & RBAC)
* bcrypt (Password hashing)
* python-jose / PyJWT (Token cryptography)

### AI & NLP

* Google Gemini API (LLM integration)
* Token counting & prompt analysis utilities

### Observability

* Structured JSON logging
* Error tracking (Sentry-compatible)

### Infrastructure

* Docker (Containerization)
* Kubernetes (Orchestration – reference)
* NGINX (Reverse proxy)

### CI/CD & Security Tooling

* GitHub Actions (CI/CD automation)
* Bandit (Static security analysis)
* Trivy (Container & dependency scanning)

---

