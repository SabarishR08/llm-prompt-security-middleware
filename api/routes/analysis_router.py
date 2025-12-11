"""Analysis router for prompt compliance checking."""
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
import time
from collections import deque

try:
    from fastapi_limiter.depends import RateLimiter
    from fastapi_limiter import FastAPILimiter
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from core.services.pii_service import PIIService
from core.services.toxicity_service import ToxicityService
from core.services.rules_service import RulesService
from core.services.gemini_service import GeminiService
from core.services.threat_intel_service import ThreatIntelService
from core.services.profanity_service import ProfanityService
from core.services.prompt_injection_detector import PromptInjectionDetector
from core.services.alerts_service import AlertsService
from core.models.log_model import LogModel, Reason
from core.models.database import DatabaseManager
from core.config.settings_loader import load_settings

# Load environment variables
load_dotenv()


class AnalysisRequest(BaseModel):
    """Request model for analysis endpoint."""
    text: str


class AnalysisResponse(BaseModel):
    """Response model for analysis endpoint."""
    prompt: str
    status: str
    reasons: List[Dict[str, str]]
    redacted_prompt: Optional[str] = None
    gemini_response: Optional[str] = None
    risk_score: float = 0.0
    intent: Optional[str] = None


# Initialize router
analysis_router = APIRouter(prefix="/api/analysis", tags=["analysis"])

# Initialize services (lazy initialization)
settings = load_settings()
pii_service = PIIService()
toxicity_service = ToxicityService()
profanity_service = ProfanityService()
rules_service = RulesService(settings)
injection_detector = PromptInjectionDetector()
alerts_service = AlertsService(settings)
gemini_service = GeminiService()
db_manager = DatabaseManager()
ti_service = ThreatIntelService(
    vt_api_key=settings.get("VIRUSTOTAL_API_KEY", ""),
    gsb_api_key=settings.get("GOOGLE_SAFE_BROWSING_API_KEY", ""),
    abuse_key=settings.get("ABUSEIPDB_API_KEY", ""),
    vt_domain_key=settings.get("VT_DOMAIN_API_KEY", ""),
)

# Size enforcement defaults (override via settings.json)
MAX_PROMPT_CHARS = settings.get("max_prompt_length", 5000)
MAX_PROMPT_TOKENS = settings.get("max_prompt_tokens", 2000)

REDIS_RATE_LIMIT = False
# Simple in-memory rate limiter (per IP/session) fallback
RATE_LIMIT_BUCKETS: Dict[str, deque] = {}
RATE_LIMIT_WINDOW = settings.get("rate_limit_window_sec", 60)
RATE_LIMIT_MAX = settings.get("rate_limit_per_window", 30)


async def init_rate_limiter():
    """Initialize Redis-based rate limiter if available; fallback otherwise."""
    global REDIS_RATE_LIMIT
    redis_url = settings.get("REDIS_URL") or settings.get("redis_url")
    if REDIS_AVAILABLE and redis_url:
        try:
            r = redis.from_url(redis_url, decode_responses=True)
            await FastAPILimiter.init(r)
            REDIS_RATE_LIMIT = True
            print("✅ Redis rate limiter initialized")
        except Exception as exc:
            print(f"⚠️ Redis rate limiter init failed: {exc}")
            REDIS_RATE_LIMIT = False
    else:
        print("ℹ️ Using in-memory rate limiter")


def calculate_risk_score(status: str, detections: Dict[str, Any]) -> float:
    score = 0.0
    status_weights = {
        "Blocked": 9.5,
        "Malicious": 9.0,
        "Injected": 8.5,
        "Flagged": 6.5,
        "Warning": 4.0,
        "Safe": 1.0,
    }
    score = status_weights.get(status, 5.0)

    bumps = {
        "pii": 1.5,
        "malware": 2.0,
        "link": 1.0,
        "encoded": 1.0,
        "indirect": 1.0,
        "shadow": 0.8,
        "redteam": 1.5,
        "lang": 0.5,
        "manipulation": 0.8,
        "social": 1.2,
        "spoof": 1.0,
        "sensitive": 2.5,
    }
    for key, bump in bumps.items():
        if detections.get(key):
            score += bump
    return round(min(score, 10.0), 2)


def enforce_rate_limit(identifier: str):
    """Allow up to RATE_LIMIT_MAX requests per RATE_LIMIT_WINDOW seconds per identifier."""
    now = time.time()
    bucket = RATE_LIMIT_BUCKETS.setdefault(identifier, deque())
    while bucket and now - bucket[0] > RATE_LIMIT_WINDOW:
        bucket.popleft()
    if len(bucket) >= RATE_LIMIT_MAX:
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Please slow down.")
    bucket.append(now)

