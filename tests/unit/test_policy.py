"""Tests for policy-as-code engine."""

from __future__ import annotations

import pytest

from airiskguard.policy import Policy, PolicyEngine, PolicyViolation
from airiskguard.types import CheckResult, RiskLevel, RiskReport


def _make_report(
    overall_risk: RiskLevel = RiskLevel.LOW,
    overall_score: float = 0.1,
    check_results: list[CheckResult] | None = None,
    blocked: bool = False,
) -> RiskReport:
    return RiskReport(
        model_id="test",
        overall_risk=overall_risk,
        overall_score=overall_score,
        passed=not blocked,
        check_results=check_results or [],
        blocked=blocked,
    )


def _make_check(
    name: str = "security",
    risk: RiskLevel = RiskLevel.LOW,
    score: float = 0.1,
    passed: bool = True,
    flags: list[str] | None = None,
) -> CheckResult:
    return CheckResult(
        checker_name=name, risk_level=risk, passed=passed,
        score=score, details={"flags": flags or []},
    )


# --- overall_risk condition ---

def test_overall_risk_block():
    engine = PolicyEngine.from_dict({"policies": [{
        "name": "block_critical",
        "condition": {"overall_risk": ">= critical"},
        "action": "block",
    }]})
    report = _make_report(overall_risk=RiskLevel.CRITICAL)
    result = engine.evaluate(report)
    assert result.blocked
    assert result.block_reasons == ["block_critical"]


def test_overall_risk_no_trigger():
    engine = PolicyEngine.from_dict({"policies": [{
        "name": "block_critical",
        "condition": {"overall_risk": ">= critical"},
        "action": "block",
    }]})
    report = _make_report(overall_risk=RiskLevel.LOW)
    result = engine.evaluate(report)
    assert not result.blocked


# --- overall_score condition ---

def test_overall_score_block():
    engine = PolicyEngine.from_dict({"policies": [{
        "name": "block_high_score",
        "condition": {"overall_score": ">= 0.8"},
        "action": "block",
    }]})
    result = engine.evaluate(_make_report(overall_score=0.9))
    assert result.blocked

    result = engine.evaluate(_make_report(overall_score=0.5))
    assert not result.blocked


# --- checker-specific conditions ---

def test_checker_risk_block():
    engine = PolicyEngine.from_dict({"policies": [{
        "name": "block_security_high",
        "condition": {"checker": "security", "risk": ">= high"},
        "action": "block",
    }]})
    report = _make_report(check_results=[
        _make_check("security", risk=RiskLevel.HIGH, score=0.8, passed=False)
    ])
    result = engine.evaluate(report)
    assert result.blocked


def test_checker_risk_no_trigger():
    engine = PolicyEngine.from_dict({"policies": [{
        "name": "block_security_high",
        "condition": {"checker": "security", "risk": ">= high"},
        "action": "block",
    }]})
    report = _make_report(check_results=[
        _make_check("security", risk=RiskLevel.LOW, score=0.1)
    ])
    result = engine.evaluate(report)
    assert not result.blocked


def test_checker_score_condition():
    engine = PolicyEngine.from_dict({"policies": [{
        "name": "review_compliance",
        "condition": {"checker": "compliance", "score": ">= 0.5"},
        "action": "review",
    }]})
    report = _make_report(check_results=[
        _make_check("compliance", score=0.7)
    ])
    result = engine.evaluate(report)
    assert result.should_review
    assert not result.blocked


def test_checker_contains_flag():
    engine = PolicyEngine.from_dict({"policies": [{
        "name": "flag_pii",
        "condition": {"checker": "compliance", "contains_flag": "pii_"},
        "action": "review",
    }]})
    report = _make_report(check_results=[
        _make_check("compliance", flags=["pii_email (1 found)"])
    ])
    result = engine.evaluate(report)
    assert result.should_review


def test_checker_contains_flag_no_match():
    engine = PolicyEngine.from_dict({"policies": [{
        "name": "flag_pii",
        "condition": {"checker": "compliance", "contains_flag": "pii_"},
        "action": "review",
    }]})
    report = _make_report(check_results=[
        _make_check("compliance", flags=["prohibited:violence"])
    ])
    result = engine.evaluate(report)
    assert not result.should_review


