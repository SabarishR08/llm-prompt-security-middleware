#  Quick Start – AI Security Compliance System

## Overview

This guide helps you **run and test the AI Security Compliance System locally** and verify its core security features such as **prompt validation, RBAC, logging, and analytics**.

---

##  System Status

Once running, the application is available at:

```
http://127.0.0.1:8000
```

---

## 🛠️ Prerequisites

* Python 3.11+
* pip
* Virtual environment (recommended)

---

## ▶️ Run the Application

```bash
# Clone repository
git clone <repo-url>
cd Prompt-Compliance-Automation

# Create virtual environment
python -m venv venv
source venv/bin/activate    # Linux/macOS
venv\Scripts\activate       # Windows

# Install dependencies
pip install -r requirements.txt

# Start application
uvicorn main:app --reload
```

---

## 🔐 Authentication & Roles

The system supports **role-based access control (RBAC)**.

### Available Roles

| Role      | Access                                    |
| --------- | ----------------------------------------- |
| Admin     | Full access (logs, analytics, management) |
| Moderator | Logs + analytics (read-only)              |
| Viewer    | Prompt analysis only                      |

> ⚠️ **Note**
> Default demo users are defined in the source code for testing purposes only.
> For production, credentials should be stored securely in a database.

---

## 🧪 Feature Testing Guide

### 1️⃣ Prompt Analysis

* Submit any prompt on the main page
* The system checks:

  * Prompt length
  * Injection patterns
  * Sensitive content indicators

Expected result:

* **Allowed** → Processed
* **Blocked** → Reason shown in response metadata

---

### 2️⃣ Role Access Control

* Click **Logs** (🔒 icon)
* Login as **Admin** or **Moderator**
* Viewer role will be denied access to logs

Expected:

* Unauthorized roles receive an access-denied message

---

### 3️⃣ Analytics Dashboard

After login (Admin / Moderator), the dashboard displays:

* Threat activity timeline
* Prompt classification statistics
* Detection summaries

Charts auto-load when logs are available.

---

## 🔌 Optional Integrations (Advanced)

### Threat Intelligence APIs

You can optionally enable external threat intelligence lookups.

Add keys to `.env`:

```bash
VIRUSTOTAL_API_KEY=your_key
GOOGLE_SAFEBROWSING_API_KEY=your_key
ABUSEIPDB_API_KEY=your_key
```

If not configured, the system runs without external lookups.

---

### Alerts (Optional)

Supports email/SMS alerts for high-risk events.

Configuration is optional and **disabled by default** for local testing.

---

## 📡 Useful Endpoints

```bash
# Health check
curl http://127.0.0.1:8000/health

# API documentation
http://127.0.0.1:8000/docs

# Prompt analysis
POST /api/analyze
```

---

## 🧪 Run Tests (Optional)

```bash
python tests/test_security_features.py
```

Expected:

```
All tests passed
```

---

## 🐛 Troubleshooting

**Module import errors**

```bash
pip install -r requirements.txt
```

**Login issues**

* Ensure correct role is selected
* Restart the server after code changes

**Dashboard not loading**

* Login using Admin or Moderator role
* Verify API is running

---

## 📚 Related Documentation


For full implementation details, see:
- **`IMPLEMENTATION_SUMMARY.md`** - Complete feature documentation
- **`PROJECT_DOCUMENTATION.md`** - Original project docs
- **`RBAC_GUIDE.md`** - Role-based access control guide



---

## ✅ Ready to Use

* App: [http://127.0.0.1:8000](http://127.0.0.1:8000)
* API Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* Health: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---
