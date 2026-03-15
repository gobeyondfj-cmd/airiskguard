"""Tests for model registry."""

import pytest

from airiskguard.core.registry import ModelRegistry
from airiskguard.exceptions import RegistryError
from airiskguard.storage.memory import MemoryStorage
from airiskguard.types import ModelLifecycle, RiskLevel


@pytest.fixture
def registry():
    return ModelRegistry(MemoryStorage())


async def test_register_model(registry):
    model = await registry.register(
        name="test", version="1.0", owner="team",
        model_id="test-1",
    )
    assert model.model_id == "test-1"
    assert model.lifecycle == ModelLifecycle.DRAFT


async def test_register_duplicate(registry):
    await registry.register(name="test", version="1.0", owner="team", model_id="test-1")
    with pytest.raises(RegistryError, match="already exists"):
        await registry.register(name="test", version="1.0", owner="team", model_id="test-1")


async def test_get_model(registry):
    await registry.register(name="test", version="1.0", owner="team", model_id="test-1")
    model = await registry.get("test-1")
    assert model.name == "test"


async def test_get_not_found(registry):
    with pytest.raises(RegistryError, match="not found"):
        await registry.get("nonexistent")


async def test_lifecycle_transitions(registry):
    await registry.register(name="test", version="1.0", owner="team", model_id="test-1")

    # DRAFT -> VALIDATION
    model = await registry.update_lifecycle("test-1", ModelLifecycle.VALIDATION)
    assert model.lifecycle == ModelLifecycle.VALIDATION

    # VALIDATION -> PRODUCTION
    model = await registry.update_lifecycle("test-1", ModelLifecycle.PRODUCTION)
    assert model.lifecycle == ModelLifecycle.PRODUCTION

    # PRODUCTION -> DEPRECATED
    model = await registry.update_lifecycle("test-1", ModelLifecycle.DEPRECATED)
    assert model.lifecycle == ModelLifecycle.DEPRECATED


async def test_invalid_lifecycle_transition(registry):
    await registry.register(name="test", version="1.0", owner="team", model_id="test-1")
    with pytest.raises(RegistryError, match="Invalid transition"):
        await registry.update_lifecycle("test-1", ModelLifecycle.DEPRECATED)


async def test_list_models(registry):
    await registry.register(name="a", version="1.0", owner="team", model_id="a-1")
    await registry.register(name="b", version="1.0", owner="team", model_id="b-1")
    models = await registry.list_models()
    assert len(models) == 2


async def test_delete_model(registry):
    await registry.register(name="test", version="1.0", owner="team", model_id="test-1")
    assert await registry.delete("test-1") is True
    assert await registry.delete("test-1") is False
