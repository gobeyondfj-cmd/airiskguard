"""Tests for storage backends."""

import pytest

from airiskguard.storage.memory import MemoryStorage
from airiskguard.types import (
    AuditEntry,
    ModelInfo,
    ReviewItem,
    ReviewStatus,
    RiskLevel,
    RiskReport,
)


@pytest.fixture
def storage():
    return MemoryStorage()


@pytest.fixture
def sample_model():
    return ModelInfo(
        model_id="m1", name="test-model", version="1.0", owner="team-a",
    )


@pytest.fixture
def sample_audit_entry():
    return AuditEntry(
        entry_id="e1", model_id="m1", action="allowed",
        risk_level=RiskLevel.LOW, score=0.1,
        input_hash="ihash", output_hash="ohash",
    )


@pytest.fixture
def sample_review_item():
    report = RiskReport(
        model_id="m1", overall_risk=RiskLevel.HIGH,
        overall_score=0.7, passed=False,
    )
    return ReviewItem(review_id="r1", model_id="m1", risk_report=report)


async def test_model_crud(storage, sample_model):
    await storage.save_model(sample_model)
    got = await storage.get_model("m1")
    assert got is not None
    assert got.name == "test-model"

    models = await storage.list_models()
    assert len(models) == 1

    deleted = await storage.delete_model("m1")
    assert deleted is True
    assert await storage.get_model("m1") is None


async def test_model_not_found(storage):
    assert await storage.get_model("nonexistent") is None


async def test_audit_entries(storage, sample_audit_entry):
    await storage.save_audit_entry(sample_audit_entry)
    entries = await storage.get_audit_entries()
    assert len(entries) == 1
    assert entries[0].entry_id == "e1"

    last = await storage.get_last_audit_entry()
    assert last is not None
    assert last.entry_id == "e1"


async def test_audit_entries_by_model(storage):
    e1 = AuditEntry(
        entry_id="e1", model_id="m1", action="allowed",
        risk_level=RiskLevel.LOW, score=0.1,
        input_hash="h1", output_hash="h2",
    )
    e2 = AuditEntry(
        entry_id="e2", model_id="m2", action="blocked",
        risk_level=RiskLevel.HIGH, score=0.8,
        input_hash="h3", output_hash="h4",
    )
    await storage.save_audit_entry(e1)
    await storage.save_audit_entry(e2)

    m1_entries = await storage.get_audit_entries(model_id="m1")
    assert len(m1_entries) == 1
    assert m1_entries[0].model_id == "m1"


async def test_review_items(storage, sample_review_item):
    await storage.save_review_item(sample_review_item)
    got = await storage.get_review_item("r1")
    assert got is not None
    assert got.status == ReviewStatus.PENDING

    items = await storage.list_review_items(status="pending")
    assert len(items) == 1

    sample_review_item.status = ReviewStatus.APPROVED
    await storage.update_review_item(sample_review_item)
    got2 = await storage.get_review_item("r1")
    assert got2.status == ReviewStatus.APPROVED


async def test_metrics(storage):
    await storage.save_metric({"model_id": "m1", "score": 0.5})
    await storage.save_metric({"model_id": "m2", "score": 0.8})
    all_metrics = await storage.get_metrics()
    assert len(all_metrics) == 2

    m1_metrics = await storage.get_metrics(model_id="m1")
    assert len(m1_metrics) == 1
