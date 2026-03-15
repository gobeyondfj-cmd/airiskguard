"""Shared fixtures for airiskguard tests."""

import pytest

from airiskguard import RiskGuard, RiskGuardConfig
from airiskguard.storage.memory import MemoryStorage


@pytest.fixture
def memory_storage():
    return MemoryStorage()


@pytest.fixture
def config():
    return RiskGuardConfig()


@pytest.fixture
async def guard(memory_storage):
    g = RiskGuard(storage=memory_storage)
    await g.initialize()
    yield g
    await g.close()
