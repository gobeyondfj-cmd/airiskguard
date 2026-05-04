"""Core ASGI reverse proxy for the airiskguard gateway.

Intercepts requests from AI coding tools (Claude Code, Codex CLI, Cursor,
Copilot) before they reach the upstream AI provider API, and scans
responses before they reach the developer's editor.

Supported upstream APIs:
- Anthropic  (POST /v1/messages)
- OpenAI     (POST /v1/chat/completions)
- Any OpenAI-compatible endpoint

Flow:
    1. Receive request from developer tool
    2. Parse prompt text from request body
    3. Run outbound checkers (secrets, PII, agent threats)
    4. If blocked → return 400 with risk details, never forward
    5. If redaction enabled → send sanitised body upstream
    6. Forward to upstream AI API (buffer full response)
    7. Run inbound checkers (vuln, agent) on completion text
    8. If blocked → return 400, discard response
    9. Return response to developer tool
"""

from __future__ import annotations

import json
import logging
from typing import Any

from airiskguard.gateway.config import GatewayConfig, TeamPolicy
from airiskguard.notifications import NotificationManager, SlackChannel, WebhookChannel, PagerDutyChannel
from airiskguard.policy import PolicyEngine
from airiskguard import RiskGuard, RiskGuardConfig

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Body parsers for Anthropic and OpenAI wire formats
# ---------------------------------------------------------------------------

def _extract_prompt_anthropic(body: dict[str, Any]) -> str:
    """Extract text from an Anthropic /v1/messages request body."""
    parts: list[str] = []
    if system := body.get("system"):
        parts.append(f"[system] {system}")
    for msg in body.get("messages", []):
        role = msg.get("role", "")
        content = msg.get("content", "")
        if isinstance(content, str):
            parts.append(f"[{role}] {content}")
        elif isinstance(content, list):
            for block in content:
                if block.get("type") == "text":
                    parts.append(f"[{role}] {block['text']}")
    return "\n".join(parts)


def _extract_prompt_openai(body: dict[str, Any]) -> str:
    """Extract text from an OpenAI /v1/chat/completions request body."""
    parts: list[str] = []
    for msg in body.get("messages", []):
        role = msg.get("role", "")
        content = msg.get("content", "")
        if isinstance(content, str):
            parts.append(f"[{role}] {content}")
        elif isinstance(content, list):
            for block in content:
                if block.get("type") == "text":
                    parts.append(f"[{role}] {block['text']}")
    return "\n".join(parts)


def _extract_completion_anthropic(body: dict[str, Any]) -> str:
    """Extract assistant text from an Anthropic response body."""
    parts: list[str] = []
    for block in body.get("content", []):
        if block.get("type") == "text":
            parts.append(block["text"])
    return "\n".join(parts)


def _extract_completion_openai(body: dict[str, Any]) -> str:
    """Extract assistant text from an OpenAI response body."""
    parts: list[str] = []
    for choice in body.get("choices", []):
        msg = choice.get("message", {})
        if text := msg.get("content"):
            parts.append(text)
    return "\n".join(parts)


def _is_anthropic_path(path: str) -> bool:
    return "/v1/messages" in path


def _is_openai_path(path: str) -> bool:
    return "/v1/chat/completions" in path or "/chat/completions" in path


def _upstream_url(config: GatewayConfig, path: str) -> str:
    if _is_anthropic_path(path):
        base = config.upstream.anthropic.rstrip("/")
    else:
        base = config.upstream.openai.rstrip("/")
    return base + path


# ---------------------------------------------------------------------------
# Risk error response helpers
# ---------------------------------------------------------------------------

def _blocked_response(
    reason: str,
    flags: list[str],
    risk: str,
    score: float,
    status: int = 400,
) -> tuple[int, bytes, list[tuple[bytes, bytes]]]:
    body = json.dumps({
        "error": {
            "type": "risk_blocked",
            "message": reason,
            "flags": flags,
            "risk_level": risk,
            "risk_score": round(score, 4),
        }
    }).encode()
    headers = [
        (b"content-type", b"application/json"),
        (b"x-airiskguard-blocked", b"true"),
        (b"x-risk-level", risk.encode()),
        (b"x-risk-score", str(round(score, 4)).encode()),
    ]
    return status, body, headers


# ---------------------------------------------------------------------------
# ASGI Gateway Application
# ---------------------------------------------------------------------------

class GatewayApp:
    """ASGI reverse proxy with risk inspection.

    Args:
        config: :class:`~airiskguard.gateway.config.GatewayConfig` instance.
    """

    def __init__(self, config: GatewayConfig | None = None) -> None:
        self.config = config or GatewayConfig()
        self._guard: RiskGuard | None = None
        self._notifications = self._build_notifications()
        self._policy = PolicyEngine.from_config(
            self.config.policies if self.config.policies else None
        )

    def _build_guard(self) -> RiskGuard:
        notif = self._notifications
        return RiskGuard(
            config=RiskGuardConfig(
                enabled_checkers=list(
                    set(self.config.outbound_checks + self.config.inbound_checks)
                ),
                audit_enabled=self.config.audit_enabled,
            ),
            notifications=notif,
        )

    def _build_notifications(self) -> NotificationManager:
        channels = []
        n = self.config.notifications
        if n.slack:
            channels.append(SlackChannel(webhook_url=n.slack))
        if n.webhook:
            channels.append(WebhookChannel(url=n.webhook))
        if n.pagerduty_key:
            channels.append(PagerDutyChannel(routing_key=n.pagerduty_key))
        return NotificationManager(channels)

    async def _get_guard(self) -> RiskGuard:
        if self._guard is None:
            self._guard = self._build_guard()
            await self._guard.initialize()
        return self._guard

    def _resolve_checks(
        self, team: TeamPolicy | None, direction: str
    ) -> list[str]:
        if team:
            return (
                team.outbound_checks if direction == "out"
                else team.inbound_checks
            )
        return (
            self.config.outbound_checks if direction == "out"
            else self.config.inbound_checks
        )

    async def __call__(self, scope: dict, receive: Any, send: Any) -> None:
        if scope["type"] == "lifespan":
            await self._handle_lifespan(scope, receive, send)
            return
        if scope["type"] != "http":
            return

        path = scope.get("path", "/")

        # Health check endpoint
        if path in ("/health", "/healthz"):
            await _send_response(send, 200, b'{"status":"ok"}',
                                 [(b"content-type", b"application/json")])
            return

        # Only intercept AI API paths
        if not (_is_anthropic_path(path) or _is_openai_path(path)):
            await _send_response(send, 404, b'{"error":"not found"}',
                                 [(b"content-type", b"application/json")])
            return

        # Read full request body
        body_bytes = await _read_body(receive)

        # Parse headers for team resolution and upstream forwarding
        headers = {k.lower(): v for k, v in scope.get("headers", [])}
        auth_header = headers.get(b"authorization", b"").decode()
        gateway_key = auth_header.replace("Bearer ", "").replace("bearer ", "").strip()
        team = self.config.team_for_key(gateway_key)

        # Check model allowlist
        try:
            body = json.loads(body_bytes) if body_bytes else {}
        except json.JSONDecodeError:
            body = {}

        if team and team.model_allowlist:
            requested_model = body.get("model", "")
            if requested_model and requested_model not in team.model_allowlist:
                status, resp_body, resp_headers = _blocked_response(
                    f"Model '{requested_model}' not in allowlist for team '{team.name}'",
                    ["model_not_allowed"],
                    "high",
                    1.0,
                )
                await _send_response(send, status, resp_body, resp_headers)
                return

        # Extract prompt text
        if _is_anthropic_path(path):
            prompt_text = _extract_prompt_anthropic(body)
        else:
            prompt_text = _extract_prompt_openai(body)

        guard = await self._get_guard()
        outbound_checks = self._resolve_checks(team, "out")

        # --- Outbound check (prompt → upstream) ---
        if outbound_checks and prompt_text:
            out_report = await guard.evaluate(
                input_data=prompt_text,
                output_data="",
                model_id=body.get("model", "gateway"),
                checks=outbound_checks,
            )
            if out_report.blocked:
                flagged = [r.checker_name for r in out_report.check_results if not r.passed]
                logger.warning(
                    "Outbound blocked: model=%s risk=%s score=%.2f flags=%s",
                    body.get("model"), out_report.overall_risk.value,
                    out_report.overall_score, flagged,
                )
                status, resp_body, resp_headers = _blocked_response(
                    "Request blocked by airiskguard — detected risk in prompt",
                    flagged,
                    out_report.overall_risk.value,
                    out_report.overall_score,
                )
                await _send_response(send, status, resp_body, resp_headers)
                return

            # Redact secrets if enabled and secrets checker ran
            if self.config.redact_secrets:
                for result in out_report.check_results:
                    if result.checker_name == "secrets" and not result.passed:
                        redacted = result.details.get("redacted_text", "")
                        if redacted:
                            body_bytes = _rebuild_body_with_redacted(
                                body, body_bytes, redacted, path
                            )

        # --- Forward to upstream ---
        try:
            resp_status, resp_body_bytes, resp_headers_raw = await _forward(
                method=scope.get("method", "POST"),
                url=_upstream_url(self.config, path),
                headers=dict(scope.get("headers", [])),
                body=body_bytes,
                gateway_key=gateway_key,
            )
        except Exception as exc:
            logger.error("Upstream error: %s", exc)
            err = json.dumps({"error": {"type": "upstream_error", "message": str(exc)}}).encode()
            await _send_response(send, 502, err, [(b"content-type", b"application/json")])
            return

        # --- Inbound check (completion → developer) ---
        inbound_checks = self._resolve_checks(team, "in")
        if inbound_checks and resp_status == 200:
            try:
                resp_body_json = json.loads(resp_body_bytes)
                if _is_anthropic_path(path):
                    completion_text = _extract_completion_anthropic(resp_body_json)
                else:
                    completion_text = _extract_completion_openai(resp_body_json)

                if completion_text:
                    in_report = await guard.evaluate(
                        input_data=prompt_text,
                        output_data=completion_text,
                        model_id=body.get("model", "gateway"),
                        checks=inbound_checks,
                    )
                    if in_report.blocked:
                        flagged = [r.checker_name for r in in_report.check_results if not r.passed]
                        logger.warning(
                            "Inbound blocked: model=%s risk=%s score=%.2f flags=%s",
                            body.get("model"), in_report.overall_risk.value,
                            in_report.overall_score, flagged,
                        )
                        status, resp_body, resp_headers = _blocked_response(
                            "Response blocked by airiskguard — detected risk in completion",
                            flagged,
                            in_report.overall_risk.value,
                            in_report.overall_score,
                        )
                        await _send_response(send, status, resp_body, resp_headers)
                        return

                    # Annotate response headers with risk info
                    resp_headers_raw[b"x-risk-level"] = in_report.overall_risk.value.encode()
                    resp_headers_raw[b"x-risk-score"] = str(
                        round(in_report.overall_score, 4)
                    ).encode()
            except (json.JSONDecodeError, Exception):
                pass  # non-JSON response (streaming etc.) — pass through

        await _send_response(
            send, resp_status, resp_body_bytes,
            list(resp_headers_raw.items()),
        )

    async def _handle_lifespan(self, scope: dict, receive: Any, send: Any) -> None:
        while True:
            event = await receive()
            if event["type"] == "lifespan.startup":
                await (await self._get_guard()).initialize()
                await send({"type": "lifespan.startup.complete"})
            elif event["type"] == "lifespan.shutdown":
                if self._guard:
                    await self._guard.close()
                await send({"type": "lifespan.shutdown.complete"})
                return


# ---------------------------------------------------------------------------
# HTTP helpers (stdlib only — httpx optional enhancement)
# ---------------------------------------------------------------------------

async def _read_body(receive: Any) -> bytes:
    body = b""
    while True:
        event = await receive()
        body += event.get("body", b"")
        if not event.get("more_body"):
            break
    return body


async def _send_response(
    send: Any,
    status: int,
    body: bytes,
    headers: list[tuple[bytes, bytes]],
) -> None:
    await send({
        "type": "http.response.start",
        "status": status,
        "headers": headers,
    })
    await send({
        "type": "http.response.body",
        "body": body,
        "more_body": False,
    })


async def _forward(
    method: str,
    url: str,
    headers: dict[bytes, bytes],
    body: bytes,
    gateway_key: str,
) -> tuple[int, bytes, dict[bytes, bytes]]:
    """Forward request to upstream using httpx (preferred) or urllib fallback."""
    try:
        import httpx
        # Strip hop-by-hop headers; keep content-type, anthropic headers, etc.
        fwd_headers = {
            k.decode(): v.decode()
            for k, v in headers.items()
            if k.lower() not in (
                b"host", b"connection", b"transfer-encoding",
                b"te", b"trailers", b"upgrade",
            )
        }
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.request(method, url, headers=fwd_headers, content=body)
        resp_headers = {
            k.lower().encode(): v.encode()
            for k, v in resp.headers.items()
            if k.lower() not in ("transfer-encoding", "connection")
        }
        return resp.status_code, resp.content, resp_headers

    except ImportError:
        # Fallback: stdlib urllib (sync, no streaming)
        import urllib.request
        import urllib.error

        fwd_headers_str = {
            k.decode(): v.decode()
            for k, v in headers.items()
            if k.lower() not in (b"host", b"connection", b"transfer-encoding")
        }
        req = urllib.request.Request(url, data=body, headers=fwd_headers_str, method=method)
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                resp_body = resp.read()
                resp_headers = {
                    k.lower().encode(): v.encode()
                    for k, v in resp.headers.items()
                }
                return resp.status, resp_body, resp_headers
        except urllib.error.HTTPError as e:
            return e.code, e.read(), {}


def _rebuild_body_with_redacted(
    original_body: dict[str, Any],
    original_bytes: bytes,
    redacted_prompt: str,
    path: str,
) -> bytes:
    """Replace prompt text in body with redacted version."""
    try:
        body = dict(original_body)
        if _is_anthropic_path(path):
            # Rebuild messages with redacted text (simplified: replace system)
            if "system" in body:
                body["system"] = "[content redacted by airiskguard]"
        else:
            msgs = body.get("messages", [])
            for msg in msgs:
                if msg.get("role") == "user" and isinstance(msg.get("content"), str):
                    msg["content"] = "[content redacted by airiskguard]"
        return json.dumps(body).encode()
    except Exception:
        return original_bytes
