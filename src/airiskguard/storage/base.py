"""Abstract base class for storage backends."""

from __future__ import annotations

import abc
from typing import Any

from airiskguard.types import AuditEntry, ModelInfo, ReviewItem


class StorageBackend(abc.ABC):
    """Abstract storage backend."""

    # --- Audit entries ---
    @abc.abstractmethod
    async def save_audit_entry(self, entry: AuditEntry) -> None: ...

    @abc.abstractmethod
    async def get_audit_entries(
        self, model_id: str | None = None, limit: int = 100
    ) -> list[AuditEntry]: ...

    @abc.abstractmethod
    async def get_last_audit_entry(self, model_id: str | None = None) -> AuditEntry | None: ...

    # --- Models ---
    @abc.abstractmethod
    async def save_model(self, model: ModelInfo) -> None: ...

    @abc.abstractmethod
    async def get_model(self, model_id: str) -> ModelInfo | None: ...

    @abc.abstractmethod
    async def list_models(self) -> list[ModelInfo]: ...

    @abc.abstractmethod
    async def delete_model(self, model_id: str) -> bool: ...

    # --- Review items ---
    @abc.abstractmethod
    async def save_review_item(self, item: ReviewItem) -> None: ...

    @abc.abstractmethod
    async def get_review_item(self, review_id: str) -> ReviewItem | None: ...

    @abc.abstractmethod
    async def list_review_items(
        self, status: str | None = None, model_id: str | None = None
    ) -> list[ReviewItem]: ...

    @abc.abstractmethod
    async def update_review_item(self, item: ReviewItem) -> None: ...

    # --- Metrics ---
    @abc.abstractmethod
    async def save_metric(self, metric: dict[str, Any]) -> None: ...

    @abc.abstractmethod
    async def get_metrics(
        self, model_id: str | None = None, limit: int = 1000
    ) -> list[dict[str, Any]]: ...

    # --- Lifecycle ---
    async def initialize(self) -> None:
        """Initialize the storage backend (create tables, etc.)."""

    async def close(self) -> None:
        """Close the storage backend."""
