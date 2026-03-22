# Compliance Framework Mapping

AIRMS v1.0 maps every control to requirements in three major international frameworks, enabling organizations to demonstrate compliance across multiple regulatory regimes using a single assessment.

## NIST AI Risk Management Framework

**46 control mappings** covering all four NIST functions:

| NIST Function | AIRMS Domains | Key Controls |
|---------------|---------------|--------------|
| **GOVERN** | Accountability & Governance | ACC-GOV-01/02/03, ACC-LCM-01/02 |
| **MAP** | Fairness, Data Quality, Transparency | FAI-BIA-01, DAT-QUA-01, TRA-DIS-01/02 |
| **MEASURE** | Safety, Security, Robustness, Fairness | SAF-HAR-01, SEC-ADV-01, ROB-DRI-01, FAI-BIA-01/02/03 |
| **MANAGE** | Safety, Human Oversight, Robustness | SAF-HAR-03, HUM-REV-01/03, ROB-DRI-02 |

## EU Artificial Intelligence Act

**38 control mappings** covering key articles for high-risk AI systems:

| EU AI Act Article | Topic | AIRMS Controls |
|-------------------|-------|----------------|
| **Article 9** | Risk Management System | SAF-HAR-01/02/03, ACC-GOV-01/03, ROB-DRI-01 |
| **Article 10** | Data Governance | SEC-PRI-01/02, DAT-QUA-01/02/03, FAI-BIA-01/02 |
| **Article 11** | Technical Documentation | ACC-COM-01 |
| **Article 12** | Record-keeping | TRA-LOG-01/02 |
| **Article 13** | Transparency | TRA-DIS-02, TRA-EXP-01 |
| **Article 14** | Human Oversight | HUM-REV-01/02/03, HUM-OVR-01/02 |
| **Article 15** | Accuracy, Robustness, Security | SAF-REL-03, SAF-HAL-01, SEC-ADV-01/02 |
| **Article 43** | Conformity Assessment | ACC-COM-02 |
| **Article 51** | Registration | ACC-LCM-01 |
| **Article 52** | Transparency Obligations | TRA-DIS-01 |
| **Article 62** | Serious Incident Reporting | SAF-HAR-03 |

## ISO/IEC 42001:2023

**21 control mappings** covering AI management system requirements:

| ISO/IEC 42001 Clause | Topic | AIRMS Controls |
|----------------------|-------|----------------|
| **5.2** | Policy | ACC-GOV-01 |
| **5.3** | Roles and Responsibilities | ACC-GOV-02 |
| **8.4** | AI System Operation | SAF-HAR-03 |
| **9.1** | Monitoring and Measurement | SAF-REL-01 |
| **9.2** | Internal Audit | ACC-COM-02 |
| **A.5.3** | AI System Inventory | ACC-LCM-01 |
| **A.5.4** | AI System Lifecycle | ACC-LCM-02/03 |
| **A.6.1.3** | Documentation | TRA-DIS-02, ACC-COM-01 |
| **A.6.2.4** | Access Control | SEC-ACC-01 |
| **A.6.2.5** | AI Security Threats | SEC-ADV-01 |
| **A.6.2.6** | Event Recording | TRA-LOG-01/02 |
| **A.7.4** | Impact Assessment | FAI-BIA-01 |
| **A.8.4** | Human Oversight | HUM-REV-02 |
| **A.8.5** | Data Management | SEC-PRI-01/02, DAT-QUA-01, DAT-INT-01 |

## Checking Coverage Programmatically

```python
from airiskguard.standards import STANDARD_V1, StandardAssessor

assessor = StandardAssessor(STANDARD_V1)

# ... set control statuses and apply checker results ...

# Check framework-specific coverage
for framework in ["NIST AI RMF", "EU AI Act", "ISO/IEC 42001"]:
    coverage = assessor.get_coverage_by_framework(framework)
    print(f"{framework}: {coverage['coverage_pct']}% "
          f"({coverage['implemented']}/{coverage['total_controls']})")
    if coverage['gaps']:
        print(f"  Gaps: {', '.join(coverage['gaps'])}")
```
