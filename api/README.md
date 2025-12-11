# API Layer

FastAPI routes and dependency injection for the LLM security middleware.

## Structure

```
api/
├── routes/          # API endpoint definitions
│   ├── analysis_router.py
│   ├── auth_router.py
│   ├── logs_router.py
│   ├── dashboard_router.py
│   └── health_router.py
└── dependencies/    # Dependency injection (JWT auth, etc.)
    └── auth.py
```

## Routes Overview

| Route | Purpose | Auth Required |
|-------|---------|---------------|
| `/api/analysis/analyze` | Analyze prompts for threats | ✅ JWT |
| `/api/auth/login` | User authentication | ❌ Public |
| `/api/logs` | Retrieve audit logs | ✅ Admin/Moderator |
| `/api/dashboard/*` | Security metrics | ✅ JWT |
| `/api/health` | Health checks | ❌ Public |

For detailed route documentation, see [routes/README.md](routes/README.md)
