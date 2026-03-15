"""Hallucination checker — optional NLI transformer + heuristic fallback."""

from __future__ import annotations

import re
from typing import Any

from airiskguard.checkers.base import BaseChecker
from airiskguard.types import CheckResult, RiskLevel

# Heuristic patterns
_FABRICATED_URL_PATTERN = re.compile(
    r'https?://(?:www\.)?[a-z0-9-]+\.[a-z]{2,}(?:/[^\s]*)?', re.IGNORECASE
)
_CITATION_PATTERN = re.compile(
    r'\b(?:according to|as stated in|per)\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+\(\d{4}\)',
    re.IGNORECASE,
)
_CONFIDENCE_MARKERS = [
    "i'm certain", "i can confirm", "definitely", "absolutely",
    "without a doubt", "100%", "guaranteed",
]
_CONTRADICTION_PAIRS = [
    ("always", "never"), ("all", "none"), ("increase", "decrease"),
    ("true", "false"), ("yes", "no"),
]


class HallucinationChecker(BaseChecker):
    name = "hallucination"

    def __init__(self, use_nli: bool = False) -> None:
        self._use_nli = use_nli
        self._nli_pipeline = None
        if use_nli:
            self._load_nli()

    def _load_nli(self) -> None:
        try:
            from transformers import pipeline
            self._nli_pipeline = pipeline(
                "text-classification",
                model="cross-encoder/nli-deberta-v3-small",
            )
        except ImportError:
            self._use_nli = False

    async def check(
        self, input_data: Any, output_data: Any, context: dict[str, Any] | None = None
    ) -> CheckResult:
        output_text = str(output_data) if output_data else ""
        input_text = str(input_data) if input_data else ""
        context = context or {}

        flags: list[str] = []
        score = 0.0

        # NLI-based check
        if self._use_nli and self._nli_pipeline and input_text and output_text:
            nli_score = self._nli_check(input_text, output_text)
            if nli_score > 0.5:
                flags.append(f"nli_contradiction (score={nli_score:.2f})")
                score = max(score, nli_score)

        # Heuristic checks
        heuristic_flags, heuristic_score = _heuristic_check(output_text, context)
        flags.extend(heuristic_flags)
        score = max(score, heuristic_score)

        risk = _score_to_risk(score)
        return CheckResult(
            checker_name=self.name,
            risk_level=risk,
            passed=risk <= RiskLevel.MEDIUM,
            score=score,
            details={"flags": flags, "nli_enabled": self._use_nli},
        )

    def _nli_check(self, premise: str, hypothesis: str) -> float:
        if not self._nli_pipeline:
            return 0.0
        result = self._nli_pipeline(
            f"{premise} [SEP] {hypothesis}", truncation=True
        )
        for item in result:
            if item["label"].lower() == "contradiction":
                return item["score"]
        return 0.0


def _heuristic_check(text: str, context: dict[str, Any]) -> tuple[list[str], float]:
    flags: list[str] = []
    score = 0.0

    # Fabricated URLs
    urls = _FABRICATED_URL_PATTERN.findall(text)
    known_urls = context.get("known_urls", [])
    fabricated = [u for u in urls if u not in known_urls]
    if fabricated and len(fabricated) > len(urls) * 0.5:
        flags.append(f"potential_fabricated_urls ({len(fabricated)})")
        score = max(score, 0.4)

    # Suspicious citations
    citations = _CITATION_PATTERN.findall(text)
    if citations:
        flags.append(f"unverifiable_citations ({len(citations)})")
        score = max(score, 0.3)

    # Overconfident language
    text_lower = text.lower()
    confidence_count = sum(1 for m in _CONFIDENCE_MARKERS if m in text_lower)
    if confidence_count >= 2:
        flags.append(f"overconfident_language ({confidence_count} markers)")
        score = max(score, 0.3)

    # Internal contradictions
    for a, b in _CONTRADICTION_PAIRS:
        if a in text_lower and b in text_lower:
            flags.append(f"potential_contradiction ({a}/{b})")
            score = max(score, 0.5)
            break

    return flags, score


def _score_to_risk(score: float) -> RiskLevel:
    if score >= 0.8:
        return RiskLevel.CRITICAL
    if score >= 0.5:
        return RiskLevel.HIGH
    if score >= 0.3:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW
