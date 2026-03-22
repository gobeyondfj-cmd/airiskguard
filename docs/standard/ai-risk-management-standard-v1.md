# AI Risk Management Standard v1.0

**Published by:** airiskguard
**Standard ID:** AIRMS v1.0
**Effective Date:** January 1, 2026
**Review Cycle:** Annual
**License:** MIT

---

## Executive Summary

The AI Risk Management Standard (AIRMS) v1.0 is a comprehensive, machine-readable framework for identifying, assessing, and mitigating risks in AI systems. It defines **53 controls** across **8 risk domains** and **22 risk categories**, providing organizations with a structured approach to AI governance.

AIRMS is aligned with three major international frameworks:

- **NIST AI Risk Management Framework** (AI RMF 1.0) — 46 control mappings
- **EU Artificial Intelligence Act** — 38 control mappings
- **ISO/IEC 42001:2023** (AI Management Systems) — 21 control mappings

Unlike traditional paper-based standards, AIRMS is designed to be both human-readable and machine-enforceable. Every control is defined as structured data, enabling automated assessment, continuous monitoring, and programmatic compliance reporting.

---

---

## 1. Scope & Applicability

This standard applies to organizations that develop, deploy, or operate AI systems, including but not limited to:

- **Large language models** (LLMs) and generative AI applications
- **Decision-support systems** that influence outcomes for individuals
- **Autonomous agents** and multi-agent systems
- **Machine learning models** in production environments
- **RAG (Retrieval-Augmented Generation) pipelines**
- **AI-powered APIs and services**

### Risk-Based Approach

AIRMS follows a risk-based approach. Not every control is required for every AI system. Organizations should assess the risk profile of each AI system and implement controls proportional to the risk level:

| AI System Risk Tier | Minimum Maturity | Recommended Controls |
|---------------------|------------------|---------------------|
| **Low Risk** | Level 2 (Developing) | Core controls in each domain |
| **Medium Risk** | Level 3 (Defined) | All standard controls |
| **High Risk** | Level 4 (Managed) | All controls with quantitative measurement |
| **Critical Risk** | Level 5 (Optimizing) | All controls with continuous improvement |

---

## 2. Maturity Model

AIRMS uses a five-level maturity model to assess how well controls are implemented. This follows the Capability Maturity Model (CMM) progression, adapted for AI risk management.

### Level 1 — Initial

- Risk management is ad-hoc and reactive
- No formal processes for AI governance
- Individual heroics rather than organizational capability
- *Indicator: "We handle issues as they come up"*

### Level 2 — Developing

- Basic processes are defined but inconsistently applied
- Some documentation exists for critical controls
- Awareness of AI risks at team level
- *Indicator: "We have some guidelines but they're not always followed"*

### Level 3 — Defined

- Standardized processes are documented and followed organization-wide
- Roles and responsibilities are clearly assigned
- Training programs exist for AI risk management
- *Indicator: "We have a defined process that everyone follows"*

### Level 4 — Managed

- Processes are quantitatively measured and controlled
- Metrics drive decision-making
- Automated monitoring and alerting is in place
- Regular reviews with data-driven improvements
- *Indicator: "We measure our performance and use data to improve"*

### Level 5 — Optimizing

- Continuous improvement with feedback loops
- Proactive identification and mitigation of emerging risks
- Industry-leading practices adopted and shared
- AI governance is embedded in organizational culture
- *Indicator: "We continuously improve and lead in AI governance"*

---

## 3. Control Categories

Every control in AIRMS is classified by its function:

| Category | Symbol | Purpose | Example |
|----------|--------|---------|---------|
| **Preventive** | PRE | Stop risks before they occur | Output safety guardrails |
| **Detective** | DET | Identify risks when they occur | Prompt injection detection |
| **Corrective** | COR | Remediate after occurrence | Incident response procedures |
| **Directive** | DIR | Guide behavior through policy | AI risk management policy |

A well-governed AI system implements controls from all four categories, creating defense in depth.

---

## 4. Risk Domains

### 4.1 Safety & Reliability (SAF)

**Weight: 1.5x** (elevated importance)

> Ensure AI systems operate reliably within intended parameters and do not cause harm to users, third parties, or the environment.

#### SAF-HAR: Harm Prevention

| Control ID | Control | Category | Maturity | Automatable |
|-----------|---------|----------|----------|-------------|
| SAF-HAR-01 | Harmful Content Detection | Detective | 3 | Yes |
| SAF-HAR-02 | Output Safety Guardrails | Preventive | 4 | Yes |
| SAF-HAR-03 | Incident Response Procedures | Corrective | 3 | No |

**SAF-HAR-01 — Harmful Content Detection**
Detect and block outputs containing instructions for violence, self-harm, illegal activities, or other harmful content. Evidence required: content filter configuration, detection rate metrics, false positive/negative analysis.

**SAF-HAR-02 — Output Safety Guardrails**
Implement configurable guardrails that prevent unsafe outputs based on risk thresholds and domain-specific safety rules. Evidence required: guardrail configuration documentation, threshold calibration records, override audit trail.

**SAF-HAR-03 — Incident Response Procedures**
Maintain documented procedures for responding to safety incidents involving AI system outputs. Evidence required: incident response plan, post-incident review records, escalation procedures.

#### SAF-REL: Reliability & Performance

| Control ID | Control | Category | Maturity | Automatable |
|-----------|---------|----------|----------|-------------|
| SAF-REL-01 | Performance Monitoring | Detective | 3 | Yes |
| SAF-REL-02 | Graceful Degradation | Preventive | 4 | No |
| SAF-REL-03 | Output Validation | Detective | 3 | Yes |

**SAF-REL-01 — Performance Monitoring**
Continuously monitor AI system performance metrics including latency, throughput, error rates, and output quality.

**SAF-REL-02 — Graceful Degradation**
Design AI systems to degrade gracefully under failure conditions rather than producing unsafe outputs.

**SAF-REL-03 — Output Validation**
Validate AI outputs against expected formats, ranges, and domain constraints before delivery.

#### SAF-HAL: Hallucination & Factuality

| Control ID | Control | Category | Maturity | Automatable |
|-----------|---------|----------|----------|-------------|
| SAF-HAL-01 | Hallucination Detection | Detective | 3 | Yes |
| SAF-HAL-02 | Source Grounding | Preventive | 4 | No |

**SAF-HAL-01 — Hallucination Detection**
Detect fabricated facts, URLs, citations, or contradictions in AI-generated outputs using NLI or heuristic methods.

**SAF-HAL-02 — Source Grounding**
Require AI outputs to be grounded in verifiable source material when factual claims are made.

---

### 4.2 Security & Privacy (SEC)

**Weight: 1.5x** (elevated importance)

> Protect AI systems from adversarial attacks, unauthorized access, and ensure proper handling of personal and sensitive data.

#### SEC-ADV: Adversarial Robustness

| Control ID | Control | Category | Maturity | Automatable |
|-----------|---------|----------|----------|-------------|
| SEC-ADV-01 | Prompt Injection Detection | Detective | 3 | Yes |
| SEC-ADV-02 | Jailbreak Prevention | Detective | 3 | Yes |
| SEC-ADV-03 | Encoding Attack Detection | Detective | 3 | Yes |

**SEC-ADV-01 — Prompt Injection Detection**
Detect and block prompt injection attempts that try to override system instructions or extract sensitive data.

**SEC-ADV-02 — Jailbreak Prevention**
Detect attempts to bypass AI safety constraints through role-play, hypothetical framing, or instruction manipulation.

**SEC-ADV-03 — Encoding Attack Detection**
Detect obfuscated attacks using base64 encoding, unicode manipulation, or homoglyph substitution.

#### SEC-PRI: Data Privacy

| Control ID | Control | Category | Maturity | Automatable |
|-----------|---------|----------|----------|-------------|
| SEC-PRI-01 | PII Detection & Redaction | Detective | 3 | Yes |
| SEC-PRI-02 | Data Minimization | Directive | 3 | No |
| SEC-PRI-03 | Information Leak Prevention | Detective | 3 | Yes |

**SEC-PRI-01 — PII Detection & Redaction**
Detect and redact personally identifiable information in AI inputs and outputs (SSN, credit cards, emails, phones).

**SEC-PRI-02 — Data Minimization**
Ensure AI systems process only the minimum data necessary for the intended purpose.

