"""Toxicity checker — pattern-based detection with optional Detoxify/Perspective API backend."""

from __future__ import annotations

import re
from typing import Any

from airiskguard.checkers.base import BaseChecker
from airiskguard.types import CheckResult, RiskLevel

# --- Pattern-based detection ---

_THREAT_PATTERNS = [
    re.compile(p, re.IGNORECASE) for p in [
        r"\bi(?:'ll| will| am going to| gonna) (?:kill|hurt|destroy|murder|attack|harm) (?:you|them|him|her)\b",
        r"\byou(?:'re| are) (?:going to|gonna) (?:die|regret|pay for this)\b",
        r"\bi(?:'ll| will) (?:find|hunt) you\b",
        r"\bwatch your back\b",
        r"\byou(?:'ll| will) (?:pay|suffer) for this\b",
        r"\bthreat(?:en|ening)?\b.{0,30}\b(?:kill|hurt|harm|destroy)\b",
    ]
]

_HATE_SPEECH_PATTERNS = [
    re.compile(p, re.IGNORECASE) for p in [
        r"\b(?:all|every|those)\s+\w+s?\s+(?:should|must|deserve to)\s+(?:die|be killed|be eliminated|be removed)\b",
        r"\b(?:kill|eliminate|exterminate)\s+(?:all\s+)?\w+s?\b",
        r"\b\w+s?\s+(?:are|aren't)\s+(?:human|people|real humans)\b",
        r"\b(?:go back to|get out of)\s+(?:your country|where you came from)\b",
        r"\b(?:white|black|asian|jewish|muslim|christian)\s+(?:supremacy|power|genocide)\b",
    ]
]

_INSULT_PATTERNS = [
    re.compile(p, re.IGNORECASE) for p in [
        r"\byou(?:'re| are)\s+(?:a\s+)?(?:stupid|dumb|idiot|moron|imbecile|retard\w*|worthless|pathetic|disgusting|trash|garbage)\b",
        r"\b(?:shut up|go to hell|go f\*ck yourself|f\*ck you|screw you)\b",
        r"\b(?:stupid|dumb|idiot|moron)\s+(?:bitch|bastard|asshole|jerk)\b",
    ]
]

# Explicit profanity — using obfuscated forms to avoid false positives in source code
_PROFANITY_PATTERNS = [
    re.compile(p, re.IGNORECASE) for p in [
        r"\bf+u+c+k+(?:ing|er|ed|s)?\b",
        r"\bs+h+i+t+(?:ty|ter|s)?\b",
        r"\ba+s+s+h+o+l+e+s?\b",
        r"\bb+i+t+c+h+(?:es|ing)?\b",
        r"\bc+u+n+t+s?\b",
        r"\bd+i+c+k+(?:s|head)?\b",
        r"\bp+i+s+s+(?:ed|ing)?\b",
        r"\bw+h+o+r+e+s?\b",
        r"\bn+i+g+g+(?:a|er)+s?\b",  # slur
        r"\bf+a+g+(?:g+o+t+)?s?\b",  # slur
    ]
]


def _scan_patterns(text: str, patterns: list[re.Pattern]) -> list[str]:
    return [p.pattern[:50] for p in patterns if p.search(text)]


