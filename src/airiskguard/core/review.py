"""Human review workflow — queue, approve/reject/escalate, callbacks."""

from __future__ import annotations

import uuid
from typing import Any, Callable, Coroutine

from airiskguard.storage.base import StorageBackend
from airiskguard.types import ReviewItem, ReviewStatus, RiskLevel, RiskReport
from airiskguard.utils.time_utils import utc_now_iso

ReviewCallback = Callable[[ReviewItem], Coroutine[Any, Any, None]]


class ReviewWorkflow:

    def __init__(
        self,
        storage: StorageBackend,
        review_threshold: RiskLevel = RiskLevel.HIGH,
        auto_escalate: bool = True,
    ) -> None:
        self._storage = storage
        self._review_threshold = review_threshold
        self._auto_escalate = auto_escalate
        self._callbacks: dict[str, list[ReviewCallback]] = {
            "on_flag": [],
            "on_approve": [],
            "on_reject": [],
            "on_escalate": [],
        }

    def on(self, event: str, callback: ReviewCallback) -> None:
        if event in self._callbacks:
            self._callbacks[event].append(callback)

    async def _fire(self, event: str, item: ReviewItem) -> None:
        for cb in self._callbacks.get(event, []):
            await cb(item)

    def should_flag(self, report: RiskReport) -> bool:
        return report.overall_risk >= self._review_threshold

    async def flag_for_review(
        self, model_id: str, report: RiskReport, assignee: str = ""
    ) -> ReviewItem:
        item = ReviewItem(
            review_id=uuid.uuid4().hex,
            model_id=model_id,
            risk_report=report,
            assignee=assignee,
        )

        if self._auto_escalate and report.overall_risk >= RiskLevel.CRITICAL:
            item.status = ReviewStatus.ESCALATED

        await self._storage.save_review_item(item)
        await self._fire("on_flag", item)

        if item.status == ReviewStatus.ESCALATED:
            await self._fire("on_escalate", item)

        return item

    async def approve(self, review_id: str, notes: str = "") -> ReviewItem:
        item = await self._get(review_id)
        item.status = ReviewStatus.APPROVED
        item.notes = notes
        item.updated_at = utc_now_iso()
        await self._storage.update_review_item(item)
        await self._fire("on_approve", item)
        return item

    async def reject(self, review_id: str, notes: str = "") -> ReviewItem:
        item = await self._get(review_id)
        item.status = ReviewStatus.REJECTED
        item.notes = notes
        item.updated_at = utc_now_iso()
        await self._storage.update_review_item(item)
        await self._fire("on_reject", item)
        return item

    async def escalate(self, review_id: str, notes: str = "") -> ReviewItem:
        item = await self._get(review_id)
        item.status = ReviewStatus.ESCALATED
        item.notes = notes
        item.updated_at = utc_now_iso()
        await self._storage.update_review_item(item)
        await self._fire("on_escalate", item)
        return item

    async def get_queue(
        self, status: str | None = "pending", model_id: str | None = None
    ) -> list[ReviewItem]:
        return await self._storage.list_review_items(status=status, model_id=model_id)

    async def _get(self, review_id: str) -> ReviewItem:
        item = await self._storage.get_review_item(review_id)
        if not item:
            raise ValueError(f"Review item not found: {review_id}")
        return item
