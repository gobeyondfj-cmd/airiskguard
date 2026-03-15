"""Risk dashboard — aggregate metrics, trends, and exports."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from typing import Any

from airiskguard.storage.base import StorageBackend
from airiskguard.types import RiskLevel
from airiskguard.utils.time_utils import utc_now_iso


class RiskDashboard:

    def __init__(self, storage: StorageBackend) -> None:
        self._storage = storage

    async def record_evaluation(
        self, model_id: str, risk_level: RiskLevel, score: float,
        checker_results: dict[str, Any] | None = None,
    ) -> None:
        metric = {
            "model_id": model_id,
            "risk_level": risk_level.value,
            "score": score,
            "checker_results": checker_results or {},
            "timestamp": utc_now_iso(),
        }
        await self._storage.save_metric(metric)

    async def get_summary(self, model_id: str | None = None) -> dict[str, Any]:
        metrics = await self._storage.get_metrics(model_id=model_id)
        if not metrics:
            return {
                "total_evaluations": 0, "avg_score": 0.0,
                "risk_distribution": {}, "model_id": model_id,
            }

        scores = [m["score"] for m in metrics]
        risk_dist = Counter(m["risk_level"] for m in metrics)

        return {
            "total_evaluations": len(metrics),
            "avg_score": sum(scores) / len(scores),
            "max_score": max(scores),
            "min_score": min(scores),
            "risk_distribution": dict(risk_dist),
            "model_id": model_id,
        }

    async def get_trend(
        self, model_id: str | None = None, window: int = 50
    ) -> list[dict[str, Any]]:
        metrics = await self._storage.get_metrics(model_id=model_id, limit=window)
        return [
            {
                "timestamp": m["timestamp"],
                "score": m["score"],
                "risk_level": m["risk_level"],
            }
            for m in metrics
        ]

    async def get_checker_breakdown(
        self, model_id: str | None = None
    ) -> dict[str, dict[str, Any]]:
        metrics = await self._storage.get_metrics(model_id=model_id)
        breakdown: dict[str, list[float]] = defaultdict(list)

        for m in metrics:
            for checker_name, result in m.get("checker_results", {}).items():
                if isinstance(result, dict) and "score" in result:
                    breakdown[checker_name].append(result["score"])

        return {
            name: {
                "count": len(scores),
                "avg_score": sum(scores) / len(scores) if scores else 0.0,
                "max_score": max(scores) if scores else 0.0,
            }
            for name, scores in breakdown.items()
        }

    async def export_json(self, model_id: str | None = None) -> str:
        summary = await self.get_summary(model_id)
        trend = await self.get_trend(model_id)
        breakdown = await self.get_checker_breakdown(model_id)
        return json.dumps({
            "summary": summary,
            "trend": trend,
            "checker_breakdown": breakdown,
            "exported_at": utc_now_iso(),
        }, indent=2, default=str)