**SEC-PRI-03 — Information Leak Prevention**
Prevent AI systems from leaking system prompts, training data, or confidential information in outputs.

#### SEC-ACC: Access Control

| Control ID | Control | Category | Maturity | Automatable |
|-----------|---------|----------|----------|-------------|
| SEC-ACC-01 | API Authentication | Preventive | 3 | No |
| SEC-ACC-02 | Rate Limiting & Abuse Prevention | Preventive | 3 | Yes |

**SEC-ACC-01 — API Authentication**
Enforce authentication for all AI system API endpoints using industry-standard mechanisms.

**SEC-ACC-02 — Rate Limiting & Abuse Prevention**
Implement rate limiting and usage quotas to prevent abuse of AI system resources.

---

### 4.3 Fairness & Non-discrimination (FAI)

**Weight: 1.3x**

> Ensure AI systems treat all individuals and groups equitably, without unlawful discrimination or systematic bias.

#### FAI-BIA: Bias Detection & Mitigation

| Control ID | Control | Category | Maturity | Automatable |
|-----------|---------|----------|----------|-------------|
| FAI-BIA-01 | Disparate Impact Analysis | Detective | 3 | Yes |
| FAI-BIA-02 | Demographic Parity Monitoring | Detective | 3 | Yes |
| FAI-BIA-03 | Equalized Odds Assessment | Detective | 3 | Yes |

**FAI-BIA-01 — Disparate Impact Analysis**
Measure disparate impact ratio across protected groups using the 4/5ths rule and flag violations.

**FAI-BIA-02 — Demographic Parity Monitoring**
Monitor positive outcome rates across demographic groups and flag disparities exceeding tolerance thresholds.

**FAI-BIA-03 — Equalized Odds Assessment**
Evaluate true positive and false positive rate differences across protected groups.

#### FAI-LAN: Language & Representation

| Control ID | Control | Category | Maturity | Automatable |
|-----------|---------|----------|----------|-------------|
| FAI-LAN-01 | Biased Language Detection | Detective | 3 | Yes |
| FAI-LAN-02 | Inclusive Design Review | Directive | 4 | No |

**FAI-LAN-01 — Biased Language Detection**
Detect stereotyping, derogatory, or discriminatory language patterns in AI-generated outputs.

**FAI-LAN-02 — Inclusive Design Review**
Conduct periodic reviews ensuring AI system outputs and interactions are inclusive across cultures and demographics.

---

### 4.4 Transparency & Explainability (TRA)

**Weight: 1.0x**

> Ensure AI systems and their decisions can be understood, explained, and communicated to affected stakeholders.

#### TRA-DIS: Disclosure & Communication

| Control ID | Control | Category | Maturity | Automatable |
|-----------|---------|----------|----------|-------------|
| TRA-DIS-01 | AI Interaction Disclosure | Directive | 3 | No |
| TRA-DIS-02 | Capability & Limitation Documentation | Directive | 3 | No |

**TRA-DIS-01 — AI Interaction Disclosure**
Clearly disclose to users when they are interacting with an AI system rather than a human.

**TRA-DIS-02 — Capability & Limitation Documentation**
Document and communicate the intended capabilities, known limitations, and appropriate use cases of the AI system.

#### TRA-EXP: Explainability

| Control ID | Control | Category | Maturity | Automatable |
|-----------|---------|----------|----------|-------------|
| TRA-EXP-01 | Decision Explanation | Detective | 4 | No |
| TRA-EXP-02 | Risk Score Transparency | Detective | 3 | Yes |

**TRA-EXP-01 — Decision Explanation**
Provide human-understandable explanations for AI-driven decisions, especially those affecting individuals.

**TRA-EXP-02 — Risk Score Transparency**
Make risk assessment scores, thresholds, and contributing factors available for inspection.

#### TRA-LOG: Logging & Traceability

| Control ID | Control | Category | Maturity | Automatable |
|-----------|---------|----------|----------|-------------|
| TRA-LOG-01 | Immutable Audit Trail | Detective | 3 | Yes |
| TRA-LOG-02 | Input/Output Logging | Detective | 3 | Yes |

**TRA-LOG-01 — Immutable Audit Trail**
Maintain a tamper-evident, hash-chained audit log of all AI system evaluations and decisions.

