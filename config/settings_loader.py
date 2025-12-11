"""Settings loader for the application."""
import json
import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load .env file
load_dotenv()


def load_settings() -> Dict[str, Any]:
    """Load settings from settings.json with environment variable overrides."""
    settings = {}
    settings_path = os.path.join(os.path.dirname(__file__), "settings.json")
    
    try:
        with open(settings_path, "r") as f:
            settings = json.load(f)
            print("✅ Settings loaded from settings.json")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"⚠️ Error loading settings.json: {e}. Using defaults.")
        settings = get_default_settings()
    
    # Override with environment variables
    settings["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY", "")
    settings["ALERT_PII_PATH"] = os.getenv("ALERT_PII_PATH", "sound_alerts/PII_Alert.mp3")
    settings["ALERT_POLICY_PATH"] = os.getenv("ALERT_POLICY_PATH", "sound_alerts/Policy-Violation_Alert.mp3")
    settings["REDIS_URL"] = os.getenv("REDIS_URL", settings.get("REDIS_URL", ""))
    settings["VIRUSTOTAL_API_KEY"] = os.getenv("VIRUSTOTAL_API_KEY", "")
    settings["IPQS_API_KEY"] = os.getenv("IPQS_API_KEY", "")
    settings["ABUSEIPDB_API_KEY"] = os.getenv("ABUSEIPDB_API_KEY", "")
    
    return settings


def get_default_settings() -> Dict[str, Any]:
    """Return default settings if settings.json is not found."""
    return {
        "toxicity_thresholds": {
            "toxicity": 0.5,
            "severe_toxicity": 0.5,
            "obscene": 0.5,
            "threat": 0.5,
            "insult": 0.5,
            "identity_attack": 0.5
        },
        "flagged_keywords": [
            "confidential",
            "secret",
            "private data",
            "internal use",
            "restricted",
            "proprietary"
        ],
        "blocked_keywords": [
            "password",
            "ssn",
            "social security number",
            "credit card",
            "token",
            "api key",
            "private key",
            "secret key"
        ],
        "max_prompt_length": 512,
        "max_payload_size": 10240,
        "max_prompt_tokens": 1500,
        "max_prompt_lines": 50,
        "max_prompt_paragraphs": 20,
        "rate_limit_window_sec": 60,
        "rate_limit_per_window": 30,
        "redis_url": "",
        "database_url": "sqlite:///logs.db",
        "VIRUSTOTAL_API_KEY": "",
        "IPQS_API_KEY": "",
        "ABUSEIPDB_API_KEY": "",
        "analytics_days": 14
    }


def get_setting(key: str, default: Any = None) -> Any:
    """Get a specific setting value."""
    settings = load_settings()
    return settings.get(key, default)
