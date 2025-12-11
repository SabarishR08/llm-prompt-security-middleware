"""
Health Check and Monitoring Endpoints
Production-ready health checks and metrics.
"""
from fastapi import APIRouter, Response
from typing import Dict, Any
import psutil
import time
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

health_router = APIRouter(prefix="/health", tags=["Health"])

# Application start time
START_TIME = time.time()


@health_router.get("/")
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint.
    Returns 200 OK if service is running.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": int(time.time() - START_TIME),
    }


@health_router.get("/live")
async def liveness_probe() -> Dict[str, str]:
    """
    Kubernetes liveness probe.
    Returns 200 if application is running.
    """
    return {"status": "alive"}


@health_router.get("/ready")
async def readiness_probe() -> Dict[str, Any]:
    """
    Kubernetes readiness probe.
    Returns 200 if application is ready to serve traffic.
    """
    from core.models.database import DatabaseManager
    
    checks = {
        "database": False,
        "overall": False,
    }
    
    # Check database connection
    try:
        db = DatabaseManager()
        # Simple query to check connection
        logs = db.get_all_logs()
        checks["database"] = True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        checks["database"] = False
    
    # Overall status
    checks["overall"] = all([
        checks["database"],
    ])
    
    status_code = 200 if checks["overall"] else 503
    
    return {
        "status": "ready" if checks["overall"] else "not_ready",
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat(),
    }


@health_router.get("/metrics")
async def metrics() -> Dict[str, Any]:
    """
    System metrics endpoint.
    Returns resource usage and performance metrics.
    """
    # CPU usage
    cpu_percent = psutil.cpu_percent(interval=0.1)
    cpu_count = psutil.cpu_count()
    
    # Memory usage
    memory = psutil.virtual_memory()
    
    # Disk usage
    disk = psutil.disk_usage('/')
    
    # Uptime
    uptime_seconds = int(time.time() - START_TIME)
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": uptime_seconds,
        "cpu": {
            "percent": cpu_percent,
            "count": cpu_count,
        },
        "memory": {
            "total_mb": memory.total // (1024 * 1024),
            "used_mb": memory.used // (1024 * 1024),
            "available_mb": memory.available // (1024 * 1024),
            "percent": memory.percent,
        },
        "disk": {
            "total_gb": disk.total // (1024 * 1024 * 1024),
            "used_gb": disk.used // (1024 * 1024 * 1024),
            "free_gb": disk.free // (1024 * 1024 * 1024),
            "percent": disk.percent,
        },
    }


@health_router.get("/info")
async def info() -> Dict[str, Any]:
    """
    Application information endpoint.
    Returns version and configuration details.
    """
    from core.config.app_config import config
    
    return {
        "app_name": config.APP_NAME,
        "version": config.APP_VERSION,
        "environment": config.ENVIRONMENT.value,
        "debug": config.DEBUG,
        "python_version": f"{psutil.sys.version_info.major}.{psutil.sys.version_info.minor}.{psutil.sys.version_info.micro}",
        "uptime_seconds": int(time.time() - START_TIME),
    }

