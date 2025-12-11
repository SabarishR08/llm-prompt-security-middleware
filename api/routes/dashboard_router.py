"""Dashboard router providing analytics and visualization endpoints."""
from fastapi import APIRouter, HTTPException, Cookie, Header
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict

from core.models.database import DatabaseManager
from core.utils.auth import UserRole, jwt_manager

dashboard_router = APIRouter(prefix="/dashboard", tags=["Dashboard"])
db = DatabaseManager()


def check_dashboard_access(token: Optional[str] = None) -> str:
    """Verify user has access to dashboard (Admin or Moderator only)."""
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    payload = jwt_manager.verify_token(token, refresh=False)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    username = payload.get("username") or payload.get("sub")
    role_value = payload.get("role")
    if not username or not role_value:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    try:
        role = UserRole(role_value)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid role")
    
    if role not in [UserRole.ADMIN, UserRole.MODERATOR]:
        raise HTTPException(
            status_code=403,
            detail="Dashboard access denied. Admin/Moderator only."
        )
    
    return username


@dashboard_router.get("/stats/overview")
async def get_overview_stats(
    auth_token: Optional[str] = Cookie(None),
    authorization: Optional[str] = Header(None)  # type: ignore
):
    """Get overview statistics for dashboard."""
    token = auth_token
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]
    check_dashboard_access(token)
    
    logs = db.get_all_logs()
    
    total_prompts = len(logs)
    blocked = sum(1 for log in logs if log.get("status") == "BLOCKED")
    flagged = sum(1 for log in logs if log.get("status") == "FLAGGED")
    allowed = sum(1 for log in logs if log.get("status") == "ALLOWED")
    
    pii_detected = sum(1 for log in logs if log.get("pii_detected"))
    injection_detected = sum(1 for log in logs if log.get("metadata", {}).get("injection_detected"))
    high_toxicity = sum(1 for log in logs if log.get("toxicity_score", 0) > 0.7)
    
    return {
        "total_prompts": total_prompts,
        "blocked": blocked,
        "flagged": flagged,
        "allowed": allowed,
        "pii_detected": pii_detected,
        "injection_attempts": injection_detected,
        "high_toxicity": high_toxicity,
        "block_rate": round((blocked / total_prompts * 100) if total_prompts > 0 else 0, 2)
    }


@dashboard_router.get("/stats/timeseries")
async def get_timeseries_data(
    days: int = 7,
    auth_token: Optional[str] = Cookie(None),
    authorization: Optional[str] = Header(None)  # type: ignore
):
    """Get time series data for threat categories over specified days."""
    token = auth_token
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]
    check_dashboard_access(token)
    
    logs = db.get_all_logs()
    cutoff_date = datetime.now() - timedelta(days=days)
    
    # Initialize data structure
    daily_stats = defaultdict(lambda: {
        "blocked": 0,
        "flagged": 0,
        "allowed": 0,
        "pii": 0,
        "injection": 0,
        "toxicity": 0
    })
    
    for log in logs:
        try:
            timestamp = datetime.fromisoformat(log.get("timestamp", "").replace("Z", "+00:00"))
            if timestamp < cutoff_date:
                continue
            
            date_key = timestamp.strftime("%Y-%m-%d")
            status = log.get("status", "ALLOWED")
            
            if status == "BLOCKED":
                daily_stats[date_key]["blocked"] += 1
            elif status == "FLAGGED":
                daily_stats[date_key]["flagged"] += 1
            else:
                daily_stats[date_key]["allowed"] += 1
            
            if log.get("pii_detected"):
                daily_stats[date_key]["pii"] += 1
            
            if log.get("metadata", {}).get("injection_detected"):
                daily_stats[date_key]["injection"] += 1
            
            if log.get("toxicity_score", 0) > 0.5:
                daily_stats[date_key]["toxicity"] += 1
        except Exception:
            continue
    
    # Convert to array format for charting
    dates = sorted(daily_stats.keys())
    return {
        "labels": dates,
        "datasets": {
            "blocked": [daily_stats[d]["blocked"] for d in dates],
            "flagged": [daily_stats[d]["flagged"] for d in dates],
            "allowed": [daily_stats[d]["allowed"] for d in dates],
            "pii": [daily_stats[d]["pii"] for d in dates],
            "injection": [daily_stats[d]["injection"] for d in dates],
            "toxicity": [daily_stats[d]["toxicity"] for d in dates]
        }
    }


