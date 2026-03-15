"""Input validation utilities."""

from __future__ import annotations

from airiskguard.exceptions import ConfigError


def validate_score(score: float) -> float:
    if not 0.0 <= score <= 1.0:
        raise ValueError(f"Score must be between 0.0 and 1.0, got {score}")
    return score


def validate_non_empty(value: str, name: str) -> str:
    if not value or not value.strip():
        raise ConfigError(f"{name} must not be empty")
    return value.strip()


def validate_model_id(model_id: str) -> str:
    return validate_non_empty(model_id, "model_id")
