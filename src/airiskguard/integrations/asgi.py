"""ASGI middleware for airiskguard."""

from __future__ import annotations

import json
from typing import Any, Callable


class RiskGuardASGIMiddleware:

    def __init__(self, app: Any, config: Any = None, checks: list[str] | None = None) -> None:
        self.app = app
        self._config = config
        self._checks = checks
        self._guard = None

    async def _get_guard(self) -> Any:
        if self._guard is None:
            from airiskguard import RiskGuard
            self._guard = RiskGuard(config=self._config)
            await self._guard.initialize()
        return self._guard

    async def __call__(self, scope: dict, receive: Callable, send: Callable) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Capture request body
        body_parts: list[bytes] = []

        async def receive_wrapper() -> dict:
            message = await receive()
            if message.get("type") == "http.request":
                body_parts.append(message.get("body", b""))
            return message

        # Capture response
        response_body_parts: list[bytes] = []
        response_started = False
        response_headers: list[tuple[bytes, bytes]] = []
        status_code = 200

        async def send_wrapper(message: dict) -> None:
            nonlocal response_started, status_code

            if message["type"] == "http.response.start":
                response_started = True
                status_code = message.get("status", 200)
                response_headers.extend(message.get("headers", []))

                # Evaluate risk
                guard = await self._get_guard()
                request_body = b"".join(body_parts)
                try:
                    input_data = json.loads(request_body) if request_body else {}
                except (json.JSONDecodeError, UnicodeDecodeError):
                    input_data = {"raw": request_body.decode("utf-8", errors="replace")}

                report = await guard.evaluate(
                    input_data=input_data,
                    output_data=None,
                    model_id=scope.get("path", "/"),
                    checks=self._checks,
                )

                # Add risk headers
                extra_headers = [
                    (b"x-risk-score", str(report.overall_score).encode()),
                    (b"x-risk-level", report.overall_risk.value.encode()),
                ]
                message = dict(message)
                message["headers"] = list(message.get("headers", [])) + extra_headers
                await send(message)
                return

            if message["type"] == "http.response.body":
                response_body_parts.append(message.get("body", b""))

            await send(message)

        await self.app(scope, receive_wrapper, send_wrapper)
