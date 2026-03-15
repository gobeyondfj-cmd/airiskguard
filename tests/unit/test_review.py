"""Tests for review workflow."""

import pytest

from airiskguard.core.review import ReviewWorkflow
from airiskguard.storage.memory import MemoryStorage
from airiskguard.types import ReviewStatus, RiskLevel, RiskReport


@pytest.fixture
def review():
    return ReviewWorkflow(MemoryStorage(), review_threshold=RiskLevel.HIGH)


def _make_report(risk: RiskLevel, score: float = 0.5) -> RiskReport:
    return RiskReport(model_id="m1", overall_risk=risk, overall_score=score, passed=risk <= RiskLevel.MEDIUM)


async def test_should_flag(review):
    assert review.should_flag(_make_report(RiskLevel.HIGH)) is True
    assert review.should_flag(_make_report(RiskLevel.CRITICAL)) is True
    assert review.should_flag(_make_report(RiskLevel.MEDIUM)) is False
    assert review.should_flag(_make_report(RiskLevel.LOW)) is False


async def test_flag_for_review(review):
    report = _make_report(RiskLevel.HIGH)
    item = await review.flag_for_review("m1", report)
    assert item.status == ReviewStatus.PENDING
    assert item.review_id


async def test_auto_escalate_critical(review):
    report = _make_report(RiskLevel.CRITICAL)
    item = await review.flag_for_review("m1", report)
    assert item.status == ReviewStatus.ESCALATED


async def test_approve(review):
    report = _make_report(RiskLevel.HIGH)
    item = await review.flag_for_review("m1", report)
    approved = await review.approve(item.review_id, notes="Looks good")
    assert approved.status == ReviewStatus.APPROVED
    assert approved.notes == "Looks good"


async def test_reject(review):
    report = _make_report(RiskLevel.HIGH)
    item = await review.flag_for_review("m1", report)
    rejected = await review.reject(item.review_id, notes="Too risky")
    assert rejected.status == ReviewStatus.REJECTED


async def test_escalate(review):
    report = _make_report(RiskLevel.HIGH)
    item = await review.flag_for_review("m1", report)
    escalated = await review.escalate(item.review_id)
    assert escalated.status == ReviewStatus.ESCALATED


async def test_get_queue(review):
    for i in range(3):
        await review.flag_for_review("m1", _make_report(RiskLevel.HIGH))
    queue = await review.get_queue(status="pending")
    assert len(queue) == 3


async def test_callbacks(review):
    flagged = []

    async def on_flag(item):
        flagged.append(item)

    review.on("on_flag", on_flag)
    await review.flag_for_review("m1", _make_report(RiskLevel.HIGH))
    assert len(flagged) == 1
