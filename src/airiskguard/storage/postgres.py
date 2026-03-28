"""PostgreSQL storage backend using asyncpg with connection pooling."""

from __future__ import annotations

import json
from typing import Any

try:
    import asyncpg
except ImportError as e:
    raise ImportError(
        "PostgreSQL backend requires asyncpg. Install with: pip install airiskguard[postgres]"
    ) from e

from airiskguard.storage.base import StorageBackend
from airiskguard.types import (
    AuditEntry,
    ModelInfo,
    ModelLifecycle,
    ReviewItem,
    ReviewStatus,
    RiskLevel,
    RiskReport,
)

_DDL = """
CREATE TABLE IF NOT EXISTS audit_entries (
    entry_id TEXT PRIMARY KEY,
    model_id TEXT NOT NULL,
    action TEXT NOT NULL,
    risk_level TEXT NOT NULL,
    score DOUBLE PRECISION NOT NULL,
    input_hash TEXT NOT NULL,
    output_hash TEXT NOT NULL,
    details JSONB NOT NULL DEFAULT '{}',
    previous_hash TEXT NOT NULL DEFAULT '',
    entry_hash TEXT NOT NULL DEFAULT '',
    timestamp TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_audit_model ON audit_entries(model_id);
CREATE INDEX IF NOT EXISTS idx_audit_ts ON audit_entries(timestamp);

CREATE TABLE IF NOT EXISTS models (
    model_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    version TEXT NOT NULL,
    owner TEXT NOT NULL,
    risk_tier TEXT NOT NULL DEFAULT 'medium',
    lifecycle TEXT NOT NULL DEFAULT 'draft',
    metadata JSONB NOT NULL DEFAULT '{}',
    registered_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE IF NOT EXISTS review_items (
    review_id TEXT PRIMARY KEY,
    model_id TEXT NOT NULL,
    risk_report JSONB NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    assignee TEXT NOT NULL DEFAULT '',
    notes TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_review_status ON review_items(status);
CREATE INDEX IF NOT EXISTS idx_review_model ON review_items(model_id);

CREATE TABLE IF NOT EXISTS metrics (
    id BIGSERIAL PRIMARY KEY,
    model_id TEXT,
    data JSONB NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_metrics_model ON metrics(model_id);
"""