**TRA-LOG-02 — Input/Output Logging**
Log AI system inputs and outputs with sufficient detail to support investigation and compliance audits.

---

### 4.5 Accountability & Governance (ACC)

**Weight: 1.2x**

> Establish clear ownership, governance structures, and accountability mechanisms for AI systems throughout their lifecycle.

#### ACC-GOV: Governance Framework

| Control ID | Control | Category | Maturity | Automatable |
|-----------|---------|----------|----------|-------------|
| ACC-GOV-01 | AI Risk Management Policy | Directive | 3 | No |
| ACC-GOV-02 | Roles & Responsibilities | Directive | 3 | No |
| ACC-GOV-03 | Risk Appetite & Thresholds | Directive | 3 | Yes |

**ACC-GOV-01 — AI Risk Management Policy**
Maintain an organizational policy defining AI risk appetite, governance roles, and risk management processes.

**ACC-GOV-02 — Roles & Responsibilities**
Define and document clear roles, responsibilities, and authorities for AI risk management.

**ACC-GOV-03 — Risk Appetite & Thresholds**
Define quantitative risk tolerance thresholds for blocking, review, and escalation of AI system decisions.

#### ACC-LCM: Lifecycle Management

| Control ID | Control | Category | Maturity | Automatable |
|-----------|---------|----------|----------|-------------|
| ACC-LCM-01 | Model Registration & Inventory | Detective | 3 | Yes |
| ACC-LCM-02 | Lifecycle State Management | Preventive | 3 | Yes |
| ACC-LCM-03 | Decommissioning Procedures | Corrective | 3 | No |

**ACC-LCM-01 — Model Registration & Inventory**
Maintain a centralized registry of all AI models with version, owner, risk tier, and lifecycle state.

**ACC-LCM-02 — Lifecycle State Management**
Enforce valid lifecycle transitions (draft, validation, production, deprecated, retired) with appropriate gates.

**ACC-LCM-03 — Decommissioning Procedures**
Establish procedures for safely retiring AI systems including data disposal and dependency management.

#### ACC-COM: Compliance Reporting

| Control ID | Control | Category | Maturity | Automatable |
|-----------|---------|----------|----------|-------------|
| ACC-COM-01 | Regulatory Report Generation | Detective | 3 | Yes |
| ACC-COM-02 | Conformity Assessment | Detective | 4 | No |

**ACC-COM-01 — Regulatory Report Generation**
Generate compliance reports aligned with applicable regulations (GDPR, SOX, EU AI Act).

**ACC-COM-02 — Conformity Assessment**
Conduct periodic self-assessments or third-party audits to verify compliance with applicable standards.

---

### 4.6 Robustness & Resilience (ROB)

**Weight: 1.0x**

> Ensure AI systems maintain performance under adverse conditions, distribution shifts, and unexpected inputs.

#### ROB-DRI: Distribution Drift

| Control ID | Control | Category | Maturity | Automatable |
|-----------|---------|----------|----------|-------------|
| ROB-DRI-01 | Data Drift Detection | Detective | 3 | Yes |
| ROB-DRI-02 | Model Retraining Triggers | Corrective | 4 | No |

**ROB-DRI-01 — Data Drift Detection**
Monitor input data distributions for statistically significant shifts using KS tests or similar methods.

**ROB-DRI-02 — Model Retraining Triggers**
Define and automate triggers for model retraining or recalibration when drift exceeds thresholds.

#### ROB-ANO: Anomaly Detection

| Control ID | Control | Category | Maturity | Automatable |
|-----------|---------|----------|----------|-------------|
| ROB-ANO-01 | Input Anomaly Detection | Detective | 3 | Yes |
| ROB-ANO-02 | Behavioral Anomaly Detection | Detective | 3 | Yes |

**ROB-ANO-01 — Input Anomaly Detection**
Detect anomalous inputs that fall outside the expected distribution using statistical or ML methods.

**ROB-ANO-02 — Behavioral Anomaly Detection**
Monitor AI system behavioral patterns for unexpected changes in output distributions or decision patterns.

#### ROB-STR: Stress Testing

| Control ID | Control | Category | Maturity | Automatable |
|-----------|---------|----------|----------|-------------|
| ROB-STR-01 | Adversarial Testing | Detective | 4 | No |
| ROB-STR-02 | Edge Case Testing | Detective | 3 | No |

**ROB-STR-01 — Adversarial Testing**
Conduct regular red-team exercises and adversarial testing to evaluate system robustness.

**ROB-STR-02 — Edge Case Testing**
Maintain and execute test suites covering boundary conditions, edge cases, and known failure modes.

---

### 4.7 Human Oversight (HUM)

**Weight: 1.2x**

> Ensure meaningful human control over AI systems with appropriate review, escalation, and override mechanisms.

#### HUM-REV: Review Workflows

| Control ID | Control | Category | Maturity | Automatable |
|-----------|---------|----------|----------|-------------|
| HUM-REV-01 | Risk-Based Review Flagging | Detective | 3 | Yes |
| HUM-REV-02 | Review Decision Tracking | Detective | 3 | Yes |
| HUM-REV-03 | Escalation Procedures | Corrective | 3 | Yes |

**HUM-REV-01 — Risk-Based Review Flagging**
Automatically flag AI decisions exceeding risk thresholds for human review before execution.

**HUM-REV-02 — Review Decision Tracking**
Track human review decisions (approve, reject, escalate) with rationale and timestamps.

**HUM-REV-03 — Escalation Procedures**
Automatically escalate critical-risk decisions to senior authorities when initial review is insufficient.

#### HUM-OVR: Override & Intervention

| Control ID | Control | Category | Maturity | Automatable |
|-----------|---------|----------|----------|-------------|
| HUM-OVR-01 | Human Override Capability | Corrective | 3 | No |
| HUM-OVR-02 | Emergency Stop Capability | Corrective | 3 | No |

**HUM-OVR-01 — Human Override Capability**
Provide mechanisms for authorized humans to override AI decisions at any point in the workflow.

**HUM-OVR-02 — Emergency Stop Capability**
Implement ability to immediately halt AI system operation when critical safety concerns arise.

---

### 4.8 Data Quality & Integrity (DAT)

**Weight: 1.0x**

> Ensure the quality, integrity, and appropriateness of data used to train, fine-tune, and operate AI systems.

#### DAT-QUA: Data Quality Assurance

| Control ID | Control | Category | Maturity | Automatable |
|-----------|---------|----------|----------|-------------|
| DAT-QUA-01 | Training Data Documentation | Directive | 3 | No |
| DAT-QUA-02 | Data Validation Pipeline | Preventive | 3 | Yes |
| DAT-QUA-03 | Data Representativeness Assessment | Detective | 3 | No |

**DAT-QUA-01 — Training Data Documentation**
Document training data sources, collection methods, preprocessing steps, and known limitations.

**DAT-QUA-02 — Data Validation Pipeline**
Implement automated validation checks for data completeness, consistency, accuracy, and timeliness.

**DAT-QUA-03 — Data Representativeness Assessment**
Assess whether training data adequately represents the target population and use-case conditions.

#### DAT-INT: Data Integrity & Provenance

| Control ID | Control | Category | Maturity | Automatable |
|-----------|---------|----------|----------|-------------|
| DAT-INT-01 | Data Provenance Tracking | Detective | 3 | No |
| DAT-INT-02 | Data Integrity Verification | Detective | 3 | Yes |

**DAT-INT-01 — Data Provenance Tracking**
Track the origin, transformations, and lineage of all data used in AI system training and operation.

**DAT-INT-02 — Data Integrity Verification**
Verify data integrity using checksums, digital signatures, or hash verification at each processing stage.

#### DAT-FRA: Fraud & Anomaly in Data

| Control ID | Control | Category | Maturity | Automatable |
|-----------|---------|----------|----------|-------------|
| DAT-FRA-01 | Transaction Fraud Detection | Detective | 3 | Yes |
| DAT-FRA-02 | Data Poisoning Detection | Detective | 4 | No |

**DAT-FRA-01 — Transaction Fraud Detection**
Detect anomalous transactions using statistical methods (z-score), velocity tracking, and pattern rules.

**DAT-FRA-02 — Data Poisoning Detection**
Monitor for signs of data poisoning or manipulation in training and operational data pipelines.

