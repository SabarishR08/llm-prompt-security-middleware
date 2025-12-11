# 🔒 RBAC Workflow Visual Guide

## The Complete User Journey

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER ACCESSES DASHBOARD                       │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                    Is auth_token cookie set?
                       /              \
                     YES              NO
                    /                  \
        ┌──────────────────┐     ┌────────────────────┐
        │ Verify token     │     │ Redirect to       │
        │ with backend     │     │ /auth.html        │
        └────────┬─────────┘     └────────┬───────────┘
                 │                        │
         Is token valid?          ┌───────────────────┐
            /      \              │   LOGIN PAGE      │
          YES      NO             │                   │
         /          \             │ • Select Role     │
    ┌────────┐  ┌────────────┐   │   (Admin/Mod/Ana) │
    │ Show   │  │ Redirect   │   │ • Enter Username  │
    │Dashboard│  │ to login   │   │ • Enter Password  │
    └────┬───┘  └─────┬──────┘   └───────────┬───────┘
         │            │                      │
         │            │          ┌───────────────────────┐
         │            │          │ Validate Credentials   │
         │            │          │ POST /api/auth/login   │
         │            │          └───────────┬───────────┘
         │            │                      │
         │            │            Is user valid?
         │            │               /      \
         │            │             YES      NO
         │            │            /          \
         │            │    ┌─────────────┐  ┌──────────────┐
         │            │    │ Create      │  │ Show error   │
         │            │    │ session &   │  │ "Invalid"    │
         │            │    │ set cookie  │  │              │
         │            │    └────────┬────┘  └──────────────┘
         │            │             │
         │            └─────────────┘
         │                    │
         │            Redirect to dashboard
         │
         │         Sidebar navigation
         │                  │
         └──────────────────┘
                    │
        ┌───────────────────────────────┐
        │  User clicks on "Logs" menu    │
        │  (shows 🔒 lock icon)          │
        └───────────────────┬────────────┘
                            │
                ┌───────────────────────────┐
                │ Request: GET /api/logs/   │
                │ Cookie: auth_token=ABC... │
                └───────────────┬───────────┘
                                │
                    ┌─────────────────────────┐
                    │ Backend RBAC Check      │
                    │                         │
                    │ 1. Token exists?        │
                    │ 2. Token valid?         │
                    │ 3. User in database?    │
                    │ 4. Role is Admin/Mod?   │
                    └──────────┬──────────────┘
                               │
                    ┌──────────────────────┐
                    │ All checks pass? ✓    │
                    │        /    \         │
                    │      YES    NO        │
                    │     /        \        │
                 ┌──────┐      ┌──────────┐
                 │ GET  │      │ 401/403  │
                 │Logs  │      │ Error    │
                 │      │      │Redirect  │
                 └──────┘      │to login  │
                    │          └──────────┘
        ┌───────────────────────────┐
        │ Show Logs Dashboard       │
        │                           │
        │ ✅ View all logs         │
        │ ✅ Filter by status      │
        │ ✅ Export CSV/JSON       │
        │ ✅ Admin: Clear logs     │
        │ ❌ User role: blocked    │
        └───────────────────────────┘
```

---

## Access Control Matrix

```
                    ┌──────────────────────────────────┐
                    │        USER ROLES                │
                    ├──────────────────────────────────┤
ENDPOINT            │ Admin │ Moderator │ Analyst │ User │
────────────────────┼───────┼───────────┼─────────┼──────┤
GET /api/logs/      │  ✅   │    ✅     │   ✅    │  ❌  │
GET /api/logs/count │  ✅   │    ✅     │   ✅    │  ❌  │
GET /api/logs/      │  ✅   │    ✅     │   ✅    │  ❌  │
  /by-status/{s}    │       │           │         │      │
GET /api/logs/      │  ✅   │    ✅     │   ✅    │  ❌  │
  /export/csv       │       │           │         │      │
GET /api/logs/      │  ✅   │    ✅     │   ✅    │  ❌  │
  /export/json      │       │           │         │      │
POST /api/logs/clear│  ✅   │    ❌     │   ❌    │  ❌  │
(DANGEROUS!)        │       │           │         │      │
└──────────────────────────────────────────────────────┘
```

---

## Error Responses

### 401 Unauthorized (No Token)
```
GET /api/logs/
→ No auth_token cookie

Response:
{
  "detail": "Authentication required - No token provided"
}

Action: Redirect to /auth.html (login)
```

### 401 Unauthorized (Expired Token)
```
GET /api/logs/
→ Token exists but expired (>8 hours old)

Response:
{
  "detail": "Invalid or expired token"
}

Action: Redirect to /auth.html (re-login)
```

### 403 Forbidden (Wrong Role)
```
GET /api/logs/
→ Token valid, but user is "User" role