class PostgreSQLStorage(StorageBackend):
    """Async PostgreSQL storage backend with connection pooling."""

    def __init__(
        self,
        dsn: str,
        min_size: int = 2,
        max_size: int = 10,
    ) -> None:
        self._dsn = dsn
        self._min_size = min_size
        self._max_size = max_size
        self._pool: asyncpg.Pool | None = None

    async def initialize(self) -> None:
        self._pool = await asyncpg.create_pool(
            self._dsn,
            min_size=self._min_size,
            max_size=self._max_size,
        )
        async with self._pool.acquire() as conn:
            await conn.execute(_DDL)

    async def close(self) -> None:
        if self._pool:
            await self._pool.close()
            self._pool = None

    @property
    def pool(self) -> asyncpg.Pool:
        if self._pool is None:
            raise RuntimeError("Storage not initialized. Call initialize() first.")
        return self._pool

    # --- Audit ---

    async def save_audit_entry(self, entry: AuditEntry) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO audit_entries
                    (entry_id, model_id, action, risk_level, score,
                     input_hash, output_hash, details, previous_hash, entry_hash, timestamp)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)
                ON CONFLICT (entry_id) DO NOTHING
                """,
                entry.entry_id, entry.model_id, entry.action,
                entry.risk_level.value, entry.score,
                entry.input_hash, entry.output_hash,
                json.dumps(entry.details), entry.previous_hash,
                entry.entry_hash, entry.timestamp,
            )

    def _row_to_audit(self, row: asyncpg.Record) -> AuditEntry:
        return AuditEntry(
            entry_id=row["entry_id"], model_id=row["model_id"], action=row["action"],
            risk_level=RiskLevel(row["risk_level"]), score=row["score"],
            input_hash=row["input_hash"], output_hash=row["output_hash"],
            details=dict(row["details"]) if row["details"] else {},
            previous_hash=row["previous_hash"], entry_hash=row["entry_hash"],
            timestamp=str(row["timestamp"]),
        )

    async def get_audit_entries(
        self, model_id: str | None = None, limit: int = 100
    ) -> list[AuditEntry]:
        async with self.pool.acquire() as conn:
            if model_id:
                rows = await conn.fetch(
                    "SELECT * FROM audit_entries WHERE model_id=$1 ORDER BY timestamp DESC LIMIT $2",
                    model_id, limit,
                )
            else:
                rows = await conn.fetch(
                    "SELECT * FROM audit_entries ORDER BY timestamp DESC LIMIT $1", limit
                )
        return [self._row_to_audit(r) for r in reversed(rows)]

    async def get_last_audit_entry(self, model_id: str | None = None) -> AuditEntry | None:
        async with self.pool.acquire() as conn:
            if model_id:
                row = await conn.fetchrow(
                    "SELECT * FROM audit_entries WHERE model_id=$1 ORDER BY timestamp DESC LIMIT 1",
                    model_id,
                )
            else:
                row = await conn.fetchrow(
                    "SELECT * FROM audit_entries ORDER BY timestamp DESC LIMIT 1"
                )
        return self._row_to_audit(row) if row else None

    # --- Models ---

    async def save_model(self, model: ModelInfo) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO models
                    (model_id, name, version, owner, risk_tier, lifecycle,
                     metadata, registered_at, updated_at)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)
                ON CONFLICT (model_id) DO UPDATE SET
                    name=$2, version=$3, owner=$4, risk_tier=$5, lifecycle=$6,
                    metadata=$7, updated_at=$9
                """,
                model.model_id, model.name, model.version, model.owner,
                model.risk_tier.value, model.lifecycle.value,
                json.dumps(model.metadata), model.registered_at, model.updated_at,
            )

    def _row_to_model(self, row: asyncpg.Record) -> ModelInfo:
        return ModelInfo(
            model_id=row["model_id"], name=row["name"], version=row["version"],
            owner=row["owner"], risk_tier=RiskLevel(row["risk_tier"]),
            lifecycle=ModelLifecycle(row["lifecycle"]),
            metadata=dict(row["metadata"]) if row["metadata"] else {},
            registered_at=str(row["registered_at"]), updated_at=str(row["updated_at"]),
        )

    async def get_model(self, model_id: str) -> ModelInfo | None:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM models WHERE model_id=$1", model_id)
        return self._row_to_model(row) if row else None

    async def list_models(self) -> list[ModelInfo]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM models")
        return [self._row_to_model(r) for r in rows]

    async def delete_model(self, model_id: str) -> bool:
        async with self.pool.acquire() as conn:
            result = await conn.execute("DELETE FROM models WHERE model_id=$1", model_id)
        return result.split()[-1] != "0"

    # --- Reviews ---

    async def save_review_item(self, item: ReviewItem) -> None:
        from airiskguard.utils.serialization import canonical_json
        report_json = canonical_json(item.risk_report)
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO review_items
                    (review_id, model_id, risk_report, status, assignee, notes,
                     created_at, updated_at)
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
                ON CONFLICT (review_id) DO NOTHING
                """,
                item.review_id, item.model_id, report_json,
                item.status.value, item.assignee, item.notes,
                item.created_at, item.updated_at,
            )

    def _row_to_review(self, row: asyncpg.Record) -> ReviewItem:
        from airiskguard.storage.sqlite import _dict_to_report
        report_data = dict(row["risk_report"]) if isinstance(row["risk_report"], dict) else json.loads(row["risk_report"])
        return ReviewItem(
            review_id=row["review_id"], model_id=row["model_id"],
            risk_report=_dict_to_report(report_data),
            status=ReviewStatus(row["status"]),
            assignee=row["assignee"], notes=row["notes"],
            created_at=str(row["created_at"]), updated_at=str(row["updated_at"]),
        )

    async def get_review_item(self, review_id: str) -> ReviewItem | None:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM review_items WHERE review_id=$1", review_id
            )
        return self._row_to_review(row) if row else None

    async def list_review_items(
        self, status: str | None = None, model_id: str | None = None
    ) -> list[ReviewItem]:
        query = "SELECT * FROM review_items WHERE TRUE"
        params: list[Any] = []
        if status:
            params.append(status)
            query += f" AND status=${len(params)}"
        if model_id:
            params.append(model_id)
            query += f" AND model_id=${len(params)}"
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
        return [self._row_to_review(r) for r in rows]

    async def update_review_item(self, item: ReviewItem) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE review_items
                SET status=$1, assignee=$2, notes=$3, updated_at=$4
                WHERE review_id=$5
                """,
                item.status.value, item.assignee, item.notes,
                item.updated_at, item.review_id,
            )

    # --- Metrics ---

    async def save_metric(self, metric: dict[str, Any]) -> None:
        from airiskguard.utils.time_utils import utc_now_iso
        async with self.pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO metrics (model_id, data, timestamp) VALUES ($1,$2,$3)",
                metric.get("model_id", ""), json.dumps(metric), utc_now_iso(),
            )

    async def get_metrics(
        self, model_id: str | None = None, limit: int = 1000
    ) -> list[dict[str, Any]]:
        async with self.pool.acquire() as conn:
            if model_id:
                rows = await conn.fetch(
                    "SELECT data FROM metrics WHERE model_id=$1 ORDER BY timestamp DESC LIMIT $2",
                    model_id, limit,
                )
            else:
                rows = await conn.fetch(
                    "SELECT data FROM metrics ORDER BY timestamp DESC LIMIT $1", limit
                )
        return [dict(r["data"]) if isinstance(r["data"], dict) else json.loads(r["data"]) for r in reversed(rows)]
