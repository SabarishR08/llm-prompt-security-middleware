"""
This module imports from main.py which contains the refactored FastAPI application.
The original monolithic app.py has been modularized into:
  - config/ : Settings and configuration management
  - models/ : Data models and database management
  - services/ : Business logic (PII, toxicity, rules, Gemini)
  - routes/ : API endpoint routers
  - utils/ : Helper utilities (alerts, caching)
  - main.py : Main FastAPI application entry point

For development:
  uvicorn app:app --reload

For production:
  uvicorn app:app --host 0.0.0.0 --port 8000
"""

from main import app

__all__ = ["app"]