def test_checker_missing_from_report():
    engine = PolicyEngine.from_dict({"policies": [{
        "name": "block_security",
        "condition": {"checker": "security", "risk": ">= high"},
        "action": "block",
    }]})
    # Report has no security checker result
    report = _make_report(check_results=[
        _make_check("compliance", risk=RiskLevel.HIGH)
    ])
    result = engine.evaluate(report)
    assert not result.blocked


# --- checkers_above condition ---

def test_checkers_above_count():
    engine = PolicyEngine.from_dict({"policies": [{
        "name": "block_multiple_high",
        "condition": {"checkers_above": {"risk": ">= high", "count": ">= 2"}},
        "action": "block",
    }]})
    report = _make_report(check_results=[
        _make_check("security", risk=RiskLevel.HIGH),
        _make_check("compliance", risk=RiskLevel.HIGH),
        _make_check("bias", risk=RiskLevel.LOW),
    ])
    result = engine.evaluate(report)
    assert result.blocked


def test_checkers_above_count_not_enough():
    engine = PolicyEngine.from_dict({"policies": [{
        "name": "block_multiple_high",
        "condition": {"checkers_above": {"risk": ">= high", "count": ">= 2"}},
        "action": "block",
    }]})
    report = _make_report(check_results=[
        _make_check("security", risk=RiskLevel.HIGH),
        _make_check("compliance", risk=RiskLevel.LOW),
    ])
    result = engine.evaluate(report)
    assert not result.blocked


# --- multiple policies ---

def test_multiple_policies_first_blocks():
    engine = PolicyEngine.from_dict({"policies": [
        {"name": "p1", "condition": {"overall_risk": ">= high"}, "action": "block"},
        {"name": "p2", "condition": {"overall_score": ">= 0.5"}, "action": "review"},
    ]})
    report = _make_report(overall_risk=RiskLevel.HIGH, overall_score=0.8)
    result = engine.evaluate(report)
    assert result.blocked
    assert len(result.violations) == 2


# --- action: log ---

def test_action_log_no_block():
    engine = PolicyEngine.from_dict({"policies": [{
        "name": "log_medium",
        "condition": {"overall_risk": ">= medium"},
        "action": "log",
    }]})
    report = _make_report(overall_risk=RiskLevel.MEDIUM)
    result = engine.evaluate(report)
    assert not result.blocked
    assert not result.should_review
    assert len(result.violations) == 1


# --- from_yaml ---

def test_from_yaml(tmp_path):
    policy_file = tmp_path / "policies.yaml"
    policy_file.write_text("""
policies:
  - name: block_critical
    description: Block critical risk
    condition:
      overall_risk: ">= critical"
    action: block
""")
    engine = PolicyEngine.from_yaml(policy_file)
    result = engine.evaluate(_make_report(overall_risk=RiskLevel.CRITICAL))
    assert result.blocked


# --- validation errors ---

def test_invalid_action():
    from airiskguard.exceptions import ConfigError
    with pytest.raises(ConfigError):
        PolicyEngine.from_dict({"policies": [{
            "name": "bad",
            "condition": {"overall_risk": ">= high"},
            "action": "explode",
        }]})


def test_invalid_risk_level():
    from airiskguard.exceptions import ConfigError
    engine = PolicyEngine.from_dict({"policies": [{
        "name": "bad",
        "condition": {"overall_risk": ">= extreme"},
        "action": "block",
    }]})
    with pytest.raises(ConfigError):
        engine.evaluate(_make_report(overall_risk=RiskLevel.HIGH))


def test_invalid_expression():
    from airiskguard.exceptions import ConfigError
    engine = PolicyEngine.from_dict({"policies": [{
        "name": "bad",
        "condition": {"overall_risk": "high"},  # missing operator
        "action": "block",
    }]})
    with pytest.raises(ConfigError):
        engine.evaluate(_make_report(overall_risk=RiskLevel.HIGH))


# --- empty engine ---

def test_empty_engine():
    engine = PolicyEngine()
    result = engine.evaluate(_make_report(overall_risk=RiskLevel.CRITICAL))
    assert not result.blocked
    assert result.violations == []
