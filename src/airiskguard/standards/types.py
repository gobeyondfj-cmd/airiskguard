"""Data models for AI risk management standards."""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


class MaturityLevel(int, enum.Enum):
    """Organizational maturity for a given control or domain.

    Follows a CMM-style 5-level progression.
    """

    INITIAL = 1       # Ad-hoc, reactive, no formal processes
    DEVELOPING = 2    # Basic processes defined but inconsistently applied
    DEFINED = 3       # Standardized processes documented and followed
    MANAGED = 4       # Quantitatively measured and controlled
    OPTIMIZING = 5    # Continuous improvement with feedback loops

    @property
    def label(self) -> str:
        return {
            1: "Initial",
            2: "Developing",
            3: "Defined",
            4: "Managed",
            5: "Optimizing",
        }[self.value]


class ControlCategory(str, enum.Enum):
    """Classification of controls by their function."""

    PREVENTIVE = "preventive"      # Stop risks before they occur
    DETECTIVE = "detective"        # Identify risks when they occur
    CORRECTIVE = "corrective"      # Remediate after occurrence
    DIRECTIVE = "directive"        # Guide behavior through policy


@dataclass
class ComplianceMapping:
    """Maps a control to an external framework requirement."""

    framework: str       # e.g. "NIST AI RMF", "EU AI Act", "ISO 42001"
    requirement_id: str  # e.g. "MAP 1.1", "Article 9", "6.1.2"
    description: str     # Brief description of the external requirement


@dataclass
class Control:
    """A specific risk mitigation control within a risk category."""

    control_id: str
    name: str
    description: str
    category: ControlCategory
    required_maturity: MaturityLevel = MaturityLevel.DEFINED
    automatable: bool = False
    checker_mapping: str = ""  # Maps to an airiskguard checker name
    compliance_mappings: list[ComplianceMapping] = field(default_factory=list)
    evidence_requirements: list[str] = field(default_factory=list)


@dataclass
class RiskCategory:
    """A specific risk category within a risk domain."""

    category_id: str
    name: str
    description: str
    controls: list[Control] = field(default_factory=list)
    weight: float = 1.0  # Relative importance within the domain


@dataclass
class RiskDomain:
    """A top-level risk domain grouping related categories."""

    domain_id: str
    name: str
    description: str
    categories: list[RiskCategory] = field(default_factory=list)
    weight: float = 1.0  # Relative importance in overall score


@dataclass
class Standard:
    """A complete AI risk management standard definition."""

    standard_id: str
    name: str
    version: str
    description: str
    domains: list[RiskDomain] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def total_controls(self) -> int:
        return sum(
            len(cat.controls)
            for d in self.domains
            for cat in d.categories
        )

    def get_domain(self, domain_id: str) -> RiskDomain | None:
        for d in self.domains:
            if d.domain_id == domain_id:
                return d
        return None

    def get_control(self, control_id: str) -> Control | None:
        for d in self.domains:
            for cat in d.categories:
                for ctrl in cat.controls:
                    if ctrl.control_id == control_id:
                        return ctrl
        return None

    def get_controls_for_framework(self, framework: str) -> list[Control]:
        """Return all controls that map to a given external framework."""
        result = []
        for d in self.domains:
            for cat in d.categories:
                for ctrl in cat.controls:
                    if any(m.framework == framework for m in ctrl.compliance_mappings):
                        result.append(ctrl)
        return result

    def get_automatable_controls(self) -> list[Control]:
        """Return all controls that can be automated via checkers."""
        result = []
        for d in self.domains:
            for cat in d.categories:
                for ctrl in cat.controls:
                    if ctrl.automatable:
                        result.append(ctrl)
        return result


# --- Assessment result types ---


@dataclass
class ControlResult:
    """Assessment result for a single control."""

    control_id: str
    control_name: str
    implemented: bool
    maturity: MaturityLevel
    meets_requirement: bool  # maturity >= control.required_maturity
    score: float  # 0.0 to 1.0
    findings: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)
    automated: bool = False


@dataclass
class DomainResult:
    """Assessment result for a risk domain."""

    domain_id: str
    domain_name: str
    score: float  # 0.0 to 1.0, weighted average of control scores
    maturity: MaturityLevel  # Minimum maturity across controls
    control_results: list[ControlResult] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)

    @property
    def implemented_count(self) -> int:
        return sum(1 for c in self.control_results if c.implemented)

    @property
    def total_count(self) -> int:
        return len(self.control_results)


@dataclass
class AssessmentResult:
    """Complete assessment result against a standard."""

    standard_id: str
    standard_version: str
    assessed_model_id: str
    overall_score: float  # 0.0 to 1.0, weighted across domains
    overall_maturity: MaturityLevel
    domain_results: list[DomainResult] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()

    @property
    def compliant(self) -> bool:
        """True if all required controls meet their maturity threshold."""
        return all(
            cr.meets_requirement
            for dr in self.domain_results
            for cr in dr.control_results
        )

    def get_gaps(self) -> list[str]:
        """Collect all gaps across domains."""
        gaps = []
        for dr in self.domain_results:
            gaps.extend(dr.gaps)
        return gaps

    def summary(self) -> dict[str, Any]:
        total_controls = sum(dr.total_count for dr in self.domain_results)
        implemented = sum(dr.implemented_count for dr in self.domain_results)
        return {
            "standard": self.standard_id,
            "version": self.standard_version,
            "model_id": self.assessed_model_id,
            "overall_score": round(self.overall_score, 3),
            "overall_maturity": self.overall_maturity.label,
            "compliant": self.compliant,
            "controls_implemented": implemented,
            "controls_total": total_controls,
            "coverage_pct": round(implemented / total_controls * 100, 1) if total_controls else 0,
            "gap_count": len(self.get_gaps()),
            "timestamp": self.timestamp,
        }
