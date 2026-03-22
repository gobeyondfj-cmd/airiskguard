# Standards API Reference

## Standard

The `Standard` dataclass represents a complete AI risk management standard.

```python
from airiskguard.standards import STANDARD_V1

# Access standard metadata
print(STANDARD_V1.standard_id)   # "AIRMS"
print(STANDARD_V1.version)       # "1.0"
print(STANDARD_V1.total_controls)  # 53
```

### Methods

**`get_domain(domain_id: str) -> RiskDomain | None`**

Retrieve a domain by its ID.

```python
domain = STANDARD_V1.get_domain("SEC")
print(domain.name)  # "Security & Privacy"
```

**`get_control(control_id: str) -> Control | None`**

Look up a specific control.

```python
ctrl = STANDARD_V1.get_control("SEC-ADV-01")
print(ctrl.name)          # "Prompt Injection Detection"
print(ctrl.automatable)   # True
print(ctrl.checker_mapping)  # "security"
```

**`get_controls_for_framework(framework: str) -> list[Control]`**

Get all controls mapped to an external framework.

```python
eu_controls = STANDARD_V1.get_controls_for_framework("EU AI Act")
print(len(eu_controls))  # 38
```

**`get_automatable_controls() -> list[Control]`**

Get all controls that can be automated via airiskguard checkers.

```python
auto = STANDARD_V1.get_automatable_controls()
print(len(auto))  # 31
```

## StandardAssessor

The assessment engine that evaluates AI systems against a standard.

```python
from airiskguard.standards import STANDARD_V1, StandardAssessor

assessor = StandardAssessor(STANDARD_V1)
```

### Methods

**`set_control_status(control_id, *, implemented, maturity, findings, evidence)`**

Record the implementation status for a control.

```python
from airiskguard.standards.types import MaturityLevel

assessor.set_control_status(
    "ACC-GOV-01",
    implemented=True,
    maturity=MaturityLevel.DEFINED,     # or integer 1-5
    findings=["Policy document reviewed"],
    evidence=["policy-v2.pdf approved 2026-01-15"],
)
```

**`apply_checker_results(risk_report: RiskReport)`**

Map automated checker results to standard controls. Passed checks get `MANAGED` maturity; failed checks get `DEVELOPING`.

```python
from airiskguard import RiskGuard

guard = RiskGuard()
report = await guard.evaluate(input_data, output_data, model_id="my-model")
assessor.apply_checker_results(report)
```

**`assess(model_id: str = "default") -> AssessmentResult`**

Run a full assessment and return structured results.

```python
result = assessor.assess(model_id="my-model")

print(result.overall_score)     # 0.0 - 1.0
print(result.overall_maturity)  # MaturityLevel enum
print(result.compliant)         # True if all controls meet requirements
print(result.get_gaps())        # List of gap descriptions
print(result.summary())         # Dict with full summary
```

**`get_coverage_by_framework(framework: str) -> dict`**

Check implementation coverage for a specific external framework.

```python
coverage = assessor.get_coverage_by_framework("EU AI Act")
# {
#     "framework": "EU AI Act",
#     "total_controls": 38,
#     "implemented": 12,
#     "coverage_pct": 31.6,
#     "gaps": ["SEC-ADV-01", "SEC-ADV-02", ...]
# }
```

## AssessmentResult

Returned by `assessor.assess()`.

### Properties

| Property | Type | Description |
|----------|------|-------------|
| `overall_score` | float | 0.0 to 1.0, weighted across domains |
| `overall_maturity` | MaturityLevel | Minimum maturity across all domains |
| `compliant` | bool | True if all required controls meet maturity |
| `domain_results` | list[DomainResult] | Per-domain assessment results |
| `recommendations` | list[str] | Prioritized improvement recommendations |
| `timestamp` | str | ISO format assessment timestamp |

### Methods

**`summary() -> dict`** — Returns a dict with key metrics:

```python
{
    "standard": "AIRMS",
    "version": "1.0",
    "model_id": "my-model",
    "overall_score": 0.42,
    "overall_maturity": "Initial",
    "compliant": False,
    "controls_implemented": 18,
    "controls_total": 53,
    "coverage_pct": 34.0,
    "gap_count": 35,
    "timestamp": "2026-01-15T10:30:00"
}
```

**`get_gaps() -> list[str]`** — All gaps across all domains.

## MaturityLevel

```python
from airiskguard.standards.types import MaturityLevel

MaturityLevel.INITIAL      # 1 - Ad-hoc, reactive
MaturityLevel.DEVELOPING   # 2 - Basic processes, inconsistent
MaturityLevel.DEFINED      # 3 - Standardized, documented
MaturityLevel.MANAGED      # 4 - Quantitatively measured
MaturityLevel.OPTIMIZING   # 5 - Continuous improvement
```

## ControlCategory

```python
from airiskguard.standards.types import ControlCategory

ControlCategory.PREVENTIVE   # Stop risks before they occur
ControlCategory.DETECTIVE    # Identify risks when they occur
ControlCategory.CORRECTIVE   # Remediate after occurrence
ControlCategory.DIRECTIVE    # Guide behavior through policy
```
