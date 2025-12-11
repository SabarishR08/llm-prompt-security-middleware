"""Logs router for log management endpoints with RBAC protection."""
from fastapi import APIRouter, HTTPException, Cookie, Request, Header
from typing import List, Dict, Any, Optional

from core.models.database import DatabaseManager
from core.models.log_model import LogModel
from core.utils.auth import UserRole, jwt_manager


# Initialize router with prefix
logs_router = APIRouter(prefix="/api/logs", tags=["Logs"])

# Database manager instance
db_manager = DatabaseManager()


def check_logs_access(token: Optional[str] = None) -> str:
    """Verify user has access to logs (Admin or Moderator only)."""
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required - No token provided")

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
        raise HTTPException(status_code=401, detail="Invalid token payload")

    # Only Admin and Moderator can access logs
    if role not in [UserRole.ADMIN, UserRole.MODERATOR]:
        raise HTTPException(
            status_code=403, 
            detail="User has no access to the Log Dashboard. Only Admin and Moderator roles allowed."
        )

    return username


@logs_router.get("/", response_model=Dict[str, List[Dict[str, Any]]])
async def get_logs(auth_token: Optional[str] = Cookie(None), authorization: Optional[str] = Header(None)):  # type: ignore
    """Retrieve all logs from the database. (Admin, Moderator only)"""
    token = auth_token
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]
    username = check_logs_access(token)
    print(f"📋 {username} fetching all logs")
    logs_list = db_manager.get_all_logs()
    db_manager.log_audit(username, "view_logs", "fetch all logs")
    return {"logs": logs_list}


@logs_router.get("/audit", response_model=Dict[str, List[Dict[str, Any]]])
async def get_audit(auth_token: Optional[str] = Cookie(None), authorization: Optional[str] = Header(None)):  # type: ignore
    """Retrieve audit trail (Admin, Moderator only)."""
    token = auth_token
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]
    username = check_logs_access(token)
    print(f"📜 {username} fetching audit trail")
    events = db_manager.get_audit_events()
    db_manager.log_audit(username, "view_audit", "fetch audit trail")
    return {"events": events}


@logs_router.get("/by-status/{status}", response_model=Dict[str, List[Dict[str, Any]]])
async def get_logs_by_status(status: str, auth_token: Optional[str] = Cookie(None), authorization: Optional[str] = Header(None)):  # type: ignore
    """Retrieve logs filtered by status. (Admin, Moderator only)"""
    token = auth_token
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]
    username = check_logs_access(token)
    print(f"📋 {username} fetching logs with status: {status}")
    logs_list = db_manager.get_logs_by_status(status)
    db_manager.log_audit(username, "view_logs", f"fetch logs status={status}")
    return {"logs": logs_list}


@logs_router.post("/clear", response_model=Dict[str, str])
async def clear_logs(auth_token: Optional[str] = Cookie(None), authorization: Optional[str] = Header(None)):  # type: ignore
    """Clear all logs from the database. (Admin only)"""
    token = auth_token
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")

    session_data = jwt_manager.verify_token(token, refresh=False)
    if not session_data:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    username = session_data.get("username") or session_data.get("sub")
    role_val = session_data.get("role")
    try:
        role = UserRole(role_val)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    if role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403, 
            detail="Access denied. Only Admin can clear logs."
        )
    
    if db_manager.clear_logs():
        print(f"🗑️ {username} (Admin) cleared all logs")
        db_manager.log_audit(username, "clear_logs", "cleared all logs")
        return {"detail": "All logs cleared"}
    else:
        raise HTTPException(status_code=500, detail="Failed to clear logs")


@logs_router.get("/count", response_model=Dict[str, int])
async def get_log_count(auth_token: Optional[str] = Cookie(None), authorization: Optional[str] = Header(None)):  # type: ignore
    """Get total count of logs. (Admin, Moderator only)"""
    token = auth_token
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]
    username = check_logs_access(token)
    print(f"📊 {username} fetching log count")
    count = db_manager.get_log_count()
    db_manager.log_audit(username, "view_logs", "count logs")
    return {"count": count}


@logs_router.get("/export/csv", response_model=Dict[str, str])
async def export_logs_csv(auth_token: Optional[str] = Cookie(None), authorization: Optional[str] = Header(None)):  # type: ignore
    """Export logs as CSV. (Admin, Moderator only)"""
    token = auth_token
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]
    username = check_logs_access(token)
    print(f"📥 {username} exporting logs as CSV")
    
    try:
        csv_content = db_manager.export_logs_csv()
        db_manager.log_audit(username, "export_logs", "csv export")
        return {"csv": csv_content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export logs: {str(e)}")


@logs_router.get("/export/json", response_model=Dict[str, List[Dict[str, Any]]])
async def export_logs_json(auth_token: Optional[str] = Cookie(None), authorization: Optional[str] = Header(None)):  # type: ignore
    """Export logs as JSON. (Admin, Moderator only)"""
    token = auth_token
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]
    username = check_logs_access(token)
    print(f"📥 {username} exporting logs as JSON")
    
    logs_list = db_manager.get_all_logs()
    db_manager.log_audit(username, "export_logs", "json export")
    return {"logs": logs_list}


@logs_router.post("/add")
async def add_log(log_data: Dict[str, Any]):
    """Add a log entry to the database (internal use)."""
    try:
        log = LogModel(
            prompt=log_data.get("prompt", ""),
            status=log_data.get("status", ""),
            reasons=log_data.get("reasons", []),
            redacted_prompt=log_data.get("redacted_prompt"),
            gemini_response=log_data.get("gemini_response")
        )
        db_manager.insert_log(log)
        return {"detail": "Log added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add log: {str(e)}")

