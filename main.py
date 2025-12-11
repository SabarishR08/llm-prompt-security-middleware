from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from contextlib import asynccontextmanager
import os
from dotenv import load_dotenv

# Routers
from api.routes.analysis_router import analysis_router
from api.routes.logs_router import logs_router
from api.routes.auth_router import auth_router
from api.routes.dashboard_router import dashboard_router
from api.routes.health_router import health_router

# Industrial-Grade Configuration
from core.config.app_config import get_config
from core.config.logging_config import setup_logging, get_logger

# Middleware
from core.middleware.rate_limit import RateLimitMiddleware
from core.middleware.request_id import RequestIDMiddleware
from core.middleware.security_headers import SecurityHeadersMiddleware
from core.middleware.performance import PerformanceMiddleware

# Config & Services
from core.config.settings_loader import load_settings
from core.models.database import DatabaseManager
from core.services.gemini_service import GeminiService

# Utils
from core.utils.cache import Cache
from core.utils.exceptions import build_error_response

# Load environment variables
load_dotenv()

# Initialize industrial-grade configuration
config = get_config()

# Setup structured logging with config values
setup_logging(log_level=config.LOG_LEVEL, log_file=config.LOG_FILE)
logger = get_logger(__name__)


# Global service instances (initialized in lifespan)
gemini_service = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager for startup/shutdown events."""
    global gemini_service
    
    # ---- Application Startup ----
    logger.info("🚀 Starting AI Security Compliance System", extra={
        "environment": config.ENVIRONMENT,
        "version": "2.0.0"
    })
    
    # Store configuration in app state
    app.state.config = config
    
    # Load legacy settings (for backward compatibility)
    settings = load_settings()
    app.state.settings = settings
    logger.info("⚙️ Configuration loaded successfully")
    
    # Configure Gemini API
    gemini_service = GeminiService()
    api_key = os.getenv("GEMINI_API_KEY", settings.get("GEMINI_API_KEY", ""))
    if api_key:
        gemini_service.configure(api_key)
        logger.info("✅ Gemini API configured")
    else:
        logger.warning("⚠️ GEMINI_API_KEY not found in environment variables")
    app.state.gemini = gemini_service
    
    # Initialize Database Manager
    db_manager = DatabaseManager()
    app.state.db = db_manager
    logger.info("🗄️ Database initialized", extra={
        "database_url": config.get_database_config()["url"][:20] + "..."
    })
    
    # Initialize Cache
    app.state.cache = Cache()
    logger.info("💾 Cache initialized")
    
    logger.info("✅ Application started successfully in %s mode", config.ENVIRONMENT)
    yield
    
    # ---- Application Shutdown ----
    logger.info("🛑 Shutting down application...")
    db_manager.close()
    logger.info("✅ Application stopped gracefully.")


# ---------------------------------
# MAIN FASTAPI APPLICATION
# ---------------------------------
app = FastAPI(
    title="AI Security Compliance System",
    description="Enterprise-Grade AI Security Log Analyzer with PII, Toxicity, Policy-Violation Detection, Threat Intelligence & Advanced Analytics",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/api/docs" if config.ENVIRONMENT != "production" else None,
    redoc_url="/api/redoc" if config.ENVIRONMENT != "production" else None,
    openapi_url="/api/openapi.json" if config.ENVIRONMENT != "production" else None,
)

# ---------------------------------
# MIDDLEWARE STACK (Order matters!)
# ---------------------------------

# 1. Request ID Middleware (first - for tracking)
app.add_middleware(RequestIDMiddleware)
logger.info("✅ Request ID middleware registered")

# 2. Performance Monitoring Middleware
app.add_middleware(PerformanceMiddleware)
logger.info("✅ Performance monitoring middleware registered")

# 3. Security Headers Middleware
app.add_middleware(SecurityHeadersMiddleware)
logger.info("✅ Security headers middleware registered")

# 4. Rate Limiting Middleware
if config.RATE_LIMIT_ENABLED:
    app.add_middleware(
        RateLimitMiddleware,
        requests=config.RATE_LIMIT_REQUESTS,
        window=config.RATE_LIMIT_WINDOW
    )
    logger.info("✅ Rate limiting middleware registered (%d req/%ds)", 
                config.RATE_LIMIT_REQUESTS, config.RATE_LIMIT_WINDOW)

# 5. CORS Middleware (last in chain)
cors_origins = config.CORS_ORIGINS if isinstance(config.CORS_ORIGINS, list) else config.CORS_ORIGINS.split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)
logger.info("🌐 CORS middleware configured for origins: %s", cors_origins)

# ---------------------------------
# STATIC FILES & ROUTERS
# ---------------------------------

# Mount static files
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
logger.info("📁 Static files mounted at /static")

# Include API Routers
app.include_router(health_router, tags=["Health & Monitoring"])
app.include_router(analysis_router, tags=["Analysis"])
app.include_router(logs_router, tags=["Logs"])
app.include_router(auth_router, tags=["Authentication"])
app.include_router(dashboard_router, tags=["Dashboard & Analytics"])
logger.info("🔌 All API routers registered")


# ---------------------------------
# API ENDPOINTS
# ---------------------------------

@app.get("/", response_class=HTMLResponse)
async def index():
    """Serve the frontend index.html."""
    logger.info("📄 Serving index.html")
    try:
        with open("frontend/templates/index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        logger.warning("frontend/templates/index.html not found, serving fallback page")
        return """
        <html>
            <head>
                <title>AI Security Compliance System</title>
                <style>
                    body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
                    h1 { color: #2563eb; }
                    .badge { background: #10b981; color: white; padding: 4px 8px; border-radius: 4px; }
                    code { background: #f3f4f6; padding: 2px 6px; border-radius: 3px; }
                </style>
            </head>
            <body>
                <h1>🔒 AI Security Compliance System</h1>
                <p><span class="badge">v2.0.0</span> <span class="badge">PRODUCTION</span></p>
                <h2>Available Endpoints:</h2>
                <ul>
                    <li><a href="/api/docs">📚 API Documentation (Swagger UI)</a></li>
                    <li><a href="/api/redoc">📖 API Documentation (ReDoc)</a></li>
                    <li><a href="/health/">🏥 Health Checks</a></li>
                    <li><a href="/health/metrics">📊 System Metrics</a></li>
                </ul>
                <h3>Features:</h3>
                <ul>
                    <li>✅ PII Detection & Masking</li>
                    <li>✅ Toxicity Analysis</li>
                    <li>✅ Policy Violation Detection</li>
                    <li>✅ Prompt Injection Prevention</li>
                    <li>✅ Threat Intelligence Integration</li>
                    <li>✅ JWT Authentication & RBAC</li>
                    <li>✅ Real-time Alerts (Email/SMS)</li>
                    <li>✅ Advanced Analytics Dashboard</li>
                </ul>
            </body>
        </html>
        """

@app.get("/settings")
async def get_settings():
    """Get non-sensitive application settings."""
    settings = load_settings()
    # Filter out sensitive information
    safe_settings = {
        k: v for k, v in settings.items() 
        if not any(secret in k.lower() for secret in ["api", "key", "secret", "password", "token"])
    }
    safe_settings["environment"] = config.ENVIRONMENT
    safe_settings["version"] = "2.0.0"
    safe_settings["rate_limiting_enabled"] = config.RATE_LIMIT_ENABLED
    return safe_settings

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """Favicon endpoint."""
    return ""


# ---------------------------------
# RUN APPLICATION
# ---------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