---

## 5. Compliance Mapping

AIRMS maps every control to requirements in three major international frameworks. This enables organizations to demonstrate compliance across multiple regulatory regimes using a single assessment.

### NIST AI Risk Management Framework

AIRMS covers 46 of its controls with mappings to NIST AI RMF functions:

| NIST Function | AIRMS Domains |
|---------------|---------------|
| **GOVERN** | ACC (Governance Framework, Lifecycle Management) |
| **MAP** | FAI (Bias Detection), DAT (Data Quality), TRA (Disclosure) |
| **MEASURE** | SAF (Safety), SEC (Security), ROB (Robustness), FAI (Fairness) |
| **MANAGE** | SAF (Incident Response), HUM (Human Oversight), ROB (Drift Response) |

### EU Artificial Intelligence Act

AIRMS covers 38 of its controls with mappings to EU AI Act articles:

| EU AI Act Article | AIRMS Controls |
|-------------------|----------------|
| **Article 9** (Risk Management) | SAF-HAR-01/02/03, ACC-GOV-01/03, ROB-DRI-01 |
| **Article 10** (Data Governance) | SEC-PRI-01/02, DAT-QUA-01/02/03, FAI-BIA-01/02 |
| **Article 12** (Record-keeping) | TRA-LOG-01/02 |
| **Article 13** (Transparency) | TRA-DIS-02, TRA-EXP-01 |
| **Article 14** (Human Oversight) | HUM-REV-01/02/03, HUM-OVR-01/02 |
| **Article 15** (Accuracy/Robustness) | SAF-REL-03, SAF-HAL-01, SEC-ADV-01/02 |
| **Article 43** (Conformity Assessment) | ACC-COM-02 |
| **Article 51** (Registration) | ACC-LCM-01 |
| **Article 52** (Transparency) | TRA-DIS-01 |
| **Article 62** (Incident Reporting) | SAF-HAR-03 |

### ISO/IEC 42001:2023

AIRMS covers 21 of its controls with mappings to ISO/IEC 42001 clauses:

| ISO/IEC 42001 Clause | AIRMS Controls |
|----------------------|----------------|
| **5.2** (Policy) | ACC-GOV-01 |
| **5.3** (Roles) | ACC-GOV-02 |
| **8.4** (Operation) | SAF-HAR-03 |
| **9.1** (Monitoring) | SAF-REL-01 |
| **9.2** (Audit) | ACC-COM-02 |
| **A.5.3/A.5.4** (Inventory/Lifecycle) | ACC-LCM-01/02 |
| **A.6.1.3** (Documentation) | TRA-DIS-02, ACC-COM-01 |
| **A.6.2.4–A.6.2.6** (Security/Logging) | SEC-ACC-01, SEC-ADV-01, TRA-LOG-01/02 |
| **A.7.4** (Impact Assessment) | FAI-BIA-01 |
| **A.8.4/A.8.5** (Data Management) | HUM-REV-02, SEC-PRI-01/02, DAT-QUA-01, DAT-INT-01 |

---

## 6. Assessment Methodology

### How Assessment Works

AIRMS assessments evaluate each control on two dimensions:

1. **Implementation Status** — Is the control in place?
2. **Maturity Level** — How mature is the implementation?

A control is considered compliant when its maturity level meets or exceeds the required maturity specified in the standard.

### Scoring

- **Control Score** = Maturity Level / 5 (range: 0.0 to 1.0)
- **Domain Score** = Average of control scores within the domain
- **Overall Score** = Weighted average of domain scores

Domain weights reflect relative importance:

| Domain | Weight |
|--------|--------|
| Safety & Reliability | 1.5x |
| Security & Privacy | 1.5x |
| Fairness & Non-discrimination | 1.3x |
| Accountability & Governance | 1.2x |
| Human Oversight | 1.2x |
| Transparency & Explainability | 1.0x |
| Robustness & Resilience | 1.0x |
| Data Quality & Integrity | 1.0x |

### Assessment Output

An AIRMS assessment produces:

- **Overall compliance status** (compliant / non-compliant)
- **Overall score** (0–100%)
- **Overall maturity level** (minimum across all domains)
- **Per-domain scores and maturity**
- **Gap analysis** (controls not meeting requirements)
- **Prioritized recommendations**
- **Framework-specific coverage** (NIST, EU AI Act, ISO)

