"""Tests for Redis storage backend (mocked redis.asyncio)."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from airiskguard.types import (
    AuditEntry,
    ModelInfo,
    ReviewItem,
    ReviewStatus,
    RiskLevel,
    RiskReport,
)

_REPORT_DICT = {
    "model_id": "m1", "overall_risk": "high", "overall_score": 0.7,
    "passed": False, "check_results": [], "blocked": False,
    "metadata": {}, "timestamp": "",
}

_AUDIT_DATA = json.dumps({
    "entry_id": "e1", "model_id": "m1", "action": "allowed",
    "risk_level": "low", "score": 0.1,
    "input_hash": "ih", "output_hash": "oh",
    "details": {}, "previous_hash": "", "entry_hash": "eh",
    "timestamp": "2024-01-01T00:00:00",
})

_MODEL_DATA = json.dumps({
    "model_id": "m1", "name": "test", "version": "1.0", "owner": "team",
    "risk_tier": "medium", "lifecycle": "draft", "metadata": {},
    "registered_at": "2024-01-01T00:00:00", "updated_at": "2024-01-01T00:00:00",
})

_REVIEW_DATA = json.dumps({
    "review_id": "r1", "model_id": "m1",
    "risk_report": _REPORT_DICT,
    "status": "pending", "assignee": "", "notes": "",
    "created_at": "2024-01-01T00:00:00", "updated_at": "2024-01-01T00:00:00",
})


@pytest.fixture
def mock_redis():
    r = AsyncMock()
    pipe = AsyncMock()
    pipe.__aenter__ = AsyncMock(return_value=pipe)
    pipe.__aexit__ = AsyncMock(return_value=False)
    pipe.execute = AsyncMock(return_value=[1, 1])
    r.pipeline = MagicMock(return_value=pipe)
    r.aclose = AsyncMock()
    return r, pipe


@pytest.fixture
async def storage(mock_redis):
    r, pipe = mock_redis
    mock_cls = MagicMock()
    mock_cls.from_url = MagicMock(return_value=r)
    with patch.dict("sys.modules", {"redis": MagicMock(), "redis.asyncio": mock_cls}):
        with patch("airiskguard.storage.redis.Redis", mock_cls):
            from airiskguard.storage.redis import RedisStorage
            s = RedisStorage(url="redis://localhost:6379")
            await s.initialize()
            yield s, r, pipe


async def test_save_model(storage):
    s, r, pipe = storage
    model = ModelInfo(model_id="m1", name="test", version="1.0", owner="team")
    await s.save_model(model)
    pipe.set.assert_called()
    pipe.sadd.assert_called()


async def test_get_model(storage):
    s, r, pipe = storage
    r.get = AsyncMock(return_value=_MODEL_DATA)
    got = await s.get_model("m1")
    assert got is not None
    assert got.model_id == "m1"
    assert got.name == "test"


async def test_get_model_missing(storage):
    s, r, pipe = storage
    r.get = AsyncMock(return_value=None)
    assert await s.get_model("missing") is None


async def test_list_models(storage):
    s, r, pipe = storage
    r.smembers = AsyncMock(return_value={"m1"})
    r.mget = AsyncMock(return_value=[_MODEL_DATA])
    models = await s.list_models()
    assert len(models) == 1
    assert models[0].model_id == "m1"


async def test_delete_model(storage):
    s, r, pipe = storage
    pipe.execute = AsyncMock(return_value=[1, 1])
    result = await s.delete_model("m1")
    assert result is True

    pipe.execute = AsyncMock(return_value=[0, 0])
    result = await s.delete_model("missing")
    assert result is False


async def test_save_audit_entry(storage):
    s, r, pipe = storage
    entry = AuditEntry(
        entry_id="e1", model_id="m1", action="allowed",
        risk_level=RiskLevel.LOW, score=0.1,
        input_hash="ih", output_hash="oh",
        entry_hash="eh", timestamp="2024-01-01T00:00:00",
    )
    await s.save_audit_entry(entry)
    pipe.set.assert_called()
    pipe.zadd.assert_called()


async def test_get_audit_entries(storage):
    s, r, pipe = storage
    r.zrevrange = AsyncMock(return_value=["e1"])
    r.mget = AsyncMock(return_value=[_AUDIT_DATA])
    entries = await s.get_audit_entries()
    assert len(entries) == 1
    assert entries[0].entry_id == "e1"


async def test_get_last_audit_entry(storage):
    s, r, pipe = storage
    r.zrevrange = AsyncMock(return_value=["e1"])
    r.get = AsyncMock(return_value=_AUDIT_DATA)
    last = await s.get_last_audit_entry()
    assert last is not None
    assert last.entry_id == "e1"

    r.zrevrange = AsyncMock(return_value=[])
    assert await s.get_last_audit_entry() is None


async def test_save_and_get_review_item(storage):
    s, r, pipe = storage
    report = RiskReport(
        model_id="m1", overall_risk=RiskLevel.HIGH,
        overall_score=0.7, passed=False,
    )
    item = ReviewItem(review_id="r1", model_id="m1", risk_report=report)
    await s.save_review_item(item)
    pipe.set.assert_called()

    r.get = AsyncMock(return_value=_REVIEW_DATA)
    got = await s.get_review_item("r1")
    assert got is not None
    assert got.review_id == "r1"
    assert got.status == ReviewStatus.PENDING


async def test_update_review_item(storage):
    s, r, pipe = storage
    r.get = AsyncMock(return_value=_REVIEW_DATA)
    report = RiskReport(
        model_id="m1", overall_risk=RiskLevel.HIGH,
        overall_score=0.7, passed=False,
    )
    item = ReviewItem(
        review_id="r1", model_id="m1", risk_report=report,
        status=ReviewStatus.APPROVED, notes="OK",
    )
    await s.update_review_item(item)
    pipe.set.assert_called()


async def test_list_review_items_all(storage):
    s, r, pipe = storage
    r.smembers = AsyncMock(return_value={"r1"})
    r.mget = AsyncMock(return_value=[_REVIEW_DATA])
    items = await s.list_review_items()
    assert len(items) == 1


async def test_list_review_items_by_status(storage):
    s, r, pipe = storage
    r.smembers = AsyncMock(return_value={"r1"})
    r.mget = AsyncMock(return_value=[_REVIEW_DATA])
    items = await s.list_review_items(status="pending")
    assert len(items) == 1


async def test_list_review_items_by_model(storage):
    s, r, pipe = storage
    r.smembers = AsyncMock(return_value={"r1"})
    r.mget = AsyncMock(return_value=[_REVIEW_DATA])
    items = await s.list_review_items(model_id="m1")
    assert len(items) == 1


async def test_list_review_items_status_and_model(storage):
    s, r, pipe = storage
    r.smembers = AsyncMock(side_effect=[{"r1"}, {"r1"}])
    r.mget = AsyncMock(return_value=[_REVIEW_DATA])
    items = await s.list_review_items(status="pending", model_id="m1")
    assert len(items) == 1


async def test_save_and_get_metrics(storage):
    s, r, pipe = storage
    await s.save_metric({"model_id": "m1", "score": 0.5})
    pipe.zadd.assert_called()

    metric_json = json.dumps({"model_id": "m1", "score": 0.5})
    r.zrevrange = AsyncMock(return_value=[metric_json])
    metrics = await s.get_metrics(model_id="m1")
    assert len(metrics) == 1
    assert metrics[0]["score"] == 0.5
