"""
Input Validation and Sanitization
Comprehensive validation for all user inputs.
"""
import re
from typing import Any, Optional
from pydantic import BaseModel, Field, validator, EmailStr
from datetime import datetime


class PromptRequest(BaseModel):
    """Validated prompt analysis request."""
    
    prompt: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="Text prompt to analyze"
    )
    metadata: Optional[dict] = Field(
        default=None,
        description="Optional metadata"
    )
    
    @validator('prompt')
    def sanitize_prompt(cls, v):
        """Sanitize prompt input."""
        if not v or not v.strip():
            raise ValueError("Prompt cannot be empty")
        
        # Remove null bytes
        v = v.replace('\x00', '')
        
        # Limit consecutive whitespace
        v = re.sub(r'\s+', ' ', v)
        
        return v.strip()
    
    class Config:
        schema_extra = {
            "example": {
                "prompt": "Analyze this text for security issues",
                "metadata": {"source": "web_form"}
            }
        }


class LoginRequest(BaseModel):
    """Validated login request."""
    
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        regex=r'^[a-zA-Z0-9_-]+$',
        description="Username (alphanumeric, underscore, hyphen only)"
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password"
    )
    role: str = Field(
        ...,
        regex=r'^(admin|moderator|viewer)$',
        description="User role"
    )
    
    @validator('username')
    def validate_username(cls, v):
        """Additional username validation."""
        if v.lower() in ['admin', 'root', 'system']:
            # Allow but log suspicious usernames
            pass
        return v.lower()
    
    class Config:
        schema_extra = {
            "example": {
                "username": "john_doe",
                "password": "SecurePass123!",
                "role": "moderator"
            }
        }


class TokenRefreshRequest(BaseModel):
    """Validated token refresh request."""
    
    refresh_token: str = Field(
        ...,
        min_length=10,
        description="JWT refresh token"
    )


class AlertConfigRequest(BaseModel):
    """Validated alert configuration request."""
    
    alert_level: str = Field(
        ...,
        regex=r'^(low|medium|high|critical)$',
        description="Minimum alert severity"
    )
    email: Optional[EmailStr] = Field(
        default=None,
        description="Alert email address"
    )
    phone: Optional[str] = Field(
        default=None,
        regex=r'^\+?[1-9]\d{1,14}$',
        description="Alert phone number (E.164 format)"
    )


class PaginationParams(BaseModel):
    """Validated pagination parameters."""
    
    page: int = Field(
        default=1,
        ge=1,
        le=1000,
        description="Page number"
    )
    page_size: int = Field(
        default=50,
        ge=1,
        le=100,
        description="Items per page"
    )
    
    @property
    def offset(self) -> int:
        """Calculate offset for database query."""
        return (self.page - 1) * self.page_size


class DateRangeFilter(BaseModel):
    """Validated date range filter."""
    
    start_date: Optional[datetime] = Field(
        default=None,
        description="Start date (ISO format)"
    )
    end_date: Optional[datetime] = Field(
        default=None,
        description="End date (ISO format)"
    )
    
    @validator('end_date')
    def validate_date_range(cls, v, values):
        """Ensure end_date is after start_date."""
        if v and values.get('start_date') and v < values['start_date']:
            raise ValueError("end_date must be after start_date")
        return v


# Utility functions for sanitization
def sanitize_sql_input(value: str) -> str:
    """
    Sanitize input to prevent SQL injection.
    Note: Use parameterized queries instead when possible.
    """
    if not value:
        return value
    
    # Remove dangerous SQL keywords
    dangerous_patterns = [
        r';\s*drop\s+',
        r';\s*delete\s+',
        r';\s*update\s+',
        r';\s*insert\s+',
        r'--',
        r'/\*',
        r'\*/',
        r'xp_',
        r'sp_',
    ]
    
    for pattern in dangerous_patterns:
        value = re.sub(pattern, '', value, flags=re.IGNORECASE)
    
    return value


def sanitize_html(value: str) -> str:
    """Remove HTML tags and dangerous characters."""
    if not value:
        return value
    
    # Remove HTML tags
    value = re.sub(r'<[^>]+>', '', value)
    
    # Remove script tags explicitly
    value = re.sub(r'<script[^>]*>.*?</script>', '', value, flags=re.IGNORECASE | re.DOTALL)
    
    # Remove dangerous characters
    value = value.replace('<', '&lt;').replace('>', '&gt;')
    
    return value


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal."""
    if not filename:
        return filename
    
    # Remove path separators
    filename = filename.replace('/', '_').replace('\\', '_')
    
    # Remove dangerous characters
    filename = re.sub(r'[^\w\s.-]', '', filename)
    
    # Remove leading dots and spaces
    filename = filename.lstrip('. ')
    
    # Limit length
    return filename[:255]


def validate_email(email: str) -> bool:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_phone(phone: str) -> bool:
    """Validate phone number (E.164 format)."""
    pattern = r'^\+?[1-9]\d{1,14}$'
    return bool(re.match(pattern, phone))


def validate_url(url: str) -> bool:
    """Validate URL format."""
    pattern = r'^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/.*)?$'
    return bool(re.match(pattern, url))
