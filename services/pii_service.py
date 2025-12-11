from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from typing import List, Dict, Any

class PIIService:
    """Service for detecting Personally Identifiable Information (PII)."""
    
    def __init__(self):
        self.analyzer = AnalyzerEngine()
        self._initialize_custom_recognizers()
    
    def _initialize_custom_recognizers(self):
        """Add custom pattern recognizers."""
        try:
            # Custom ATM PIN recognizer
            atm_pin_pattern = Pattern(name="ATM_PIN", regex=r"\b\d{4,6}\b", score=0.85)
            atm_pin_recognizer = PatternRecognizer(
                supported_entity="ATM_PIN",
                patterns=[atm_pin_pattern]
            )
            self.analyzer.registry.add_recognizer(atm_pin_recognizer)
            print("✅ Custom ATM PIN recognizer added")
        except Exception as e:
            print(f"⚠️ Error adding custom recognizers: {e}")
    
    def detect_pii(self, text: str) -> Dict[str, Any]:
        """Detect PII in the given text."""
        try:
            results = self.analyzer.analyze(text=text, language="en")
            
            if not results:
                return {
                    "has_pii": False,
                    "entities": [],
                    "redacted_text": None
                }
            
            # Extract unique entity types
            pii_entities = sorted(list(set([res.entity_type for res in results])))
            
            # Redact PII
            redacted_text = text
            for res in reversed(results):
                redacted_text = redacted_text[:res.start] + f"[{res.entity_type}]" + redacted_text[res.end:]
            
            print(f"🛡️ PII detected: {pii_entities}")
            
            return {
                "has_pii": True,
                "entities": pii_entities,
                "redacted_text": redacted_text,
                "sensitive_entities": any(ent in pii_entities for ent in ["PHONE_NUMBER", "CREDIT_CARD", "ATM_PIN"])
            }
        except Exception as e:
            print(f"❌ PII analysis failed: {e}")
            return {
                "has_pii": False,
                "entities": [],
                "redacted_text": None,
                "error": str(e)
            }
