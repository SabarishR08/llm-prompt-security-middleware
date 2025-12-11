"""Authentication and authorization utilities for RBAC with JWT + bcrypt."""
from typing import Optional, List, Dict
from datetime import datetime, timedelta
import os
import secrets
import hashlib
from enum import Enum

try:
    import bcrypt  # type: ignore
    BCRYPT_AVAILABLE = True
except ImportError:  # pragma: no cover - fallback path
    BCRYPT_AVAILABLE = False

import jwt


class UserRole(str, Enum):
    """User roles for the system."""
    ADMIN = "admin"
    MODERATOR = "moderator"
    VIEWER = "viewer"


class Permission(str, Enum):
    """Permissions in the system."""
    VIEW_LOGS = "view_logs"
    CLEAR_LOGS = "clear_logs"
    EXPORT_LOGS = "export_logs"
    VIEW_SETTINGS = "view_settings"
    CHANGE_SETTINGS = "change_settings"
    MANAGE_USERS = "manage_users"
    VIEW_ANALYTICS = "view_analytics"


# Role-based permissions mapping
ROLE_PERMISSIONS = {
    UserRole.ADMIN: [
        Permission.VIEW_LOGS,
        Permission.CLEAR_LOGS,
        Permission.EXPORT_LOGS,
        Permission.VIEW_SETTINGS,
        Permission.CHANGE_SETTINGS,
        Permission.MANAGE_USERS,
        Permission.VIEW_ANALYTICS,
    ],
    UserRole.MODERATOR: [
        Permission.VIEW_LOGS,
        Permission.EXPORT_LOGS,
        Permission.VIEW_SETTINGS,
        Permission.VIEW_ANALYTICS,
    ],
    UserRole.VIEWER: [
        Permission.VIEW_LOGS,
    ],
}


def hash_password(password: str) -> str:
    """Hash a password using bcrypt when available, fallback to SHA256."""
    if BCRYPT_AVAILABLE:
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode(), salt).decode()
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against the stored hash."""
    if BCRYPT_AVAILABLE and password_hash.startswith("$2"):
        try:
            return bcrypt.checkpw(password.encode(), password_hash.encode())
        except ValueError:
            return False
    return hashlib.sha256(password.encode()).hexdigest() == password_hash


class User:
    """In-memory user model."""

    def __init__(self, username: str, password: str, role: UserRole):
        self.username = username
        self.password_hash = hash_password(password)
        self.role = role
        self.created_at = datetime.now()

    def check_password(self, password: str) -> bool:
        return verify_password(password, self.password_hash)

    def has_permission(self, permission: Permission) -> bool:
        return permission in ROLE_PERMISSIONS.get(self.role, [])

    def get_permissions(self) -> List[str]:
        return [p.value for p in ROLE_PERMISSIONS.get(self.role, [])]


# Sample users (in production, use a database)
USERS_DB: Dict[str, User] = {
    "admin": User("admin", "admin123", UserRole.ADMIN),
    "moderator": User("moderator", "mod123", UserRole.MODERATOR),
    "viewer": User("viewer", "viewer123", UserRole.VIEWER),
}


class JWTManager:
    """Issue and verify JWT access/refresh tokens."""

    def __init__(self):
        self.secret = os.getenv("SECRET_KEY", "change-me")
        self.refresh_secret = os.getenv("REFRESH_SECRET_KEY", self.secret + "-refresh")
        self.algorithm = "HS256"
        self.access_ttl_minutes = int(os.getenv("ACCESS_TOKEN_MINUTES", "60"))
        self.refresh_ttl_minutes = int(os.getenv("REFRESH_TOKEN_MINUTES", "4320"))  # 3 days

    def create_access_token(self, username: str, role: UserRole) -> str:
        payload = {
            "sub": username,
            "role": role.value,
            "type": "access",
            "exp": datetime.utcnow() + timedelta(minutes=self.access_ttl_minutes),
        }
        return jwt.encode(payload, self.secret, algorithm=self.algorithm)

    def create_refresh_token(self, username: str, role: UserRole) -> str:
        payload = {
            "sub": username,
            "role": role.value,
            "type": "refresh",
            "exp": datetime.utcnow() + timedelta(minutes=self.refresh_ttl_minutes),
        }
        return jwt.encode(payload, self.refresh_secret, algorithm=self.algorithm)

    def verify_token(self, token: str, refresh: bool = False) -> Optional[Dict[str, str]]:
        try:
            secret = self.refresh_secret if refresh else self.secret
            payload = jwt.decode(token, secret, algorithms=[self.algorithm])
            return {"username": payload.get("sub"), "role": payload.get("role"), "type": payload.get("type")}
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None


jwt_manager = JWTManager()


def require_role(*allowed_roles: UserRole):
    """Helper to check if role is allowed."""
    def checker(role_value: str) -> bool:
        return role_value in [r.value for r in allowed_roles]

    return checker
