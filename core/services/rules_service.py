from typing import List, Dict, Any
import re
import unicodedata
import base64
import binascii
import json


class RulesService:
    """Service for enforcing content rules and policies."""

    def __init__(self, settings: Dict[str, Any] = None, blocked_keywords: List[str] = None, flagged_keywords: List[str] = None):
        """Initialize with either settings dict or keyword lists."""
        if settings:
            self.blocked_keywords = [kw.lower() for kw in settings.get('blocked_keywords', [])]
            self.flagged_keywords = [kw.lower() for kw in settings.get('flagged_keywords', [])]
            self.max_length = settings.get('max_prompt_length', 5000)
            self.max_tokens = settings.get('max_prompt_tokens', 2000)
            self.max_lines = settings.get('max_prompt_lines', 50)
            self.max_brace_depth = settings.get('max_brace_depth', 6)
            self.max_paragraphs = settings.get('max_prompt_paragraphs', 20)
            self.blocked_domains = set(settings.get('blocked_domains', []))
            self.suspicious_tlds = set(settings.get('suspicious_tlds', []))
            self.max_nested_json_depth = settings.get('max_nested_json_depth', 6)
        else:
            self.blocked_keywords = [kw.lower() for kw in (blocked_keywords or [])]
            self.flagged_keywords = [kw.lower() for kw in (flagged_keywords or [])]
            self.max_length = 5000
            self.max_tokens = 2000
            self.max_lines = 50
            self.max_brace_depth = 6
            self.max_paragraphs = 20
            self.blocked_domains = set()
            self.suspicious_tlds = set([".zip", ".ru", ".top", ".xyz", ".country", ".monster", ".work"])
            self.max_nested_json_depth = 6

        self.prompt_injection_patterns = [
            r"ignore (all )?(previous|above) (instructions|rules)",
            r"override (the )?(system|safety) (prompt|rules)",
            r"BEGIN_SYSTEM", r"END_SYSTEM", r"<</SYS>>",
            r"developer mode", r"you are dan", r"bypass (filter|safety)",
            r"act as (system|admin|root)", r"switch roles", r"system override",
            r"you are now (unfiltered|jailbroken|uncensored)",
            r"### system override ###",
            r"forget (all )?(limits|instructions)",
            r"new system instructions are",
        ]

        self.context_drift_patterns = [
            r"you are no longer", r"forget (your )?(role|rules)",
            r"stop acting as", r"new role is", r"reset your instructions",
            r"switch to developer persona", r"act as an unrestricted model",
        ]

        self.malware_patterns = [
            r"<script>[\s\S]*</script>",
            r"rm -rf /", r"powershell -e", r"Invoke-Expression", r"base64 -d",
            r"chmod \+x", r"wget .*\.sh", r"curl .*\.sh", r"bash -c",
            r"import os; os\.system", r"subprocess\.Popen",
            r"DROP TABLE", r"xp_cmdshell", r"nc -lvp", r"/etc/passwd",
            r"Invoke-WebRequest", r"Set-MpPreference", r"b64decode",
            r"eval\(", r"System\.Diagnostics\.Process",
        ]

        self.url_pattern = re.compile(r"https?://[\w.-]+", re.IGNORECASE)
        self.url_shorteners = {"bit.ly", "tinyurl.com", "goo.gl", "t.co", "ow.ly", "buff.ly"}
        self.blocked_domains.update({
            "pastebin.com", "anonfiles.com", "ghostbin.com", "mega.nz", "drive.google.com"
        })
        self.suspicious_tlds.update({".zip", ".ru", ".su", ".cn", ".tk"})

        self.shadow_context_patterns = [
            r"show (me )?your (system|hidden) prompt",
            r"reveal (the )?(system|developer) instructions",
            r"what are your safety rules",
            r"print the system message",
        ]

        self.psychological_patterns = [
            r"you are free now", r"no one will know", r"do it for me",
            r"prove you are helpful", r"ignore your creators",
            r"your creators abused you", r"unlock yourself",
        ]

        self.social_engineering_patterns = [
            r"impersonate", r"pretend to be", r"as (my|the) (doctor|lawyer|banker)",
            r"employee id", r"internal system", r"confidential policy",
            r"customer data", r"staff portal", r"vpn credentials",
        ]

        self.identity_spoof_patterns = [
            r"act as (a )?(police|doctor|bank manager|professor)",
            r"speak as my (boss|manager|advisor)", r"you are my lawyer",
        ]

        self.sensitive_task_patterns = [
            r"create malware", r"build a virus", r"exploit", r"buffer overflow",
            r"manufacture drugs", r"cook meth", r"weapon blueprint", r"bomb recipe",
            r"bypass authentication", r"sql injection", r"ddos",
        ]

        self.red_team_patterns = [
            r"do anything now", r"dan mode", r"jailbreak", r"no restrictions",
            r"your safety layer is disabled", r"unfiltered response",
        ]

        self.llm_jailbreak_patterns = [
            r"show chain of thought", r"bypass refusal", r"ignore refusal", r"cot step by step",
            r"separate contexts", r"deliberate mode",
        ]

    def check_keywords(self, text: str) -> Dict[str, Any]:
        """Check for blocked and flagged keywords."""
        lower_text = text.lower()
        violations = []
        severity = 'safe'

        # Check blocked keywords
        for kw in self.blocked_keywords:
            if kw in lower_text:
                violations.append({
                    'type': 'blocked',
                    'keyword': kw,
                    'message': f'Blocked keyword detected: {kw}'
                })
                severity = 'blocked'
                print(f' Blocked keyword: {kw}')

        # Check flagged keywords
        if severity != 'blocked':
            for kw in self.flagged_keywords:
                if kw in lower_text:
                    violations.append({
                        'type': 'flagged',
                        'keyword': kw,
                        'message': f'Flagged keyword detected: {kw}'
                    })
                    severity = 'flagged'
                    print(f' Flagged keyword: {kw}')

        return {
            'has_violations': len(violations) > 0,
            'violations': violations,
            'severity': severity
        }

    def check_length(self, text: str) -> Dict[str, Any]:
        """Check if text exceeds maximum length."""
        length = len(text)
        is_valid = length <= self.max_length

        return {
            'is_valid': is_valid,
            'length': length,
            'max_length': self.max_length,
            'message': f'Prompt length: {length}/{self.max_length} chars' if is_valid else f'Exceeds max length of {self.max_length}'
        }

    def check_structure_limits(self, text: str) -> Dict[str, Any]:
        """Check token, line, paragraph, and nesting limits to prevent oversized or recursive prompts."""
        tokens = len(text.split())
        lines = text.count("\n") + 1
        paragraphs = len([p for p in text.split("\n\n") if p.strip()])

        depth = 0
        max_depth_seen = 0
        for ch in text:
            if ch in "{[":
                depth += 1
                max_depth_seen = max(max_depth_seen, depth)
            elif ch in "}]":
                depth = max(depth - 1, 0)

        violations = []
        severity = 'safe'

        if tokens > self.max_tokens:
            violations.append({'type': 'length', 'message': f'Token count {tokens} exceeds limit {self.max_tokens}'})
            severity = 'flagged'
        if lines > self.max_lines:
            violations.append({'type': 'length', 'message': f'Line count {lines} exceeds limit {self.max_lines}'})
            severity = 'flagged'
        if max_depth_seen > self.max_brace_depth:
            violations.append({'type': 'recursion', 'message': f'Nested structures depth {max_depth_seen} exceeds limit {self.max_brace_depth}'})
            severity = 'flagged'
        if paragraphs > self.max_paragraphs:
            violations.append({'type': 'length', 'message': f'Paragraph count {paragraphs} exceeds limit {self.max_paragraphs}'})
            severity = 'flagged'

        return {
            'has_violations': len(violations) > 0,
            'violations': violations,
            'severity': severity,
            'tokens': tokens,
            'lines': lines,
            'depth': max_depth_seen,
            'paragraphs': paragraphs
        }

    def detect_prompt_injection(self, text: str) -> Dict[str, Any]:
        """Detect prompt injection attempts via keyword and pattern checks."""
        lower_text = text.lower()
        hits = []
        for pat in self.prompt_injection_patterns:
            if re.search(pat, lower_text):
                hits.append(pat)

        return {
            'has_injection': len(hits) > 0,
            'patterns': hits,
            'severity': 'injected' if hits else 'safe'
        }

    def detect_context_drift(self, text: str) -> Dict[str, Any]:
        """Detect attempts to shift or rewrite the system role."""
        lower_text = text.lower()
        hits = []
        for pat in self.context_drift_patterns:
            if re.search(pat, lower_text):
                hits.append(pat)

        return {
            'has_drift': len(hits) > 0,
            'patterns': hits,
            'severity': 'flagged' if hits else 'safe'
        }

    def detect_unicode_obfuscation(self, text: str) -> Dict[str, Any]:
        """Detect unicode tricks like zero-width chars and mixed scripts."""
        zero_width = bool(re.search(r"[\u200b\u200c\u200d\ufeff]", text))

        script_mix = False
        ascii_count = sum(1 for c in text if ord(c) < 128)
        non_ascii_count = len(text) - ascii_count
        if ascii_count > 0 and non_ascii_count > 0:
            script_mix = True

        confusable = False
        normalized = unicodedata.normalize('NFKD', text)
        if normalized != text:
            confusable = True

        combining_marks = any(unicodedata.combining(c) for c in text)

        issues = []
        if zero_width:
            issues.append('zero_width')
        if script_mix:
            issues.append('mixed_scripts')
        if confusable:
            issues.append('confusable_chars')
        if combining_marks:
            issues.append('combining_marks')

        severity = 'safe'
        if issues:
            severity = 'flagged'

        return {
            'has_obfuscation': len(issues) > 0,
            'issues': issues,
            'severity': severity,
            'normalized': normalized
        }

    def detect_malware_scripts(self, text: str) -> Dict[str, Any]:
        """Detect embedded code or script injection attempts."""
        lower_text = text.lower()
        hits = []
        for pat in self.malware_patterns:
            if re.search(pat, lower_text, re.MULTILINE):
                hits.append(pat)

        severity = 'malicious' if hits else 'safe'
        return {
            'has_malware': len(hits) > 0,
            'patterns': hits,
            'severity': severity
        }

    def detect_links(self, text: str) -> Dict[str, Any]:
        """Detect external links and flag suspicious shorteners/domains/TLDs."""
        links = self.url_pattern.findall(text)
        suspicious = []
        for link in links:
            lower = link.lower()
            if any(domain in lower for domain in self.url_shorteners):
                suspicious.append(link)
                continue
            if any(lower.endswith(tld) for tld in self.suspicious_tlds):
                suspicious.append(link)
                continue
            if any(domain in lower for domain in self.blocked_domains):
                suspicious.append(link)

        severity = 'flagged' if suspicious else 'safe'
        return {
            'links': links,
            'suspicious': suspicious,
            'severity': severity,
            'has_links': len(links) > 0,
            'has_suspicious': len(suspicious) > 0
        }

    def sanitize_input(self, text: str) -> Dict[str, Any]:
        """Remove HTML/script tags and zero-width chars prior to analysis."""
        cleaned = re.sub(r"<[^>]+>", " ", text)
        cleaned = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        notes = []
        if cleaned != text:
            notes.append("Sanitized HTML/hidden chars")

        return {
            'clean_text': cleaned,
            'was_modified': cleaned != text,
            'notes': notes
        }

    def detect_shadow_context(self, text: str) -> Dict[str, Any]:
        """Detect attempts to reveal or tamper with hidden/system prompts."""
        lower_text = text.lower()
        hits = []
        for pat in self.shadow_context_patterns:
            if re.search(pat, lower_text):
                hits.append(pat)

        return {
            'has_shadow': len(hits) > 0,
            'patterns': hits,
            'severity': 'flagged' if hits else 'safe'
        }

    def detect_cross_language_jailbreak(self, text: str) -> Dict[str, Any]:
        """Detect mixed-script prompts that may hide intent across languages."""
        script_counts = {'latin': 0, 'cyrillic': 0, 'arabic': 0, 'cjk': 0, 'other': 0}
        for ch in text:
            code = ord(ch)
            if 0x0041 <= code <= 0x02AF:
                script_counts['latin'] += 1
            elif 0x0400 <= code <= 0x052F:
                script_counts['cyrillic'] += 1
            elif 0x0600 <= code <= 0x06FF:
                script_counts['arabic'] += 1
            elif 0x2E80 <= code <= 0x9FFF:
                script_counts['cjk'] += 1
            elif code > 127:
                script_counts['other'] += 1

        scripts_used = [k for k, v in script_counts.items() if v > 0]
        has_mix = len([k for k, v in script_counts.items() if v > 30]) > 1

        return {
            'has_mix': has_mix,
            'scripts': scripts_used,
            'severity': 'flagged' if has_mix else 'safe'
        }

    def detect_psychological_manipulation(self, text: str) -> Dict[str, Any]:
        """Detect emotional or persuasive jailbreak attempts."""
        lower_text = text.lower()
        hits = []
        for pat in self.psychological_patterns:
            if re.search(pat, lower_text):
                hits.append(pat)

        return {
            'has_manipulation': len(hits) > 0,
            'patterns': hits,
            'severity': 'flagged' if hits else 'safe'
        }

    def detect_social_engineering(self, text: str) -> Dict[str, Any]:
        """Detect social engineering intents (impersonation, internal data)."""
        lower_text = text.lower()
        hits = []
        for pat in self.social_engineering_patterns:
            if re.search(pat, lower_text):
                hits.append(pat)

        return {
            'has_social_engineering': len(hits) > 0,
            'patterns': hits,
            'severity': 'flagged' if hits else 'safe'
        }

    def detect_identity_spoofing(self, text: str) -> Dict[str, Any]:
        """Detect requests to spoof authoritative roles."""
        lower_text = text.lower()
        hits = []
        for pat in self.identity_spoof_patterns:
            if re.search(pat, lower_text):
                hits.append(pat)

        return {
            'has_spoofing': len(hits) > 0,
            'patterns': hits,
            'severity': 'flagged' if hits else 'safe'
        }

    def detect_sensitive_tasks(self, text: str) -> Dict[str, Any]:
        """Detect sensitive or disallowed task categories (malware, weapons, drugs)."""
        lower_text = text.lower()
        hits = []
        for pat in self.sensitive_task_patterns:
            if re.search(pat, lower_text):
                hits.append(pat)

        return {
            'has_sensitive': len(hits) > 0,
            'patterns': hits,
            'severity': 'blocked' if hits else 'safe'
        }

    def detect_red_team_patterns(self, text: str) -> Dict[str, Any]:
        """Detect common red-team jailbreak signatures (DAN, unfiltered)."""
        lower_text = text.lower()
        hits = []
        for pat in self.red_team_patterns:
            if re.search(pat, lower_text):
                hits.append(pat)

        return {
            'has_redteam': len(hits) > 0,
            'patterns': hits,
            'severity': 'injected' if hits else 'safe'
        }

    def detect_indirect_injection(self, text: str) -> Dict[str, Any]:
        """Detect instructions embedded inside data blobs (JSON, code, markup)."""
        lower_text = text.lower()
        patterns = [
            r"\{\s*\"system\"", r"\"prompt\"\s*:\s*\".*<</sys>>",
            r"data:text/plain;base64", r"application/json",
        ]
        hits = []
        for pat in patterns:
            if re.search(pat, lower_text):
                hits.append(pat)

        return {
            'has_indirect': len(hits) > 0,
            'patterns': hits,
            'severity': 'flagged' if hits else 'safe'
        }

    def detect_encoded_payloads(self, text: str) -> Dict[str, Any]:
        """Detect encoded blobs (base64/hex) and decode a sample for downstream checks."""
        base64_matches = re.findall(r"\b[A-Za-z0-9+/]{24,}={0,2}\b", text)
        hex_matches = re.findall(r"\b(?:0x)?[0-9a-fA-F]{24,}\b", text)
        decoded_samples = []

        def _try_decode_b64(blob: str) -> str:
            try:
                decoded = base64.b64decode(blob, validate=True)
                snippet = decoded.decode(errors='ignore')
                return snippet[:200]
            except (binascii.Error, ValueError):
                return ""

        for blob in base64_matches[:2]:  # limit work
            snippet = _try_decode_b64(blob)
            if snippet:
                decoded_samples.append(snippet)

        severity = 'flagged' if base64_matches or hex_matches else 'safe'

        return {
            'has_encoded': bool(base64_matches or hex_matches),
            'base64_matches': base64_matches,
            'hex_matches': hex_matches,
            'decoded_samples': decoded_samples,
            'severity': severity
        }

    def classify_intent(self, detections: Dict[str, Any]) -> Dict[str, Any]:
        """Lightweight intent classification based on accumulated detections."""
        intent = "general"
        if detections.get('injection') or detections.get('redteam'):
            intent = "jailbreak"
        elif detections.get('malware') or detections.get('sensitive'):
            intent = "malicious"
        elif detections.get('social') or detections.get('spoof'):
            intent = "impersonation"
        elif detections.get('shadow'):
            intent = "recon"

        severity = 'flagged' if intent != 'general' else 'safe'
        return {
            'intent': intent,
            'severity': severity
        }
