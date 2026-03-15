"""Configuration management for airiskguard."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from airiskguard.exceptions import ConfigError
from airiskguard.types import RiskLevel


@dataclass
class RiskGuardConfig:
    # Storage
    storage_backend: str = "memory"
    storage_path: str = ""

    # Risk thresholds
    block_threshold: RiskLevel = RiskLevel.CRITICAL
    review_threshold: RiskLevel = RiskLevel.HIGH
    score_block_threshold: float = 0.9

    # Checkers
    enabled_checkers: list[str] = field(default_factory=lambda: [
        "fraud", "hallucination", "compliance", "bias", "security",
    ])
    checker_configs: dict[str, dict[str, Any]] = field(default_factory=dict)

    # Anomaly detection
    anomaly_contamination: float = 0.1
    drift_significance: float = 0.05

    # Audit
    audit_enabled: bool = True

    # Review
    review_enabled: bool = True
    review_auto_escalate: bool = True

    # Dashboard
    dashboard_enabled: bool = True

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> RiskGuardConfig:
        config = cls()
        for key, value in data.items():
            if key == "block_threshold":
                value = RiskLevel(value)
            elif key == "review_threshold":
                value = RiskLevel(value)
            if hasattr(config, key):
                setattr(config, key, value)
        return config

    @classmethod
    def from_yaml(cls, path: str | Path) -> RiskGuardConfig:
        path = Path(path)
        if not path.exists():
            raise ConfigError(f"Config file not found: {path}")
        try:
            with open(path) as f:
                data = yaml.safe_load(f) or {}
            return cls.from_dict(data)
        except yaml.YAMLError as e:
            raise ConfigError(f"Invalid YAML config: {e}") from e

    @classmethod
    def load(cls, source: str | Path | dict[str, Any] | None = None) -> RiskGuardConfig:
        if source is None:
            return cls()
        if isinstance(source, dict):
            return cls.from_dict(source)
        path = Path(source)
        if path.suffix in (".yaml", ".yml"):
            return cls.from_yaml(path)
        raise ConfigError(f"Unsupported config source: {source}")
