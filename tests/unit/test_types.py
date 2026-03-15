"""Tests for types module."""

from airiskguard.types import (
    AuditEntry,
    CheckResult,
    ModelInfo,
    ModelLifecycle,
    ReviewItem,
    ReviewStatus,
    RiskLevel,
    RiskReport,
)


def test_risk_level_ordering():
    assert RiskLevel.LOW < RiskLevel.MEDIUM
    assert RiskLevel.MEDIUM < RiskLevel.HIGH
    assert RiskLevel.HIGH < RiskLevel.CRITICAL
    assert RiskLevel.CRITICAL >= RiskLevel.HIGH


def test_risk_level_values():
    assert RiskLevel.LOW.value == "low"
    assert RiskLevel.CRITICAL.value == "critical"


def test_model_lifecycle():
    assert ModelLifecycle.DRAFT.value == "draft"
    assert ModelLifecycle.PRODUCTION.value == "production"


def test_review_status():
    assert ReviewStatus.PENDING.value == "pending"
    assert ReviewStatus.ESCALATED.value == "escalated"


def test_check_result_defaults():
    r = CheckResult(checker_name="test", risk_level=RiskLevel.LOW, passed=True, score=0.1)
    assert r.checker_name == "test"
    assert r.timestamp  # auto-set


def test_risk_report_defaults():
    r = RiskReport(model_id="m1", overall_risk=RiskLevel.LOW, overall_score=0.1, passed=True)
    assert r.blocked is False
    assert r.check_results == []
    assert r.timestamp


def test_model_info_defaults():
    m = ModelInfo(model_id="m1", name="test", version="1.0", owner="owner")
    assert m.lifecycle == ModelLifecycle.DRAFT
    assert m.risk_tier == RiskLevel.MEDIUM
    assert m.registered_at
    assert m.updated_at


def test_audit_entry_defaults():
    e = AuditEntry(
        entry_id="e1", model_id="m1", action="test",
        risk_level=RiskLevel.LOW, score=0.0,
        input_hash="abc", output_hash="def",
    )
    assert e.timestamp
    assert e.previous_hash == ""


def test_review_item_defaults():
    report = RiskReport(model_id="m1", overall_risk=RiskLevel.HIGH, overall_score=0.7, passed=False)
    item = ReviewItem(review_id="r1", model_id="m1", risk_report=report)
    assert item.status == ReviewStatus.PENDING
    assert item.created_at
