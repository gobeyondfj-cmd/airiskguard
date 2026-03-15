"""Fraud checker — amount anomaly (z-score), velocity, pattern rules."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from airiskguard.checkers.base import BaseChecker
from airiskguard.types import CheckResult, RiskLevel


class FraudChecker(BaseChecker):
    name = "fraud"

    def __init__(
        self,
        amount_threshold_z: float = 3.0,
        velocity_window: int = 10,
        velocity_max: int = 5,
    ) -> None:
        self._amount_threshold_z = amount_threshold_z
        self._velocity_window = velocity_window
        self._velocity_max = velocity_max
        self._history: list[float] = []
        self._user_tx_counts: defaultdict[str, int] = defaultdict(int)

    async def check(
        self, input_data: Any, output_data: Any, context: dict[str, Any] | None = None
    ) -> CheckResult:
        context = context or {}
        flags: list[str] = []
        score = 0.0

        # Amount anomaly via z-score
        amount = _extract_amount(input_data)
        if amount is not None:
            self._history.append(amount)
            if len(self._history) >= 5:
                import numpy as np
                arr = np.array(self._history)
                mean, std = arr.mean(), arr.std()
                if std > 0:
                    z = abs((amount - mean) / std)
                    if z > self._amount_threshold_z:
                        flags.append(f"amount_anomaly (z={z:.2f})")
                        score = max(score, min(z / (self._amount_threshold_z * 2), 1.0))

        # Velocity check
        user_id = _extract_user_id(input_data, context)
        if user_id:
            self._user_tx_counts[user_id] += 1
            count = self._user_tx_counts[user_id]
            if count > self._velocity_max:
                flags.append(f"velocity_exceeded (count={count})")
                score = max(score, min(count / (self._velocity_max * 3), 1.0))

        # Pattern rules
        pattern_flags = _check_patterns(input_data, context)
        flags.extend(pattern_flags)
        if pattern_flags:
            score = max(score, 0.6)

        risk = _score_to_risk(score)
        return CheckResult(
            checker_name=self.name,
            risk_level=risk,
            passed=risk <= RiskLevel.MEDIUM,
            score=score,
            details={"flags": flags, "amount": amount, "user_id": user_id},
        )


def _extract_amount(data: Any) -> float | None:
    if isinstance(data, dict):
        for key in ("amount", "total", "value", "price"):
            if key in data:
                try:
                    return float(data[key])
                except (ValueError, TypeError):
                    pass
    return None


def _extract_user_id(data: Any, context: dict[str, Any]) -> str | None:
    if isinstance(data, dict):
        for key in ("user_id", "customer_id", "account_id"):
            if key in data:
                return str(data[key])
    return context.get("user_id")


def _check_patterns(data: Any, context: dict[str, Any]) -> list[str]:
    flags = []
    if isinstance(data, dict):
        # Round amount pattern
        amount = _extract_amount(data)
        if amount and amount > 1000 and amount == int(amount):
            flags.append("round_large_amount")

        # Mismatched currency/country
        if data.get("currency") and data.get("country"):
            # Simple heuristic
            known = {"US": "USD", "GB": "GBP", "EU": "EUR", "JP": "JPY"}
            expected = known.get(data["country"])
            if expected and data["currency"] != expected:
                flags.append("currency_country_mismatch")

    return flags


def _score_to_risk(score: float) -> RiskLevel:
    if score >= 0.8:
        return RiskLevel.CRITICAL
    if score >= 0.5:
        return RiskLevel.HIGH
    if score >= 0.3:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW
