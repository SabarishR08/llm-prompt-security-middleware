"""
Centralized Logging Configuration
Production-grade logging with structured output and rotation.
"""
import logging
import logging.handlers
import sys
from pathlib import Path
from datetime import datetime
from typing import Any, Dict
import json


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "ip_address"):
            log_data["ip_address"] = record.ip_address
        
        return json.dumps(log_data)


def setup_logging(
    log_level: str = "INFO",
    log_file: str = "logs/app.log",
    max_bytes: int = 10485760,  # 10MB
    backup_count: int = 5,
    enable_json: bool = True,
) -> None:
    """
    Setup application logging with file rotation and structured output.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file
        max_bytes: Maximum log file size before rotation
        backup_count: Number of backup files to keep
        enable_json: Enable JSON formatted logs
    """
    # Create logs directory if it doesn't exist
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create formatters
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    
    file_formatter = JSONFormatter() if enable_json else console_formatter
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(console_formatter)
    
    # Create rotating file handler
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(file_formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # Reduce noise from third-party libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    
    logging.info(f"Logging configured: level={log_level}, file={log_file}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.
    
    Args:
        name: Logger name (usually __name__)
    
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


class LoggerAdapter(logging.LoggerAdapter):
    """Custom logger adapter for adding context to logs."""
    
    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """Add extra context to log messages."""
        extra = kwargs.get("extra", {})
        
        # Add context from adapter
        for key, value in self.extra.items():
            if key not in extra:
                extra[key] = value
        
        kwargs["extra"] = extra
        return msg, kwargs


def get_request_logger(request_id: str, user_id: str = None, ip_address: str = None) -> LoggerAdapter:
    """
    Get a logger with request context.
    
    Args:
        request_id: Unique request identifier
        user_id: User identifier (optional)
        ip_address: Client IP address (optional)
    
    Returns:
        Logger adapter with request context
    """
    logger = logging.getLogger("request")
    
    extra = {"request_id": request_id}
    if user_id:
        extra["user_id"] = user_id
    if ip_address:
        extra["ip_address"] = ip_address
    
    return LoggerAdapter(logger, extra)
