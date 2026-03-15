"""Flask integration helper."""

from __future__ import annotations

from typing import Any


def add_risk_guard(
    app: Any,
    config: Any = None,
    checks: list[str] | None = None,
) -> None:
    from airiskguard.integrations.wsgi import RiskGuardWSGIMiddleware

    app.wsgi_app = RiskGuardWSGIMiddleware(app.wsgi_app, config=config, checks=checks)
