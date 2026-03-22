"""Assessment engine for evaluating AI systems against a standard."""

from __future__ import annotations

from typing import Any

from airiskguard.standards.types import (
    AssessmentResult,
    Control,
    ControlResult,
    DomainResult,
    MaturityLevel,
    Standard,
)


class StandardAssessor:
    """Evaluates an AI system's compliance against a risk management standard.

    Usage::

        from airiskguard.standards import STANDARD_V1, StandardAssessor

        assessor = StandardAssessor(STANDARD_V1)

        # Provide evidence of implemented controls
        assessor.set_control_status("SEC-ADV-01", implemented=True, maturity=3)
        assessor.set_control_status("SEC-ADV-02", implemented=True, maturity=4)

        # Integrate automated checker results
        assessor.apply_checker_results(risk_report)

        # Run assessment
        result = assessor.assess(model_id="my-model")
        print(result.summary())
    """

    def __init__(self, standard: Standard) -> None:
        self.standard = standard
        self._control_evidence: dict[str, _ControlEvidence] = {}

    def set_control_status(
        self,
        control_id: str,
        *,
        implemented: bool = True,
        maturity: int | MaturityLevel = MaturityLevel.DEFINED,
        findings: list[str] | None = None,
        evidence: list[str] | None = None,
    ) -> None:
        """Record the implementation status for a specific control."""
        ctrl = self.standard.get_control(control_id)
        if ctrl is None:
            raise ValueError(f"Unknown control: {control_id}")

        mat = MaturityLevel(maturity) if isinstance(maturity, int) else maturity
        self._control_evidence[control_id] = _ControlEvidence(
            implemented=implemented,
            maturity=mat,
            findings=findings or [],
            evidence=evidence or [],
            automated=False,
        )

    def apply_checker_results(
        self,
        risk_report: Any,
    ) -> None:
        """Map automated checker results to standard controls.

        Accepts a ``RiskReport`` from airiskguard's evaluation pipeline
        and marks the corresponding controls as implemented.
        """
        from airiskguard.types import RiskReport

        if not isinstance(risk_report, RiskReport):
            raise TypeError("Expected a RiskReport instance")

        checker_names = {r.checker_name for r in risk_report.check_results}

        for domain in self.standard.domains:
            for category in domain.categories:
                for control in category.controls:
                    if not control.automatable or not control.checker_mapping:
                        continue
                    if control.checker_mapping in checker_names:
                        check = next(
                            r for r in risk_report.check_results
                            if r.checker_name == control.checker_mapping
                        )
                        # Automated checks pass → control is working
                        maturity = (
                            MaturityLevel.MANAGED if check.passed
                            else MaturityLevel.DEVELOPING
                        )
                        self._control_evidence[control.control_id] = _ControlEvidence(
                            implemented=True,
                            maturity=maturity,
                            findings=[
                                f"Automated check score: {check.score:.2f}",
                                f"Risk level: {check.risk_level.value}",
                            ],
                            evidence=[
                                f"Checker '{check.checker_name}' ran at {check.timestamp}",
                            ],
                            automated=True,
                        )

    def assess(self, model_id: str = "default") -> AssessmentResult:
        """Run a full assessment and return structured results."""
        domain_results: list[DomainResult] = []
        domain_weights_total = 0.0
        weighted_score_sum = 0.0

        for domain in self.standard.domains:
            dr = self._assess_domain(domain)
            domain_results.append(dr)
            weighted_score_sum += dr.score * domain.weight
            domain_weights_total += domain.weight

        overall_score = (
            weighted_score_sum / domain_weights_total
            if domain_weights_total > 0
            else 0.0
        )

        # Overall maturity is the minimum across domains
        all_maturities = [dr.maturity for dr in domain_results]
        overall_maturity = min(all_maturities) if all_maturities else MaturityLevel.INITIAL

        recommendations = self._generate_recommendations(domain_results)

        return AssessmentResult(
            standard_id=self.standard.standard_id,
            standard_version=self.standard.version,
            assessed_model_id=model_id,
            overall_score=overall_score,
            overall_maturity=overall_maturity,
            domain_results=domain_results,
            recommendations=recommendations,
        )

    def get_coverage_by_framework(self, framework: str) -> dict[str, Any]:
        """Return coverage statistics for a specific external framework."""
        controls = self.standard.get_controls_for_framework(framework)
        implemented = sum(
            1 for c in controls
            if c.control_id in self._control_evidence
            and self._control_evidence[c.control_id].implemented
        )
        return {
            "framework": framework,
            "total_controls": len(controls),
            "implemented": implemented,
            "coverage_pct": round(implemented / len(controls) * 100, 1) if controls else 0,
            "gaps": [
                c.control_id for c in controls
                if c.control_id not in self._control_evidence
                or not self._control_evidence[c.control_id].implemented
            ],
        }

    def _assess_domain(self, domain: Any) -> DomainResult:
        control_results: list[ControlResult] = []
        gaps: list[str] = []

        for category in domain.categories:
            for control in category.controls:
                cr = self._assess_control(control)
                control_results.append(cr)
                if not cr.meets_requirement:
                    gaps.append(
                        f"[{control.control_id}] {control.name}: "
                        f"requires {control.required_maturity.label}, "
                        f"current {cr.maturity.label}"
                    )

        if control_results:
            avg_score = sum(cr.score for cr in control_results) / len(control_results)
            min_maturity = min(cr.maturity for cr in control_results)
        else:
            avg_score = 0.0
            min_maturity = MaturityLevel.INITIAL

        return DomainResult(
            domain_id=domain.domain_id,
            domain_name=domain.name,
            score=avg_score,
            maturity=min_maturity,
            control_results=control_results,
            gaps=gaps,
        )

    def _assess_control(self, control: Control) -> ControlResult:
        evidence = self._control_evidence.get(control.control_id)

        if evidence is None:
            return ControlResult(
                control_id=control.control_id,
                control_name=control.name,
                implemented=False,
                maturity=MaturityLevel.INITIAL,
                meets_requirement=False,
                score=0.0,
                findings=["Control not implemented"],
            )

        meets = evidence.maturity >= control.required_maturity
        # Score: maturity / 5, capped at 1.0
        score = min(evidence.maturity.value / 5.0, 1.0)
        if not evidence.implemented:
            score = 0.0

        return ControlResult(
            control_id=control.control_id,
            control_name=control.name,
            implemented=evidence.implemented,
            maturity=evidence.maturity,
            meets_requirement=meets,
            score=score,
            findings=evidence.findings,
            evidence=evidence.evidence,
            automated=evidence.automated,
        )

    def _generate_recommendations(
        self, domain_results: list[DomainResult]
    ) -> list[str]:
        recommendations: list[str] = []

        # Find domains with lowest scores
        sorted_domains = sorted(domain_results, key=lambda d: d.score)
        for dr in sorted_domains[:3]:
            if dr.score < 0.6:
                recommendations.append(
                    f"Priority: Improve '{dr.domain_name}' domain "
                    f"(score: {dr.score:.0%}, {dr.implemented_count}/{dr.total_count} controls)"
                )

        # Find unimplemented controls
        unimplemented = []
        for dr in domain_results:
            for cr in dr.control_results:
                if not cr.implemented:
                    unimplemented.append(f"{cr.control_id} ({cr.control_name})")

        if unimplemented:
            recommendations.append(
                f"Implement {len(unimplemented)} missing controls: "
                + ", ".join(unimplemented[:5])
                + ("..." if len(unimplemented) > 5 else "")
            )

        # Find controls that don't meet maturity requirements
        under_maturity = []
        for dr in domain_results:
            for cr in dr.control_results:
                if cr.implemented and not cr.meets_requirement:
                    under_maturity.append(cr.control_id)

        if under_maturity:
            recommendations.append(
                f"Increase maturity for {len(under_maturity)} controls: "
                + ", ".join(under_maturity[:5])
                + ("..." if len(under_maturity) > 5 else "")
            )

        # Suggest automation
        automatable = self.standard.get_automatable_controls()
        auto_not_done = [
            c.control_id for c in automatable
            if c.control_id not in self._control_evidence
            or not self._control_evidence[c.control_id].automated
        ]
        if auto_not_done:
            recommendations.append(
                f"Automate {len(auto_not_done)} eligible controls via airiskguard checkers: "
                + ", ".join(auto_not_done[:5])
                + ("..." if len(auto_not_done) > 5 else "")
            )

        return recommendations


class _ControlEvidence:
    """Internal tracking of evidence for a control."""

    __slots__ = ("implemented", "maturity", "findings", "evidence", "automated")

    def __init__(
        self,
        implemented: bool,
        maturity: MaturityLevel,
        findings: list[str],
        evidence: list[str],
        automated: bool,
    ) -> None:
        self.implemented = implemented
        self.maturity = maturity
        self.findings = findings
        self.evidence = evidence
        self.automated = automated
