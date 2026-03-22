"""Tests for AI Risk Management Standard v1.0 and assessment engine."""

from __future__ import annotations

import pytest

from airiskguard.standards import (
    STANDARD_V1,
    StandardAssessor,
    get_standard,
)
from airiskguard.standards.types import (
    ControlCategory,
    MaturityLevel,
)
from airiskguard.types import CheckResult, RiskLevel, RiskReport


# ── Standard definition tests ───────────────────────────────────────


class TestStandardV1Definition:
    def test_standard_metadata(self):
        assert STANDARD_V1.standard_id == "AIRMS"
        assert STANDARD_V1.version == "1.0"
        assert STANDARD_V1.name == "AI Risk Management Standard"

    def test_has_eight_domains(self):
        assert len(STANDARD_V1.domains) == 8

    def test_domain_ids(self):
        ids = [d.domain_id for d in STANDARD_V1.domains]
        assert ids == ["SAF", "SEC", "FAI", "TRA", "ACC", "ROB", "HUM", "DAT"]

    def test_total_controls(self):
        # Verify we have a substantial number of controls
        assert STANDARD_V1.total_controls >= 40

    def test_all_controls_have_ids(self):
        for d in STANDARD_V1.domains:
            for cat in d.categories:
                for ctrl in cat.controls:
                    assert ctrl.control_id, f"Control missing ID in {cat.category_id}"
                    assert ctrl.name, f"Control {ctrl.control_id} missing name"
                    assert ctrl.description, f"Control {ctrl.control_id} missing description"

    def test_control_ids_unique(self):
        ids = []
        for d in STANDARD_V1.domains:
            for cat in d.categories:
                for ctrl in cat.controls:
                    ids.append(ctrl.control_id)
        assert len(ids) == len(set(ids)), "Duplicate control IDs found"

    def test_get_control_by_id(self):
        ctrl = STANDARD_V1.get_control("SEC-ADV-01")
        assert ctrl is not None
        assert ctrl.name == "Prompt Injection Detection"
        assert ctrl.automatable is True
        assert ctrl.checker_mapping == "security"

    def test_get_control_nonexistent(self):
        assert STANDARD_V1.get_control("NOPE-01") is None

    def test_get_domain_by_id(self):
        dom = STANDARD_V1.get_domain("FAI")
        assert dom is not None
        assert dom.name == "Fairness & Non-discrimination"

    def test_get_domain_nonexistent(self):
        assert STANDARD_V1.get_domain("NOPE") is None

    def test_compliance_mappings_present(self):
        """Ensure controls have compliance mappings to external frameworks."""
        mapped = 0
        for d in STANDARD_V1.domains:
            for cat in d.categories:
                for ctrl in cat.controls:
                    if ctrl.compliance_mappings:
                        mapped += 1
        # Most controls should have at least one mapping
        assert mapped > STANDARD_V1.total_controls * 0.7

    def test_automatable_controls(self):
        auto = STANDARD_V1.get_automatable_controls()
        assert len(auto) > 10
        for ctrl in auto:
            assert ctrl.automatable is True

    def test_get_controls_for_nist(self):
        nist_controls = STANDARD_V1.get_controls_for_framework("NIST AI RMF")
        assert len(nist_controls) > 10

    def test_get_controls_for_eu_ai_act(self):
        eu_controls = STANDARD_V1.get_controls_for_framework("EU AI Act")
        assert len(eu_controls) > 10

    def test_get_controls_for_iso(self):
        iso_controls = STANDARD_V1.get_controls_for_framework("ISO/IEC 42001")
        assert len(iso_controls) > 5

    def test_get_standard_v1(self):
        s = get_standard("1.0")
        assert s is STANDARD_V1

    def test_get_standard_unknown(self):
        with pytest.raises(ValueError, match="Unknown standard version"):
            get_standard("99.0")

    def test_control_categories_valid(self):
        for d in STANDARD_V1.domains:
            for cat in d.categories:
                for ctrl in cat.controls:
                    assert isinstance(ctrl.category, ControlCategory)

    def test_checker_mappings_valid(self):
        valid_checkers = {"security", "compliance", "hallucination", "bias", "fraud"}
        for d in STANDARD_V1.domains:
            for cat in d.categories:
                for ctrl in cat.controls:
                    if ctrl.checker_mapping:
                        assert ctrl.checker_mapping in valid_checkers, (
                            f"{ctrl.control_id} maps to unknown checker: {ctrl.checker_mapping}"
                        )


# ── Assessor tests ──────────────────────────────────────────────────


