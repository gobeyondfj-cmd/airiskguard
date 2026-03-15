"""FastAPI integration helper."""

from __future__ import annotations

from typing import Any


def add_risk_guard(
    app: Any,
    config: Any = None,
    checks: list[str] | None = None,
) -> None:
    from airiskguard.integrations.asgi import RiskGuardASGIMiddleware

    app.add_middleware(RiskGuardASGIMiddleware, config=config, checks=checks)
