# Industrial-Grade Deployment Guide

## Overview
This guide provides production deployment instructions for the AI Security Compliance System with enterprise-level configurations.

---

## 🚀 Quick Start (Development)

### Prerequisites
- Python 3.12+
- PostgreSQL 15+ (for production)
- Redis 7+ (for caching)
- Docker & Docker Compose (recommended)

### Local Development Setup

```bash
# 1. Clone and navigate
cd Prompt-Compliance-Automation

# 2. Create virtual environment
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your settings

# 5. Run database migrations
alembic upgrade head

# 6. Start application
uvicorn main:app --reload
```

---

## 🐳 Docker Deployment

### Build and Run with Docker Compose

```bash
# 1. Configure environment
cp .env.example .env
# Edit .env with production values

# 2. Build and start services
docker-compose up -d --build

# 3. Check health
curl http://localhost/health/live

# 4. View logs
docker-compose logs -f app

# 5. Stop services
docker-compose down
```

### Individual Docker Commands

```bash
# Build image
docker build -t ai-security-app:latest .

# Run container
docker run -d \
  --name ai-security \
  -p 8000:8000 \
  --env-file .env \
  ai-security-app:latest

# View logs
docker logs -f ai-security

# Execute commands in container
docker exec -it ai-security bash
```

---

## ☸️ Kubernetes Deployment

### Prerequisites
- Kubernetes cluster (v1.28+)
- kubectl configured
- cert-manager for TLS certificates
- Ingress controller (nginx)

### Deploy to Kubernetes

```bash
# 1. Create namespace
kubectl create namespace ai-security

# 2. Create secrets
kubectl create secret generic ai-security-secrets \
  --from-literal=database-url="postgresql://user:pass@postgres:5432/db" \
  --from-literal=redis-url="redis://redis:6379/0" \
  --from-literal=secret-key="your-secret-key" \
  --from-literal=jwt-secret-key="your-jwt-secret" \
  -n ai-security

# 3. Apply configurations
kubectl apply -f k8s/deployment.yaml

# 4. Check deployment status
kubectl get pods -n ai-security
kubectl get services -n ai-security
kubectl get ingress -n ai-security

# 5. View logs
kubectl logs -f deployment/ai-security-app -n ai-security

# 6. Scale deployment
kubectl scale deployment ai-security-app --replicas=5 -n ai-security
```

### Update Deployment

```bash
# Rolling update
kubectl set image deployment/ai-security-app \
  app=your-registry/ai-security-app:v2.0.0 \
  -n ai-security

# Monitor rollout
kubectl rollout status deployment/ai-security-app -n ai-security

# Rollback if needed
kubectl rollout undo deployment/ai-security-app -n ai-security
```

---

## 🔧 Production Configuration

### Environment Variables

**Critical Production Settings:**

```bash
# Security
SECRET_KEY=<64-char-random-string>
JWT_SECRET_KEY=<64-char-random-string>

# Database (PostgreSQL)
DATABASE_URL=postgresql://user:password@host:5432/db
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40

# Redis Cache
REDIS_URL=redis://redis:6379/0
CACHE_TTL=3600

# Application
ENVIRONMENT=production
WORKERS=4  # 2-4 x CPU cores
LOG_LEVEL=INFO

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# Monitoring
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project
ENABLE_METRICS=true
```

### Database Migration

```bash
# Generate migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one version
alembic downgrade -1

# View migration history
alembic history
```

### SSL/TLS Configuration