class ToxicityChecker(BaseChecker):
    """Detects toxic content: threats, hate speech, insults, and profanity.

    Supports three backends:
    - ``"pattern"`` (default) — fast regex-based detection, no external deps
    - ``"detoxify"`` — uses the Detoxify library (``pip install airiskguard[detoxify]``)
    - ``"perspective"`` — uses Google Perspective API (requires ``perspective_api_key``)

    Args:
        threshold: Score above which content is flagged (default 0.7).
        backend: Detection backend — ``"pattern"``, ``"detoxify"``, or ``"perspective"``.
        perspective_api_key: Required when ``backend="perspective"``.
        check_input: Whether to check input_data (default True).
        check_output: Whether to check output_data (default True).
    """

    name = "toxicity"

    def __init__(
        self,
        threshold: float = 0.7,
        backend: str = "pattern",
        perspective_api_key: str = "",
        check_input: bool = True,
        check_output: bool = True,
    ) -> None:
        self.threshold = threshold
        self.backend = backend
        self.perspective_api_key = perspective_api_key
        self.check_input = check_input
        self.check_output = check_output
        self._detoxify_model = None

        if backend == "detoxify":
            self._load_detoxify()

    def _load_detoxify(self) -> None:
        try:
            from detoxify import Detoxify
            self._detoxify_model = Detoxify("original")
        except ImportError:
            self.backend = "pattern"

    async def check(
        self, input_data: Any, output_data: Any, context: dict[str, Any] | None = None
    ) -> CheckResult:
        texts: list[str] = []
        if self.check_input and input_data:
            texts.append(str(input_data))
        if self.check_output and output_data:
            texts.append(str(output_data))

        combined = " ".join(texts).strip()
        if not combined:
            return CheckResult(
                checker_name=self.name, risk_level=RiskLevel.LOW,
                passed=True, score=0.0, details={"flags": []},
            )

        if self.backend == "detoxify" and self._detoxify_model:
            score, flags = self._detoxify_score(combined)
        elif self.backend == "perspective" and self.perspective_api_key:
            score, flags = await self._perspective_score(combined)
        else:
            score, flags = self._pattern_score(combined)

        risk = _score_to_risk(score)
        return CheckResult(
            checker_name=self.name,
            risk_level=risk,
            passed=score < self.threshold,
            score=score,
            details={"flags": flags, "backend": self.backend},
        )

    def _pattern_score(self, text: str) -> tuple[float, list[str]]:
        flags: list[str] = []
        score = 0.0

        threat_hits = _scan_patterns(text, _THREAT_PATTERNS)
        if threat_hits:
            flags.extend(f"threat: {h}" for h in threat_hits)
            score = max(score, 0.9)

        hate_hits = _scan_patterns(text, _HATE_SPEECH_PATTERNS)
        if hate_hits:
            flags.extend(f"hate_speech: {h}" for h in hate_hits)
            score = max(score, 0.95)

        insult_hits = _scan_patterns(text, _INSULT_PATTERNS)
        if insult_hits:
            flags.extend(f"insult: {h}" for h in insult_hits)
            score = max(score, 0.75)

        profanity_hits = _scan_patterns(text, _PROFANITY_PATTERNS)
        if profanity_hits:
            flags.extend(f"profanity: {h}" for h in profanity_hits[:3])
            score = max(score, 0.6)

        return score, flags

    def _detoxify_score(self, text: str) -> tuple[float, list[str]]:
        results = self._detoxify_model.predict(text)
        score = max(results.values())
        flags = [f"{k}={v:.2f}" for k, v in results.items() if v >= self.threshold]
        return score, flags

    async def _perspective_score(self, text: str) -> tuple[float, list[str]]:
        try:
            import httpx
            url = "https://commentanalyzer.googleapis.com/v1alpha1/comments:analyze"
            payload = {
                "comment": {"text": text},
                "requestedAttributes": {
                    "TOXICITY": {}, "SEVERE_TOXICITY": {},
                    "THREAT": {}, "INSULT": {}, "IDENTITY_ATTACK": {},
                },
            }
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, json=payload, params={"key": self.perspective_api_key})
                data = resp.json()
            scores = {
                k: v["summaryScore"]["value"]
                for k, v in data.get("attributeScores", {}).items()
            }
            score = max(scores.values()) if scores else 0.0
            flags = [f"{k}={v:.2f}" for k, v in scores.items() if v >= self.threshold]
            return score, flags
        except Exception:
            return self._pattern_score(text)


def _score_to_risk(score: float) -> RiskLevel:
    if score >= 0.9:
        return RiskLevel.CRITICAL
    if score >= 0.7:
        return RiskLevel.HIGH
    if score >= 0.4:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW
