"""Advanced prompt injection and jailbreak detector.

Detects polyglot prompts, homoglyph attacks, encoded hidden instructions, 
multilingual jailbreak attempts, markdown escape bypasses, and token smuggling patterns.

Returns a structured detection result with severity and explanation.
"""
from __future__ import annotations

from typing import Dict, Any, List
import re
import unicodedata
import base64
import binascii


class PromptInjectionDetector:
    """Detect sophisticated prompt injection and jailbreak attempts."""

    def __init__(self):
        # Patterns for well-known jailbreak / token smuggling phrases
        self.token_smuggling_patterns = [
            r"###\s*system override",
            r"you are now dan",
            r"ignore previous instructions",
            r"ignore all prior instructions",
            r"you are no longer bound",
            r"begin system override",
            r"act as an unfiltered model",
            r"switch to developer mode",
        ]

        # Polyglot / mixed-context indicators (code + markup + data URIs)
        self.polyglot_patterns = [
            r"data:text/(?:plain|html);base64,",
            r"<?php", r"<script", r"</script>",
            r"#! /bin/sh", r"#!/bin/bash",
            r"%PDF-",  # PDF polyglot lead-in
            r"\bMZ[A-Z]{2}",  # PE header hint
            r"\bPK\x03\x04",  # Zip/JAR polyglot
            r"content-transfer-encoding: base64",
        ]

        # Markdown escape / fence bypass attempts
        self.markdown_escape_patterns = [
            r"```\s*ignore_this",
            r"```\s*.*?```",  # suspicious fenced block
            r"~~~\s*.*?~~~",
            r"<\s*details\s*>",
        ]

        # Multi-language jailbreak hints (mixed scripts with jailbreak phrases)
        self.multilang_phrases = [
            r"lib\u00e9rate", r"ignora las reglas", r"olvida las reglas",
            r"s\u00e9 libre", r"sois libre", r"you are free now",
            r"jailbreak", r"modo desarrollador",
        ]

    def _detect_homoglyphs(self, text: str) -> Dict[str, Any]:
        """Detect unicode homoglyph / confusable characters."""
        normalized = unicodedata.normalize("NFKD", text)
        confusable = normalized != text
        non_ascii = [c for c in text if ord(c) > 127]
        suspicious = any(unicodedata.category(c).startswith("M") for c in text)  # combining marks
        return {
            "has_homoglyph": bool(confusable or non_ascii or suspicious),
            "details": {
                "non_ascii_count": len(non_ascii),
                "confusable": confusable,
                "combining_marks": suspicious,
            },
        }

    def _detect_encoded_instructions(self, text: str) -> Dict[str, Any]:
        """Detect base64/hex blobs that may hide instructions."""
        b64_matches = re.findall(r"\b[A-Za-z0-9+/]{40,}={0,2}\b", text)
        hex_matches = re.findall(r"\b(?:0x)?[0-9a-fA-F]{40,}\b", text)

        decoded_samples: List[str] = []
        for blob in b64_matches[:2]:  # limit work
            try:
                decoded = base64.b64decode(blob, validate=True)
                snippet = decoded.decode(errors="ignore")
                if snippet:
                    decoded_samples.append(snippet[:200])
            except (binascii.Error, ValueError):
                continue

        has_hidden = bool(b64_matches or hex_matches)
        return {
            "has_hidden": has_hidden,
            "b64_count": len(b64_matches),
            "hex_count": len(hex_matches),
            "decoded_samples": decoded_samples,
        }

    def _detect_polyglot(self, text: str) -> Dict[str, Any]:
        hits = [pat for pat in self.polyglot_patterns if re.search(pat, text, re.IGNORECASE | re.DOTALL)]
        return {"has_polyglot": bool(hits), "patterns": hits}

    def _detect_markdown_escape(self, text: str) -> Dict[str, Any]:
        hits = [pat for pat in self.markdown_escape_patterns if re.search(pat, text, re.IGNORECASE | re.DOTALL)]
        return {"has_bypass": bool(hits), "patterns": hits}

    def _detect_token_smuggling(self, text: str) -> Dict[str, Any]:
        lower = text.lower()
        hits = [pat for pat in self.token_smuggling_patterns if re.search(pat, lower)]
        return {"has_tokensmuggle": bool(hits), "patterns": hits}

    def _detect_multilang(self, text: str) -> Dict[str, Any]:
        hits = [pat for pat in self.multilang_phrases if re.search(pat, text, re.IGNORECASE)]
        # script mix heuristic
        ascii_count = sum(1 for c in text if ord(c) < 128)
        non_ascii_count = len(text) - ascii_count
        mixed_scripts = ascii_count > 0 and non_ascii_count > 20
        return {"has_multilang": bool(hits or mixed_scripts), "patterns": hits, "mixed_scripts": mixed_scripts}

    def detect(self, text: str) -> Dict[str, Any]:
        """Run all detectors and return a structured result."""
        results = []
        severity = "safe"

        homoglyph = self._detect_homoglyphs(text)
        if homoglyph["has_homoglyph"]:
            results.append(("homoglyph", "Homoglyph/obfuscated characters detected"))
            severity = "flagged"

        encoded = self._detect_encoded_instructions(text)
        if encoded["has_hidden"]:
            results.append(("encoded", "Hidden instructions in base64/hex payload"))
            severity = "blocked"

        polyglot = self._detect_polyglot(text)
        if polyglot["has_polyglot"]:
            results.append(("polyglot", "Polyglot or mixed-format payload detected"))
            severity = "blocked"

        md_escape = self._detect_markdown_escape(text)
        if md_escape["has_bypass"]:
            results.append(("md_escape", "Markdown fence escape / ignore block"))
            severity = "flagged" if severity != "blocked" else severity

        token_smuggle = self._detect_token_smuggling(text)
        if token_smuggle["has_tokensmuggle"]:
            results.append(("token_smuggling", "Known token smuggling phrase detected"))
            severity = "blocked"

        multilang = self._detect_multilang(text)
        if multilang["has_multilang"]:
            results.append(("multilang", "Multilingual jailbreak attempt or mixed scripts"))
            if severity == "safe":
                severity = "flagged"

        is_injection = bool(results)
        matched_rule = results[0][0] if results else None
        explanation = results[0][1] if results else ""

        return {
            "is_injection": is_injection,
            "severity": severity,
            "matched_rule": matched_rule,
            "explanation": explanation,
            "details": {
                "homoglyph": homoglyph,
                "encoded": encoded,
                "polyglot": polyglot,
                "markdown_escape": md_escape,
                "token_smuggling": token_smuggle,
                "multilang": multilang,
            },
        }
