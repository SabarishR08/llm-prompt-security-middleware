"""Threat intelligence lookups for URLs, domains, and IPs with caching."""
import requests
import time
import re
from typing import Dict, Any, Optional


class ThreatIntelService:
    def __init__(self, vt_api_key: str = "", gsb_api_key: str = "", abuse_key: str = "", vt_domain_key: str = ""):
        self.vt_api_key = vt_api_key
        self.vt_domain_key = vt_domain_key or vt_api_key
        self.gsb_api_key = gsb_api_key
        self.abuse_key = abuse_key
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl_seconds = 3600

    def _get_cached(self, key: str) -> Optional[Dict[str, Any]]:
        entry = self.cache.get(key)
        if entry and (time.time() - entry.get("ts", 0) < self.ttl_seconds):
            return entry["data"]
        return None

    def _set_cache(self, key: str, data: Dict[str, Any]):
        self.cache[key] = {"ts": time.time(), "data": data}

    def _vt_url_lookup(self, url: str, verdicts: list, details: list):
        if not self.vt_api_key:
            return
        try:
            resp = requests.post(
                "https://www.virustotal.com/api/v3/urls",
                data={"url": url},
                headers={"x-apikey": self.vt_api_key},
                timeout=6,
            )
            if resp.status_code in (200, 201):
                data = resp.json()
                # fetch analysis stats
                stats = data.get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
                malicious = stats.get("malicious", 0) + stats.get("suspicious", 0)
                if malicious > 0:
                    verdicts.append("malicious")
                    details.append(f"VirusTotal reports {malicious} detections")
                else:
                    verdicts.append("clean")
            else:
                details.append(f"VT status {resp.status_code}")
        except Exception as exc:
            details.append(f"VT error: {exc}")

    def _gsb_lookup(self, url: str, verdicts: list, details: list):
        if not self.gsb_api_key:
            return
        body = {
            "client": {"clientId": "ai-compliance", "clientVersion": "1.0"},
            "threatInfo": {
                "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE"],
                "platformTypes": ["ANY_PLATFORM"],
                "threatEntryTypes": ["URL"],
                "threatEntries": [{"url": url}],
            },
        }
        try:
            resp = requests.post(
                f"https://safebrowsing.googleapis.com/v4/threatMatches:find?key={self.gsb_api_key}",
                json=body,
                timeout=6,
            )
            if resp.status_code == 200:
                data = resp.json()
                if data.get("matches"):
                    verdicts.append("unsafe")
                    details.append("Google Safe Browsing match")
            else:
                details.append(f"GSB status {resp.status_code}")
        except Exception as exc:
            details.append(f"GSB error: {exc}")

    def check_url_reputation(self, url: str) -> Dict[str, Any]:
        cached = self._get_cached(f"url:{url}")
        if cached:
            return cached

        verdicts: list = []
        details: list = []

        self._vt_url_lookup(url, verdicts, details)
        self._gsb_lookup(url, verdicts, details)

        verdict = "unknown"
        if any(v in verdicts for v in ["malicious", "unsafe", "phishing"]):
            verdict = "malicious"
        elif verdicts:
            verdict = "clean"

        result = {"url": url, "verdict": verdict, "details": details}
        self._set_cache(f"url:{url}", result)
        return result

    def check_domain_reputation(self, domain: str) -> Dict[str, Any]:
        cache_key = f"domain:{domain}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached

        verdicts: list = []
        details: list = []

        if self.vt_domain_key:
            try:
                resp = requests.get(
                    f"https://www.virustotal.com/api/v3/domains/{domain}",
                    headers={"x-apikey": self.vt_domain_key},
                    timeout=6,
                )
                if resp.status_code == 200:
                    stats = resp.json().get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
                    malicious = stats.get("malicious", 0) + stats.get("suspicious", 0)
                    if malicious > 0:
                        verdicts.append("malicious")
                        details.append(f"VT domain detections: {malicious}")
                    else:
                        verdicts.append("clean")
                else:
                    details.append(f"VT domain status {resp.status_code}")
            except Exception as exc:
                details.append(f"VT domain error: {exc}")

        verdict = "malicious" if "malicious" in verdicts else ("clean" if verdicts else "unknown")
        result = {"domain": domain, "verdict": verdict, "details": details}
        self._set_cache(cache_key, result)
        return result

    def check_ip_reputation(self, ip: str) -> Dict[str, Any]:
        cache_key = f"ip:{ip}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        verdict = "unknown"
        details = []
        if self.abuse_key:
            try:
                resp = requests.get(
                    "https://api.abuseipdb.com/api/v2/check",
                    params={"ipAddress": ip, "maxAgeInDays": 90},
                    headers={"Key": self.abuse_key, "Accept": "application/json"},
                    timeout=6,
                )
                if resp.status_code == 200:
                    data = resp.json().get("data", {})
                    score = data.get("abuseConfidenceScore", 0)
                    if score >= 50:
                        verdict = "malicious"
                        details.append(f"AbuseIPDB score {score}")
                    else:
                        verdict = "clean"
                else:
                    details.append(f"AbuseIPDB status {resp.status_code}")
            except Exception as exc:
                details.append(f"AbuseIPDB error: {exc}")
        result = {"ip": ip, "verdict": verdict, "details": details}
        self._set_cache(cache_key, result)
        return result

    def multi_source_reputation_lookup(self, indicator: str) -> Dict[str, Any]:
        """Auto-detect indicator type and perform consolidated lookup."""
        if re.match(r"^https?://", indicator, re.IGNORECASE):
            return self.check_url_reputation(indicator)
        if re.match(r"^\d+\.\d+\.\d+\.\d+$", indicator):
            return self.check_ip_reputation(indicator)
        return self.check_domain_reputation(indicator)
