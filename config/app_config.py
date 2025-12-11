"""
Application Configuration Module
Centralized configuration management with environment-specific settings.
"""
import os
from typing import Any, Dict, Optional
from enum import Enum
from pathlib import Path
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()


class Environment(str, Enum):
    """Application environment types."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class Config:
    """Base configuration class."""
    
    # Application
    APP_NAME: str = "AI Security Compliance System"
    APP_VERSION: str = "3.0.0"
    ENVIRONMENT: Environment = Environment(os.getenv("ENVIRONMENT", "development"))
    DEBUG: bool = ENVIRONMENT == Environment.DEVELOPMENT
    
    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    WORKERS: int = int(os.getenv("WORKERS", "4"))
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-this-in-production-please")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", SECRET_KEY)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    CORS_ORIGINS: list = os.getenv("CORS_ORIGINS", "*").split(",")
    CORS_ALLOW_CREDENTIALS: bool = True
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
    RATE_LIMIT_REQUESTS: int = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
    RATE_LIMIT_WINDOW: int = int(os.getenv("RATE_LIMIT_WINDOW", "60"))  # seconds
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./logs.db")
    DATABASE_POOL_SIZE: int = int(os.getenv("DATABASE_POOL_SIZE", "10"))
    DATABASE_MAX_OVERFLOW: int = int(os.getenv("DATABASE_MAX_OVERFLOW", "20"))
    
    # Cache
    REDIS_URL: Optional[str] = os.getenv("REDIS_URL", None)
    CACHE_TTL: int = int(os.getenv("CACHE_TTL", "3600"))  # 1 hour
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/app.log")
    LOG_MAX_BYTES: int = 10485760  # 10MB
    LOG_BACKUP_COUNT: int = 5
    
    # Monitoring
    SENTRY_DSN: Optional[str] = os.getenv("SENTRY_DSN", None)
    ENABLE_METRICS: bool = os.getenv("ENABLE_METRICS", "false").lower() == "true"
    
    # Security Settings
    MAX_PROMPT_LENGTH: int = int(os.getenv("MAX_PROMPT_LENGTH", "5000"))
    MAX_PROMPT_TOKENS: int = int(os.getenv("MAX_PROMPT_TOKENS", "2000"))
    MAX_PAYLOAD_SIZE: int = int(os.getenv("MAX_PAYLOAD_SIZE", "10240"))
    
    # API Keys
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    VIRUSTOTAL_API_KEY: str = os.getenv("VIRUSTOTAL_API_KEY", "")
    GOOGLE_SAFEBROWSING_API_KEY: str = os.getenv("GOOGLE_SAFEBROWSING_API_KEY", "")
    ABUSEIPDB_API_KEY: str = os.getenv("ABUSEIPDB_API_KEY", "")
    
    # Alert Settings
    ALERT_LEVEL: str = os.getenv("ALERT_LEVEL", "high")
    SMTP_HOST: str = os.getenv("SMTP_HOST", "")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: str = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM_EMAIL: str = os.getenv("SMTP_FROM_EMAIL", "")
    SMTP_TO_EMAIL: str = os.getenv("SMTP_TO_EMAIL", "")
    
    SENDGRID_API_KEY: str = os.getenv("SENDGRID_API_KEY", "")
    SENDGRID_FROM_EMAIL: str = os.getenv("SENDGRID_FROM_EMAIL", "")
    SENDGRID_TO_EMAIL: str = os.getenv("SENDGRID_TO_EMAIL", "")
    
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_FROM_NUMBER: str = os.getenv("TWILIO_FROM_NUMBER", "")
    TWILIO_TO_NUMBER: str = os.getenv("TWILIO_TO_NUMBER", "")
    
    @classmethod
    def load_from_file(cls, file_path: str = "settings.json") -> Dict[str, Any]:
        """Load additional settings from JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    @classmethod
    def validate(cls) -> bool:
        """Validate critical configuration settings."""
        errors = []
        
        if cls.ENVIRONMENT == Environment.PRODUCTION:
            if cls.SECRET_KEY == "change-this-in-production-please":
                errors.append("SECRET_KEY must be changed in production")
            
            if cls.DEBUG:
                errors.append("DEBUG must be False in production")
            
            if "*" in cls.CORS_ORIGINS:
                errors.append("CORS_ORIGINS should not allow all origins in production")
        
        if errors:
            raise ValueError(f"Configuration validation failed: {', '.join(errors)}")
        
        return True
    
    @classmethod
    def get_database_config(cls) -> Dict[str, Any]:
        """Get database configuration."""
        return {
            "url": cls.DATABASE_URL,
            "pool_size": cls.DATABASE_POOL_SIZE,
            "max_overflow": cls.DATABASE_MAX_OVERFLOW,
            "echo": cls.DEBUG,
        }
    
    @classmethod
    def get_logging_config(cls) -> Dict[str, Any]:
        """Get logging configuration."""
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": cls.LOG_FORMAT,
                },
                "json": {
                    "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                    "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": cls.LOG_LEVEL,
                    "formatter": "default",
                    "stream": "ext://sys.stdout",
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": cls.LOG_LEVEL,
                    "formatter": "json",
                    "filename": cls.LOG_FILE,
                    "maxBytes": cls.LOG_MAX_BYTES,
                    "backupCount": cls.LOG_BACKUP_COUNT,
                },
            },
            "root": {
                "level": cls.LOG_LEVEL,
                "handlers": ["console", "file"],
            },
        }


class DevelopmentConfig(Config):
    """Development environment configuration."""
    DEBUG = True
    LOG_LEVEL = "DEBUG"


class ProductionConfig(Config):
    """Production environment configuration."""
    DEBUG = False
    LOG_LEVEL = "WARNING"
    RATE_LIMIT_ENABLED = True


class TestingConfig(Config):
    """Testing environment configuration."""
    ENVIRONMENT = Environment.TESTING
    DATABASE_URL = "sqlite:///./test.db"
    DEBUG = True


# Configuration factory
def get_config() -> Config:
    """Get configuration based on environment."""
    env = os.getenv("ENVIRONMENT", "development")
    
    configs = {
        "development": DevelopmentConfig,
        "production": ProductionConfig,
        "testing": TestingConfig,
        "staging": ProductionConfig,
    }
    
    config_class = configs.get(env, DevelopmentConfig)
    config = config_class()
    
    # Validate configuration
    if env == "production":
        config.validate()
    
    return config


# Global config instance
config = get_config()
