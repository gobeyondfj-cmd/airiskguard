"""Secrets/credential leak checker for airiskguard.

Scans prompts and code sent to AI coding assistants for secrets that
should never leave the corporate network:

- AI provider API keys (Anthropic, OpenAI, Google, Cohere, Hugging Face)
- Cloud credentials (AWS, GCP, Azure)
- Source control tokens (GitHub, GitLab, Bitbucket)
- Private keys and certificates
- Database connection strings with embedded credentials
- Generic high-entropy secrets (passwords, tokens in code)
- JWT tokens
- Payment keys (Stripe, PayPal)
"""

from __future__ import annotations

import math
import re
from typing import Any

from airiskguard.checkers.base import BaseChecker
from airiskguard.types import CheckResult, RiskLevel

# ---------------------------------------------------------------------------
# Pattern registry — (label, compiled_regex, score, risk_level)
# ---------------------------------------------------------------------------

_PATTERNS: list[tuple[str, re.Pattern[str], float, RiskLevel]] = [
    # --- AI provider keys ---
    ("anthropic_api_key",
     re.compile(r"sk-ant-[A-Za-z0-9\-_]{20,}"),
     0.95, RiskLevel.CRITICAL),

    ("openai_api_key",
     re.compile(r"sk-[A-Za-z0-9]{20,}"),
     0.95, RiskLevel.CRITICAL),

    ("google_ai_key",
     re.compile(r"AIza[0-9A-Za-z\-_]{35}"),
     0.90, RiskLevel.CRITICAL),

    ("cohere_api_key",
     re.compile(r"[A-Za-z0-9]{40}(?=\s|$|['\"])"),
     0.60, RiskLevel.MEDIUM),  # lower — too broad, needs context

    ("huggingface_token",
     re.compile(r"hf_[A-Za-z0-9]{34,}"),
     0.90, RiskLevel.CRITICAL),

    # --- Cloud credentials ---
    ("aws_access_key",
     re.compile(r"AKIA[0-9A-Z]{16}"),
     0.97, RiskLevel.CRITICAL),

    ("aws_secret_key",
     re.compile(r"(?i)aws.{0,20}secret.{0,20}['\"]([A-Za-z0-9/+=]{40})['\"]"),
     0.95, RiskLevel.CRITICAL),

    ("gcp_service_account",
     re.compile(r'"type"\s*:\s*"service_account"'),
     0.90, RiskLevel.CRITICAL),

    ("azure_connection_string",
     re.compile(r"DefaultEndpointsProtocol=https;AccountName=[^;]+;AccountKey=[A-Za-z0-9+/=]{60,}"),
     0.95, RiskLevel.CRITICAL),

    # --- Source control tokens ---
    ("github_token",
     re.compile(r"gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{82,}"),
     0.97, RiskLevel.CRITICAL),

    ("gitlab_token",
     re.compile(r"glpat-[A-Za-z0-9\-_]{20,}"),
     0.95, RiskLevel.CRITICAL),

    ("bitbucket_token",
     re.compile(r"ATBB[A-Za-z0-9]{32,}"),
     0.90, RiskLevel.CRITICAL),

    # --- Private keys ---
    ("private_key_pem",
     re.compile(r"-----BEGIN\s(?:RSA|EC|DSA|OPENSSH|PGP)?\s?PRIVATE KEY-----"),
     0.99, RiskLevel.CRITICAL),

    ("private_key_p12",
     re.compile(r"(?i)\.p12|\.pfx|PKCS#12"),
     0.70, RiskLevel.HIGH),

    # --- Database connection strings with credentials ---
    ("db_connection_string",
     re.compile(
         r"(?i)(postgresql|mysql|mongodb|redis|mssql|oracle)"
         r"://[^:@\s]+:[^@\s]{4,}@[^\s'\"]+"
     ),
     0.92, RiskLevel.CRITICAL),

    # --- JWT tokens ---
    ("jwt_token",
     re.compile(r"eyJ[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+"),
     0.80, RiskLevel.HIGH),

    # --- Payment keys ---
    ("stripe_secret_key",
     re.compile(r"sk_live_[A-Za-z0-9]{24,}"),
     0.99, RiskLevel.CRITICAL),

    ("stripe_restricted_key",
     re.compile(r"rk_live_[A-Za-z0-9]{24,}"),
     0.95, RiskLevel.CRITICAL),

    # --- Generic hardcoded secrets in code ---
    ("hardcoded_password",
     re.compile(
         r"(?i)(?:password|passwd|pwd|secret|api_key|apikey|auth_token|access_token)"
         r"\s*=\s*['\"][^'\"]{6,}['\"]"
     ),
     0.75, RiskLevel.HIGH),

    ("hardcoded_bearer",
     re.compile(r"(?i)bearer\s+[A-Za-z0-9\-._~+/]{20,}"),
     0.80, RiskLevel.HIGH),
]

# ---------------------------------------------------------------------------
# Shannon entropy for catching high-entropy strings not matched by patterns
# ---------------------------------------------------------------------------

_ENTROPY_RE = re.compile(r"['\"]([A-Za-z0-9+/=_\-]{30,})['\"]")
_ENTROPY_THRESHOLD = 4.5  # bits per character


def _shannon_entropy(s: str) -> float:
    if not s:
        return 0.0
    freq = {}
    for c in s:
        freq[c] = freq.get(c, 0) + 1
    n = len(s)
    return -sum((f / n) * math.log2(f / n) for f in freq.values())


def _high_entropy_strings(text: str) -> list[str]:
    """Find quoted strings with suspiciously high entropy."""
    found = []
    for m in _ENTROPY_RE.finditer(text):
        candidate = m.group(1)
        if _shannon_entropy(candidate) >= _ENTROPY_THRESHOLD:
            found.append(candidate[:12] + "…")
    return found


class SecretsChecker(BaseChecker):
    """Detects secrets and credentials in prompts sent to AI coding assistants.

    Checks for AI provider keys, cloud credentials, source control tokens,
    private keys, database connection strings, JWT tokens, and high-entropy
    strings that look like secrets.

    Args:
        entropy_check: Also flag high-entropy quoted strings (default True).
                       May produce false positives on hashed values.
        redact: Replace matched secrets with ``[REDACTED]`` in details (default True).
    """

    name = "secrets"

    def __init__(
        self,
        entropy_check: bool = True,
        redact: bool = True,
    ) -> None:
        self.entropy_check = entropy_check
        self.redact = redact

    async def check(
        self,
        input_data: Any,
        output_data: Any,
        context: dict[str, Any] | None = None,
    ) -> CheckResult:
        # For coding assistants, secrets appear in the prompt (input), not the output
        text = _to_str(input_data) + "\n" + _to_str(output_data)

        flags: list[str] = []
        max_score = 0.0
        max_risk = RiskLevel.LOW
        redacted = text

        for label, pattern, score, risk in _PATTERNS:
            if pattern.search(text):
                flags.append(label)
                if score > max_score:
                    max_score = score
                    max_risk = risk
                if self.redact:
                    redacted = pattern.sub(f"[REDACTED:{label.upper()}]", redacted)

        if self.entropy_check and not flags:
            # Only run entropy if no named pattern found (avoid double-counting)
            hi_entropy = _high_entropy_strings(text)
            if hi_entropy:
                flags.append("high_entropy_string")
                if 0.65 > max_score:
                    max_score = 0.65
                    max_risk = RiskLevel.MEDIUM

        passed = len(flags) == 0
        details: dict[str, Any] = {
            "flags": flags,
            "secret_count": len(flags),
        }
        if self.redact and not passed:
            details["redacted_text"] = redacted

        return CheckResult(
            checker_name=self.name,
            risk_level=max_risk if flags else RiskLevel.LOW,
            passed=passed,
            score=max_score,
            details=details,
        )


def _to_str(data: Any) -> str:
    if isinstance(data, str):
        return data
    if isinstance(data, dict):
        return " ".join(str(v) for v in data.values())
    if isinstance(data, (list, tuple)):
        return " ".join(_to_str(i) for i in data)
    return str(data) if data else ""
