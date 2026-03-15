"""In-memory storage backend for development and testing."""

from __future__ import annotations

from typing import Any

from airiskguard.storage.base import StorageBackend
from airiskguard.types import AuditEntry, ModelInfo, ReviewItem


class MemoryStorage(StorageBackend):

    def __init__(self) -> None:
        self._audit: list[AuditEntry] = []
        self._models: dict[str, ModelInfo] = {}
        self._reviews: dict[str, ReviewItem] = {}
        self._metrics: list[dict[str, Any]] = []

    # --- Audit ---
    async def save_audit_entry(self, entry: AuditEntry) -> None:
        self._audit.append(entry)

    async def get_audit_entries(
        self, model_id: str | None = None, limit: int = 100
    ) -> list[AuditEntry]:
        entries = self._audit
        if model_id:
            entries = [e for e in entries if e.model_id == model_id]
        return entries[-limit:]

    async def get_last_audit_entry(self, model_id: str | None = None) -> AuditEntry | None:
        entries = self._audit
        if model_id:
            entries = [e for e in entries if e.model_id == model_id]
        return entries[-1] if entries else None

    # --- Models ---
    async def save_model(self, model: ModelInfo) -> None:
        self._models[model.model_id] = model

    async def get_model(self, model_id: str) -> ModelInfo | None:
        return self._models.get(model_id)

    async def list_models(self) -> list[ModelInfo]:
        return list(self._models.values())

    async def delete_model(self, model_id: str) -> bool:
        return self._models.pop(model_id, None) is not None

    # --- Reviews ---
    async def save_review_item(self, item: ReviewItem) -> None:
        self._reviews[item.review_id] = item

    async def get_review_item(self, review_id: str) -> ReviewItem | None:
        return self._reviews.get(review_id)

    async def list_review_items(
        self, status: str | None = None, model_id: str | None = None
    ) -> list[ReviewItem]:
        items = list(self._reviews.values())
        if status:
            items = [i for i in items if i.status.value == status]
        if model_id:
            items = [i for i in items if i.model_id == model_id]
        return items

    async def update_review_item(self, item: ReviewItem) -> None:
        self._reviews[item.review_id] = item

    # --- Metrics ---
    async def save_metric(self, metric: dict[str, Any]) -> None:
        self._metrics.append(metric)

    async def get_metrics(
        self, model_id: str | None = None, limit: int = 1000
    ) -> list[dict[str, Any]]:
        metrics = self._metrics
        if model_id:
            metrics = [m for m in metrics if m.get("model_id") == model_id]
        return metrics[-limit:]
