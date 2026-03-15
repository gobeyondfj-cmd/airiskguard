"""airiskguard — AI Risk Governance Framework.

Provides model registry, audit logs, risk dashboards, anomaly detection,
regulatory reports, and human review workflows for AI applications.
"""

from __future__ import annotations

import asyncio
from typing import Any

from airiskguard._version import __version__
from airiskguard.checkers.base import BaseChecker
from airiskguard.checkers.registry import get_checker
from airiskguard.config import RiskGuardConfig
from airiskguard.core.anomaly import AnomalyDetector
from airiskguard.core.audit import AuditLog
from airiskguard.core.dashboard import RiskDashboard
from airiskguard.core.registry import ModelRegistry
from airiskguard.core.reports import ReportGenerator
from airiskguard.core.review import ReviewWorkflow
from airiskguard.exceptions import RiskBlockedError
from airiskguard.integrations.decorator import risk_guard
from airiskguard.storage.base import StorageBackend
from airiskguard.storage.memory import MemoryStorage
from airiskguard.storage.sqlite import SQLiteStorage
from airiskguard.types import (
    CheckResult,
    ModelInfo,
    ModelLifecycle,
    ReviewStatus,
    RiskLevel,
    RiskReport,
)

__all__ = [
    "AnomalyDetector",
    "AuditLog",
    "CheckResult",
    "ModelInfo",
    "ModelLifecycle",
    "ModelRegistry",
    "MemoryStorage",
    "ReportGenerator",
    "ReviewStatus",
    "ReviewWorkflow",
    "RiskBlockedError",
    "RiskDashboard",
    "RiskGuard",
    "RiskGuardConfig",
    "RiskLevel",
    "RiskReport",
    "SQLiteStorage",
    "StorageBackend",
    "__version__",
    "risk_guard",
]


class RiskGuard:
    """Main orchestrator wiring storage, checkers, and core features."""

    def __init__(
        self,
        config: str | dict[str, Any] | RiskGuardConfig | None = None,
        storage: StorageBackend | None = None,
    ) -> None:
        if isinstance(config, RiskGuardConfig):
            self.config = config
        else:
            self.config = RiskGuardConfig.load(config)

        self.storage = storage or self._create_storage()
        self.registry = ModelRegistry(self.storage)
        self.audit = AuditLog(self.storage)
        self.dashboard = RiskDashboard(self.storage)
        self.anomaly = AnomalyDetector(
            contamination=self.config.anomaly_contamination,
            drift_significance=self.config.drift_significance,
        )
        self.reports = ReportGenerator(self.storage)
        self.review = ReviewWorkflow(
            self.storage,
            review_threshold=self.config.review_threshold,
            auto_escalate=self.config.review_auto_escalate,
        )
        self._checkers: dict[str, BaseChecker] = {}
        self._initialized = False

    def _create_storage(self) -> StorageBackend:
        backend = self.config.storage_backend
        if backend == "sqlite":
            path = self.config.storage_path or "airiskguard.db"
            return SQLiteStorage(db_path=path)
        if backend == "json":
            path = self.config.storage_path or ".airiskguard"
            from airiskguard.storage.json_file import JSONFileStorage
            return JSONFileStorage(directory=path)
        return MemoryStorage()

    async def initialize(self) -> None:
        if self._initialized:
            return
        await self.storage.initialize()
        self._load_checkers()
        self._initialized = True

    def _load_checkers(self) -> None:
        for name in self.config.enabled_checkers:
            checker_config = self.config.checker_configs.get(name, {})
            try:
                self._checkers[name] = get_checker(name, checker_config)
            except KeyError:
                pass

    async def evaluate(
        self,
        input_data: Any,
        output_data: Any,
        model_id: str = "default",
        checks: list[str] | None = None,
        context: dict[str, Any] | None = None,
    ) -> RiskReport:
        if not self._initialized:
            await self.initialize()

        context = context or {}
        checker_names = checks or list(self._checkers.keys())
        results: list[CheckResult] = []

        for name in checker_names:
            checker = self._checkers.get(name)
            if not checker:
                continue
            result = await checker.check(input_data, output_data, context)
            results.append(result)

        # Aggregate
        if results:
            max_score = max(r.score for r in results)
            max_risk = max(r.risk_level for r in results)
        else:
            max_score = 0.0
            max_risk = RiskLevel.LOW

        blocked = (
            max_risk >= self.config.block_threshold
            or max_score >= self.config.score_block_threshold
        )
        passed = all(r.passed for r in results) if results else True

        report = RiskReport(
            model_id=model_id,
            overall_risk=max_risk,
            overall_score=max_score,
            passed=passed,
            check_results=results,
            blocked=blocked,
        )

        # Audit logging
        if self.config.audit_enabled:
            await self.audit.log_decision(
                model_id=model_id,
                action="blocked" if blocked else "allowed",
                risk_level=max_risk,
                score=max_score,
                input_data=input_data,
                output_data=output_data,
                details={"check_results": [r.checker_name for r in results]},
            )

        # Dashboard metrics
        if self.config.dashboard_enabled:
            checker_results = {
                r.checker_name: {"score": r.score, "risk_level": r.risk_level.value}
                for r in results
            }
            await self.dashboard.record_evaluation(
                model_id=model_id,
                risk_level=max_risk,
                score=max_score,
                checker_results=checker_results,
            )

        # Review workflow
        if self.config.review_enabled and self.review.should_flag(report):
            await self.review.flag_for_review(model_id, report)

        return report

    def evaluate_sync(
        self,
        input_data: Any,
        output_data: Any,
        model_id: str = "default",
        checks: list[str] | None = None,
        context: dict[str, Any] | None = None,
    ) -> RiskReport:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(
                    asyncio.run,
                    self.evaluate(input_data, output_data, model_id, checks, context),
                )
                return future.result()
        else:
            return asyncio.run(
                self.evaluate(input_data, output_data, model_id, checks, context)
            )

    async def close(self) -> None:
        await self.storage.close()
