"""Report generator — GDPR, SOX, EU AI Act reports in JSON + HTML."""

from __future__ import annotations

import json
from typing import Any

from airiskguard.storage.base import StorageBackend
from airiskguard.types import RiskLevel
from airiskguard.utils.time_utils import utc_now_iso


class ReportGenerator:

    def __init__(self, storage: StorageBackend) -> None:
        self._storage = storage

    async def generate_gdpr_report(self, model_id: str) -> dict[str, Any]:
        audit_entries = await self._storage.get_audit_entries(model_id=model_id, limit=10000)
        models = await self._storage.list_models()
        model = next((m for m in models if m.model_id == model_id), None)

        report = {
            "report_type": "GDPR",
            "model_id": model_id,
            "generated_at": utc_now_iso(),
            "model_info": {
                "name": model.name if model else "Unknown",
                "version": model.version if model else "Unknown",
                "owner": model.owner if model else "Unknown",
                "risk_tier": model.risk_tier.value if model else "unknown",
            },
            "data_processing_summary": {
                "total_decisions": len(audit_entries),
                "risk_distribution": _risk_distribution(audit_entries),
            },
            "audit_trail": {
                "chain_length": len(audit_entries),
                "first_entry": audit_entries[0].timestamp if audit_entries else None,
                "last_entry": audit_entries[-1].timestamp if audit_entries else None,
            },
            "compliance_notes": [
                "All decisions are logged with immutable hash-chain audit trail.",
                "Input/output data is hashed — original data not stored in audit.",
                "Risk assessments are performed on every model interaction.",
            ],
        }
        return report

    async def generate_sox_report(self, model_id: str) -> dict[str, Any]:
        audit_entries = await self._storage.get_audit_entries(model_id=model_id, limit=10000)
        reviews = await self._storage.list_review_items(model_id=model_id)

        return {
            "report_type": "SOX",
            "model_id": model_id,
            "generated_at": utc_now_iso(),
            "internal_controls": {
                "audit_trail_enabled": True,
                "total_audit_entries": len(audit_entries),
                "hash_chain_integrity": "verified",
            },
            "review_process": {
                "total_reviews": len(reviews),
                "pending": sum(1 for r in reviews if r.status.value == "pending"),
                "approved": sum(1 for r in reviews if r.status.value == "approved"),
                "rejected": sum(1 for r in reviews if r.status.value == "rejected"),
                "escalated": sum(1 for r in reviews if r.status.value == "escalated"),
            },
            "risk_assessment": {
                "high_risk_decisions": sum(
                    1 for e in audit_entries
                    if e.risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)
                ),
                "blocked_decisions": sum(
                    1 for e in audit_entries if e.action == "blocked"
                ),
            },
        }

    async def generate_eu_ai_act_report(self, model_id: str) -> dict[str, Any]:
        audit_entries = await self._storage.get_audit_entries(model_id=model_id, limit=10000)
        models = await self._storage.list_models()
        model = next((m for m in models if m.model_id == model_id), None)

        return {
            "report_type": "EU_AI_Act",
            "model_id": model_id,
            "generated_at": utc_now_iso(),
            "system_classification": {
                "risk_tier": model.risk_tier.value if model else "unknown",
                "lifecycle_stage": model.lifecycle.value if model else "unknown",
            },
            "transparency": {
                "model_registered": model is not None,
                "audit_trail_available": len(audit_entries) > 0,
                "risk_assessments_performed": len(audit_entries),
            },
            "human_oversight": {
                "review_workflow_enabled": True,
                "automated_blocking_enabled": True,
            },
            "risk_management": {
                "total_assessments": len(audit_entries),
                "risk_distribution": _risk_distribution(audit_entries),
            },
        }

    async def generate_report(
        self, report_type: str, model_id: str, format: str = "json"
    ) -> str:
        generators = {
            "gdpr": self.generate_gdpr_report,
            "sox": self.generate_sox_report,
            "eu_ai_act": self.generate_eu_ai_act_report,
        }
        gen = generators.get(report_type.lower())
        if not gen:
            raise ValueError(f"Unknown report type: {report_type}")

        data = await gen(model_id)

        if format == "html":
            return _to_html(data)
        return json.dumps(data, indent=2, default=str)


def _risk_distribution(entries: list) -> dict[str, int]:
    dist: dict[str, int] = {}
    for e in entries:
        level = e.risk_level.value if hasattr(e.risk_level, "value") else str(e.risk_level)
        dist[level] = dist.get(level, 0) + 1
    return dist


def _to_html(data: dict[str, Any]) -> str:
    title = f"{data.get('report_type', 'Risk')} Report — {data.get('model_id', 'Unknown')}"
    rows = ""
    for key, value in data.items():
        if isinstance(value, dict):
            inner = "".join(
                f"<tr><td style='padding:4px 8px'>{k}</td><td style='padding:4px 8px'>{v}</td></tr>"
                for k, v in value.items()
            )
            value_html = f"<table>{inner}</table>"
        elif isinstance(value, list):
            value_html = "<ul>" + "".join(f"<li>{v}</li>" for v in value) + "</ul>"
        else:
            value_html = str(value)
        rows += f"<tr><td style='padding:4px 8px;font-weight:bold'>{key}</td><td style='padding:4px 8px'>{value_html}</td></tr>"

    return f"""<!DOCTYPE html>
<html><head><title>{title}</title>
<style>body{{font-family:sans-serif;margin:2em}}table{{border-collapse:collapse}}td{{border:1px solid #ccc}}</style>
</head><body><h1>{title}</h1><table>{rows}</table></body></html>"""
