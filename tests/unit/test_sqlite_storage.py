"""Tests for SQLite storage backend."""

import tempfile
import os

import pytest

from airiskguard.storage.sqlite import SQLiteStorage
from airiskguard.types import (
    AuditEntry,
    ModelInfo,
    ReviewItem,
    ReviewStatus,
    RiskLevel,
    RiskReport,
)


@pytest.fixture
async def storage():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    s = SQLiteStorage(db_path=path)
    await s.initialize()
    yield s
    await s.close()
    os.unlink(path)


async def test_model_crud(storage):
    model = ModelInfo(model_id="m1", name="test", version="1.0", owner="team")
    await storage.save_model(model)

    got = await storage.get_model("m1")
    assert got is not None
    assert got.name == "test"

    models = await storage.list_models()
    assert len(models) == 1

    assert await storage.delete_model("m1") is True
    assert await storage.get_model("m1") is None


async def test_audit_entries(storage):
    entry = AuditEntry(
        entry_id="e1", model_id="m1", action="allowed",
        risk_level=RiskLevel.LOW, score=0.1,
        input_hash="ih", output_hash="oh",
        entry_hash="eh", timestamp="2024-01-01T00:00:00",
    )
    await storage.save_audit_entry(entry)

    entries = await storage.get_audit_entries()
    assert len(entries) == 1
    assert entries[0].entry_id == "e1"

    last = await storage.get_last_audit_entry()
    assert last.entry_id == "e1"


async def test_review_items(storage):
    report = RiskReport(
        model_id="m1", overall_risk=RiskLevel.HIGH,
        overall_score=0.7, passed=False,
    )
    item = ReviewItem(
        review_id="r1", model_id="m1", risk_report=report,
    )
    await storage.save_review_item(item)

    got = await storage.get_review_item("r1")
    assert got is not None
    assert got.status == ReviewStatus.PENDING

    got.status = ReviewStatus.APPROVED
    got.notes = "OK"
    await storage.update_review_item(got)

    updated = await storage.get_review_item("r1")
    assert updated.status == ReviewStatus.APPROVED


async def test_metrics(storage):
    await storage.save_metric({"model_id": "m1", "score": 0.5})
    metrics = await storage.get_metrics(model_id="m1")
    assert len(metrics) == 1
    assert metrics[0]["score"] == 0.5