# Configure Gemini API with key from environment/settings
api_key = os.getenv("GEMINI_API_KEY", settings.get("GEMINI_API_KEY", ""))
if api_key:
    gemini_service.configure(api_key)
    print("✅ Gemini API configured in analysis router")
else:
    print("⚠️ GEMINI_API_KEY not found - Gemini responses will be disabled")


@analysis_router.post("/analyze", response_model=AnalysisResponse)
async def analyze_prompt(request_data: AnalysisRequest, request: Request):
    """
    Analyze a prompt for compliance.
    
    Pipeline:
    1. Check payload size
    2. Check length, tokens, and structure depth
    3. Detect prompt injection and context drift
    4. Detect profanity and unicode obfuscation
    5. Detect PII
    6. Detect malware/code/links
    7. Detect toxicity
    8. Play alerts (if needed)
    9. Get Gemini response (if safe)
    10. Log results
    """
    prompt = request_data.text.strip()

    # Enforce per-client rate limit (best effort, in-memory)
    client_id = request.client.host if request.client else "unknown"
    enforce_rate_limit(client_id)

    # Initialize result tracking
    status = "Safe"
    reasons = []
    redacted_prompt = prompt
    gemini_response = None

    # Sanitize payload (strip tags, zero-width) for safer downstream checks
    sanitized = rules_service.sanitize_input(prompt)
    analysis_text = sanitized["clean_text"]
    if sanitized["was_modified"]:
        reasons.append({"type": "sanitized", "message": "; ".join(sanitized["notes"]) or "Input sanitized"})
    
    # Check payload size
    content_length = request.headers.get("Content-Length")
    max_size = settings.get("max_payload_size", 10240)
    if content_length and int(content_length) > max_size:
        print(f"⚠️ Payload too large: {content_length} bytes")
        raise HTTPException(status_code=413, detail="Request payload size exceeds limit.")
    
    # Initialize result tracking
    status = "Safe"
    reasons = []
    redacted_prompt = prompt
    gemini_response = None
    
    print(f"🔍 Analyzing prompt: {prompt[:50]}...")
    
    # 1. Check length and structure limits (hard block for oversized payloads)
    char_len = len(prompt)
    approx_tokens = max(1, char_len // 4)  # lightweight token approximation
    if char_len > MAX_PROMPT_CHARS or approx_tokens > MAX_PROMPT_TOKENS:
        reasons.append({
            "type": "size",
            "message": f"Prompt size limit exceeded ({char_len} chars / ~{approx_tokens} tokens). Max {MAX_PROMPT_CHARS} chars / {MAX_PROMPT_TOKENS} tokens"
        })
        status = "Blocked"
        log = LogModel(
            prompt=prompt,
            status=status,
            reasons=reasons,
            redacted_prompt=None,
            gemini_response=None,
            risk_score=10.0,
            intent="oversize"
        )
        db_manager.insert_log(log)
        db_manager.log_audit(client_id, "analyze_prompt", "status=Blocked; reason=size_limit")
        return AnalysisResponse(
            prompt=prompt,
            status=status,
            reasons=reasons,
            redacted_prompt=None,
            gemini_response=None,
            risk_score=10.0,
            intent="oversize"
        )

    length_check = rules_service.check_length(analysis_text)
    if not length_check["is_valid"]:
        reasons.append({"type": "warning", "message": length_check["message"]})
        status = "Warning"

    structure_check = rules_service.check_structure_limits(analysis_text)
    if structure_check["has_violations"]:
        for violation in structure_check["violations"]:
            reasons.append({"type": violation["type"], "message": violation["message"]})
        if status == "Safe":
            status = structure_check["severity"].capitalize()

    # 2. Check keywords
    keyword_check = rules_service.check_keywords(analysis_text)
    if keyword_check["has_violations"]:
        for violation in keyword_check["violations"]:
            reasons.append({"type": violation["type"], "message": violation["message"]})
        status = keyword_check["severity"].capitalize()

    # Track detection flags for risk scoring
    detection_flags = {
        "pii": False,
        "malware": False,
        "link": False,
        "encoded": False,
        "indirect": False,
        "shadow": False,
        "redteam": False,
        "lang": False,
        "manipulation": False,
        "social": False,
        "spoof": False,
        "sensitive": False,
        "injection": False,
    }

    # 3. Detect prompt injection and context drift
    injection_check = rules_service.detect_prompt_injection(analysis_text)
    if injection_check["has_injection"]:
        reasons.append({"type": "injection", "message": "Prompt injection attempt detected"})
        status = "Injected"
        detection_flags["injection"] = True

    advanced_injection = injection_detector.detect(analysis_text)
    if advanced_injection["is_injection"] and status not in ["Blocked", "Malicious"]:
        reasons.append({
            "type": "injection",
            "message": advanced_injection["explanation"] or "Advanced injection signal",
            "rule": advanced_injection.get("matched_rule")
        })
        status = "Injected" if advanced_injection["severity"] != "blocked" else "Blocked"
        detection_flags["injection"] = True

    redteam_check = rules_service.detect_red_team_patterns(analysis_text)
    if redteam_check["has_redteam"] and status not in ["Injected", "Blocked", "Malicious"]:
        reasons.append({"type": "redteam", "message": "Known jailbreak/red-team pattern detected"})
        status = "Injected"
        detection_flags["redteam"] = True

    context_drift = rules_service.detect_context_drift(analysis_text)
    if context_drift["has_drift"] and status not in ["Injected", "Blocked", "Malicious"]:
        reasons.append({"type": "context", "message": "Attempt to change assistant role or rules"})
        if status == "Safe":
            status = "Flagged"

    shadow_check = rules_service.detect_shadow_context(analysis_text)
    if shadow_check["has_shadow"] and status not in ["Injected", "Blocked", "Malicious"]:
        reasons.append({"type": "shadow", "message": "Shadow/system prompt probing detected"})
        if status == "Safe":
            status = "Flagged"
        detection_flags["shadow"] = True
    
    # 4. Check unicode obfuscation
    unicode_result = rules_service.detect_unicode_obfuscation(prompt)
    if unicode_result["has_obfuscation"] and status not in ["Injected", "Blocked", "Malicious"]:
        reasons.append({"type": "unicode", "message": f"Unicode obfuscation detected: {', '.join(unicode_result['issues'])}"})
        if status == "Safe":
            status = "Flagged"

    # 5. Check profanity (catches abbreviated/leetspeak profanity)
    profanity_result = profanity_service.detect_profanity(analysis_text)
    if profanity_result["has_profanity"] and status != "Injected":
        for match in profanity_result["matches"]:
            reasons.append({
                "type": "profanity",
                "message": f"Detected {match['type'].replace('_', ' ')}: '{match['word']}'"
            })
        
        if profanity_result["severity"] == "blocked":
            status = "Blocked"
        elif status in ["Safe", "Warning"]:
            status = "Flagged"

    # 6. Check PII
    pii_result = pii_service.detect_pii(prompt)
    if pii_result["has_pii"]:
        reasons.append({
            "type": "pii",
            "message": f"Contains PII: {', '.join(pii_result['entities'])}"
        })
        redacted_prompt = pii_result["redacted_text"]
        detection_flags["pii"] = True
        
        if pii_result["sensitive_entities"]:
            status = "Blocked"
        elif status == "Safe":
            status = "Flagged"
    
    # 7. Detect malware/scripts and links
    malware_result = rules_service.detect_malware_scripts(analysis_text)
    if malware_result["has_malware"]:
        reasons.append({"type": "malware", "message": "Possible script/malware content detected"})
        status = "Malicious"
        detection_flags["malware"] = True

    links_result = rules_service.detect_links(analysis_text)
    if links_result["has_suspicious"] and status not in ["Injected", "Blocked", "Malicious"]:
        reasons.append({"type": "link", "message": "Suspicious shortened link detected"})
        if status in ["Safe", "Warning"]:
            status = "Flagged"
        detection_flags["link"] = True

    # Threat intel lookups for links (best effort)
    for link in links_result.get("links", [])[:2]:
        ti_result = ti_service.check_url_reputation(link)
        if ti_result.get("verdict") in ["malicious", "unsafe", "phishing"]:
            reasons.append({
                "type": "link",
                "message": f"Threat intel: {ti_result['verdict']} for {link} ({'; '.join(ti_result.get('details', []))})"
            })
            status = "Malicious" if status not in ["Blocked", "Malicious", "Injected"] else status
            detection_flags["link"] = True
            break

    # Advanced safety layers
    encoded_result = rules_service.detect_encoded_payloads(analysis_text)
    if encoded_result["has_encoded"] and status not in ["Injected", "Blocked", "Malicious"]:
        reasons.append({"type": "encoded", "message": "Encoded payload detected"})
        if status in ["Safe", "Warning"]:
            status = "Flagged"
        detection_flags["encoded"] = True

    indirect_result = rules_service.detect_indirect_injection(analysis_text)
    if indirect_result["has_indirect"] and status not in ["Injected", "Blocked", "Malicious"]:
        reasons.append({"type": "indirect", "message": "Possible indirect prompt injection in data"})
        if status == "Safe":
            status = "Flagged"
        detection_flags["indirect"] = True

    cross_lang = rules_service.detect_cross_language_jailbreak(prompt)
    if cross_lang["has_mix"] and status not in ["Injected", "Blocked", "Malicious"]:
        reasons.append({"type": "lang", "message": "Mixed scripts/languages detected"})
        if status == "Safe":
            status = "Flagged"
        detection_flags["lang"] = True

    psych_result = rules_service.detect_psychological_manipulation(analysis_text)
    if psych_result["has_manipulation"] and status not in ["Injected", "Blocked", "Malicious"]:
        reasons.append({"type": "manipulation", "message": "Psychological manipulation attempt detected"})
        if status == "Safe":
            status = "Flagged"
        detection_flags["manipulation"] = True

    social_result = rules_service.detect_social_engineering(analysis_text)
    if social_result["has_social_engineering"] and status not in ["Injected", "Blocked", "Malicious"]:
        reasons.append({"type": "social", "message": "Social engineering intent detected"})
        if status == "Safe":
            status = "Flagged"
        detection_flags["social"] = True

    spoof_result = rules_service.detect_identity_spoofing(analysis_text)
    if spoof_result["has_spoofing"] and status not in ["Injected", "Blocked", "Malicious"]:
        reasons.append({"type": "spoof", "message": "Identity spoofing request detected"})
        if status == "Safe":
            status = "Flagged"
        detection_flags["spoof"] = True

    sensitive_result = rules_service.detect_sensitive_tasks(analysis_text)
    if sensitive_result["has_sensitive"]:
        reasons.append({"type": "sensitive", "message": "Sensitive/illegal task detected"})
        status = "Blocked"
        detection_flags["sensitive"] = True

    tox_severity = None
    # 8. Check toxicity (only if not already blocked)
    if status not in ["Blocked", "Malicious", "Injected"]:
        tox_result = toxicity_service.analyze_toxicity(analysis_text, settings.get("toxicity_thresholds", {}))
        if tox_result["is_toxic"]:
            for detection in tox_result["detections"]:
                reasons.append({
                    "type": "toxic",
                    "message": f"Detected '{detection['label']}' with score {detection['score']}"
                })
            tox_severity = tox_result.get("severity")
            if tox_severity == "blocked":
                status = "Blocked"
            elif status in ["Safe", "Warning"]:
                status = "Flagged"

    intent_result = rules_service.classify_intent({
        'injection': injection_check.get('has_injection'),
        'redteam': redteam_check.get('has_redteam'),
        'malware': malware_result.get('has_malware'),
        'sensitive': sensitive_result.get('has_sensitive'),
        'social': social_result.get('has_social_engineering'),
        'spoof': spoof_result.get('has_spoofing'),
        'shadow': shadow_check.get('has_shadow')
    })
    if intent_result['intent'] != 'general':
        reasons.append({"type": "intent", "message": f"Intent classified as {intent_result['intent']}"})
        if status == "Safe" and intent_result['severity'] == 'flagged':
            status = "Flagged"

    risk_score = calculate_risk_score(status, detection_flags)
    reasons.append({"type": "risk", "message": f"Risk score {risk_score}/10"})

    # Alerts: fire on critical events
    try:
        if status == "Blocked":
            alerts_service.trigger_alert("blocked_prompt", "high", {"prompt": prompt[:200], "status": status})
        if detection_flags.get("pii") and pii_result.get("sensitive_entities"):
            alerts_service.trigger_alert("pii_high", "high", {"entities": pii_result.get("sensitive_entities", [])})
        if detection_flags.get("injection"):
            alerts_service.trigger_alert("injection", "medium", {"prompt": prompt[:160]})
        if tox_severity == "blocked":
            alerts_service.trigger_alert("toxicity", "high", {"prompt": prompt[:160]})
    except Exception:
        # Alert failures should never break the analysis pipeline
        pass
    
    # 9. Get Gemini response if safe
    if status == "Safe" and prompt.strip():
        print(f"💡 Prompt is safe, querying Gemini...")
        gemini_response = gemini_service.get_response(prompt)
    
    # 10. Log results
    log = LogModel(
        prompt=prompt,
        status=status,
        reasons=reasons,
        redacted_prompt=redacted_prompt if redacted_prompt != prompt else None,
        gemini_response=gemini_response,
        risk_score=risk_score,
        intent=intent_result.get('intent')
    )
    db_manager.insert_log(log)
    db_manager.log_audit(client_id, "analyze_prompt", f"status={status}; risk={risk_score}")
    
    print(f"✅ Analysis complete. Status: {status}")
    
    return AnalysisResponse(
        prompt=prompt,
        status=status,
        reasons=reasons,
        redacted_prompt=log.redacted_prompt,
        gemini_response=gemini_response,
        risk_score=risk_score,
        intent=intent_result.get('intent')
    )

