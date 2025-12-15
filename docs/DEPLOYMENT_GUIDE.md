# Deployment Guide

## Overview

This document describes how to deploy the **AI Threat Detection & Security Ops Platform** in development and production environments using **Docker** and **Kubernetes**.

---

## 🚀 Quick Start (Local Development)

### Prerequisites

* Python 3.11+
* Docker & Docker Compose
* PostgreSQL (optional, SQLite supported for local testing)
* Redis (optional)

### Local Setup

```bash
# Clone repository
git clone <repo-url>
cd ai-threat-detection-security-ops

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env

# Run application
uvicorn main:app --reload
```

Application runs at:

```
http://localhost:8000
```

---

## 🐳 Docker Deployment (Recommended)

### Docker Compose

```bash
# Configure environment
cp .env.example .env

# Build and start services
docker-compose up -d --build

# View logs
docker-compose logs -f app

# Stop services
docker-compose down
```

### Health Check

```bash
curl http://localhost:8000/health
```

---

## ☸️ Kubernetes Deployment (Optional / Advanced)

### Prerequisites

* Kubernetes cluster
* kubectl configured
* Ingress controller (nginx recommended)

### Deploy Steps

```bash
# Create namespace
kubectl create namespace ai-security

# Apply manifests
kubectl apply -f k8s/ -n ai-security

# Verify deployment
kubectl get pods -n ai-security
kubectl get services -n ai-security
```

### Scaling

```bash
kubectl scale deployment ai-security-app --replicas=3 -n ai-security
```

---

## 🔧 Environment Configuration

### Required Variables

```bash
# Application
ENVIRONMENT=production
LOG_LEVEL=INFO

# Security
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-secret

# Database
DATABASE_URL=postgresql://user:password@host:5432/db

# Cache (optional)
REDIS_URL=redis://redis:6379/0
```

---

## 🩺 Health & Monitoring

### Health Endpoints

```bash
# Liveness
/health/live

# Readiness
/health/ready
```

Example:

```bash
curl http://localhost:8000/health/live
```

---

## 🔒 Basic Security Practices

* Use strong secret keys
* Do not expose `.env` files
* Enable HTTPS in production
* Restrict CORS origins
* Run containers as non-root users
* Keep dependencies updated

---

## 🧪 Smoke Testing

```bash
curl http://localhost:8000/health/live
curl http://localhost:8000/docs
```

---

## 🔧 Troubleshooting

### Application Not Starting

```bash
docker-compose logs app
```

### Database Connection Issues

```bash
echo $DATABASE_URL
```

### High Resource Usage

```bash
docker stats
```

---

## 📦 Update Procedure

1. Pull latest code
2. Update environment variables if needed
3. Rebuild containers
4. Restart services
5. Verify health endpoints

---

## 📚 References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [OWASP Security Guidelines](https://owasp.org/)
- [12-Factor App Methodology](https://12factor.net/)
