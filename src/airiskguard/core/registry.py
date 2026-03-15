"""Model registry — register, version, and manage model lifecycles."""

from __future__ import annotations

import uuid
from typing import Any

from airiskguard.exceptions import RegistryError
from airiskguard.storage.base import StorageBackend
from airiskguard.types import ModelInfo, ModelLifecycle, RiskLevel
from airiskguard.utils.time_utils import utc_now_iso

_VALID_TRANSITIONS: dict[ModelLifecycle, set[ModelLifecycle]] = {
    ModelLifecycle.DRAFT: {ModelLifecycle.VALIDATION, ModelLifecycle.RETIRED},
    ModelLifecycle.VALIDATION: {ModelLifecycle.PRODUCTION, ModelLifecycle.DRAFT, ModelLifecycle.RETIRED},
    ModelLifecycle.PRODUCTION: {ModelLifecycle.DEPRECATED, ModelLifecycle.RETIRED},
    ModelLifecycle.DEPRECATED: {ModelLifecycle.RETIRED, ModelLifecycle.PRODUCTION},
    ModelLifecycle.RETIRED: set(),
}


class ModelRegistry:

    def __init__(self, storage: StorageBackend) -> None:
        self._storage = storage

    async def register(
        self,
        name: str,
        version: str,
        owner: str,
        risk_tier: RiskLevel = RiskLevel.MEDIUM,
        model_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ModelInfo:
        model_id = model_id or f"{name}-{version}-{uuid.uuid4().hex[:8]}"
        existing = await self._storage.get_model(model_id)
        if existing:
            raise RegistryError(f"Model already exists: {model_id}")
        model = ModelInfo(
            model_id=model_id, name=name, version=version, owner=owner,
            risk_tier=risk_tier, metadata=metadata or {},
        )
        await self._storage.save_model(model)
        return model

    async def get(self, model_id: str) -> ModelInfo:
        model = await self._storage.get_model(model_id)
        if not model:
            raise RegistryError(f"Model not found: {model_id}")
        return model

    async def list_models(self) -> list[ModelInfo]:
        return await self._storage.list_models()

    async def update_lifecycle(self, model_id: str, new_state: ModelLifecycle) -> ModelInfo:
        model = await self.get(model_id)
        valid = _VALID_TRANSITIONS.get(model.lifecycle, set())
        if new_state not in valid:
            raise RegistryError(
                f"Invalid transition: {model.lifecycle.value} -> {new_state.value}"
            )
        model.lifecycle = new_state
        model.updated_at = utc_now_iso()
        await self._storage.save_model(model)
        return model

    async def update_metadata(self, model_id: str, metadata: dict[str, Any]) -> ModelInfo:
        model = await self.get(model_id)
        model.metadata.update(metadata)
        model.updated_at = utc_now_iso()
        await self._storage.save_model(model)
        return model

    async def delete(self, model_id: str) -> bool:
        return await self._storage.delete_model(model_id)
