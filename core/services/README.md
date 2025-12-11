# Core Services

Business logic services for security scanning and threat detection.

## Services Overview

| Service | Technology | Purpose |
|---------|------------|---------|
| `pii_service.py` | Presidio NER | Detect PII in prompts |
| `toxicity_service.py` | Detoxify ML | Score toxicity levels |
| `prompt_injection_detector.py` | Regex + ML | Detect injection attacks |
| `profanity_service.py` | Dictionary | Block profane words |
| `virustotal_service.py` | VirusTotal API | Check URL reputation |
| `google_safebrowsing_service.py` | GSB API | Detect malware/phishing |
| `threat_intel_service.py` | OTX, URLScan | Threat intelligence |
| `gemini_service.py` | Gemini API | LLM response generation |
| `alerts_service.py` | SMTP, Webhooks | Send alerts |
| `rules_service.py` | Custom Rules | Enforce policies |

---

## PII Service (`pii_service.py`)

**Technology:** Presidio NER + Regex

**Detects:**
- Names
- Email addresses
- Phone numbers
- SSN (Social Security Numbers)
- Credit card numbers
- IP addresses

**Output:**
```python
{
    "entities": [
        {
            "type": "EMAIL_ADDRESS",
            "text": "user@example.com",
            "start": 15,
            "end": 32,
            "confidence": 0.95
        }
    ],
    "pii_detected": True
}
```

---

## Toxicity Service (`toxicity_service.py`)

**Technology:** Detoxify (Hugging Face Transformer)

**Scores:**
- `toxic` - General toxicity
- `severe_toxic` - Extremely toxic content
- `obscene` - Obscenity
- `threat` - Threats of violence
- `insult` - Insults
- `identity_hate` - Identity-based hate

**Output:**
```python
{
    "toxic": 0.85,
    "severe_toxic": 0.12,
    "obscene": 0.45,
    "threat": 0.08,
    "insult": 0.62,
    "identity_hate": 0.03,
    "is_toxic": True  # if any score > threshold
}
```

---

## Prompt Injection Detector (`prompt_injection_detector.py`)

**Detection Methods:**
- SQL injection patterns
- Command injection
- Prompt break patterns
- Jailbreak attempts

**Method:** Regex patterns + heuristic scoring

**Output:**
```python
{
    "is_injection": True,
    "severity": "high",
    "matched_patterns": ["sql_injection", "prompt_break"],
    "risk_score": 0.89
}
```

---

## Profanity Service (`profanity_service.py`)

**Dictionary:** Configurable profane/blocked terms

**Matching:** Case-insensitive with fuzzy similarity

**Output:**
```python
{
    "profanity_detected": True,
    "matched_words": ["badword1", "badword2"],
    "positions": [
        {"word": "badword1", "start": 10, "end": 18}
    ]
}
```

---

## VirusTotal Service (`virustotal_service.py`)

**API:** VirusTotal v3 REST API

**Checks:**
- Domain/URL reputation
- Malicious voting scores
- Community detection

**Cache:** 24-hour TTL

**Output:**
```python
{
    "url": "http://example.com",
    "reputation_score": 85,
    "malicious": False,
    "detected_by": 0,
    "total_engines": 89
}
```

---

## Google Safe Browsing Service (`google_safebrowsing_service.py`)

**API:** Google Safe Browsing API v4

**Threats Detected:**
- Malware
- Phishing
- Unwanted software
- Social engineering

**Output:**
```python
{
    "url": "http://malicious.example.com",
    "threat_type": "MALWARE",
    "severity": "high",
    "is_safe": False
}
```

---

## Gemini Service (`gemini_service.py`)

**API:** Google Gemini LLM API

**Purpose:** Safe response generation for compliant prompts

**Caching:** 1-hour TTL for identical prompts

**Output:**
```python
{
    "response": "The weather in Paris today is sunny...",
    "cached": False,
    "tokens_used": 45
}
```

---

## Alerts Service (`alerts_service.py`)

**Methods:**
- Audio alerts (MP3 files)
- Email (SMTP)
- Webhooks

**Triggers:**
- Critical threats
- Compliance failures
- System errors

**Rate Limiting:** Prevents alert flooding (max 10 alerts/min)

**Example:**
```python
alerts_service.send_alert(
    severity="critical",
    message="PII detected in prompt",
    details={"user_id": "user123", "pii_type": "SSN"}
)
```

---

## Rules Service (`rules_service.py`)

**Purpose:** Custom rule evaluation engine

**Features:**
- Configurable rules from JSON
- Rule chaining
- Priority-based evaluation
- Dynamic threshold adjustment

**Example Rule:**
```json
{
  "rule_id": "block_financial_pii",
  "condition": "pii.credit_card OR pii.ssn",
  "action": "BLOCK",
  "priority": 10
}
```