Response:
{
  "detail": "Access denied. Only Admin and Moderator can view logs. Your role: user"
}

Action: Show error message
```

### 200 OK (Success)
```
GET /api/logs/
→ Token valid, user is Admin/Moderator

Response:
{
  "logs": [
    {
      "id": 1,
      "prompt": "...",
      "status": "Safe",
      ...
    }
  ]
}

Action: Display logs in dashboard
```

---

## State Machine Diagram

```
                    ┌─────────────┐
                    │  ANONYMOUS  │
                    │ (No Token)  │
                    └────────┬────┘
                             │
                    Click Login → POST /api/auth/login
                    (credentials)  │
                             │
                    ┌────────┴──────────┐
                    │                   │
               ✅ Valid              ❌ Invalid
                    │                   │
                    ▼                   │
            ┌──────────────┐            │
            │ AUTHENTICATED│            │
            │ (Has Token)  │◄───────────┘
            └──────┬───────┘
                   │
          Access resource?
             /          \
        Admin/      User/Analyst
        Moderator
           │              │
           ▼              ▼
      ┌────────┐    ┌──────────┐
      │ ALLOWED│    │ FORBIDDEN│
      │        │    │ (403)    │
      └────────┘    └──────────┘
```

---

## Code Flow Execution

```
Browser Request
    │
    ├─ Cookie with auth_token: "abc123..."
    │
    ▼
┌─────────────────────────────────────┐
│ FastAPI Endpoint Handler            │
│ @logs_router.get("/")               │
│ async def get_logs(                 │
│    auth_token: Cookie = None        │
│ )                                   │
└────────┬────────────────────────────┘
         │
         ▼
    check_logs_access(auth_token)
         │
    ┌────┴────────────────────┐
    │ VALIDATION CHAIN        │
    │                         │
    ├─ if not token:          │
    │   401 Unauthorized      │
    │                         │
    ├─ if not valid_session:  │
    │   401 Unauthorized      │
    │                         │
    ├─ if role not in [       │
    │    ADMIN, MODERATOR     │
    │  ]:                     │
    │   403 Forbidden         │
    │                         │
    └─ return username        │
         │                    │
         ▼
    (Now safe to proceed)
    db_manager.get_all_logs()
         │
         ▼
    return {"logs": [...]}
         │
         ▼
    Browser displays logs
```

---

## Production Hardening Checklist

```
SECURITY UPGRADES NEEDED:

☐ Password Hashing
  └─ SHA256 → bcrypt (with salt & rounds=12)

☐ Token Security
  └─ Secrets → JWT with RS256 signature
  └─ Expiry → Add exp claim

☐ Transport Security
  └─ secure=True on cookies (HTTPS only)
  └─ Enforce SSL/TLS

☐ Session Management
  └─ In-memory → Redis/PostgreSQL
  └─ Survives server restart

☐ Rate Limiting
  └─ Prevent brute force attacks
  └─ Limit login attempts (e.g., 5/min)

☐ Audit Logging
  └─ Log all auth attempts (success/failure)
  └─ Log all admin actions
  └─ Log all failed RBAC checks

☐ Multi-Factor Authentication
  └─ TOTP (Google Authenticator)
  └─ SMS/Email verification

☐ API Security
  └─ CORS: Restrict origins (not *)
  └─ CSRF: Add CSRF tokens
  └─ XSS: Sanitize all inputs

☐ Monitoring
  └─ Alert on suspicious patterns
  └─ Dashboard for security events
```

---

## Quick Reference: Testing Commands

```bash
# Test 1: Login as Admin
curl -X POST http://localhost:8000/api/auth/login \
  -d "username=admin&password=admin123"

# Test 2: Access logs with token
curl -X GET http://localhost:8000/api/logs/ \
  -H "Cookie: auth_token=YOUR_TOKEN_HERE"

# Test 3: Access logs as different user
curl -X GET http://localhost:8000/api/logs/ \
  -H "Cookie: auth_token=USER_TOKEN" \
  # Expected: 403 Forbidden

# Test 4: Verify token
curl -X GET http://localhost:8000/api/auth/verify \
  -H "Cookie: auth_token=YOUR_TOKEN_HERE"

# Test 5: Logout
curl -X POST http://localhost:8000/api/auth/logout \
  -H "Cookie: auth_token=YOUR_TOKEN_HERE"
```

---

## Summary

Your RBAC system protects logs through:

1. **Authentication** → Users must login
2. **Authorization** → Only specific roles allowed
3. **Session Management** → Tokens expire after 8 hours
4. **Audit Logging** → Track who accessed what
5. **Secure Cookies** → HttpOnly prevents XSS attacks

Result: **Sensitive logs are only accessible to trusted admins/moderators**

