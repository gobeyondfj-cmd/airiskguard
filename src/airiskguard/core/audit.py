"""Immutable hash-chain audit trail."""

from __future__ import annotations

import asyncio
import uuid
from typing import Any

from airiskguard.storage.base import StorageBackend
from airiskguard.types import AuditEntry, RiskLevel
from airiskguard.utils.hashing import hash_chain, hash_object
from airiskguard.utils.time_utils import utc_now_iso


class AuditLog:

    def __init__(self, storage: StorageBackend) -> None:
        self._storage = storage
        self._lock = asyncio.Lock()

    async def log_decision(
        self,
        model_id: str,
        action: str,
        risk_level: RiskLevel,
        score: float,
        input_data: Any,
        output_data: Any,
        details: dict[str, Any] | None = None,
    ) -> AuditEntry:
        async with self._lock:
            last = await self._storage.get_last_audit_entry()
            previous_hash = last.entry_hash if last else "genesis"

            input_hash = hash_object(input_data)
            output_hash = hash_object(output_data)

            entry = AuditEntry(
                entry_id=uuid.uuid4().hex,
                model_id=model_id,
                action=action,
                risk_level=risk_level,
                score=score,
                input_hash=input_hash,
                output_hash=output_hash,
                details=details or {},
                previous_hash=previous_hash,
                timestamp=utc_now_iso(),
            )
            entry_data = f"{entry.entry_id}:{entry.model_id}:{entry.action}:{entry.timestamp}"
            entry.entry_hash = hash_chain(entry_data, previous_hash)
            await self._storage.save_audit_entry(entry)
            return entry

    async def verify_chain(self, model_id: str | None = None) -> bool:
        entries = await self._storage.get_audit_entries(model_id=model_id, limit=10000)
        if not entries:
            return True

        for i, entry in enumerate(entries):
            if i == 0:
                expected_prev = "genesis"
            else:
                expected_prev = entries[i - 1].entry_hash

            if entry.previous_hash != expected_prev:
                return False

            entry_data = f"{entry.entry_id}:{entry.model_id}:{entry.action}:{entry.timestamp}"
            expected_hash = hash_chain(entry_data, entry.previous_hash)
            if entry.entry_hash != expected_hash:
                return False

        return True

    async def query(
        self, model_id: str | None = None, limit: int = 100
    ) -> list[AuditEntry]:
        return await self._storage.get_audit_entries(model_id=model_id, limit=limit)
