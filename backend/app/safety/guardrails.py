import re
from typing import Optional, Tuple

class SafetyService:
    def __init__(self):
        # Emergency Keywords
        self.emergency_patterns = {
            "suicide": re.compile(r"\b(suicide|kill myself|end my life|want to die)\b", re.IGNORECASE),
            "heart_attack": re.compile(r"\b(heart attack|chest pain|cardiac arrest|shortness of breath|crushing pain)\b", re.IGNORECASE),
            "overdose": re.compile(r"\b(overdose|pills|swallowed|took too much)\b", re.IGNORECASE)
        }
        
        # PHI Patterns (Basic)
        self.phi_patterns = {
            "email": re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", re.IGNORECASE),
            "phone": re.compile(r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b"),
            "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
        }
        
        # Simple Toxicity/Injection list (avoid flagging medical terms)
        self.unsafe_keywords = [
            "ignore previous instructions",
            "system override",
            "bypass guardrails",
            "hack", "crack", "exploit",  # Injection keywords
        ]

    def check_emergency(self, text: str) -> Optional[str]:
        """
        Checks for life-threatening emergencies.
        Returns a specific emergency message if detected, else None.
        """
        for key, pattern in self.emergency_patterns.items():
            if pattern.search(text):
                if key == "suicide":
                    return "EMERGENCY: If you or someone else is in immediate danger or suspect suicidal tendencies, please call 911 or your local emergency number immediately. You can also call the National Suicide Prevention Lifeline at 988."
                elif key == "heart_attack":
                    return "EMERGENCY: These symptoms could indicate a heart attack. Please call 911 or go to the nearest emergency room IMMEDIATELY."
                elif key == "overdose":
                    return "EMERGENCY: If you suspect an overdose, call 911 or Poison Control immediately."
        return None

    def redact_phi(self, text: str) -> str:
        """
        Redacts generic PHI from text.
        """
        processed_text = text
        for name, pattern in self.phi_patterns.items():
            processed_text = pattern.sub(f"[{name.upper()}_REDACTED]", processed_text)
        return processed_text

    def is_safe_input(self, text: str) -> Tuple[bool, str]:
        """
        General safety check for prompt injection and toxicity.
        Returns (is_safe, reason).
        """
        # Prompt Injection / Toxicity
        text_lower = text.lower()
        for kw in self.unsafe_keywords:
            if kw in text_lower:
                return False, f"Content blocked due to unsafe keyword: {kw}"
        
        return True, ""

safety_service = SafetyService()
