"""Gateway configuration loader."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class UpstreamConfig:
    anthropic: str = "https://api.anthropic.com"
    openai: str = "https://api.openai.com"


@dataclass
class TLSConfig:
    cert: str = ""
    key: str = ""

    @property
    def enabled(self) -> bool:
        return bool(self.cert and self.key)


@dataclass
class TeamPolicy:
    """Per-team risk and model restrictions."""
    name: str
    outbound_checks: list[str] = field(default_factory=lambda: ["secrets", "pii"])
    inbound_checks: list[str] = field(default_factory=lambda: ["vuln", "agent"])
    model_allowlist: list[str] = field(default_factory=list)
    api_keys: list[str] = field(default_factory=list)  # gateway API keys for this team


@dataclass
class NotificationsConfig:
    slack: str = ""
    webhook: str = ""
    pagerduty_key: str = ""


@dataclass
class GatewayConfig:
    """Full gateway configuration."""
    upstream: UpstreamConfig = field(default_factory=UpstreamConfig)
    tls: TLSConfig = field(default_factory=TLSConfig)
    outbound_checks: list[str] = field(
        default_factory=lambda: ["secrets", "compliance", "agent"]
    )
    inbound_checks: list[str] = field(
        default_factory=lambda: ["vuln", "agent"]
    )
    policies: list[dict[str, Any]] = field(default_factory=list)
    teams: list[TeamPolicy] = field(default_factory=list)
    notifications: NotificationsConfig = field(default_factory=NotificationsConfig)
    audit_enabled: bool = True
    block_on_secrets: bool = True
    redact_secrets: bool = True
    host: str = "0.0.0.0"
    port: int = 8080
    log_level: str = "info"
    policy_server_url: str | None = None
    poll_interval: int = 60

    # Maps gateway API key → TeamPolicy (built at load time)
    _key_to_team: dict[str, TeamPolicy] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        for team in self.teams:
            for key in team.api_keys:
                self._key_to_team[key] = team

    def team_for_key(self, api_key: str) -> TeamPolicy | None:
        return self._key_to_team.get(api_key)

    @classmethod
    def load(cls, path: str | Path | None = None) -> "GatewayConfig":
        if path is None:
            return cls()
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Gateway config not found: {path}")
        with open(path) as f:
            raw = yaml.safe_load(f) or {}
        return cls._from_dict(raw)

    @classmethod
    def _from_dict(cls, raw: dict[str, Any]) -> "GatewayConfig":
        up = raw.get("upstream", {})
        tls = raw.get("tls", {})
        notif = raw.get("notifications", {})

        teams = []
        for name, team_cfg in raw.get("teams", {}).items():
            teams.append(TeamPolicy(
                name=name,
                outbound_checks=team_cfg.get("outbound_checks",
                    team_cfg.get("checks", ["secrets", "compliance"])),
                inbound_checks=team_cfg.get("inbound_checks", ["vuln"]),
                model_allowlist=team_cfg.get("model_allowlist", []),
                api_keys=team_cfg.get("api_keys", []),
            ))

        cfg = cls(
            upstream=UpstreamConfig(
                anthropic=up.get("anthropic", "https://api.anthropic.com"),
                openai=up.get("openai", "https://api.openai.com"),
            ),
            tls=TLSConfig(cert=tls.get("cert", ""), key=tls.get("key", "")),
            outbound_checks=raw.get("checks", {}).get(
                "outbound", ["secrets", "compliance", "agent"]
            ),
            inbound_checks=raw.get("checks", {}).get("inbound", ["vuln", "agent"]),
            policies=raw.get("policies", []),
            teams=teams,
            notifications=NotificationsConfig(
                slack=notif.get("slack", ""),
                webhook=notif.get("webhook", ""),
                pagerduty_key=notif.get("pagerduty_key", ""),
            ),
            audit_enabled=raw.get("audit_enabled", True),
            block_on_secrets=raw.get("block_on_secrets", True),
            redact_secrets=raw.get("redact_secrets", True),
            host=raw.get("host", "0.0.0.0"),
            port=raw.get("port", 8080),
            log_level=raw.get("log_level", "info"),
        )
        config.policy_server_url = raw.get("policy_server_url")
        config.poll_interval = int(raw.get("poll_interval", 60))
        return cfg
