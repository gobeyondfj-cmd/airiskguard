"""Name-based checker lookup registry."""

from __future__ import annotations

from typing import Any

from airiskguard.checkers.base import BaseChecker

_REGISTRY: dict[str, type[BaseChecker]] = {}


def register_checker(name: str, checker_cls: type[BaseChecker]) -> None:
    _REGISTRY[name] = checker_cls


def get_checker(name: str, config: dict[str, Any] | None = None) -> BaseChecker:
    if name not in _REGISTRY:
        raise KeyError(f"Unknown checker: {name}. Available: {list(_REGISTRY.keys())}")
    return _REGISTRY[name](**(config or {}))


def list_checkers() -> list[str]:
    return list(_REGISTRY.keys())


def _auto_register() -> None:
    from airiskguard.checkers.agent import AgentChecker
    from airiskguard.checkers.bias import BiasChecker
    from airiskguard.checkers.compliance import ComplianceChecker
    from airiskguard.checkers.fraud import FraudChecker
    from airiskguard.checkers.hallucination import HallucinationChecker
    from airiskguard.checkers.secrets import SecretsChecker
    from airiskguard.checkers.security import SecurityChecker
    from airiskguard.checkers.toxicity import ToxicityChecker
    from airiskguard.checkers.vuln import VulnChecker

    for cls in (AgentChecker, FraudChecker, HallucinationChecker, ComplianceChecker,
                BiasChecker, SecurityChecker, ToxicityChecker, SecretsChecker, VulnChecker):
        register_checker(cls.name, cls)


_auto_register()