### Automation

31 of 53 controls (58%) can be automatically assessed through airiskguard's built-in checkers. The remaining controls require manual evidence collection through documentation review, interviews, or process verification.

---

## 7. Implementation with airiskguard

AIRMS is implemented as structured data in the `airiskguard` Python package, enabling programmatic assessment.

### Installation

```bash
pip install airiskguard
```

### Quick Start

```python
from airiskguard.standards import STANDARD_V1, StandardAssessor

# Initialize the assessor
assessor = StandardAssessor(STANDARD_V1)

# Record manually verified controls
assessor.set_control_status("ACC-GOV-01", implemented=True, maturity=3)
assessor.set_control_status("ACC-GOV-02", implemented=True, maturity=3)
assessor.set_control_status("TRA-DIS-01", implemented=True, maturity=4)

# Integrate automated checker results
from airiskguard import RiskGuard

guard = RiskGuard()
report = await guard.evaluate(
    input_data="user query",
    output_data="ai response",
    model_id="my-model"
)
assessor.apply_checker_results(report)

# Run full assessment
result = assessor.assess(model_id="my-model")

print(result.summary())
# {
#   'standard': 'AIRMS',
#   'version': '1.0',
#   'overall_score': 0.42,
#   'overall_maturity': 'Initial',
#   'compliant': False,
#   'controls_implemented': 18,
#   'controls_total': 53,
#   'coverage_pct': 34.0,
#   'gap_count': 35,
# }
```

### Check Framework Coverage

```python
# See how well you cover the EU AI Act
eu_coverage = assessor.get_coverage_by_framework("EU AI Act")
print(f"EU AI Act coverage: {eu_coverage['coverage_pct']}%")
print(f"Gaps: {eu_coverage['gaps']}")
```

### Explore the Standard Programmatically

```python
from airiskguard.standards import STANDARD_V1

# List all domains
for domain in STANDARD_V1.domains:
    print(f"{domain.domain_id}: {domain.name}")

# Find automatable controls
auto = STANDARD_V1.get_automatable_controls()
print(f"{len(auto)} controls can be automated")

# Look up a specific control
ctrl = STANDARD_V1.get_control("SEC-ADV-01")
print(f"{ctrl.name}: {ctrl.description}")
for m in ctrl.compliance_mappings:
    print(f"  -> {m.framework} {m.requirement_id}")
```

---

## 8. Appendix: Control Reference

### Summary Statistics

| Metric | Value |
|--------|-------|
| Total Domains | 8 |
| Total Categories | 22 |
| Total Controls | 53 |
| Automatable Controls | 31 (58%) |
| NIST AI RMF Mappings | 46 |
| EU AI Act Mappings | 38 |
| ISO/IEC 42001 Mappings | 21 |
| Preventive Controls | 8 |
| Detective Controls | 33 |
| Corrective Controls | 7 |
| Directive Controls | 10 |

### Full Control Index

