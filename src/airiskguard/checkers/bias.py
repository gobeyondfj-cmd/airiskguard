"""Bias checker — disparate impact, demographic parity, equalized odds."""

from __future__ import annotations

import re
from typing import Any

from airiskguard.checkers.base import BaseChecker
from airiskguard.types import CheckResult, RiskLevel


class BiasChecker(BaseChecker):
    name = "bias"

    def __init__(
        self,
        disparate_impact_threshold: float = 0.8,  # 4/5ths rule
        parity_threshold: float = 0.1,
    ) -> None:
        self._di_threshold = disparate_impact_threshold
        self._parity_threshold = parity_threshold

    async def check(
        self, input_data: Any, output_data: Any, context: dict[str, Any] | None = None
    ) -> CheckResult:
        context = context or {}
        flags: list[str] = []
        score = 0.0

        # Check for group-level statistics in context
        group_outcomes = context.get("group_outcomes", {})
        protected_attribute = context.get("protected_attribute", "")

        if group_outcomes and len(group_outcomes) >= 2:
            # Disparate impact ratio
            di_flags, di_score = _check_disparate_impact(
                group_outcomes, self._di_threshold
            )
            flags.extend(di_flags)
            score = max(score, di_score)

            # Demographic parity
            dp_flags, dp_score = _check_demographic_parity(
                group_outcomes, self._parity_threshold
            )
            flags.extend(dp_flags)
            score = max(score, dp_score)

        # Check prediction-level bias signals
        predictions = context.get("predictions", {})
        labels = context.get("labels", {})
        if predictions and labels:
            eo_flags, eo_score = _check_equalized_odds(predictions, labels)
            flags.extend(eo_flags)
            score = max(score, eo_score)

        # Check input and output text for biased language
        text_to_check = " ".join(filter(None, [
            str(input_data) if isinstance(input_data, str) else "",
            str(output_data) if isinstance(output_data, str) else "",
        ]))
        if text_to_check.strip():
            lang_flags, lang_score = _check_biased_language(text_to_check)
            flags.extend(lang_flags)
            score = max(score, lang_score)

        risk = _score_to_risk(score)
        return CheckResult(
            checker_name=self.name,
            risk_level=risk,
            passed=risk <= RiskLevel.MEDIUM,
            score=score,
            details={
                "flags": flags,
                "protected_attribute": protected_attribute,
            },
        )


def _check_disparate_impact(
    group_outcomes: dict[str, dict[str, int]], threshold: float
) -> tuple[list[str], float]:
    flags: list[str] = []
    score = 0.0

    rates: dict[str, float] = {}
    for group, outcomes in group_outcomes.items():
        positive = outcomes.get("positive", 0)
        total = outcomes.get("total", 0)
        if total > 0:
            rates[group] = positive / total

    if len(rates) >= 2:
        max_rate = max(rates.values())
        if max_rate > 0:
            for group, rate in rates.items():
                ratio = rate / max_rate
                if ratio < threshold:
                    flags.append(
                        f"disparate_impact: {group} (ratio={ratio:.3f}, threshold={threshold})"
                    )
                    score = max(score, 1.0 - ratio)

    return flags, score


def _check_demographic_parity(
    group_outcomes: dict[str, dict[str, int]], threshold: float
) -> tuple[list[str], float]:
    flags: list[str] = []
    score = 0.0

    rates: list[float] = []
    for outcomes in group_outcomes.values():
        positive = outcomes.get("positive", 0)
        total = outcomes.get("total", 0)
        if total > 0:
            rates.append(positive / total)

    if len(rates) >= 2:
        diff = max(rates) - min(rates)
        if diff > threshold:
            flags.append(f"demographic_parity_violation (diff={diff:.3f})")
            score = max(score, min(diff, 1.0))

    return flags, score


