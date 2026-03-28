"""Tests for PostgreSQL storage backend (mocked asyncpg pool)."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from airiskguard.types import (
    AuditEntry,
    ModelInfo,
    ModelLifecycle,
    ReviewItem,
    ReviewStatus,
    RiskLevel,
    RiskReport,
)


def _make_audit_record(**kwargs) -> MagicMock:
    defaults = dict(
        entry_id="e1", model_id="m1", action="allowed",
        risk_level="low", score=0.1,
        input_hash="ih", output_hash="oh",
        details={}, previous_hash="", entry_hash="eh",
        timestamp="2024-01-01T00:00:00+00:00",
    )
    defaults.update(kwargs)
    r = MagicMock()
    r.__getitem__ = lambda self, k: defaults[k]
    return r


def _make_model_record(**kwargs) -> MagicMock:
    defaults = dict(
        model_id="m1", name="test", version="1.0", owner="team",
        risk_tier="medium", lifecycle="draft", metadata={},
        registered_at="2024-01-01T00:00:00+00:00",
        updated_at="2024-01-01T00:00:00+00:00",
    )
    defaults.update(kwargs)
    r = MagicMock()
    r.__getitem__ = lambda self, k: defaults[k]
    return r


def _make_review_record(**kwargs) -> MagicMock:
    report_dict = {
        "model_id": "m1", "overall_risk": "high", "overall_score": 0.7,
        "passed": False, "check_results": [], "blocked": False,
        "metadata": {}, "timestamp": "",
    }
    defaults = dict(
        review_id="r1", model_id="m1",
        risk_report=report_dict,
        status="pending", assignee="", notes="",
        created_at="2024-01-01T00:00:00+00:00",
        updated_at="2024-01-01T00:00:00+00:00",
    )
    defaults.update(kwargs)
    r = MagicMock()
    r.__getitem__ = lambda self, k: defaults[k]
    return r


@pytest.fixture
def mock_pool():
    conn = AsyncMock()
    conn.execute = AsyncMock(return_value="DELETE 1")
    conn.fetch = AsyncMock(return_value=[])
    conn.fetchrow = AsyncMock(return_value=None)

    pool = MagicMock()
    pool.acquire = MagicMock(return_value=AsyncMock(
        __aenter__=AsyncMock(return_value=conn),
        __aexit__=AsyncMock(return_value=False),
    ))
    pool.close = AsyncMock()
    return pool, conn


@pytest.fixture
async def storage(mock_pool):
    pool, conn = mock_pool
    with patch("asyncpg.create_pool", new=AsyncMock(return_value=pool)):
        from airiskguard.storage.postgres import PostgreSQLStorage
        s = PostgreSQLStorage(dsn="postgresql://localhost/test")
        await s.initialize()
        yield s, conn


async def test_save_and_get_model(storage):
    s, conn = storage
    model = ModelInfo(model_id="m1", name="test", version="1.0", owner="team")
    await s.save_model(model)
    conn.execute.assert_called()

    conn.fetchrow = AsyncMock(return_value=_make_model_record())
    got = await s.get_model("m1")
    assert got is not None
    assert got.model_id == "m1"
    assert got.name == "test"


async def test_list_models(storage):
    s, conn = storage
    conn.fetch = AsyncMock(return_value=[_make_model_record()])
    models = await s.list_models()
    assert len(models) == 1
    assert models[0].model_id == "m1"


async def test_delete_model(storage):
    s, conn = storage
    conn.execute = AsyncMock(return_value="DELETE 1")
    result = await s.delete_model("m1")
    assert result is True

    conn.execute = AsyncMock(return_value="DELETE 0")
    result = await s.delete_model("missing")
    assert result is False


async def test_save_and_get_audit_entry(storage):
    s, conn = storage
    entry = AuditEntry(
        entry_id="e1", model_id="m1", action="allowed",
        risk_level=RiskLevel.LOW, score=0.1,
        input_hash="ih", output_hash="oh",
        entry_hash="eh", timestamp="2024-01-01T00:00:00",
    )
    await s.save_audit_entry(entry)
    conn.execute.assert_called()

    conn.fetch = AsyncMock(return_value=[_make_audit_record()])
    entries = await s.get_audit_entries()
    assert len(entries) == 1
    assert entries[0].entry_id == "e1"


async def test_get_last_audit_entry(storage):
    s, conn = storage
    conn.fetchrow = AsyncMock(return_value=_make_audit_record())
    last = await s.get_last_audit_entry()
    assert last is not None
    assert last.entry_id == "e1"

    conn.fetchrow = AsyncMock(return_value=None)
    assert await s.get_last_audit_entry() is None


async def test_save_and_get_review_item(storage):
    s, conn = storage
    report = RiskReport(
        model_id="m1", overall_risk=RiskLevel.HIGH,
        overall_score=0.7, passed=False,
    )
    item = ReviewItem(review_id="r1", model_id="m1", risk_report=report)
    await s.save_review_item(item)
    conn.execute.assert_called()

    conn.fetchrow = AsyncMock(return_value=_make_review_record())
    got = await s.get_review_item("r1")
    assert got is not None
    assert got.review_id == "r1"
    assert got.status == ReviewStatus.PENDING


async def test_update_review_item(storage):
    s, conn = storage
    report = RiskReport(
        model_id="m1", overall_risk=RiskLevel.HIGH,
        overall_score=0.7, passed=False,
    )
    item = ReviewItem(
        review_id="r1", model_id="m1", risk_report=report,
        status=ReviewStatus.APPROVED, notes="OK",
    )
    await s.update_review_item(item)
    conn.execute.assert_called()


async def test_list_review_items(storage):
    s, conn = storage
    conn.fetch = AsyncMock(return_value=[_make_review_record()])
    items = await s.list_review_items()
    assert len(items) == 1

    items = await s.list_review_items(status="pending")
    assert len(items) == 1

    items = await s.list_review_items(model_id="m1")
    assert len(items) == 1

    items = await s.list_review_items(status="pending", model_id="m1")
    assert len(items) == 1


async def test_save_and_get_metrics(storage):
    s, conn = storage
    await s.save_metric({"model_id": "m1", "score": 0.5})
    conn.execute.assert_called()

    conn.fetch = AsyncMock(return_value=[
        MagicMock(**{"__getitem__": lambda self, k: {"model_id": "m1", "score": 0.5} if k == "data" else None})
    ])
    metrics = await s.get_metrics(model_id="m1")
    assert len(metrics) == 1