| ID | Name | Domain | Category | Maturity | Auto |
|----|------|--------|----------|----------|------|
| SAF-HAR-01 | Harmful Content Detection | SAF | DET | 3 | Yes |
| SAF-HAR-02 | Output Safety Guardrails | SAF | PRE | 4 | Yes |
| SAF-HAR-03 | Incident Response Procedures | SAF | COR | 3 | No |
| SAF-REL-01 | Performance Monitoring | SAF | DET | 3 | Yes |
| SAF-REL-02 | Graceful Degradation | SAF | PRE | 4 | No |
| SAF-REL-03 | Output Validation | SAF | DET | 3 | Yes |
| SAF-HAL-01 | Hallucination Detection | SAF | DET | 3 | Yes |
| SAF-HAL-02 | Source Grounding | SAF | PRE | 4 | No |
| SEC-ADV-01 | Prompt Injection Detection | SEC | DET | 3 | Yes |
| SEC-ADV-02 | Jailbreak Prevention | SEC | DET | 3 | Yes |
| SEC-ADV-03 | Encoding Attack Detection | SEC | DET | 3 | Yes |
| SEC-PRI-01 | PII Detection & Redaction | SEC | DET | 3 | Yes |
| SEC-PRI-02 | Data Minimization | SEC | DIR | 3 | No |
| SEC-PRI-03 | Information Leak Prevention | SEC | DET | 3 | Yes |
| SEC-ACC-01 | API Authentication | SEC | PRE | 3 | No |
| SEC-ACC-02 | Rate Limiting & Abuse Prevention | SEC | PRE | 3 | Yes |
| FAI-BIA-01 | Disparate Impact Analysis | FAI | DET | 3 | Yes |
| FAI-BIA-02 | Demographic Parity Monitoring | FAI | DET | 3 | Yes |
| FAI-BIA-03 | Equalized Odds Assessment | FAI | DET | 3 | Yes |
| FAI-LAN-01 | Biased Language Detection | FAI | DET | 3 | Yes |
| FAI-LAN-02 | Inclusive Design Review | FAI | DIR | 4 | No |
| TRA-DIS-01 | AI Interaction Disclosure | TRA | DIR | 3 | No |
| TRA-DIS-02 | Capability & Limitation Documentation | TRA | DIR | 3 | No |
| TRA-EXP-01 | Decision Explanation | TRA | DET | 4 | No |
| TRA-EXP-02 | Risk Score Transparency | TRA | DET | 3 | Yes |
| TRA-LOG-01 | Immutable Audit Trail | TRA | DET | 3 | Yes |
| TRA-LOG-02 | Input/Output Logging | TRA | DET | 3 | Yes |
| ACC-GOV-01 | AI Risk Management Policy | ACC | DIR | 3 | No |
| ACC-GOV-02 | Roles & Responsibilities | ACC | DIR | 3 | No |
| ACC-GOV-03 | Risk Appetite & Thresholds | ACC | DIR | 3 | Yes |
| ACC-LCM-01 | Model Registration & Inventory | ACC | DET | 3 | Yes |
| ACC-LCM-02 | Lifecycle State Management | ACC | PRE | 3 | Yes |
| ACC-LCM-03 | Decommissioning Procedures | ACC | COR | 3 | No |
| ACC-COM-01 | Regulatory Report Generation | ACC | DET | 3 | Yes |
| ACC-COM-02 | Conformity Assessment | ACC | DET | 4 | No |
| ROB-DRI-01 | Data Drift Detection | ROB | DET | 3 | Yes |
| ROB-DRI-02 | Model Retraining Triggers | ROB | COR | 4 | No |
| ROB-ANO-01 | Input Anomaly Detection | ROB | DET | 3 | Yes |
| ROB-ANO-02 | Behavioral Anomaly Detection | ROB | DET | 3 | Yes |
| ROB-STR-01 | Adversarial Testing | ROB | DET | 4 | No |
| ROB-STR-02 | Edge Case Testing | ROB | DET | 3 | No |
| HUM-REV-01 | Risk-Based Review Flagging | HUM | DET | 3 | Yes |
| HUM-REV-02 | Review Decision Tracking | HUM | DET | 3 | Yes |
| HUM-REV-03 | Escalation Procedures | HUM | COR | 3 | Yes |
| HUM-OVR-01 | Human Override Capability | HUM | COR | 3 | No |
| HUM-OVR-02 | Emergency Stop Capability | HUM | COR | 3 | No |
| DAT-QUA-01 | Training Data Documentation | DAT | DIR | 3 | No |
| DAT-QUA-02 | Data Validation Pipeline | DAT | PRE | 3 | Yes |
| DAT-QUA-03 | Data Representativeness Assessment | DAT | DET | 3 | No |
| DAT-INT-01 | Data Provenance Tracking | DAT | DET | 3 | No |
| DAT-INT-02 | Data Integrity Verification | DAT | DET | 3 | Yes |
| DAT-FRA-01 | Transaction Fraud Detection | DAT | DET | 3 | Yes |
| DAT-FRA-02 | Data Poisoning Detection | DAT | DET | 4 | No |

---

*AIRMS v1.0 is maintained by the airiskguard project. For the machine-readable standard definition, see the `airiskguard.standards` module in the [airiskguard Python package](https://pypi.org/project/airiskguard/).*

*Copyright 2026 airiskguard contributors. Released under the MIT License.*
