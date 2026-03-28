"""Redis storage backend using redis[asyncio]."""

from __future__ import annotations

import json
from typing import Any

try:
    from redis.asyncio import Redis
except ImportError as e:
    raise ImportError(
        "Redis backend requires redis. Install with: pip install airiskguard[redis]"
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

# Key patterns
_AUDIT_KEY = "airiskguard:audit"          # sorted set, score = timestamp epoch
_AUDIT_MODEL_KEY = "airiskguard:audit:{model_id}"
_AUDIT_ENTRY_KEY = "airiskguard:audit:entry:{entry_id}"
_MODEL_KEY = "airiskguard:model:{model_id}"
_MODELS_SET = "airiskguard:models"
_REVIEW_KEY = "airiskguard:review:{review_id}"
_REVIEWS_SET = "airiskguard:reviews"
_REVIEW_STATUS_SET = "airiskguard:reviews:status:{status}"
_REVIEW_MODEL_SET = "airiskguard:reviews:model:{model_id}"
_METRICS_KEY = "airiskguard:metrics"
_METRICS_MODEL_KEY = "airiskguard:metrics:{model_id}"


def _ts(iso: str) -> float:
    """Convert ISO timestamp string to float epoch for sorted set score."""
    from datetime import datetime, timezone
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return dt.timestamp()
    except Exception:
        return 0.0


class RedisStorage(StorageBackend):
    """Async Redis storage backend.

    Uses sorted sets (score = epoch timestamp) for time-ordered audit/metrics,
    and hashes/strings for models and review items.
    """

    def __init__(self, url: str = "redis://localhost:6379", key_prefix: str = "") -> None:
        self._url = url
        self._prefix = key_prefix
        self._redis: Redis | None = None

    def _k(self, key: str) -> str:
        return f"{self._prefix}{key}" if self._prefix else key

    async def initialize(self) -> None:
        self._redis = Redis.from_url(self._url, decode_responses=True)

    async def close(self) -> None:
        if self._redis:
            await self._redis.aclose()
            self._redis = None

    @property
    def r(self) -> Redis:
        if self._redis is None:
            raise RuntimeError("Storage not initialized. Call initialize() first.")
        return self._redis

    # --- Audit ---

    async def save_audit_entry(self, entry: AuditEntry) -> None:
        data = json.dumps({
            "entry_id": entry.entry_id, "model_id": entry.model_id,
            "action": entry.action, "risk_level": entry.risk_level.value,
            "score": entry.score, "input_hash": entry.input_hash,
            "output_hash": entry.output_hash, "details": entry.details,
            "previous_hash": entry.previous_hash, "entry_hash": entry.entry_hash,
            "timestamp": entry.timestamp,
        })
        score = _ts(entry.timestamp)
        pipe = self.r.pipeline()
        pipe.set(self._k(_AUDIT_ENTRY_KEY.format(entry_id=entry.entry_id)), data)
        pipe.zadd(self._k(_AUDIT_KEY), {entry.entry_id: score})
        pipe.zadd(self._k(_AUDIT_MODEL_KEY.format(model_id=entry.model_id)), {entry.entry_id: score})
        await pipe.execute()

    def _deserialize_audit(self, raw: str) -> AuditEntry:
        d = json.loads(raw)
        return AuditEntry(
            entry_id=d["entry_id"], model_id=d["model_id"], action=d["action"],
            risk_level=RiskLevel(d["risk_level"]), score=d["score"],
            input_hash=d["input_hash"], output_hash=d["output_hash"],
            details=d.get("details", {}), previous_hash=d["previous_hash"],
            entry_hash=d["entry_hash"], timestamp=d["timestamp"],
        )

    async def _fetch_audit_ids(
        self, key: str, limit: int
    ) -> list[str]:
        # newest first
        return await self.r.zrevrange(self._k(key), 0, limit - 1)

    async def get_audit_entries(
        self, model_id: str | None = None, limit: int = 100
    ) -> list[AuditEntry]:
        key = _AUDIT_MODEL_KEY.format(model_id=model_id) if model_id else _AUDIT_KEY
        ids = await self._fetch_audit_ids(key, limit)
        if not ids:
            return []
        raws = await self.r.mget([self._k(_AUDIT_ENTRY_KEY.format(entry_id=i)) for i in ids])
        entries = [self._deserialize_audit(r) for r in raws if r]
        return list(reversed(entries))  # chronological order

    async def get_last_audit_entry(self, model_id: str | None = None) -> AuditEntry | None:
        key = _AUDIT_MODEL_KEY.format(model_id=model_id) if model_id else _AUDIT_KEY
        ids = await self.r.zrevrange(self._k(key), 0, 0)
        if not ids:
            return None
        raw = await self.r.get(self._k(_AUDIT_ENTRY_KEY.format(entry_id=ids[0])))
        return self._deserialize_audit(raw) if raw else None

    # --- Models ---

    async def save_model(self, model: ModelInfo) -> None:
        data = json.dumps({
            "model_id": model.model_id, "name": model.name, "version": model.version,
            "owner": model.owner, "risk_tier": model.risk_tier.value,
            "lifecycle": model.lifecycle.value, "metadata": model.metadata,
            "registered_at": model.registered_at, "updated_at": model.updated_at,
        })
        pipe = self.r.pipeline()
        pipe.set(self._k(_MODEL_KEY.format(model_id=model.model_id)), data)
        pipe.sadd(self._k(_MODELS_SET), model.model_id)
        await pipe.execute()

    def _deserialize_model(self, raw: str) -> ModelInfo:
        d = json.loads(raw)
        return ModelInfo(
            model_id=d["model_id"], name=d["name"], version=d["version"],
            owner=d["owner"], risk_tier=RiskLevel(d["risk_tier"]),
            lifecycle=ModelLifecycle(d["lifecycle"]),
            metadata=d.get("metadata", {}),
            registered_at=d["registered_at"], updated_at=d["updated_at"],
        )

    async def get_model(self, model_id: str) -> ModelInfo | None:
        raw = await self.r.get(self._k(_MODEL_KEY.format(model_id=model_id)))
        return self._deserialize_model(raw) if raw else None

    async def list_models(self) -> list[ModelInfo]:
        ids = await self.r.smembers(self._k(_MODELS_SET))
        if not ids:
            return []
        raws = await self.r.mget([self._k(_MODEL_KEY.format(model_id=i)) for i in ids])
        return [self._deserialize_model(r) for r in raws if r]

    async def delete_model(self, model_id: str) -> bool:
        pipe = self.r.pipeline()
        pipe.delete(self._k(_MODEL_KEY.format(model_id=model_id)))
        pipe.srem(self._k(_MODELS_SET), model_id)
        results = await pipe.execute()
        return results[0] > 0

    # --- Reviews ---

    async def save_review_item(self, item: ReviewItem) -> None:
        from airiskguard.utils.serialization import canonical_json
        data = json.dumps({
            "review_id": item.review_id, "model_id": item.model_id,
            "risk_report": json.loads(canonical_json(item.risk_report)),
            "status": item.status.value, "assignee": item.assignee,
            "notes": item.notes, "created_at": item.created_at,
            "updated_at": item.updated_at,
        })
        pipe = self.r.pipeline()
        pipe.set(self._k(_REVIEW_KEY.format(review_id=item.review_id)), data)
        pipe.sadd(self._k(_REVIEWS_SET), item.review_id)
        pipe.sadd(self._k(_REVIEW_STATUS_SET.format(status=item.status.value)), item.review_id)
        pipe.sadd(self._k(_REVIEW_MODEL_SET.format(model_id=item.model_id)), item.review_id)
        await pipe.execute()

    def _deserialize_review(self, raw: str) -> ReviewItem:
        from airiskguard.storage.sqlite import _dict_to_report
        d = json.loads(raw)
        return ReviewItem(
            review_id=d["review_id"], model_id=d["model_id"],
            risk_report=_dict_to_report(d["risk_report"]),
            status=ReviewStatus(d["status"]),
            assignee=d["assignee"], notes=d["notes"],
            created_at=d["created_at"], updated_at=d["updated_at"],
        )

    async def get_review_item(self, review_id: str) -> ReviewItem | None:
        raw = await self.r.get(self._k(_REVIEW_KEY.format(review_id=review_id)))
        return self._deserialize_review(raw) if raw else None

    async def list_review_items(
        self, status: str | None = None, model_id: str | None = None
    ) -> list[ReviewItem]:
        if status and model_id:
            status_ids = await self.r.smembers(self._k(_REVIEW_STATUS_SET.format(status=status)))
            model_ids = await self.r.smembers(self._k(_REVIEW_MODEL_SET.format(model_id=model_id)))
            ids = status_ids & model_ids
        elif status:
            ids = await self.r.smembers(self._k(_REVIEW_STATUS_SET.format(status=status)))
        elif model_id:
            ids = await self.r.smembers(self._k(_REVIEW_MODEL_SET.format(model_id=model_id)))
        else:
            ids = await self.r.smembers(self._k(_REVIEWS_SET))
        if not ids:
            return []
        raws = await self.r.mget([self._k(_REVIEW_KEY.format(review_id=i)) for i in ids])
        return [self._deserialize_review(r) for r in raws if r]

    async def update_review_item(self, item: ReviewItem) -> None:
        raw = await self.r.get(self._k(_REVIEW_KEY.format(review_id=item.review_id)))
        if not raw:
            return
        d = json.loads(raw)
        old_status = d["status"]
        d["status"] = item.status.value
        d["assignee"] = item.assignee
        d["notes"] = item.notes
        d["updated_at"] = item.updated_at
        pipe = self.r.pipeline()
        pipe.set(self._k(_REVIEW_KEY.format(review_id=item.review_id)), json.dumps(d))
        if old_status != item.status.value:
            pipe.srem(self._k(_REVIEW_STATUS_SET.format(status=old_status)), item.review_id)
            pipe.sadd(self._k(_REVIEW_STATUS_SET.format(status=item.status.value)), item.review_id)
        await pipe.execute()

    # --- Metrics ---

    async def save_metric(self, metric: dict[str, Any]) -> None:
        from airiskguard.utils.time_utils import utc_now_iso
        ts = utc_now_iso()
        score = _ts(ts)
        data = json.dumps(metric)
        pipe = self.r.pipeline()
        pipe.zadd(self._k(_METRICS_KEY), {data: score})
        if metric.get("model_id"):
            pipe.zadd(
                self._k(_METRICS_MODEL_KEY.format(model_id=metric["model_id"])),
                {data: score},
            )
        await pipe.execute()

    async def get_metrics(
        self, model_id: str | None = None, limit: int = 1000
    ) -> list[dict[str, Any]]:
        key = _METRICS_MODEL_KEY.format(model_id=model_id) if model_id else _METRICS_KEY
        # newest first, then reverse for chronological
        raws = await self.r.zrevrange(self._k(key), 0, limit - 1)
        return [json.loads(r) for r in reversed(raws)]
