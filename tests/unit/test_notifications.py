"""Tests for NotificationManager and channels."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from airiskguard.notifications import (
    AlertPayload,
    EmailChannel,
    NotificationManager,
    PagerDutyChannel,
    SlackChannel,
    WebhookChannel,
    _build_payload,
)
from airiskguard.types import CheckResult, RiskLevel, RiskReport


def _make_report(blocked: bool = True, risk: RiskLevel = RiskLevel.HIGH) -> RiskReport:
    return RiskReport(
        model_id="test-model",
        overall_risk=risk,
        overall_score=0.9 if blocked else 0.1,
        passed=not blocked,
        blocked=blocked,
        check_results=[
            CheckResult(checker_name="security", risk_level=risk, passed=not blocked, score=0.9)
        ],
    )


# --- AlertPayload ---

def test_build_payload():
    report = _make_report(blocked=True)
    payload = _build_payload(report)
    assert payload.model_id == "test-model"
    assert payload.blocked is True
    assert payload.overall_risk == "high"
    assert len(payload.check_results) == 1


def test_payload_to_dict():
    report = _make_report()
    payload = _build_payload(report)
    d = payload.to_dict()
    assert d["source"] == "airiskguard"
    assert d["blocked"] is True
    assert "timestamp" in d


def test_payload_summary():
    report = _make_report()
    payload = _build_payload(report)
    assert "BLOCKED" in payload.summary()
    assert "test-model" in payload.summary()


# --- NotificationManager ---

async def test_manager_no_channels():
    mgr = NotificationManager()
    report = _make_report(blocked=True)
    await mgr.notify(report)  # should not raise


async def test_manager_skips_non_blocked():
    channel = AsyncMock()
    mgr = NotificationManager([channel], on_block_only=True)
    report = _make_report(blocked=False)
    await mgr.notify(report)
    channel.send.assert_not_called()


async def test_manager_notifies_blocked():
    channel = MagicMock()
    channel.send = AsyncMock()
    mgr = NotificationManager([channel])
    report = _make_report(blocked=True)
    await mgr.notify(report)
    channel.send.assert_called_once()


async def test_manager_channel_failure_does_not_raise():
    channel = MagicMock()
    channel.send = AsyncMock(side_effect=Exception("network error"))
    mgr = NotificationManager([channel])
    report = _make_report(blocked=True)
    await mgr.notify(report)  # should not raise


async def test_manager_multiple_channels():
    ch1 = MagicMock()
    ch1.send = AsyncMock()
    ch2 = MagicMock()
    ch2.send = AsyncMock()
    mgr = NotificationManager([ch1, ch2])
    await mgr.notify(_make_report(blocked=True))
    ch1.send.assert_called_once()
    ch2.send.assert_called_once()


def test_manager_add_channel():
    mgr = NotificationManager()
    ch = MagicMock()
    mgr.add_channel(ch)
    assert len(mgr._channels) == 1


# --- WebhookChannel ---

async def test_webhook_skips_non_blocked():
    ch = WebhookChannel(url="https://example.com/hook", only_blocked=True)
    payload = _build_payload(_make_report(blocked=False))
    with patch("airiskguard.notifications._post_json") as mock_post:
        await ch.send(payload)
        mock_post.assert_not_called()


async def test_webhook_sends_blocked():
    ch = WebhookChannel(url="https://example.com/hook")
    payload = _build_payload(_make_report(blocked=True))
    with patch("airiskguard.notifications._post_json") as mock_post:
        await ch.send(payload)
        mock_post.assert_called_once()
        args = mock_post.call_args
        assert args[0][0] == "https://example.com/hook"


async def test_webhook_failure_logs_warning():
    ch = WebhookChannel(url="https://example.com/hook")
    payload = _build_payload(_make_report(blocked=True))
    with patch("airiskguard.notifications._post_json", side_effect=Exception("timeout")):
        await ch.send(payload)  # should not raise


# --- SlackChannel ---

async def test_slack_sends_blocked():
    ch = SlackChannel(webhook_url="https://hooks.slack.com/test")
    payload = _build_payload(_make_report(blocked=True))
    with patch("airiskguard.notifications._post_json") as mock_post:
        await ch.send(payload)
        mock_post.assert_called_once()
        body = mock_post.call_args[0][1]
        assert "blocks" in body


async def test_slack_skips_non_blocked():
    ch = SlackChannel(webhook_url="https://hooks.slack.com/test")
    payload = _build_payload(_make_report(blocked=False))
    with patch("airiskguard.notifications._post_json") as mock_post:
        await ch.send(payload)
        mock_post.assert_not_called()


# --- PagerDutyChannel ---

async def test_pagerduty_sends_blocked():
    ch = PagerDutyChannel(routing_key="abc123")
    payload = _build_payload(_make_report(blocked=True, risk=RiskLevel.CRITICAL))
    with patch("airiskguard.notifications._post_json") as mock_post:
        await ch.send(payload)
        mock_post.assert_called_once()
        body = mock_post.call_args[0][1]
        assert body["event_action"] == "trigger"
        assert body["payload"]["severity"] == "critical"


async def test_pagerduty_skips_non_blocked():
    ch = PagerDutyChannel(routing_key="abc123")
    payload = _build_payload(_make_report(blocked=False))
    with patch("airiskguard.notifications._post_json") as mock_post:
        await ch.send(payload)
        mock_post.assert_not_called()


# --- EmailChannel ---

async def test_email_skips_non_blocked():
    ch = EmailChannel(
        smtp_host="smtp.example.com", username="u", password="p",
        from_addr="from@example.com", to_addrs=["to@example.com"],
    )
    payload = _build_payload(_make_report(blocked=False))
    with patch("smtplib.SMTP") as mock_smtp:
        await ch.send(payload)
        mock_smtp.assert_not_called()


async def test_email_failure_does_not_raise():
    ch = EmailChannel(
        smtp_host="smtp.example.com", username="u", password="p",
        from_addr="from@example.com", to_addrs=["to@example.com"],
    )
    payload = _build_payload(_make_report(blocked=True))
    with patch("smtplib.SMTP", side_effect=Exception("connection refused")):
        await ch.send(payload)  # should not raise