class TestStandardAssessor:
    def setup_method(self):
        self.assessor = StandardAssessor(STANDARD_V1)

    def test_assess_empty(self):
        """No evidence → all controls unimplemented."""
        result = self.assessor.assess(model_id="test-model")
        assert result.overall_score == 0.0
        assert result.overall_maturity == MaturityLevel.INITIAL
        assert result.compliant is False
        assert len(result.get_gaps()) > 0

    def test_set_control_status(self):
        self.assessor.set_control_status(
            "SEC-ADV-01", implemented=True, maturity=MaturityLevel.DEFINED
        )
        result = self.assessor.assess()
        # Find the specific control result
        sec_ctrl = None
        for dr in result.domain_results:
            for cr in dr.control_results:
                if cr.control_id == "SEC-ADV-01":
                    sec_ctrl = cr
                    break
        assert sec_ctrl is not None
        assert sec_ctrl.implemented is True
        assert sec_ctrl.maturity == MaturityLevel.DEFINED

    def test_set_control_status_invalid(self):
        with pytest.raises(ValueError, match="Unknown control"):
            self.assessor.set_control_status("NOPE-01", implemented=True)

    def test_maturity_as_int(self):
        self.assessor.set_control_status("SEC-ADV-01", implemented=True, maturity=4)
        result = self.assessor.assess()
        for dr in result.domain_results:
            for cr in dr.control_results:
                if cr.control_id == "SEC-ADV-01":
                    assert cr.maturity == MaturityLevel.MANAGED

    def test_control_score_calculation(self):
        """Score = maturity / 5."""
        self.assessor.set_control_status(
            "SEC-ADV-01", implemented=True, maturity=MaturityLevel.OPTIMIZING
        )
        result = self.assessor.assess()
        for dr in result.domain_results:
            for cr in dr.control_results:
                if cr.control_id == "SEC-ADV-01":
                    assert cr.score == 1.0

    def test_unimplemented_score_zero(self):
        self.assessor.set_control_status(
            "SEC-ADV-01", implemented=False, maturity=MaturityLevel.DEFINED
        )
        result = self.assessor.assess()
        for dr in result.domain_results:
            for cr in dr.control_results:
                if cr.control_id == "SEC-ADV-01":
                    assert cr.score == 0.0

    def test_apply_checker_results(self):
        """Checker results auto-populate control evidence."""
        report = RiskReport(
            model_id="test",
            overall_risk=RiskLevel.LOW,
            overall_score=0.1,
            passed=True,
            check_results=[
                CheckResult(
                    checker_name="security",
                    risk_level=RiskLevel.LOW,
                    passed=True,
                    score=0.1,
                ),
                CheckResult(
                    checker_name="bias",
                    risk_level=RiskLevel.LOW,
                    passed=True,
                    score=0.05,
                ),
            ],
        )
        self.assessor.apply_checker_results(report)
        result = self.assessor.assess()

        # Security checker maps to SEC-ADV-01, SEC-ADV-02, SEC-ADV-03, SEC-PRI-03
        for dr in result.domain_results:
            for cr in dr.control_results:
                if cr.control_id == "SEC-ADV-01":
                    assert cr.implemented is True
                    assert cr.automated is True
                    assert cr.maturity == MaturityLevel.MANAGED

    def test_apply_checker_results_failed_check(self):
        """Failed checker → maturity DEVELOPING."""
        report = RiskReport(
            model_id="test",
            overall_risk=RiskLevel.HIGH,
            overall_score=0.8,
            passed=False,
            check_results=[
                CheckResult(
                    checker_name="security",
                    risk_level=RiskLevel.HIGH,
                    passed=False,
                    score=0.8,
                ),
            ],
        )
        self.assessor.apply_checker_results(report)
        result = self.assessor.assess()
        for dr in result.domain_results:
            for cr in dr.control_results:
                if cr.control_id == "SEC-ADV-01":
                    assert cr.maturity == MaturityLevel.DEVELOPING

    def test_apply_checker_results_type_error(self):
        with pytest.raises(TypeError, match="Expected a RiskReport"):
            self.assessor.apply_checker_results({"not": "a report"})

    def test_summary(self):
        result = self.assessor.assess(model_id="test-model")
        s = result.summary()
        assert s["standard"] == "AIRMS"
        assert s["version"] == "1.0"
        assert s["model_id"] == "test-model"
        assert "overall_score" in s
        assert "controls_total" in s
        assert "coverage_pct" in s

    def test_recommendations_generated(self):
        result = self.assessor.assess()
        assert len(result.recommendations) > 0

    def test_domain_results_complete(self):
        result = self.assessor.assess()
        assert len(result.domain_results) == 8
        for dr in result.domain_results:
            assert dr.domain_id
            assert dr.domain_name
            assert len(dr.control_results) > 0

    def test_framework_coverage(self):
        self.assessor.set_control_status("SEC-ADV-01", implemented=True, maturity=3)
        coverage = self.assessor.get_coverage_by_framework("NIST AI RMF")
        assert coverage["framework"] == "NIST AI RMF"
        assert coverage["total_controls"] > 0
        assert coverage["implemented"] >= 1
        assert 0 <= coverage["coverage_pct"] <= 100

    def test_full_compliance_scenario(self):
        """Implement all controls at required maturity → compliant."""
        for domain in STANDARD_V1.domains:
            for cat in domain.categories:
                for ctrl in cat.controls:
                    self.assessor.set_control_status(
                        ctrl.control_id,
                        implemented=True,
                        maturity=max(ctrl.required_maturity, MaturityLevel.DEFINED),
                    )
        result = self.assessor.assess()
        assert result.compliant is True
        assert result.overall_score > 0.5
        assert len(result.get_gaps()) == 0