@dashboard_router.get("/stats/pii-trends")
async def get_pii_trends(
    auth_token: Optional[str] = Cookie(None),
    authorization: Optional[str] = Header(None)  # type: ignore
):
    """Get PII detection trends by category."""
    token = auth_token
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]
    check_dashboard_access(token)
    
    logs = db.get_all_logs()
    
    pii_categories = defaultdict(int)
    
    for log in logs:
        pii_types = log.get("pii_types", [])
        for pii_type in pii_types:
            pii_categories[pii_type] += 1
    
    return {
        "labels": list(pii_categories.keys()),
        "data": list(pii_categories.values())
    }


@dashboard_router.get("/stats/toxicity-heatmap")
async def get_toxicity_heatmap(
    auth_token: Optional[str] = Cookie(None),
    authorization: Optional[str] = Header(None)  # type: ignore
):
    """Get toxicity score distribution for heatmap visualization."""
    token = auth_token
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]
    check_dashboard_access(token)
    
    logs = db.get_all_logs()
    
    # Create score buckets
    buckets = {
        "0.0-0.2": 0,
        "0.2-0.4": 0,
        "0.4-0.6": 0,
        "0.6-0.8": 0,
        "0.8-1.0": 0
    }
    
    for log in logs:
        score = log.get("toxicity_score", 0)
        if score < 0.2:
            buckets["0.0-0.2"] += 1
        elif score < 0.4:
            buckets["0.2-0.4"] += 1
        elif score < 0.6:
            buckets["0.4-0.6"] += 1
        elif score < 0.8:
            buckets["0.6-0.8"] += 1
        else:
            buckets["0.8-1.0"] += 1
    
    return {
        "labels": list(buckets.keys()),
        "data": list(buckets.values())
    }


@dashboard_router.get("/stats/injection-attempts")
async def get_injection_attempts(
    days: int = 30,
    auth_token: Optional[str] = Cookie(None),
    authorization: Optional[str] = Header(None)  # type: ignore
):
    """Get injection attempt statistics over time."""
    token = auth_token
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]
    check_dashboard_access(token)
    
    logs = db.get_all_logs()
    cutoff_date = datetime.now() - timedelta(days=days)
    
    injection_types = defaultdict(int)
    daily_injections = defaultdict(int)
    
    for log in logs:
        try:
            timestamp = datetime.fromisoformat(log.get("timestamp", "").replace("Z", "+00:00"))
            if timestamp < cutoff_date:
                continue
            
            metadata = log.get("metadata", {})
            if metadata.get("injection_detected"):
                date_key = timestamp.strftime("%Y-%m-%d")
                daily_injections[date_key] += 1
                
                matched_rule = metadata.get("injection_rule", "unknown")
                injection_types[matched_rule] += 1
        except Exception:
            continue
    
    dates = sorted(daily_injections.keys())
    
    return {
        "timeline": {
            "labels": dates,
            "data": [daily_injections[d] for d in dates]
        },
        "types": {
            "labels": list(injection_types.keys()),
            "data": list(injection_types.values())
        }
    }


@dashboard_router.get("/stats/weekly-summary")
async def get_weekly_summary(
    auth_token: Optional[str] = Cookie(None),
    authorization: Optional[str] = Header(None)  # type: ignore
):
    """Get weekly summary statistics."""
    token = auth_token
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]
    check_dashboard_access(token)
    
    logs = db.get_all_logs()
    week_ago = datetime.now() - timedelta(days=7)
    
    weekly_logs = []
    for log in logs:
        try:
            timestamp = datetime.fromisoformat(log.get("timestamp", "").replace("Z", "+00:00"))
            if timestamp >= week_ago:
                weekly_logs.append(log)
        except Exception:
            continue
    
    total_this_week = len(weekly_logs)
    blocked_this_week = sum(1 for log in weekly_logs if log.get("status") == "BLOCKED")
    pii_this_week = sum(1 for log in weekly_logs if log.get("pii_detected"))
    injection_this_week = sum(1 for log in weekly_logs if log.get("metadata", {}).get("injection_detected"))
    
    avg_toxicity = (
        sum(log.get("toxicity_score", 0) for log in weekly_logs) / total_this_week
        if total_this_week > 0 else 0
    )
    
    return {
        "total_prompts": total_this_week,
        "blocked_prompts": blocked_this_week,
        "pii_detected": pii_this_week,
        "injection_attempts": injection_this_week,
        "avg_toxicity_score": round(avg_toxicity, 3),
        "block_rate_percent": round((blocked_this_week / total_this_week * 100) if total_this_week > 0 else 0, 2)
    }

