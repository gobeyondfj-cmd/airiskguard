"""JSON file storage backend for debugging and simple persistence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from airiskguard.storage.base import StorageBackend
from airiskguard.types import (
    AuditEntry,
    CheckResult,
    ModelInfo,
    ModelLifecycle,
    ReviewItem,
    ReviewStatus,
    RiskLevel,
    RiskReport,
)
from airiskguard.utils.serialization import canonical_json


class JSONFileStorage(StorageBackend):

    def __init__(self, directory: str = ".airiskguard") -> None:
        self._dir = Path(directory)

    async def initialize(self) -> None:
        self._dir.mkdir(parents=True, exist_ok=True)
        for name in ("audit", "models", "reviews", "metrics"):
            path = self._dir / f"{name}.json"
            if not path.exists():
                path.write_text("[]" if name != "models" else "{}")

    def _read(self, name: str) -> Any:
        path = self._dir / f"{name}.json"
        if not path.exists():
            return [] if name != "models" else {}
        return json.loads(path.read_text())

    def _write(self, name: str, data: Any) -> None:
        path = self._dir / f"{name}.json"
        path.write_text(json.dumps(data, indent=2, default=str))

    # --- Audit ---
    async def save_audit_entry(self, entry: AuditEntry) -> None:
        entries = self._read("audit")
        entries.append(json.loads(canonical_json(entry)))
        self._write("audit", entries)

    async def get_audit_entries(
        self, model_id: str | None = None, limit: int = 100
    ) -> list[AuditEntry]:
        entries = self._read("audit")
        if model_id:
            entries = [e for e in entries if e["model_id"] == model_id]
        return [_dict_to_audit(e) for e in entries[-limit:]]

    async def get_last_audit_entry(self, model_id: str | None = None) -> AuditEntry | None:
        entries = await self.get_audit_entries(model_id=model_id, limit=1)
        return entries[-1] if entries else None

    # --- Models ---
    async def save_model(self, model: ModelInfo) -> None:
        models = self._read("models")
        models[model.model_id] = json.loads(canonical_json(model))
        self._write("models", models)

    async def get_model(self, model_id: str) -> ModelInfo | None:
        models = self._read("models")
        d = models.get(model_id)
        return _dict_to_model(d) if d else None

    async def list_models(self) -> list[ModelInfo]:
        models = self._read("models")
        return [_dict_to_model(m) for m in models.values()]

    async def delete_model(self, model_id: str) -> bool:
        models = self._read("models")
        if model_id in models:
            del models[model_id]
            self._write("models", models)
            return True
        return False

    # --- Reviews ---
    async def save_review_item(self, item: ReviewItem) -> None:
        reviews = self._read("reviews")
        reviews.append(json.loads(canonical_json(item)))
        self._write("reviews", reviews)

    async def get_review_item(self, review_id: str) -> ReviewItem | None:
        reviews = self._read("reviews")
        for r in reviews:
            if r["review_id"] == review_id:
                return _dict_to_review(r)
        return None

    async def list_review_items(
        self, status: str | None = None, model_id: str | None = None
    ) -> list[ReviewItem]:
        reviews = self._read("reviews")
        if status:
            reviews = [r for r in reviews if r["status"] == status]
        if model_id:
            reviews = [r for r in reviews if r["model_id"] == model_id]
        return [_dict_to_review(r) for r in reviews]

    async def update_review_item(self, item: ReviewItem) -> None:
        reviews = self._read("reviews")
        for i, r in enumerate(reviews):
            if r["review_id"] == item.review_id:
                reviews[i] = json.loads(canonical_json(item))
                break
        self._write("reviews", reviews)

    # --- Metrics ---
    async def save_metric(self, metric: dict[str, Any]) -> None:
        metrics = self._read("metrics")
        metrics.append(metric)
        self._write("metrics", metrics)

    async def get_metrics(
        self, model_id: str | None = None, limit: int = 1000
    ) -> list[dict[str, Any]]:
        metrics = self._read("metrics")
        if model_id:
            metrics = [m for m in metrics if m.get("model_id") == model_id]
        return metrics[-limit:]


def _dict_to_audit(d: dict[str, Any]) -> AuditEntry:
    return AuditEntry(
        entry_id=d["entry_id"], model_id=d["model_id"], action=d["action"],
        risk_level=RiskLevel(d["risk_level"]), score=d["score"],
        input_hash=d["input_hash"], output_hash=d["output_hash"],
        details=d.get("details", {}), previous_hash=d.get("previous_hash", ""),
        entry_hash=d.get("entry_hash", ""), timestamp=d.get("timestamp", ""),
    )


def _dict_to_model(d: dict[str, Any]) -> ModelInfo:
    return ModelInfo(
        model_id=d["model_id"], name=d["name"], version=d["version"], owner=d["owner"],
        risk_tier=RiskLevel(d.get("risk_tier", "medium")),
        lifecycle=ModelLifecycle(d.get("lifecycle", "draft")),
        metadata=d.get("metadata", {}),
        registered_at=d.get("registered_at", ""), updated_at=d.get("updated_at", ""),
    )


def _dict_to_review(d: dict[str, Any]) -> ReviewItem:
    report_data = d["risk_report"]
    checks = [
        CheckResult(
            checker_name=c["checker_name"], risk_level=RiskLevel(c["risk_level"]),
            passed=c["passed"], score=c["score"],
            details=c.get("details", {}), timestamp=c.get("timestamp", ""),
        )
        for c in report_data.get("check_results", [])
    ]
    report = RiskReport(
        model_id=report_data["model_id"],
        overall_risk=RiskLevel(report_data["overall_risk"]),
        overall_score=report_data["overall_score"], passed=report_data["passed"],
        check_results=checks, blocked=report_data.get("blocked", False),
        metadata=report_data.get("metadata", {}), timestamp=report_data.get("timestamp", ""),
    )
    return ReviewItem(
        review_id=d["review_id"], model_id=d["model_id"], risk_report=report,
        status=ReviewStatus(d["status"]), assignee=d.get("assignee", ""),
        notes=d.get("notes", ""), created_at=d.get("created_at", ""),
        updated_at=d.get("updated_at", ""),
    )
