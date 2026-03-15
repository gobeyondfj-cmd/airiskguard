"""Tests for report generator."""

import json

import pytest

from airiskguard.core.audit import AuditLog
from airiskguard.core.registry import ModelRegistry
from airiskguard.core.reports import ReportGenerator
from airiskguard.storage.memory import MemoryStorage
from airiskguard.types import RiskLevel


@pytest.fixture
async def reports():
    storage = MemoryStorage()
    registry = ModelRegistry(storage)
    audit = AuditLog(storage)
    rg = ReportGenerator(storage)

    await registry.register(name="test", version="1.0", owner="team", model_id="m1")
    for i in range(3):
        await audit.log_decision(
            model_id="m1", action="allowed",
            risk_level=RiskLevel.LOW, score=0.1,
            input_data=f"in{i}", output_data=f"out{i}",
        )
    return rg


async def test_gdpr_report(reports):
    report = await reports.generate_gdpr_report("m1")
    assert report["report_type"] == "GDPR"
    assert report["model_id"] == "m1"
    assert report["data_processing_summary"]["total_decisions"] == 3


async def test_sox_report(reports):
    report = await reports.generate_sox_report("m1")
    assert report["report_type"] == "SOX"
    assert report["internal_controls"]["total_audit_entries"] == 3


async def test_eu_ai_act_report(reports):
    report = await reports.generate_eu_ai_act_report("m1")
    assert report["report_type"] == "EU_AI_Act"
    assert report["transparency"]["model_registered"] is True


async def test_generate_report_json(reports):
    output = await reports.generate_report("gdpr", "m1", format="json")
    data = json.loads(output)
    assert data["report_type"] == "GDPR"


async def test_generate_report_html(reports):
    output = await reports.generate_report("gdpr", "m1", format="html")
    assert "<html>" in output
    assert "GDPR" in output


async def test_unknown_report_type(reports):
    with pytest.raises(ValueError, match="Unknown report type"):
        await reports.generate_report("unknown", "m1")
