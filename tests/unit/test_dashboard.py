"""Tests for risk dashboard."""

import json

import pytest

from airiskguard.core.dashboard import RiskDashboard
from airiskguard.storage.memory import MemoryStorage
from airiskguard.types import RiskLevel


@pytest.fixture
def dashboard():
    return RiskDashboard(MemoryStorage())


async def test_record_and_summary(dashboard):
    await dashboard.record_evaluation("m1", RiskLevel.LOW, 0.1)
    await dashboard.record_evaluation("m1", RiskLevel.MEDIUM, 0.4)
    await dashboard.record_evaluation("m1", RiskLevel.HIGH, 0.7)

    summary = await dashboard.get_summary(model_id="m1")
    assert summary["total_evaluations"] == 3
    assert 0.3 < summary["avg_score"] < 0.5


async def test_empty_summary(dashboard):
    summary = await dashboard.get_summary()
    assert summary["total_evaluations"] == 0
    assert summary["avg_score"] == 0.0


async def test_get_trend(dashboard):
    for i in range(5):
        await dashboard.record_evaluation("m1", RiskLevel.LOW, i * 0.1)
    trend = await dashboard.get_trend(model_id="m1")
    assert len(trend) == 5


async def test_checker_breakdown(dashboard):
    await dashboard.record_evaluation(
        "m1", RiskLevel.LOW, 0.2,
        checker_results={"fraud": {"score": 0.1}, "security": {"score": 0.3}},
    )
    await dashboard.record_evaluation(
        "m1", RiskLevel.LOW, 0.3,
        checker_results={"fraud": {"score": 0.2}, "security": {"score": 0.4}},
    )
    breakdown = await dashboard.get_checker_breakdown(model_id="m1")
    assert "fraud" in breakdown
    assert breakdown["fraud"]["count"] == 2


async def test_export_json(dashboard):
    await dashboard.record_evaluation("m1", RiskLevel.LOW, 0.1)
    exported = await dashboard.export_json()
    data = json.loads(exported)
    assert "summary" in data
    assert "trend" in data
    assert "exported_at" in data
