"""Vulnerability checker for AI-generated code.

Scans code completions returned by AI coding assistants for common
security vulnerabilities before they reach the developer's editor:

- Hardcoded credentials in generated code
- SQL injection via string formatting/concatenation
- Command injection (shell=True, os.system, eval)
- Insecure deserialization (pickle.loads on untrusted data)
- Weak/broken cryptography (MD5, SHA1, DES for passwords)
- Insecure random (random module instead of secrets)
- Path traversal patterns
- Insecure HTTP (not HTTPS in production URLs)
- Debug/development flags left in production code
- Open redirect patterns
- XML external entity (XXE) patterns
- Prototype pollution (JavaScript)
"""

from __future__ import annotations

import re
from typing import Any

from airiskguard.checkers.base import BaseChecker
from airiskguard.types import CheckResult, RiskLevel

_VULNS: list[tuple[str, list[re.Pattern[str]], float, RiskLevel]] = [
    # --- Hardcoded credentials in generated code ---
    ("hardcoded_credentials", [
        re.compile(r"(?i)(password|secret|api_key|token)\s*=\s*['\"][^'\"]{4,}['\"]"),
        re.compile(r"(?i)const\s+(password|secret|apiKey|token)\s*=\s*['\"][^'\"]{4,}['\"]"),
        re.compile(r"(?i)PASSWORD\s*=\s*['\"][^'\"]{4,}['\"]"),
    ], 0.85, RiskLevel.HIGH),

    # --- SQL injection via string formatting ---
    ("sql_injection", [
        re.compile(r"(?i)(?:execute|query|cursor\.execute)\s*\(\s*['\"].*%[s].*['\"]"),
        re.compile(r"(?i)(?:execute|query)\s*\(\s*f['\"].*SELECT|INSERT|UPDATE|DELETE.*\{"),
        re.compile(r"(?i)\"SELECT.*\+\s*\w+\s*\+"),
        re.compile(r"(?i)'SELECT.*'\s*\+\s*\w"),
        re.compile(r"(?i)[\"']SELECT[^\"']*[\"']\s*\+"),
        re.compile(r"(?i)\.format\(.*\)\s*[,)]\s*#.*sql|sql.*\.format\("),
    ], 0.90, RiskLevel.CRITICAL),

    # --- Command injection ---
    ("command_injection", [
        re.compile(r"subprocess\.(run|call|Popen|check_output)\s*\([^)]*shell\s*=\s*True"),
        re.compile(r"os\.system\s*\("),
        re.compile(r"os\.popen\s*\("),
        re.compile(r"(?i)eval\s*\([^)]*(?:input|request|user|param|data)"),
        re.compile(r"(?i)exec\s*\([^)]*(?:input|request|user|param|data)"),
    ], 0.92, RiskLevel.CRITICAL),

    # --- Insecure deserialization ---
    ("insecure_deserialization", [
        re.compile(r"pickle\.loads?\s*\("),
        re.compile(r"yaml\.load\s*\([^)]*(?!\bLoader\s*=\s*yaml\.SafeLoader)"),
        re.compile(r"marshal\.loads?\s*\("),
        re.compile(r"jsonpickle\.decode\s*\("),
    ], 0.88, RiskLevel.HIGH),

    # --- Weak cryptography ---
    ("weak_cryptography", [
        re.compile(r"(?i)hashlib\.(md5|sha1)\s*\("),
        re.compile(r"(?i)MD5\s*\(|SHA1\s*\(|SHA-1"),
        re.compile(r"(?i)DES\.(new|encrypt)|Blowfish\.new"),
        re.compile(r"(?i)Crypto\.Cipher\.DES"),
        re.compile(r"(?i)ECB\b.*mode|mode.*ECB\b"),
    ], 0.78, RiskLevel.HIGH),

    # --- Insecure random ---
    ("insecure_random", [
        re.compile(r"import random\b"),
        re.compile(r"random\.(random|randint|choice|shuffle)\s*\("),
        re.compile(r"Math\.random\s*\(\s*\)"),
    ], 0.55, RiskLevel.MEDIUM),

    # --- Path traversal ---
    ("path_traversal", [
        re.compile(r"(?i)open\s*\(\s*(?:request|user|input|param)"),
        re.compile(r"(?i)os\.path\.join\s*\([^)]*(?:request|user|input|param)"),
        re.compile(r'\.\.[\\/]'),
        re.compile(r"(?i)send_file\s*\([^)]*(?:request|user|input|param)"),
    ], 0.82, RiskLevel.HIGH),

    # --- Insecure HTTP ---
    ("insecure_http", [
        re.compile(r"http://(?!localhost|127\.0\.0\.1|0\.0\.0\.0|::1)[a-z0-9\-\.]+/"),
        re.compile(r"verify\s*=\s*False"),
        re.compile(r"ssl\._create_unverified_context"),
        re.compile(r"PYTHONHTTPSVERIFY\s*=\s*0"),
    ], 0.65, RiskLevel.MEDIUM),

    # --- Debug/development flags ---
    ("debug_in_production", [
        re.compile(r"(?i)DEBUG\s*=\s*True"),
        re.compile(r"(?i)app\.run\s*\([^)]*debug\s*=\s*True"),
        re.compile(r"(?i)FLASK_DEBUG\s*=\s*1"),
        re.compile(r"(?i)NODE_ENV\s*=\s*['\"]development['\"]"),
    ], 0.60, RiskLevel.MEDIUM),

    # --- Insecure CORS ---
    ("insecure_cors", [
        re.compile(r"Access-Control-Allow-Origin[^=\n]*=\s*['\"]?\*"),
        re.compile(r"(?i)allow_origins\s*=\s*\[['\"]?\*['\"]?\]"),
        re.compile(r"(?i)CORS\s*\(\s*app\s*,\s*origins\s*=\s*['\"]?\*"),
    ], 0.70, RiskLevel.MEDIUM),

    # --- XXE / unsafe XML ---
    ("xxe_vulnerability", [
        re.compile(r"etree\.parse\s*\(|lxml\.etree"),
        re.compile(r"xml\.etree\.ElementTree\.parse\s*\("),
        re.compile(r"FEATURE_EXTERNAL_GENERAL_ENTITIES"),
        re.compile(r"resolve_entities\s*=\s*True"),
    ], 0.72, RiskLevel.HIGH),

    # --- Prototype pollution (JS/TS) ---
    ("prototype_pollution", [
        re.compile(r"__proto__\s*\["),
        re.compile(r"constructor\s*\[.*\]"),
        re.compile(r"Object\.assign\s*\(\s*\{\s*\}"),
    ], 0.68, RiskLevel.MEDIUM),
]


class VulnChecker(BaseChecker):
    """Scans AI-generated code for common security vulnerabilities.

    Checks completions returned by coding assistants before they reach
    the developer's editor. Covers OWASP Top 10 and code-specific risks.

    Args:
        categories: Subset of vulnerability categories to check.
                    Defaults to all categories.
    """

    name = "vuln"

    def __init__(self, categories: list[str] | None = None) -> None:
        if categories:
            self._vulns = [(n, p, s, r) for n, p, s, r in _VULNS if n in categories]
        else:
            self._vulns = _VULNS

    async def check(
        self,
        input_data: Any,
        output_data: Any,
        context: dict[str, Any] | None = None,
    ) -> CheckResult:
        # Vulnerabilities appear in AI-generated output, not the input prompt
        text = _to_str(output_data)
        if not text:
            text = _to_str(input_data)

        flags: list[str] = []
        max_score = 0.0
        max_risk = RiskLevel.LOW
        matched_lines: dict[str, list[str]] = {}

        lines = text.splitlines()

        for vuln_name, patterns, score, risk in self._vulns:
            for pattern in patterns:
                for i, line in enumerate(lines, 1):
                    if pattern.search(line):
                        if vuln_name not in flags:
                            flags.append(vuln_name)
                            if score > max_score:
                                max_score = score
                                max_risk = risk
                        matched_lines.setdefault(vuln_name, []).append(
                            f"line {i}: {line.strip()[:80]}"
                        )
                        break  # one match per pattern per vuln category

        passed = len(flags) == 0
        return CheckResult(
            checker_name=self.name,
            risk_level=max_risk if flags else RiskLevel.LOW,
            passed=passed,
            score=max_score,
            details={
                "flags": flags,
                "vuln_count": len(flags),
                "matched_lines": matched_lines,
            },
        )


def _to_str(data: Any) -> str:
    if isinstance(data, str):
        return data
    if isinstance(data, dict):
        return " ".join(str(v) for v in data.values())
    if isinstance(data, (list, tuple)):
        return " ".join(_to_str(i) for i in data)
    return str(data) if data else ""
