"""Abstract base class for risk checkers."""

from __future__ import annotations

import abc
from typing import Any

from airiskguard.types import CheckResult


class BaseChecker(abc.ABC):
    name: str = "base"

    @abc.abstractmethod
    async def check(
        self, input_data: Any, output_data: Any, context: dict[str, Any] | None = None
    ) -> CheckResult: ...
