"""@risk_guard decorator for sync and async functions."""

from __future__ import annotations

import asyncio
import functools
from dataclasses import dataclass
from typing import Any, Callable

from airiskguard.exceptions import RiskBlockedError
from airiskguard.types import RiskReport


@dataclass
class RiskGuardedResult:
    result: Any
    report: RiskReport


def risk_guard(
    checks: list[str] | None = None,
    model_id: str = "default",
    block_on_risk: bool = True,
    config: Any = None,
) -> Callable:
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> RiskGuardedResult:
            from airiskguard import RiskGuard

            guard = RiskGuard(config=config)
            await guard.initialize()

            # Build input from args/kwargs
            input_data = {"args": args, "kwargs": kwargs}

            try:
                result = await func(*args, **kwargs)
            except Exception:
                raise

            report = await guard.evaluate(
                input_data=input_data,
                output_data=result,
                model_id=model_id,
                checks=checks,
            )

            if block_on_risk and report.blocked:
                raise RiskBlockedError(
                    f"Risk check blocked: {report.overall_risk.value} "
                    f"(score={report.overall_score:.2f})",
                    report=report,
                )

            return RiskGuardedResult(result=result, report=report)

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> RiskGuardedResult:
            from airiskguard import RiskGuard

            guard = RiskGuard(config=config)

            input_data = {"args": args, "kwargs": kwargs}
            result = func(*args, **kwargs)

            report = guard.evaluate_sync(
                input_data=input_data,
                output_data=result,
                model_id=model_id,
                checks=checks,
            )

            if block_on_risk and report.blocked:
                raise RiskBlockedError(
                    f"Risk check blocked: {report.overall_risk.value} "
                    f"(score={report.overall_score:.2f})",
                    report=report,
                )

            return RiskGuardedResult(result=result, report=report)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator
