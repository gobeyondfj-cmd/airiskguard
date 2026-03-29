"""Policy-as-code engine for airiskguard.

Declarative YAML rules evaluated against RiskReport — no Python required
for common governance patterns.

Example policy YAML::

    policies:
      - name: block_high_security
        description: Block any high-risk security findings
        condition:
          checker: security
          risk: ">= high"
        action: block

      - name: flag_pii_output
        description: Flag for human review if PII found
        condition:
          checker: compliance
          score: ">= 0.5"
          contains_flag: "pii_"
        action: review

      - name: block_overall_critical
        description: Block if overall risk is critical
        condition:
          overall_risk: ">= critical"
        action: block

      - name: block_combined
        description: Block if multiple checkers flag high risk
        condition:
          checkers_above:
            risk: ">= high"
            count: ">= 2"
        action: block
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from airiskguard.exceptions import ConfigError
from airiskguard.types import CheckResult, RiskLevel, RiskReport

_RISK_ORDER = [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
_RISK_MAP = {r.value: r for r in RiskLevel}

_OP_RE = re.compile(r"^\s*(>=|<=|>|<|==|!=)\s*(.+)\s*$")


def _parse_op(expr: str) -> tuple[str, str]:
    """Parse '>= high' → ('>=', 'high')."""
    m = _OP_RE.match(str(expr))
    if not m:
        raise ConfigError(f"Invalid policy expression: {expr!r}. Expected e.g. '>= high' or '< 0.5'")
    return m.group(1), m.group(2).strip()


def _compare_risk(actual: RiskLevel, op: str, target_str: str) -> bool:
    target = _RISK_MAP.get(target_str)
    if target is None:
        raise ConfigError(f"Unknown risk level in policy: {target_str!r}")
    a, t = _RISK_ORDER.index(actual), _RISK_ORDER.index(target)
    return _apply_op(a, op, t)


def _compare_score(actual: float, op: str, target_str: str) -> bool:
    try:
        target = float(target_str)
    except ValueError:
        raise ConfigError(f"Invalid score value in policy: {target_str!r}")
    return _apply_op(actual, op, target)


def _compare_int(actual: int, op: str, target_str: str) -> bool:
    try:
        target = int(target_str)
    except ValueError:
        raise ConfigError(f"Invalid integer value in policy: {target_str!r}")
    return _apply_op(actual, op, target)


def _apply_op(a: Any, op: str, b: Any) -> bool:
    if op == ">=": return a >= b
    if op == "<=": return a <= b
    if op == ">":  return a > b
    if op == "<":  return a < b
    if op == "==": return a == b
    if op == "!=": return a != b
    raise ConfigError(f"Unknown operator: {op!r}")


@dataclass
class PolicyViolation:
    policy_name: str
    action: str  # "block" | "review" | "log"
    description: str
    matched_checker: str | None = None
    matched_score: float | None = None
    matched_risk: str | None = None


@dataclass
class PolicyResult:
    violations: list[PolicyViolation] = field(default_factory=list)

    @property
    def blocked(self) -> bool:
        return any(v.action == "block" for v in self.violations)

    @property
    def should_review(self) -> bool:
        return any(v.action in ("block", "review") for v in self.violations)

    @property
    def block_reasons(self) -> list[str]:
        return [v.policy_name for v in self.violations if v.action == "block"]


@dataclass
class Policy:
    name: str
    condition: dict[str, Any]
    action: str  # "block" | "review" | "log"
    description: str = ""

    def evaluate(self, report: RiskReport) -> PolicyViolation | None:
        """Return a PolicyViolation if this policy is triggered, else None."""
        cond = self.condition

        # --- overall_risk condition ---
        if "overall_risk" in cond:
            op, val = _parse_op(cond["overall_risk"])
            if _compare_risk(report.overall_risk, op, val):
                return PolicyViolation(
                    policy_name=self.name, action=self.action,
                    description=self.description,
                    matched_risk=report.overall_risk.value,
                )

        # --- overall_score condition ---
        if "overall_score" in cond:
            op, val = _parse_op(cond["overall_score"])
            if _compare_score(report.overall_score, op, val):
                return PolicyViolation(
                    policy_name=self.name, action=self.action,
                    description=self.description,
                    matched_score=report.overall_score,
                )

        # --- checker-specific condition ---
        if "checker" in cond:
            checker_name = cond["checker"]
            result = _find_checker_result(report, checker_name)
            if result is None:
                return None
            if not _checker_matches(result, cond):
                return None
            return PolicyViolation(
                policy_name=self.name, action=self.action,
                description=self.description,
                matched_checker=checker_name,
                matched_score=result.score,
                matched_risk=result.risk_level.value,
            )

        # --- checkers_above: count multiple checkers above threshold ---
        if "checkers_above" in cond:
            sub = cond["checkers_above"]
            risk_expr = sub.get("risk")
            score_expr = sub.get("score")
            count_expr = sub.get("count", ">= 1")
            count = 0
            for result in report.check_results:
                ok = True
                if risk_expr:
                    op, val = _parse_op(risk_expr)
                    ok = ok and _compare_risk(result.risk_level, op, val)
                if score_expr:
                    op, val = _parse_op(score_expr)
                    ok = ok and _compare_score(result.score, op, val)
                if ok:
                    count += 1
            op, val = _parse_op(count_expr)
            if _compare_int(count, op, val):
                return PolicyViolation(
                    policy_name=self.name, action=self.action,
                    description=self.description,
                )

        return None


def _find_checker_result(report: RiskReport, checker_name: str) -> CheckResult | None:
    for r in report.check_results:
        if r.checker_name == checker_name:
            return r
    return None


def _checker_matches(result: CheckResult, cond: dict[str, Any]) -> bool:
    """Check risk, score, and contains_flag sub-conditions for a checker result."""
    if "risk" in cond:
        op, val = _parse_op(cond["risk"])
        if not _compare_risk(result.risk_level, op, val):
            return False

    if "score" in cond:
        op, val = _parse_op(cond["score"])
        if not _compare_score(result.score, op, val):
            return False

    if "contains_flag" in cond:
        prefix = cond["contains_flag"]
        flags = result.details.get("flags", [])
        if not any(prefix in str(f) for f in flags):
            return False

    if "passed" in cond:
        expected = bool(cond["passed"])
        if result.passed != expected:
            return False

    return True


class PolicyEngine:
    """Evaluates a set of declarative policies against a RiskReport.

    Args:
        policies: List of :class:`Policy` objects.
    """

    def __init__(self, policies: list[Policy] | None = None) -> None:
        self._policies: list[Policy] = policies or []

    def add_policy(self, policy: Policy) -> None:
        self._policies.append(policy)

    def evaluate(self, report: RiskReport) -> PolicyResult:
        """Evaluate all policies against a report and return violations."""
        result = PolicyResult()
        for policy in self._policies:
            violation = policy.evaluate(report)
            if violation:
                result.violations.append(violation)
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PolicyEngine:
        """Load policies from a dict (e.g. parsed YAML)."""
        raw_policies = data.get("policies", [])
        policies = []
        for p in raw_policies:
            if "name" not in p or "condition" not in p or "action" not in p:
                raise ConfigError(f"Policy missing required fields (name, condition, action): {p}")
            if p["action"] not in ("block", "review", "log"):
                raise ConfigError(f"Invalid policy action {p['action']!r}. Must be block, review, or log.")
            policies.append(Policy(
                name=p["name"],
                condition=p["condition"],
                action=p["action"],
                description=p.get("description", ""),
            ))
        return cls(policies)

    @classmethod
    def from_yaml(cls, path: str | Path) -> PolicyEngine:
        """Load policies from a YAML file."""
        path = Path(path)
        if not path.exists():
            raise ConfigError(f"Policy file not found: {path}")
        try:
            with open(path) as f:
                data = yaml.safe_load(f) or {}
            return cls.from_dict(data)
        except yaml.YAMLError as e:
            raise ConfigError(f"Invalid policy YAML: {e}") from e

    @classmethod
    def from_config(cls, source: str | Path | dict[str, Any] | list[dict] | None) -> PolicyEngine:
        """Load from a path, dict with 'policies' key, or list of policy dicts."""
        if source is None:
            return cls()
        if isinstance(source, list):
            return cls.from_dict({"policies": source})
        if isinstance(source, dict):
            return cls.from_dict(source)
        return cls.from_yaml(source)