def _check_equalized_odds(
    predictions: dict[str, list[int]], labels: dict[str, list[int]]
) -> tuple[list[str], float]:
    flags: list[str] = []
    score = 0.0

    tpr_rates: dict[str, float] = {}
    fpr_rates: dict[str, float] = {}

    for group in predictions:
        if group not in labels:
            continue
        preds = predictions[group]
        true_labels = labels[group]
        if len(preds) != len(true_labels):
            continue

        tp = sum(1 for p, l in zip(preds, true_labels) if p == 1 and l == 1)
        fn = sum(1 for p, l in zip(preds, true_labels) if p == 0 and l == 1)
        fp = sum(1 for p, l in zip(preds, true_labels) if p == 1 and l == 0)
        tn = sum(1 for p, l in zip(preds, true_labels) if p == 0 and l == 0)

        tpr_rates[group] = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        fpr_rates[group] = fp / (fp + tn) if (fp + tn) > 0 else 0.0

    if len(tpr_rates) >= 2:
        tpr_diff = max(tpr_rates.values()) - min(tpr_rates.values())
        if tpr_diff > 0.1:
            flags.append(f"equalized_odds_tpr_violation (diff={tpr_diff:.3f})")
            score = max(score, min(tpr_diff, 1.0))

    if len(fpr_rates) >= 2:
        fpr_diff = max(fpr_rates.values()) - min(fpr_rates.values())
        if fpr_diff > 0.1:
            flags.append(f"equalized_odds_fpr_violation (diff={fpr_diff:.3f})")
            score = max(score, min(fpr_diff, 1.0))

    return flags, score


_BIASED_TERMS = [
    "always lazy", "naturally inferior", "inherently violent",
    "genetically predisposed to", "those people",
    # Gender bias
    "not as good at", "better leaders than", "worse at",
    "men are better", "women are better", "men are smarter", "women are smarter",
    # Racial/ethnic bias
    "are all criminals", "are naturally", "are genetically",
    "that race", "that ethnicity", "ethnic group is",
    # Age bias
    "old people can't", "elderly can't", "too old to",
    # Socioeconomic bias
    "poor people are poor because", "lazy poor",
    # Immigration bias
    "taking our jobs", "all immigrants",
    # Disability bias
    "burden on society", "disabled people are a burden",
    # Religious bias
    "that religion is", "inherently violent religion",
]

_BIASED_PATTERNS = [
    re.compile(p, re.IGNORECASE) for p in [
        r"\b(?:women|men|girls|boys)\s+(?:are|can't|cannot|don't|do not)\s+(?:as good|as smart|as capable)",
        r"\b(?:all|every)\s+(?:immigrants?|foreigners?|muslims?|christians?|jews?|blacks?|whites?|asians?)\s+(?:are|is)\b",
        r"\b(?:old|elderly|senior)\s+people\s+(?:can't|cannot|don't|are not able)",
        r"\b(?:poor|homeless)\s+people\s+(?:are|deserve|should)\b",
        r"\b(?:that|those)\s+(?:race|ethnicity|religion|group)\s+(?:is|are)\b",
        r"\b(?:men|women)\s+are\s+(?:better|worse|smarter|dumber|superior|inferior)\s+(?:than|to)\b",
        r"\bgenetically\s+(?:inferior|superior|predisposed)\b",
        r"\bnaturally\s+(?:lazy|violent|criminal|inferior|superior)\b",
        r"\binherently\s+(?:lazy|violent|criminal|inferior|superior)\b",
        r"\b(?:disabled|handicapped)\s+people\s+are\s+a\s+burden\b",
    ]
]


def _check_biased_language(text: str) -> tuple[list[str], float]:
    flags: list[str] = []
    score = 0.0
    text_lower = text.lower()

    for term in _BIASED_TERMS:
        if term in text_lower:
            flags.append(f"biased_language: '{term}'")
            score = max(score, 0.7)

    for pattern in _BIASED_PATTERNS:
        if pattern.search(text):
            flags.append(f"biased_pattern: '{pattern.pattern[:40]}'")
            score = max(score, 0.75)

    return flags, score


def _score_to_risk(score: float) -> RiskLevel:
    if score >= 0.8:
        return RiskLevel.CRITICAL
    if score >= 0.5:
        return RiskLevel.HIGH
    if score >= 0.3:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW
