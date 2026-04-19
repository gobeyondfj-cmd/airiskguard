"""Incident response notifications for airiskguard.

Sends alerts when evaluations are blocked, supporting:
- Generic webhooks (POST JSON)
- Slack incoming webhooks
- Email (SMTP)
- PagerDuty Events API v2

Usage::

    from airiskguard import RiskGuard
    from airiskguard.notifications import NotificationManager, WebhookChannel, SlackChannel

    guard = RiskGuard(
        notifications=NotificationManager([
            WebhookChannel(url="https://hooks.example.com/alert"),
            SlackChannel(webhook_url="https://hooks.slack.com/services/..."),
        ])
    )

All channels are fire-and-forget async — a notification failure never
blocks or raises in the evaluation path.
"""

from __future__ import annotations

import json
import logging
import smtplib
import ssl
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from email.mime.text import MIMEText
from typing import Any, TYPE_CHECKING
from urllib.request import Request, urlopen
from urllib.error import URLError

if TYPE_CHECKING:
    from airiskguard.types import RiskReport

logger = logging.getLogger(__name__)


@dataclass
class AlertPayload:
    """Normalised alert sent to all channels."""
    model_id: str
    overall_risk: str
    overall_score: float
    blocked: bool
    check_results: list[dict[str, Any]]
    policy_violations: list[dict[str, Any]]
    timestamp: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": "airiskguard",
            "model_id": self.model_id,
            "overall_risk": self.overall_risk,
            "overall_score": round(self.overall_score, 4),
            "blocked": self.blocked,
            "check_results": self.check_results,
            "policy_violations": self.policy_violations,
            "timestamp": self.timestamp,
        }

    def summary(self) -> str:
        return (
            f"[airiskguard] BLOCKED — model={self.model_id} "
            f"risk={self.overall_risk} score={self.overall_score:.2f} "
            f"at {self.timestamp}"
        )


def _build_payload(report: "RiskReport") -> AlertPayload:
    from airiskguard.types import RiskReport  # local import avoids circular
    return AlertPayload(
        model_id=report.model_id,
        overall_risk=report.overall_risk.value,
        overall_score=report.overall_score,
        blocked=report.blocked,
        check_results=[
            {"checker": r.checker_name, "risk": r.risk_level.value, "score": r.score, "passed": r.passed}
            for r in report.check_results
        ],
        policy_violations=report.metadata.get("policy_violations", []),
        timestamp=report.timestamp,
    )


def _post_json(url: str, data: dict[str, Any], headers: dict[str, str] | None = None) -> None:
    body = json.dumps(data).encode()
    req_headers = {"Content-Type": "application/json", **(headers or {})}
    req = Request(url, data=body, headers=req_headers, method="POST")
    with urlopen(req, timeout=10) as resp:
        resp.read()


class NotificationChannel(ABC):
    """Base class for notification channels."""

    @abstractmethod
    async def send(self, payload: AlertPayload) -> None: ...


@dataclass
class WebhookChannel(NotificationChannel):
    """POST JSON alert to any HTTP endpoint.

    Args:
        url: Webhook URL.
        headers: Extra HTTP headers (e.g. Authorization).
        only_blocked: Only fire when evaluation is blocked (default True).
    """
    url: str
    headers: dict[str, str] = field(default_factory=dict)
    only_blocked: bool = True

    async def send(self, payload: AlertPayload) -> None:
        if self.only_blocked and not payload.blocked:
            return
        try:
            _post_json(self.url, payload.to_dict(), self.headers)
        except (URLError, Exception) as exc:
            logger.warning("WebhookChannel failed: %s", exc)


