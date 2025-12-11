# Configuration Management

Configuration loading, validation, and logging setup.

## Files

### `app_config.py`
Loads and validates application configuration from environment variables and `.env` file.

**Features:**
- Environment variable parsing
- Type validation
- Default values
- Required field checking

**Usage:**
```python
from core.config.app_config import get_config

config = get_config()
print(config.GEMINI_API_KEY)
print(config.PII_THRESHOLD)
```

---

### `logging_config.py`
Configures structured logging (console + file output).

**Features:**
- JSON-formatted logs
- Log rotation (max 10MB per file)
- Separate log levels for console and file
- Request ID correlation

**Usage:**
```python
from core.config.logging_config import setup_logging

logger = setup_logging()
logger.info("Application started", extra={"version": "1.0"})
```

**Log Format:**
```json
{
  "timestamp": "2025-12-11T10:30:00Z",
  "level": "INFO",
  "message": "Request processed",
  "request_id": "uuid-here",
  "duration_ms": 45
}
```

---

### `settings_loader.py`
Loads rules and thresholds from JSON configuration files.

**Features:**
- Hot-reload of settings
- Schema validation
- Merge with environment overrides

**Usage:**
```python
from core.config.settings_loader import load_settings

settings = load_settings("settings.json")
print(settings["toxicity_threshold"])
```

**Settings Structure:**
```json
{
  "thresholds": {
    "pii": 0.5,
    "toxicity": 0.7,
    "injection": 0.6
  },
  "rules": [
    {
      "id": "block_pii",
      "enabled": true,
      "action": "BLOCK"
    }
  ]
}
```

---

## Environment Variables

Key configuration variables:

```bash
# API Keys
GEMINI_API_KEY=your_key
VIRUSTOTAL_API_KEY=your_key
GOOGLE_SAFEBROWSING_API_KEY=your_key

# Thresholds
PII_THRESHOLD=0.5
TOXICITY_THRESHOLD=0.7
INJECTION_THRESHOLD=0.6

# Security
JWT_SECRET_KEY=your-secret-min-32-chars
JWT_EXPIRATION_HOURS=24

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
```
