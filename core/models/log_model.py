import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional
import json


class LogModel:
    """Data model for logs with risk scoring and integrity chain."""

    def __init__(self, prompt: str, status: str, reasons: List[Dict[str, str]],
                 redacted_prompt: Optional[str] = None, gemini_response: Optional[str] = None,
                 risk_score: float = 0.0, intent: Optional[str] = None,
                 integrity_hash: Optional[str] = None, prev_hash: Optional[str] = None):
        self.prompt = prompt
        self.status = status
        self.reasons = reasons
        self.redacted_prompt = redacted_prompt
        self.gemini_response = gemini_response
        self.timestamp = datetime.now().isoformat()
        self.risk_score = risk_score
        self.intent = intent or "general"
        self.integrity_hash = integrity_hash
        self.prev_hash = prev_hash

    def to_dict(self) -> Dict[str, Any]:
        """Convert log to dictionary."""
        return {
            "prompt": self.prompt,
            "status": self.status,
            "reasons": self.reasons,
            "redacted_prompt": self.redacted_prompt,
            "gemini_response": self.gemini_response,
            "timestamp": self.timestamp,
            "risk_score": self.risk_score,
            "intent": self.intent,
            "integrity_hash": self.integrity_hash,
            "prev_hash": self.prev_hash
        }

    def to_tuple(self) -> tuple:
        """Convert log to tuple for database insertion."""
        return (
            self.prompt,
            self.status,
            json.dumps(self.reasons),
            self.timestamp,
            self.redacted_prompt,
            self.gemini_response,
            self.risk_score,
            self.intent,
            self.integrity_hash,
            self.prev_hash
        )


class Reason:
    """Reason model for prompt analysis."""
    def __init__(self, type: str, message: str):
        self.type = type
        self.message = message
    
    def to_dict(self) -> Dict[str, str]:
        return {"type": self.type, "message": self.message}
