"""Core types: enums and dataclasses for airiskguard."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


class RiskLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    def __ge__(self, other: RiskLevel) -> bool:
        order = list(RiskLevel)
        return order.index(self) >= order.index(other)

    def __gt__(self, other: RiskLevel) -> bool:
        order = list(RiskLevel)
        return order.index(self) > order.index(other)

    def __le__(self, other: RiskLevel) -> bool:
        order = list(RiskLevel)
        return order.index(self) <= order.index(other)

    def __lt__(self, other: RiskLevel) -> bool:
        order = list(RiskLevel)
        return order.index(self) < order.index(other)


class ModelLifecycle(str, enum.Enum):
    DRAFT = "draft"
    VALIDATION = "validation"
    PRODUCTION = "production"
    DEPRECATED = "deprecated"
    RETIRED = "retired"


class ReviewStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"


@dataclass
class CheckResult:
    checker_name: str
    risk_level: RiskLevel
    passed: bool
    score: float  # 0.0 (safe) to 1.0 (risky)
    details: dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()


@dataclass
class RiskReport:
    model_id: str
    overall_risk: RiskLevel
    overall_score: float
    passed: bool
    check_results: list[CheckResult] = field(default_factory=list)
    blocked: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()


@dataclass
class ModelInfo:
    model_id: str
    name: str
    version: str
    owner: str
    risk_tier: RiskLevel = RiskLevel.MEDIUM
    lifecycle: ModelLifecycle = ModelLifecycle.DRAFT
    metadata: dict[str, Any] = field(default_factory=dict)
    registered_at: str = ""
    updated_at: str = ""

    def __post_init__(self) -> None:
        now = datetime.utcnow().isoformat()
        if not self.registered_at:
            self.registered_at = now
        if not self.updated_at:
            self.updated_at = now


@dataclass
class AuditEntry:
    entry_id: str
    model_id: str
    action: str
    risk_level: RiskLevel
    score: float
    input_hash: str
    output_hash: str
    details: dict[str, Any] = field(default_factory=dict)
    previous_hash: str = ""
    entry_hash: str = ""
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()


@dataclass
class ReviewItem:
    review_id: str
    model_id: str
    risk_report: RiskReport
    status: ReviewStatus = ReviewStatus.PENDING
    assignee: str = ""
    notes: str = ""
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self) -> None:
        now = datetime.utcnow().isoformat()
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now
