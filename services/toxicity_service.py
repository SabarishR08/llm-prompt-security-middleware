from detoxify import Detoxify
from typing import Dict, Any

class ToxicityService:
    """Service for detecting toxic content in prompts."""
    
    def __init__(self):
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load the Detoxify model."""
        try:
            self.model = Detoxify('original')
            print("✅ Detoxify model loaded")
        except Exception as e:
            print(f"❌ Error loading Detoxify model: {e}")
            self.model = None
    
    def analyze_toxicity(self, text: str, thresholds: Dict[str, float]) -> Dict[str, Any]:
        """Analyze toxicity of the given text."""
        if not self.model:
            return {
                "is_toxic": False,
                "detections": [],
                "severity": "safe",
                "error": "Detoxify model not loaded"
            }
        
        try:
            results = self.model.predict(text)
            detections = []
            is_toxic = False
            severity = "safe"
            
            for label, score in results.items():
                if label in thresholds:
                    threshold = thresholds[label]
                    if score > threshold:
                        detections.append({
                            "label": label,
                            "score": score,
                            "threshold": threshold
                        })
                        print(f"☣️ Toxicity detected: {label} score={score:.2f}")
                        is_toxic = True
                        
                        # Determine severity level
                        if label in ["severe_toxicity", "threat"]:
                            severity = "blocked"
                        elif severity != "blocked":
                            severity = "flagged"
            
            return {
                "is_toxic": is_toxic,
                "detections": detections,
                "all_scores": results,
                "severity": severity
            }
        except Exception as e:
            print(f"❌ Toxicity analysis failed: {e}")
            return {
                "is_toxic": False,
                "detections": [],
                "severity": "safe",
                "error": str(e)
            }
