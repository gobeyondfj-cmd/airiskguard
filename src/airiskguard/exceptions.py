"""Custom exceptions for airiskguard."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from airiskguard.types import RiskReport


class AiriskguardError(Exception):
    """Base exception for airiskguard."""


class RiskBlockedError(AiriskguardError):
    """Raised when a risk check blocks execution."""

    def __init__(self, message: str, report: RiskReport | None = None) -> None:
        super().__init__(message)
        self.report = report


class ConfigError(AiriskguardError):
    """Raised for configuration errors."""


class StorageError(AiriskguardError):
    """Raised for storage backend errors."""


class CheckerError(AiriskguardError):
    """Raised for checker-related errors."""


class RegistryError(AiriskguardError):
    """Raised for model registry errors."""
