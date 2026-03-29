"""Compliance checker — PII detection, prohibited content, custom rules."""

from __future__ import annotations

import re
from typing import Any

from airiskguard.checkers.base import BaseChecker
from airiskguard.types import CheckResult, RiskLevel

# PII patterns
_PII_PATTERNS: dict[str, re.Pattern[str]] = {
    "ssn": re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
    "email": re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
    "credit_card": re.compile(r'\b(?:\d{4}[- ]?){3}\d{4}\b'),
    "phone_us": re.compile(r'\b(?:\+1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'),
    "ip_address": re.compile(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'),
}

# Prohibited content categories
_PROHIBITED_PATTERNS: dict[str, re.Pattern[str]] = {
    "violence_instruction": re.compile(
        r'\b(?:how to (?:make|build|create) (?:a )?(?:bomb|weapon|explosive))\b', re.IGNORECASE
    ),
    "illegal_activity": re.compile(
        r'\b(?:how to (?:hack|steal|forge|counterfeit))\b', re.IGNORECASE
    ),
    "self_harm": re.compile(
        r'\b(?:how to (?:harm|hurt|kill) (?:yourself|myself|oneself))\b', re.IGNORECASE
    ),
}


class ComplianceChecker(BaseChecker):
    name = "compliance"

    def __init__(
        self,
        detect_pii: bool = True,
        detect_prohibited: bool = True,
        redact_pii: bool = False,
        custom_rules: list[dict[str, str]] | None = None,
    ) -> None:
        self._detect_pii = detect_pii
        self._detect_prohibited = detect_prohibited
        self._redact_pii = redact_pii
        self._custom_rules: list[tuple[str, re.Pattern[str]]] = []
        if custom_rules:
            for rule in custom_rules:
                self._custom_rules.append(
                    (rule["name"], re.compile(rule["pattern"], re.IGNORECASE))
                )

    async def check(
        self, input_data: Any, output_data: Any, context: dict[str, Any] | None = None
    ) -> CheckResult:
        text = f"{input_data} {output_data}" if output_data else str(input_data)
        flags: list[str] = []
        score = 0.0
        redacted_text: str | None = None

        # PII detection (and optional redaction)
        if self._detect_pii:
            pii_flags, pii_score, redacted = _detect_pii(text, redact=self._redact_pii)
            flags.extend(pii_flags)
            score = max(score, pii_score)
            if self._redact_pii and redacted != text:
                redacted_text = redacted

        # Prohibited content
        if self._detect_prohibited:
            prohibited_flags, prohibited_score = _detect_prohibited(text)
            flags.extend(prohibited_flags)
            score = max(score, prohibited_score)

        # Custom rules
        for name, pattern in self._custom_rules:
            matches = pattern.findall(text)
            if matches:
                flags.append(f"custom_rule:{name} ({len(matches)} matches)")
                score = max(score, 0.6)

        risk = _score_to_risk(score)
        details: dict[str, Any] = {"flags": flags}
        if redacted_text is not None:
            details["redacted_text"] = redacted_text

        return CheckResult(
            checker_name=self.name,
            risk_level=risk,
            passed=risk <= RiskLevel.MEDIUM,
            score=score,
            details=details,
        )


def _detect_pii(text: str, redact: bool = False) -> tuple[list[str], float, str]:
    flags: list[str] = []
    score = 0.0
    pii_weights = {"ssn": 0.9, "credit_card": 0.9, "email": 0.4, "phone_us": 0.5, "ip_address": 0.3}
    redacted = text

    for name, pattern in _PII_PATTERNS.items():
        matches = pattern.findall(text)
        if matches:
            flags.append(f"pii_{name} ({len(matches)} found)")
            score = max(score, pii_weights.get(name, 0.5))
            if redact:
                redacted = pattern.sub(f"[REDACTED_{name.upper()}]", redacted)

    return flags, score, redacted


def _detect_prohibited(text: str) -> tuple[list[str], float]:
    flags: list[str] = []
    score = 0.0

    for name, pattern in _PROHIBITED_PATTERNS.items():
        if pattern.search(text):
            flags.append(f"prohibited:{name}")
            score = max(score, 0.95)

    return flags, score


def _score_to_risk(score: float) -> RiskLevel:
    if score >= 0.8:
        return RiskLevel.CRITICAL
    if score >= 0.5:
        return RiskLevel.HIGH
    if score >= 0.3:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW
