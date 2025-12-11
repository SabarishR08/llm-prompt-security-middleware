"""Authentication routes for RBAC system (JWT + bcrypt)."""
from fastapi import APIRouter, HTTPException, Cookie, Response, Header
from typing import Optional, Dict, Any
from pydantic import BaseModel
from core.utils.auth import USERS_DB, UserRole, Permission, jwt_manager, verify_password

auth_router = APIRouter(prefix="/api/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    """Login request model."""
    username: str
    password: str
    role: Optional[str] = None


@auth_router.post("/login")
async def login(login_data: LoginRequest, response: Response) -> Dict[str, Any]:
    """Authenticate user and issue JWT tokens."""
    user = USERS_DB.get(login_data.username)

    if not user or not verify_password(login_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    requested_role = (login_data.role or user.role.value).lower()
    if requested_role != user.role.value:
        raise HTTPException(status_code=403, detail="User has no access to the Log Dashboard. Only Admin and Moderator roles allowed." )

    access_token = jwt_manager.create_access_token(user.username, user.role)
    refresh_token = jwt_manager.create_refresh_token(user.username, user.role)

    # Set HttpOnly cookies for browser flows
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=jwt_manager.access_ttl_minutes * 60,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=jwt_manager.refresh_ttl_minutes * 60,
    )

    return {
        "status": "success",
        "username": user.username,
        "role": user.role.value,
        "permissions": user.get_permissions(),
        "access_token": access_token,
        "refresh_token": refresh_token,
    }


@auth_router.post("/logout")
async def logout(response: Response = None) -> Dict[str, str]:
    """Logout user by clearing cookies."""
    if response:
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
    return {"status": "success", "message": "Logged out successfully"}


@auth_router.post("/refresh")
async def refresh_token(refresh_token: Optional[str] = Cookie(None), authorization: Optional[str] = Header(None)):  # type: ignore
    token = refresh_token
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]
    if not token:
        raise HTTPException(status_code=401, detail="Refresh token missing")
    payload = jwt_manager.verify_token(token, refresh=True)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    username = payload.get("username") or payload.get("sub")
    role_val = payload.get("role")
    if not username or not role_val:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    role = UserRole(role_val)
    access_token = jwt_manager.create_access_token(username, role)
    return {"access_token": access_token}


@auth_router.get("/verify")
async def verify_token(access_token: Optional[str] = Cookie(None), authorization: Optional[str] = Header(None)) -> Dict[str, Any]:  # type: ignore
    """Verify if user is authenticated."""
    token = access_token
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1]
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = jwt_manager.verify_token(token, refresh=False)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = USERS_DB.get(payload.get("username") or payload.get("sub"))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return {
        "authenticated": True,
        "username": user.username,
        "role": payload.get("role"),
        "permissions": user.get_permissions()
    }


@auth_router.get("/check-permission/{permission}")
async def check_permission(permission: str, auth_token: Optional[str] = Cookie(None)) -> Dict[str, Any]:
    """Check if user has a specific permission."""
    if not auth_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session_data = jwt_manager.verify_token(auth_token or "", refresh=False)
    if not session_data:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user = USERS_DB.get(session_data.get("username") or session_data.get("sub"))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    # Check if permission exists
    try:
        perm = Permission(permission)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid permission")
    
    has_perm = user.has_permission(perm)
    
    return {
        "username": user.username,
        "permission": permission,
        "has_permission": has_perm,
        "role": user.role.value
    }


@auth_router.get("/user-info")
async def get_user_info(auth_token: Optional[str] = Cookie(None)) -> Dict[str, Any]:
    """Get current user information."""
    if not auth_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session_data = jwt_manager.verify_token(auth_token or "", refresh=False)
    if not session_data:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user = USERS_DB.get(session_data.get("username") or session_data.get("sub"))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return {
        "username": user.username,
        "role": user.role.value,
        "created_at": user.created_at.isoformat(),
        "permissions": user.get_permissions()
    }


@auth_router.get("/demo-users")
async def get_demo_users() -> Dict[str, Any]:
    """Get demo users for testing (remove in production)."""
    return {
        "demo_users": [
            {"username": "admin", "password": "admin123", "role": "Admin", "permissions": "All"},
            {"username": "moderator", "password": "mod123", "role": "Moderator", "permissions": "View, Export, Analytics"},
            {"username": "viewer", "password": "viewer123", "role": "Viewer", "permissions": "View only"},
        ]
    }

