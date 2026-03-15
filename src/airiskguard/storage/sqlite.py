"""SQLite storage backend using aiosqlite."""

from __future__ import annotations

import json
from typing import Any

import aiosqlite

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


class SQLiteStorage(StorageBackend):

    def __init__(self, db_path: str = "airiskguard.db") -> None:
        self._db_path = db_path
        self._db: aiosqlite.Connection | None = None

    async def initialize(self) -> None:
        self._db = await aiosqlite.connect(self._db_path)
        await self._db.executescript("""
            CREATE TABLE IF NOT EXISTS audit_entries (
                entry_id TEXT PRIMARY KEY,
                model_id TEXT NOT NULL,
                action TEXT NOT NULL,
                risk_level TEXT NOT NULL,
                score REAL NOT NULL,
                input_hash TEXT NOT NULL,
                output_hash TEXT NOT NULL,
                details TEXT NOT NULL DEFAULT '{}',
                previous_hash TEXT NOT NULL DEFAULT '',
                entry_hash TEXT NOT NULL DEFAULT '',
                timestamp TEXT NOT NULL
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
                metadata TEXT NOT NULL DEFAULT '{}',
                registered_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS review_items (
                review_id TEXT PRIMARY KEY,
                model_id TEXT NOT NULL,
                risk_report TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                assignee TEXT NOT NULL DEFAULT '',
                notes TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_review_status ON review_items(status);
            CREATE INDEX IF NOT EXISTS idx_review_model ON review_items(model_id);

            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_id TEXT,
                data TEXT NOT NULL,
                timestamp TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_metrics_model ON metrics(model_id);
        """)
        await self._db.commit()

    async def close(self) -> None:
        if self._db:
            await self._db.close()
            self._db = None

    @property
    def db(self) -> aiosqlite.Connection:
        if self._db is None:
            raise RuntimeError("Storage not initialized. Call initialize() first.")
        return self._db

    # --- Audit ---
    async def save_audit_entry(self, entry: AuditEntry) -> None:
        await self.db.execute(
            "INSERT INTO audit_entries VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (
                entry.entry_id, entry.model_id, entry.action,
                entry.risk_level.value, entry.score,
                entry.input_hash, entry.output_hash,
                json.dumps(entry.details), entry.previous_hash,
                entry.entry_hash, entry.timestamp,
            ),
        )
        await self.db.commit()

    def _row_to_audit(self, row: aiosqlite.Row) -> AuditEntry:
        return AuditEntry(
            entry_id=row[0], model_id=row[1], action=row[2],
            risk_level=RiskLevel(row[3]), score=row[4],
            input_hash=row[5], output_hash=row[6],
            details=json.loads(row[7]), previous_hash=row[8],
            entry_hash=row[9], timestamp=row[10],
        )

    async def get_audit_entries(
        self, model_id: str | None = None, limit: int = 100
    ) -> list[AuditEntry]:
        if model_id:
            cursor = await self.db.execute(
                "SELECT * FROM audit_entries WHERE model_id=? ORDER BY timestamp DESC LIMIT ?",
                (model_id, limit),
            )
        else:
            cursor = await self.db.execute(
                "SELECT * FROM audit_entries ORDER BY timestamp DESC LIMIT ?", (limit,)
            )
        rows = await cursor.fetchall()
        return [self._row_to_audit(r) for r in reversed(rows)]

    async def get_last_audit_entry(self, model_id: str | None = None) -> AuditEntry | None:
        if model_id:
            cursor = await self.db.execute(
                "SELECT * FROM audit_entries WHERE model_id=? ORDER BY timestamp DESC LIMIT 1",
                (model_id,),
            )
        else:
            cursor = await self.db.execute(
                "SELECT * FROM audit_entries ORDER BY timestamp DESC LIMIT 1"
            )
        row = await cursor.fetchone()
        return self._row_to_audit(row) if row else None

    # --- Models ---
    async def save_model(self, model: ModelInfo) -> None:
        await self.db.execute(
            "INSERT OR REPLACE INTO models VALUES (?,?,?,?,?,?,?,?,?)",
            (
                model.model_id, model.name, model.version, model.owner,
                model.risk_tier.value, model.lifecycle.value,
                json.dumps(model.metadata), model.registered_at, model.updated_at,
            ),
        )
        await self.db.commit()

    async def get_model(self, model_id: str) -> ModelInfo | None:
        cursor = await self.db.execute("SELECT * FROM models WHERE model_id=?", (model_id,))
        row = await cursor.fetchone()
        if not row:
            return None
        return ModelInfo(
            model_id=row[0], name=row[1], version=row[2], owner=row[3],
            risk_tier=RiskLevel(row[4]), lifecycle=ModelLifecycle(row[5]),
            metadata=json.loads(row[6]), registered_at=row[7], updated_at=row[8],
        )

    async def list_models(self) -> list[ModelInfo]:
        cursor = await self.db.execute("SELECT * FROM models")
        rows = await cursor.fetchall()
        return [
            ModelInfo(
                model_id=r[0], name=r[1], version=r[2], owner=r[3],
                risk_tier=RiskLevel(r[4]), lifecycle=ModelLifecycle(r[5]),
                metadata=json.loads(r[6]), registered_at=r[7], updated_at=r[8],
            )
            for r in rows
        ]

    async def delete_model(self, model_id: str) -> bool:
        cursor = await self.db.execute("DELETE FROM models WHERE model_id=?", (model_id,))
        await self.db.commit()
        return cursor.rowcount > 0

    # --- Reviews ---
    async def save_review_item(self, item: ReviewItem) -> None:
        await self.db.execute(
            "INSERT INTO review_items VALUES (?,?,?,?,?,?,?,?)",
            (
                item.review_id, item.model_id,
                json.dumps(_report_to_dict(item.risk_report)),
                item.status.value, item.assignee, item.notes,
                item.created_at, item.updated_at,
            ),
        )
        await self.db.commit()

    async def get_review_item(self, review_id: str) -> ReviewItem | None:
        cursor = await self.db.execute(
            "SELECT * FROM review_items WHERE review_id=?", (review_id,)
        )
        row = await cursor.fetchone()
        return self._row_to_review(row) if row else None

    async def list_review_items(
        self, status: str | None = None, model_id: str | None = None
    ) -> list[ReviewItem]:
        query = "SELECT * FROM review_items WHERE 1=1"
        params: list[str] = []
        if status:
            query += " AND status=?"
            params.append(status)
        if model_id:
            query += " AND model_id=?"
            params.append(model_id)
        cursor = await self.db.execute(query, params)
        return [self._row_to_review(r) for r in await cursor.fetchall()]

    async def update_review_item(self, item: ReviewItem) -> None:
        await self.db.execute(
            "UPDATE review_items SET status=?, assignee=?, notes=?, updated_at=? WHERE review_id=?",
            (item.status.value, item.assignee, item.notes, item.updated_at, item.review_id),
        )
        await self.db.commit()

    def _row_to_review(self, row: aiosqlite.Row) -> ReviewItem:
        report_data = json.loads(row[2])
        report = _dict_to_report(report_data)
        return ReviewItem(
            review_id=row[0], model_id=row[1], risk_report=report,
            status=ReviewStatus(row[3]), assignee=row[4], notes=row[5],
            created_at=row[6], updated_at=row[7],
        )

    # --- Metrics ---
    async def save_metric(self, metric: dict[str, Any]) -> None:
        from airiskguard.utils.time_utils import utc_now_iso
        await self.db.execute(
            "INSERT INTO metrics (model_id, data, timestamp) VALUES (?,?,?)",
            (metric.get("model_id", ""), json.dumps(metric), utc_now_iso()),
        )
        await self.db.commit()

    async def get_metrics(
        self, model_id: str | None = None, limit: int = 1000
    ) -> list[dict[str, Any]]:
        if model_id:
            cursor = await self.db.execute(
                "SELECT data FROM metrics WHERE model_id=? ORDER BY timestamp DESC LIMIT ?",
                (model_id, limit),
            )
        else:
            cursor = await self.db.execute(
                "SELECT data FROM metrics ORDER BY timestamp DESC LIMIT ?", (limit,)
            )
        rows = await cursor.fetchall()
        return [json.loads(r[0]) for r in reversed(rows)]


def _report_to_dict(report: RiskReport) -> dict[str, Any]:
    from airiskguard.utils.serialization import canonical_json
    return json.loads(canonical_json(report))


def _dict_to_report(d: dict[str, Any]) -> RiskReport:
    from airiskguard.types import CheckResult
    checks = [
        CheckResult(
            checker_name=c["checker_name"], risk_level=RiskLevel(c["risk_level"]),
            passed=c["passed"], score=c["score"],
            details=c.get("details", {}), timestamp=c.get("timestamp", ""),
        )
        for c in d.get("check_results", [])
    ]
    return RiskReport(
        model_id=d["model_id"], overall_risk=RiskLevel(d["overall_risk"]),
        overall_score=d["overall_score"], passed=d["passed"],
        check_results=checks, blocked=d.get("blocked", False),
        metadata=d.get("metadata", {}), timestamp=d.get("timestamp", ""),
    )