@dataclass
class SlackChannel(NotificationChannel):
    """Send a Slack message via incoming webhook.

    Args:
        webhook_url: Slack incoming webhook URL.
        only_blocked: Only fire when evaluation is blocked (default True).
    """
    webhook_url: str
    only_blocked: bool = True

    async def send(self, payload: AlertPayload) -> None:
        if self.only_blocked and not payload.blocked:
            return
        risk_emoji = {"critical": ":rotating_light:", "high": ":warning:", "medium": ":yellow_circle:"}.get(
            payload.overall_risk, ":white_circle:"
        )
        checkers_text = "\n".join(
            f"  • `{r['checker']}` — {r['risk']} ({r['score']:.2f})"
            for r in payload.check_results if not r["passed"]
        ) or "  _none_"
        violations_text = "\n".join(
            f"  • `{v['policy']}` ({v['action']})"
            for v in payload.policy_violations
        ) or "  _none_"

        message = {
            "text": f"{risk_emoji} *airiskguard BLOCKED* — `{payload.model_id}`",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": (
                            f"{risk_emoji} *airiskguard blocked an evaluation*\n"
                            f"*Model:* `{payload.model_id}`\n"
                            f"*Risk:* `{payload.overall_risk}` (score: `{payload.overall_score:.2f}`)\n"
                            f"*Time:* {payload.timestamp}"
                        ),
                    },
                },
                {
                    "type": "section",
                    "fields": [
                        {"type": "mrkdwn", "text": f"*Flagged checkers:*\n{checkers_text}"},
                        {"type": "mrkdwn", "text": f"*Policy violations:*\n{violations_text}"},
                    ],
                },
            ],
        }
        try:
            _post_json(self.webhook_url, message)
        except (URLError, Exception) as exc:
            logger.warning("SlackChannel failed: %s", exc)


@dataclass
class EmailChannel(NotificationChannel):
    """Send an email alert via SMTP.

    Args:
        smtp_host: SMTP server hostname.
        smtp_port: SMTP port (default 587 for STARTTLS).
        username: SMTP username.
        password: SMTP password.
        from_addr: Sender address.
        to_addrs: List of recipient addresses.
        only_blocked: Only fire when evaluation is blocked (default True).
    """
    smtp_host: str
    username: str
    password: str
    from_addr: str
    to_addrs: list[str]
    smtp_port: int = 587
    only_blocked: bool = True

    async def send(self, payload: AlertPayload) -> None:
        if self.only_blocked and not payload.blocked:
            return
        subject = f"[airiskguard] BLOCKED — {payload.model_id} ({payload.overall_risk})"
        body = json.dumps(payload.to_dict(), indent=2)
        msg = MIMEText(body, "plain")
        msg["Subject"] = subject
        msg["From"] = self.from_addr
        msg["To"] = ", ".join(self.to_addrs)
        try:
            ctx = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls(context=ctx)
                server.login(self.username, self.password)
                server.sendmail(self.from_addr, self.to_addrs, msg.as_string())
        except Exception as exc:
            logger.warning("EmailChannel failed: %s", exc)


@dataclass
class PagerDutyChannel(NotificationChannel):
    """Trigger a PagerDuty incident via Events API v2.

    Args:
        routing_key: PagerDuty integration routing key.
        only_blocked: Only fire when evaluation is blocked (default True).
    """
    routing_key: str
    only_blocked: bool = True
    _url: str = "https://events.pagerduty.com/v2/enqueue"

    async def send(self, payload: AlertPayload) -> None:
        if self.only_blocked and not payload.blocked:
            return
        event = {
            "routing_key": self.routing_key,
            "event_action": "trigger",
            "payload": {
                "summary": payload.summary(),
                "severity": "critical" if payload.overall_risk == "critical" else "error",
                "source": "airiskguard",
                "custom_details": payload.to_dict(),
            },
        }
        try:
            _post_json(self._url, event)
        except (URLError, Exception) as exc:
            logger.warning("PagerDutyChannel failed: %s", exc)


class NotificationManager:
    """Manages a list of notification channels.

    Args:
        channels: List of :class:`NotificationChannel` instances.
        on_block_only: Global override — if True, only notify on blocked evaluations.
    """

    def __init__(
        self,
        channels: list[NotificationChannel] | None = None,
        on_block_only: bool = True,
    ) -> None:
        self._channels = channels or []
        self.on_block_only = on_block_only

    def add_channel(self, channel: NotificationChannel) -> None:
        self._channels.append(channel)

    async def notify(self, report: "RiskReport") -> None:
        """Fire all channels for this report. Never raises."""
        if not self._channels:
            return
        if self.on_block_only and not report.blocked:
            return
        payload = _build_payload(report)
        for channel in self._channels:
            try:
                await channel.send(payload)
            except Exception as exc:
                logger.warning("Notification channel %s failed: %s", type(channel).__name__, exc)
