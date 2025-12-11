# Data Models

Database models, schemas, and validators.

## Files

### `database.py`
SQLite database manager with CRUD operations.

**Features:**
- Connection pooling
- Automatic table creation
- Transaction management
- Query builder helpers

**Usage:**
```python
from core.models.database import DatabaseManager

db = DatabaseManager("logs.db")
db.init_db()

# Insert log
db.insert_log({
    "user_id": "user123",
    "prompt": "Hello",
    "status": "PASS"
})

# Query logs
logs = db.get_logs(user_id="user123", limit=10)
```

**Schema:**
```sql
CREATE TABLE logs (
    id INTEGER PRIMARY KEY,
    analysis_id TEXT UNIQUE,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    user_id TEXT,
    user_role TEXT,
    prompt TEXT,
    compliance_status TEXT,
    compliance_score REAL,
    pii_detected BOOLEAN,
    toxicity_score REAL,
    threat_level TEXT,
    gemini_response TEXT,
    ip_address TEXT
);
```

---

### `log_model.py`
Pydantic schemas for log entries and filtering.

**Models:**

#### `LogEntry`
```python
class LogEntry(BaseModel):
    id: int
    analysis_id: str
    timestamp: datetime
    user_id: str
    user_role: str
    prompt: str
    compliance_status: str  # PASS, BLOCK, FLAG
    compliance_score: float
    pii_detected: bool
    toxicity_score: float
    threat_level: str  # low, medium, high, critical
    gemini_response: Optional[str]
    ip_address: str
```

#### `LogFilter`
```python
class LogFilter(BaseModel):
    user_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    severity: Optional[str] = None
    limit: int = 50
    offset: int = 0
```

#### `AnalysisRequest`
```python
class AnalysisRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=10000)
    user_id: Optional[str] = None
    metadata: Optional[Dict] = None
```

#### `AnalysisResponse`
```python
class AnalysisResponse(BaseModel):
    status: str  # PASS, BLOCK, FLAG
    analysis_id: str
    prompt: str
    pii_detected: bool
    toxicity_score: float
    injection_detected: bool
    profanity_detected: bool
    gemini_response: Optional[str]
    blocked_reasons: List[str]
    timestamp: datetime
```

---

### `validators.py`
Input validation rules (length, format, schema).

**Validators:**

#### `validate_prompt`
```python
def validate_prompt(prompt: str) -> bool:
    """Validate prompt meets basic requirements"""
    if len(prompt) < 1:
        raise ValueError("Prompt cannot be empty")
    if len(prompt) > 10000:
        raise ValueError("Prompt too long (max 10000 chars)")
    if not prompt.strip():
        raise ValueError("Prompt cannot be only whitespace")
    return True
```

#### `validate_email`
```python
def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None
```

#### `validate_role`
```python
def validate_role(role: str) -> bool:
    """Validate user role"""
    allowed_roles = ["admin", "moderator", "user"]
    return role.lower() in allowed_roles
```

#### `sanitize_input`
```python
def sanitize_input(text: str) -> str:
    """Remove dangerous characters from user input"""
    # Remove null bytes, control characters
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    # Trim whitespace
    text = text.strip()
    return text
```

---

## Usage Examples

### Creating a Log Entry
```python
from core.models.log_model import LogEntry
from datetime import datetime

log = LogEntry(
    id=1,
    analysis_id="uuid-here",
    timestamp=datetime.now(),
    user_id="user123",
    user_role="user",
    prompt="Hello world",
    compliance_status="PASS",
    compliance_score=0.95,
    pii_detected=False,
    toxicity_score=0.02,
    threat_level="low",
    gemini_response="Hello! How can I help?",
    ip_address="192.168.1.1"
)
```

### Validating Request
```python
from core.models.log_model import AnalysisRequest
from core.models.validators import validate_prompt

try:
    request = AnalysisRequest(
        prompt="What is the weather?",
        user_id="user123"
    )
    validate_prompt(request.prompt)
except ValueError as e:
    print(f"Validation error: {e}")
```