**For Docker Compose (Let's Encrypt):**

```bash
# 1. Install certbot
sudo apt-get install certbot python3-certbot-nginx

# 2. Obtain certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# 3. Auto-renewal
sudo crontab -e
# Add: 0 0 1 * * certbot renew --quiet
```

**For Kubernetes:**

```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Create ClusterIssuer
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@yourdomain.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
```

---

## 📊 Monitoring & Health Checks

### Health Endpoints

```bash
# Liveness probe
curl http://localhost:8000/health/live

# Readiness probe
curl http://localhost:8000/health/ready

# Detailed metrics
curl http://localhost:8000/health/metrics

# System info
curl http://localhost:8000/health/info
```

### Monitoring Setup

**Prometheus + Grafana:**

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'ai-security-app'
    static_configs:
      - targets: ['app:8000']
    metrics_path: '/health/metrics'
    scrape_interval: 15s
```

**Application Logging:**

```bash
# View application logs
docker-compose logs -f app

# Kubernetes logs
kubectl logs -f deployment/ai-security-app -n ai-security

# Filter by severity
kubectl logs deployment/ai-security-app -n ai-security | grep ERROR
```

---

## 🔒 Security Checklist

### Pre-Production Checklist

- [ ] Change all default secrets and passwords
- [ ] Enable HTTPS with valid SSL certificates
- [ ] Configure CORS for specific domains only
- [ ] Enable rate limiting on all endpoints
- [ ] Set up database connection pooling
- [ ] Configure Redis authentication
- [ ] Enable security headers (CSP, HSTS, etc.)
- [ ] Set up automated backups
- [ ] Configure monitoring and alerting
- [ ] Enable audit logging
- [ ] Review and update firewall rules
- [ ] Implement intrusion detection
- [ ] Set up log aggregation
- [ ] Configure DDoS protection
- [ ] Enable container scanning
- [ ] Implement secrets management (Vault/AWS Secrets Manager)

### Security Hardening

```bash
# Database: Create read-only user for analytics
CREATE USER readonly WITH PASSWORD 'secure_password';
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly;

# Redis: Require authentication
# In redis.conf:
requirepass your_redis_password
rename-command CONFIG ""
rename-command FLUSHDB ""
rename-command FLUSHALL ""

# Firewall rules (example)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw deny 8000/tcp  # Block direct access
sudo ufw enable
```

---

## 🧪 Testing in Production

### Smoke Tests

```bash
#!/bin/bash
# smoke-test.sh

BASE_URL="https://yourdomain.com"

# Health check
echo "Testing health endpoint..."
curl -f $BASE_URL/health/live || exit 1

# API availability
echo "Testing API availability..."
curl -f $BASE_URL/api/docs || exit 1

# Database connection
echo "Testing database..."
curl -f $BASE_URL/health/ready || exit 1

echo "All smoke tests passed!"
```

### Load Testing

```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Run load test
ab -n 10000 -c 100 https://yourdomain.com/health/live

# Or use Locust
pip install locust
locust -f tests/load_test.py --host=https://yourdomain.com
```

---

## 🔄 CI/CD Pipeline

### GitHub Actions

The `.github/workflows/ci-cd.yml` pipeline automatically:

1. **Test**: Runs unit tests with coverage
2. **Security Scan**: Trivy + Bandit vulnerability scanning
3. **Build**: Creates Docker image and pushes to registry
4. **Deploy**: Deploys to Kubernetes on main branch
5. **Notify**: Sends deployment notifications

**Required GitHub Secrets:**

- `KUBECONFIG`: Base64-encoded Kubernetes config
- `REGISTRY_USERNAME`: Container registry username
- `REGISTRY_PASSWORD`: Container registry password

---

## 📈 Performance Optimization

### Application Tuning

```bash
# Gunicorn workers (2-4 x CPU cores)
WORKERS=4

# Database connection pool
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40

# Redis connection pool
REDIS_MAX_CONNECTIONS=50
```

### Database Optimization

```sql
-- Create indexes for frequently queried columns
CREATE INDEX idx_logs_timestamp ON logs(timestamp);
CREATE INDEX idx_logs_severity ON logs(severity);
CREATE INDEX idx_logs_user_id ON logs(user_id);

-- Analyze query performance
EXPLAIN ANALYZE SELECT * FROM logs WHERE severity = 'critical';

-- Enable query caching
ALTER TABLE logs SET (autovacuum_enabled = true);
```

---

## 🔧 Troubleshooting

### Common Issues

**Connection Refused:**
```bash
# Check if service is running
docker-compose ps
kubectl get pods -n ai-security

# Check logs
docker-compose logs app
kubectl logs deployment/ai-security-app -n ai-security
```

**Database Connection Error:**
```bash
# Test database connectivity
docker exec -it postgres psql -U ai_security -d ai_security_db

# Check connection string
echo $DATABASE_URL
```

**High Memory Usage:**
```bash
# Check memory usage
docker stats
kubectl top pods -n ai-security

# Adjust limits in docker-compose.yml or k8s/deployment.yaml
```

---

## 📞 Support & Maintenance

### Backup & Restore

```bash
# Backup PostgreSQL
pg_dump -U ai_security ai_security_db > backup_$(date +%Y%m%d).sql

# Restore PostgreSQL
psql -U ai_security ai_security_db < backup_20240115.sql

# Backup Redis
redis-cli --rdb /backup/dump.rdb

# Automated backups (cron)
0 2 * * * /scripts/backup.sh
```

### Update Procedure

1. Test updates in staging environment
2. Create database backup
3. Deploy new version with rolling update
4. Monitor health checks and error logs
5. Rollback if issues detected

---

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [OWASP Security Guidelines](https://owasp.org/)
- [12-Factor App Methodology](https://12factor.net/)

---

**Deployment Version:** 2.0.0  
**Last Updated:** 2024  
**Maintained By:** DevSecOps Team
