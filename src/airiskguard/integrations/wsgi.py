"""WSGI middleware for airiskguard."""

from __future__ import annotations

import asyncio
import json
from typing import Any, Callable


class RiskGuardWSGIMiddleware:

    def __init__(self, app: Any, config: Any = None, checks: list[str] | None = None) -> None:
        self.app = app
        self._config = config
        self._checks = checks
        self._guard = None

    def _get_guard(self) -> Any:
        if self._guard is None:
            from airiskguard import RiskGuard
            self._guard = RiskGuard(config=self._config)
        return self._guard

    def __call__(self, environ: dict[str, Any], start_response: Callable) -> Any:
        # Read request body
        content_length = int(environ.get("CONTENT_LENGTH", 0) or 0)
        body = environ["wsgi.input"].read(content_length) if content_length > 0 else b""

        try:
            input_data = json.loads(body) if body else {}
        except (json.JSONDecodeError, UnicodeDecodeError):
            input_data = {"raw": body.decode("utf-8", errors="replace")}

        # Evaluate risk synchronously
        guard = self._get_guard()
        report = guard.evaluate_sync(
            input_data=input_data,
            output_data=None,
            model_id=environ.get("PATH_INFO", "/"),
            checks=self._checks,
        )

        # Reset stream position for downstream app
        from io import BytesIO
        environ["wsgi.input"] = BytesIO(body)

        # Capture and modify response
        captured_status = [None]
        captured_headers = [None]

        def custom_start_response(status: str, headers: list, exc_info: Any = None) -> Any:
            headers.append(("X-Risk-Score", str(report.overall_score)))
            headers.append(("X-Risk-Level", report.overall_risk.value))
            captured_status[0] = status
            captured_headers[0] = headers
            return start_response(status, headers, exc_info)

        return self.app(environ, custom_start_response)
