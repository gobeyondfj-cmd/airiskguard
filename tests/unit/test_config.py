"""Tests for config module."""

import tempfile
from pathlib import Path

import pytest

from airiskguard.config import RiskGuardConfig
from airiskguard.exceptions import ConfigError
from airiskguard.types import RiskLevel


def test_default_config():
    cfg = RiskGuardConfig()
    assert cfg.storage_backend == "memory"
    assert cfg.block_threshold == RiskLevel.CRITICAL
    assert "fraud" in cfg.enabled_checkers


def test_from_dict():
    cfg = RiskGuardConfig.from_dict({
        "storage_backend": "sqlite",
        "block_threshold": "high",
        "enabled_checkers": ["fraud", "security"],
    })
    assert cfg.storage_backend == "sqlite"
    assert cfg.block_threshold == RiskLevel.HIGH
    assert cfg.enabled_checkers == ["fraud", "security"]


def test_from_yaml():
    with tempfile.NamedTemporaryFile(suffix=".yaml", mode="w", delete=False) as f:
        f.write("storage_backend: sqlite\nblock_threshold: high\n")
        f.flush()
        cfg = RiskGuardConfig.from_yaml(f.name)
    assert cfg.storage_backend == "sqlite"
    assert cfg.block_threshold == RiskLevel.HIGH


def test_from_yaml_missing():
    with pytest.raises(ConfigError, match="not found"):
        RiskGuardConfig.from_yaml("/nonexistent/path.yaml")


def test_load_none():
    cfg = RiskGuardConfig.load(None)
    assert cfg.storage_backend == "memory"


def test_load_dict():
    cfg = RiskGuardConfig.load({"storage_backend": "json"})
    assert cfg.storage_backend == "json"


def test_load_unsupported():
    with pytest.raises(ConfigError, match="Unsupported"):
        RiskGuardConfig.load("config.txt")
