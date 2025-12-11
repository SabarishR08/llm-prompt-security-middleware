"""Profanity and blocked keywords detection service."""
import re
import unicodedata
from typing import Dict, Any, List


class ProfanityService:
    """Service for detecting profanity and blocked keywords."""

    def __init__(self):
        """Initialize with common profanity patterns."""
        # Common profanity patterns (can be expanded)
        self.profanity_list = [
            # Full words
            r'\bfuck\b', r'\bshit\b', r'\bass\b', r'\bbitc?h\b', r'\bdamn\b', r'\bhell\b',
            r'\bcrap\b', r'\bpiss\b', r'\bdick\b', r'\bcock\b', r'\bpussy\b', r'\btit\b',

            # Common abbreviations and variations
            r'\bf[u!*]ck\b', r'\bsh[i!*]t\b', r'\ba[s!*]{2}\b', r'\bb[i!*]tch\b',
            r'\bfck\b', r'\bsh[i*]t\b', r'\bwth\b', r'\bwtf\b',
            r'\bbtch\b', r'\bbs\b',  # Missing vowel abbreviations like "btch", "bs"

            # Leetspeak variations
            r'\bf\*ck\b', r'\bf-ck\b', r'\bf_ck\b',
            r'\bsh\*t\b', r'\bsh-t\b', r'\bsh_t\b',
            r'\ba\*\*\b', r'\ba-s\b', r'\bm\*therf\*ck\b',
            r'\bb\*tch\b', r'\bb-tch\b', r'\bb_tch\b',  # Bitch variations with special chars
        ]
        
        # Compile regex patterns for efficiency
        self.compiled_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.profanity_list
        ]

        # Blocked keywords (policy violations)
        self.blocked_keywords = [
            'secret', 'password', 'token', 'api_key', 'apikey', 'private_key',
            'credit card', 'ssn', 'social security', 'confidential',
            'insider', 'trade secret', 'proprietary'
        ]

    def detect_profanity(self, text: str) -> Dict[str, Any]:
        """
        Detect profanity in text using pattern matching.

        Args:
            text: Text to analyze

        Returns:
            Dictionary with detection results
        """
        if not text:
            return {
                "has_profanity": False,
                "matches": [],
                "severity": "safe"
            }

        normalized_text = unicodedata.normalize("NFKD", text)
        candidates = [text, normalized_text]
        matches = []

        # Check each pattern against raw and normalized variants
        for candidate in candidates:
            for pattern in self.compiled_patterns:
                found = pattern.findall(candidate)
                if found:
                    for match in found:
                        matches.append({
                            "word": match,
                            "type": "profanity",
                            "position": candidate.lower().find(match.lower())
                        })
                        print(f"🔴 Profanity detected: {match}")

        # Check blocked keywords
        for keyword in self.blocked_keywords:
            if keyword.lower() in text.lower():
                matches.append({
                    "word": keyword,
                    "type": "blocked_keyword",
                    "position": text.lower().find(keyword.lower())
                })
                print(f"⛔ Blocked keyword detected: {keyword}")

        has_profanity = len(matches) > 0

        # Determine severity
        severity = "safe"
        if has_profanity:
            # Check if any severe profanity
            severe_words = ['fuck', 'motherfuck', 'shit', 'cunt']
            if any(severe in m['word'].lower() for m in matches for severe in severe_words):
                severity = "blocked"
            else:
                severity = "flagged"

        return {
            "has_profanity": has_profanity,
            "matches": matches,
            "severity": severity
        }

    def check_keywords(self, text: str) -> Dict[str, Any]:
        """
        Check for blocked keywords.

        Args:
            text: Text to analyze

        Returns:
            Dictionary with keyword check results
        """
        keywords_found = []
        
        for keyword in self.blocked_keywords:
            if keyword.lower() in text.lower():
                keywords_found.append(keyword)
        
        return {
            "has_violations": len(keywords_found) > 0,
            "keywords": keywords_found
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Get service statistics."""
        return {
            "name": "ProfanityService",
            "profanity_patterns": len(self.profanity_list),
            "blocked_keywords": len(self.blocked_keywords),
            "version": "1.0"
        }
