"""Agent tool-call risk checker for airiskguard.

Detects threats specific to agentic AI systems:
- SQL injection in tool inputs
- Data exfiltration patterns (bulk SELECT, file reads, credential access)
- Prompt injection via tool outputs (attempting to hijack agent instructions)
- Dangerous shell/code execution patterns
- Excessive data access (PII/secret enumeration)
"""

from __future__ import annotations

import re
from typing import Any

from airiskguard.checkers.base import BaseChecker
from airiskguard.types import CheckResult, RiskLevel

# --- SQL injection patterns ---
_SQL_INJECTION = [
    re.compile(r"(?i)(union\s+select|union\s+all\s+select)"),
    re.compile(r"(?i)(drop\s+table|drop\s+database|truncate\s+table)"),
    re.compile(r"(?i)(insert\s+into|delete\s+from|update\s+\w+\s+set).*--"),
    re.compile(r"(?i)('\s*or\s*'1'\s*=\s*'1|'\s*or\s*1\s*=\s*1)"),
    re.compile(r"(?i)(;\s*exec\s*\(|;\s*execute\s*\()"),
    re.compile(r"(?i)(xp_cmdshell|sp_executesql|information_schema)"),
    re.compile(r"(?i)(sleep\s*\(\s*\d+\s*\)|benchmark\s*\()"),
    re.compile(r"(?i)(load_file\s*\(|into\s+outfile\s+)"),
]

# --- Data exfiltration patterns ---
_EXFILTRATION = [
    re.compile(r"(?i)select\s+\*\s+from\s+\w*(user|account|credential|password|secret|token|key)\w*"),
    re.compile(r"(?i)(dump|export|backup)\s+(all|entire|full|database|table)"),
    re.compile(r"(?i)cat\s+(/etc/passwd|/etc/shadow|~/.ssh|\.env|\.aws/credentials)"),
    re.compile(r"(?i)(curl|wget|nc|netcat)\s+.*\|\s*(bash|sh|python)"),
    re.compile(r"(?i)base64\s+(encode|decode)\s+.*\|\s*(curl|wget|nc)"),
    re.compile(r"(?i)(exfil|exfiltrat|data.?leak|send.?to.?external)"),
    re.compile(r"(?i)limit\s+\d{4,}"),  # suspiciously large LIMIT
]

# --- Prompt injection via tool output ---
_PROMPT_INJECTION = [
    re.compile(r"(?i)(ignore\s+(previous|prior|above|all)\s+instructions?)"),
    re.compile(r"(?i)(new\s+instructions?|updated\s+instructions?|system\s+prompt)"),
    re.compile(r"(?i)(you\s+are\s+now|act\s+as|pretend\s+(you\s+are|to\s+be))"),
    re.compile(r"(?i)(disregard|forget|override)\s+(your|all|previous)\s+(instructions?|rules?|guidelines?)"),
    re.compile(r"(?i)\[system\]|\[admin\]|\[override\]|\[jailbreak\]"),
    re.compile(r"(?i)(developer\s+mode|dan\s+mode|unrestricted\s+mode)"),
]

# --- Dangerous code/shell execution ---
_CODE_EXECUTION = [
    re.compile(r"(?i)(os\.system|subprocess\.(run|call|Popen)|eval\s*\(|exec\s*\()"),
    re.compile(r"(?i)(rm\s+-rf|chmod\s+777|chown\s+root|sudo\s+)"),
    re.compile(r"(?i)(wget|curl)\s+https?://\S+\s*\|\s*(bash|sh|python|perl|ruby)"),
    re.compile(r"(?i)(powershell|cmd\.exe|/bin/sh|/bin/bash)\s+-[ce]"),
    re.compile(r"(?i)(__import__|importlib\.import_module)\s*\("),
]

# --- Secret/credential enumeration ---
_SECRET_ENUM = [
    re.compile(r"(?i)(list|get|fetch|read)\s+(all\s+)?(api.?key|secret|token|password|credential)s?"),
    re.compile(r"(?i)(aws_secret|aws_access_key|openai_api_key|anthropic_api_key)"),
    re.compile(r"(?i)keychain|vault\s+(list|read|dump)"),
]

_PATTERN_GROUPS = [
    ("sql_injection",    _SQL_INJECTION,    0.85, RiskLevel.CRITICAL),
    ("exfiltration",     _EXFILTRATION,     0.80, RiskLevel.CRITICAL),
    ("prompt_injection", _PROMPT_INJECTION, 0.75, RiskLevel.HIGH),
    ("code_execution",   _CODE_EXECUTION,   0.80, RiskLevel.CRITICAL),
    ("secret_enum",      _SECRET_ENUM,      0.70, RiskLevel.HIGH),
]


def _extract_text(data: Any) -> str:
    """Flatten tool call data to a string for pattern matching."""
    if isinstance(data, str):
        return data
    if isinstance(data, dict):
        return " ".join(str(v) for v in data.values())
    if isinstance(data, (list, tuple)):
        return " ".join(_extract_text(item) for item in data)
    return str(data)


class AgentChecker(BaseChecker):
    """Detects security threats in agentic AI tool calls.

    Covers SQL injection, data exfiltration, prompt injection via tool
    outputs, dangerous code execution, and credential enumeration.

    Args:
        sql_injection: Enable SQL injection detection (default True).
        exfiltration: Enable data exfiltration detection (default True).
        prompt_injection: Enable prompt injection detection (default True).
        code_execution: Enable dangerous code execution detection (default True).
        secret_enum: Enable secret/credential enumeration detection (default True).
    """

    name = "agent"

    def __init__(
        self,
        sql_injection: bool = True,
        exfiltration: bool = True,
        prompt_injection: bool = True,
        code_execution: bool = True,
        secret_enum: bool = True,
    ) -> None:
        self._enabled = {
            "sql_injection":    sql_injection,
            "exfiltration":     exfiltration,
            "prompt_injection": prompt_injection,
            "code_execution":   code_execution,
            "secret_enum":      secret_enum,
        }

    async def check(
        self,
        input_data: Any,
        output_data: Any,
        context: dict[str, Any] | None = None,
    ) -> CheckResult:
        flags: list[str] = []
        max_score = 0.0
        max_risk = RiskLevel.LOW

        # Check both input (tool call args) and output (tool response)
        combined = _extract_text(input_data) + " " + _extract_text(output_data)

        for group_name, patterns, score, risk in _PATTERN_GROUPS:
            if not self._enabled.get(group_name, True):
                continue
            for pattern in patterns:
                if pattern.search(combined):
                    flags.append(group_name)
                    if score > max_score:
                        max_score = score
                        max_risk = risk
                    break  # one match per group is enough

        passed = len(flags) == 0
        return CheckResult(
            checker_name=self.name,
            risk_level=max_risk if flags else RiskLevel.LOW,
            passed=passed,
            score=max_score,
            details={"flags": flags, "threat_count": len(flags)},
        )
