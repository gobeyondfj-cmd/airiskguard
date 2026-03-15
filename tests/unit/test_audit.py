"""Tests for audit log."""

import pytest

from airiskguard.core.audit import AuditLog
from airiskguard.storage.memory import MemoryStorage
from airiskguard.types import RiskLevel


@pytest.fixture
def audit():
    return AuditLog(MemoryStorage())


async def test_log_decision(audit):
    entry = await audit.log_decision(
        model_id="m1", action="allowed",
        risk_level=RiskLevel.LOW, score=0.1,
        input_data={"test": True}, output_data={"result": "ok"},
    )
    assert entry.entry_id
    assert entry.entry_hash
    assert entry.previous_hash == "genesis"


async def test_hash_chain(audit):
    e1 = await audit.log_decision(
        model_id="m1", action="allowed",
        risk_level=RiskLevel.LOW, score=0.1,
        input_data="input1", output_data="output1",
    )
    e2 = await audit.log_decision(
        model_id="m1", action="allowed",
        risk_level=RiskLevel.LOW, score=0.2,
        input_data="input2", output_data="output2",
    )
    assert e2.previous_hash == e1.entry_hash


async def test_verify_chain(audit):
    for i in range(5):
        await audit.log_decision(
            model_id="m1", action="allowed",
            risk_level=RiskLevel.LOW, score=0.1,
            input_data=f"input{i}", output_data=f"output{i}",
        )
    assert await audit.verify_chain() is True


async def test_verify_empty_chain(audit):
    assert await audit.verify_chain() is True


async def test_query(audit):
    for i in range(3):
        await audit.log_decision(
            model_id=f"m{i % 2}", action="allowed",
            risk_level=RiskLevel.LOW, score=0.1,
            input_data=f"input{i}", output_data=f"output{i}",
        )
    all_entries = await audit.query()
    assert len(all_entries) == 3

    m0_entries = await audit.query(model_id="m0")
    assert len(m0_entries) == 2
