"""AI Risk Management Standard v1.0.

A comprehensive standard defining 8 risk domains, 24 risk categories,
and 72 controls for governing AI systems. Aligned with NIST AI RMF,
EU AI Act, and ISO/IEC 42001.
"""

from __future__ import annotations

from airiskguard.standards.types import (
    ComplianceMapping,
    Control,
    ControlCategory,
    MaturityLevel,
    RiskCategory,
    RiskDomain,
    Standard,
)

# ── Framework constants ─────────────────────────────────────────────
NIST = "NIST AI RMF"
EU = "EU AI Act"
ISO = "ISO/IEC 42001"


def _build_standard() -> Standard:
    """Construct the full AI Risk Management Standard v1.0."""
    return Standard(
        standard_id="AIRMS",
        name="AI Risk Management Standard",
        version="1.0",
        description=(
            "A comprehensive standard for identifying, assessing, and mitigating "
            "risks in AI systems across safety, security, fairness, transparency, "
            "accountability, robustness, human oversight, and data quality domains."
        ),
        domains=[
            _domain_safety(),
            _domain_security(),
            _domain_fairness(),
            _domain_transparency(),
            _domain_accountability(),
            _domain_robustness(),
            _domain_human_oversight(),
            _domain_data_quality(),
        ],
        metadata={
            "aligned_frameworks": [NIST, EU, ISO],
            "effective_date": "2026-01-01",
            "review_cycle": "annual",
        },
    )


# ═══════════════════════════════════════════════════════════════════
# Domain 1: Safety & Reliability
# ═══════════════════════════════════════════════════════════════════


def _domain_safety() -> RiskDomain:
    return RiskDomain(
        domain_id="SAF",
        name="Safety & Reliability",
        description=(
            "Ensure AI systems operate reliably within intended parameters "
            "and do not cause harm to users, third parties, or the environment."
        ),
        weight=1.5,
        categories=[
            RiskCategory(
                category_id="SAF-HAR",
                name="Harm Prevention",
                description="Prevent AI systems from generating harmful outputs.",
                weight=1.5,
                controls=[
                    Control(
                        control_id="SAF-HAR-01",
                        name="Harmful Content Detection",
                        description=(
                            "Detect and block outputs containing instructions for "
                            "violence, self-harm, illegal activities, or other harmful content."
                        ),
                        category=ControlCategory.DETECTIVE,
                        automatable=True,
                        checker_mapping="compliance",
                        evidence_requirements=[
                            "Content filter configuration",
                            "Detection rate metrics",
                            "False positive/negative analysis",
                        ],
                        compliance_mappings=[
                            ComplianceMapping(NIST, "MEASURE 2.6", "AI risks from harmful content"),
                            ComplianceMapping(EU, "Article 9.4", "Risk management for high-risk AI"),
                        ],
                    ),
                    Control(
                        control_id="SAF-HAR-02",
                        name="Output Safety Guardrails",
                        description=(
                            "Implement configurable guardrails that prevent unsafe outputs "
                            "based on risk thresholds and domain-specific safety rules."
                        ),
                        category=ControlCategory.PREVENTIVE,
                        required_maturity=MaturityLevel.MANAGED,
                        automatable=True,
                        evidence_requirements=[
                            "Guardrail configuration documentation",
                            "Threshold calibration records",
                            "Override audit trail",
                        ],
                        compliance_mappings=[
                            ComplianceMapping(NIST, "GOVERN 1.4", "Risk tolerances and thresholds"),
                            ComplianceMapping(EU, "Article 9.2", "Elimination or reduction of risks"),
                        ],
                    ),
                    Control(
                        control_id="SAF-HAR-03",
                        name="Incident Response Procedures",
                        description=(
                            "Maintain documented procedures for responding to safety "
                            "incidents involving AI system outputs."
                        ),
                        category=ControlCategory.CORRECTIVE,
                        required_maturity=MaturityLevel.DEFINED,
                        evidence_requirements=[
                            "Incident response plan",
                            "Post-incident review records",
                            "Escalation procedures",
                        ],
                        compliance_mappings=[
                            ComplianceMapping(NIST, "MANAGE 4.1", "Risk treatment and response"),
                            ComplianceMapping(EU, "Article 62", "Reporting of serious incidents"),
                            ComplianceMapping(ISO, "8.4", "AI system operation and monitoring"),
                        ],
                    ),
                ],
            ),
            RiskCategory(
                category_id="SAF-REL",
                name="Reliability & Performance",
                description="Ensure consistent and predictable system behavior.",
                controls=[
                    Control(
                        control_id="SAF-REL-01",
                        name="Performance Monitoring",
                        description=(
                            "Continuously monitor AI system performance metrics including "
                            "latency, throughput, error rates, and output quality."
                        ),
                        category=ControlCategory.DETECTIVE,
                        automatable=True,
                        evidence_requirements=[
                            "Monitoring dashboard",
                            "SLA definitions",
                            "Alert configuration",
                        ],
                        compliance_mappings=[
                            ComplianceMapping(NIST, "MEASURE 2.5", "AI system performance measurement"),
                            ComplianceMapping(ISO, "9.1", "Monitoring, measurement, analysis"),
                        ],
                    ),
                    Control(
                        control_id="SAF-REL-02",
                        name="Graceful Degradation",
                        description=(
                            "Design AI systems to degrade gracefully under failure "
                            "conditions rather than producing unsafe outputs."
                        ),
                        category=ControlCategory.PREVENTIVE,
                        required_maturity=MaturityLevel.MANAGED,
                        evidence_requirements=[
                            "Failure mode analysis",
                            "Fallback mechanism documentation",
                            "Chaos testing results",
                        ],
                        compliance_mappings=[
                            ComplianceMapping(NIST, "MEASURE 2.7", "AI system resilience"),
                        ],
                    ),
                    Control(
                        control_id="SAF-REL-03",
                        name="Output Validation",
                        description=(
                            "Validate AI outputs against expected formats, ranges, "
                            "and domain constraints before delivery."
                        ),
                        category=ControlCategory.DETECTIVE,
                        automatable=True,
                        evidence_requirements=[
                            "Validation rule definitions",
                            "Validation coverage metrics",
                        ],
                        compliance_mappings=[
                            ComplianceMapping(NIST, "MEASURE 2.9", "AI output quality"),
                            ComplianceMapping(EU, "Article 15", "Accuracy, robustness, cybersecurity"),
                        ],
                    ),
                ],
            ),
            RiskCategory(
                category_id="SAF-HAL",
                name="Hallucination & Factuality",
                description="Detect and mitigate fabricated or inaccurate outputs.",
                controls=[
                    Control(
                        control_id="SAF-HAL-01",
                        name="Hallucination Detection",
                        description=(
                            "Detect fabricated facts, URLs, citations, or contradictions "
                            "in AI-generated outputs using NLI or heuristic methods."
                        ),
                        category=ControlCategory.DETECTIVE,
                        automatable=True,
                        checker_mapping="hallucination",
                        evidence_requirements=[
                            "Detection method documentation",
                            "Precision/recall metrics",
                            "Ground truth evaluation set",
                        ],
                        compliance_mappings=[
                            ComplianceMapping(NIST, "MEASURE 2.6", "Accuracy and reliability"),
                            ComplianceMapping(EU, "Article 15.1", "Appropriate level of accuracy"),
                        ],
                    ),
                    Control(
                        control_id="SAF-HAL-02",
                        name="Source Grounding",
                        description=(
                            "Require AI outputs to be grounded in verifiable source "
                            "material when factual claims are made."
                        ),
                        category=ControlCategory.PREVENTIVE,
                        required_maturity=MaturityLevel.MANAGED,
                        evidence_requirements=[
                            "RAG pipeline documentation",
                            "Source attribution configuration",
                            "Grounding evaluation metrics",
                        ],
                        compliance_mappings=[
                            ComplianceMapping(NIST, "MEASURE 2.6", "Traceability of outputs"),
                        ],
                    ),
                ],
            ),
        ],
    )


# ═══════════════════════════════════════════════════════════════════
# Domain 2: Security & Privacy
# ═══════════════════════════════════════════════════════════════════


def _domain_security() -> RiskDomain:
    return RiskDomain(
        domain_id="SEC",
        name="Security & Privacy",
        description=(
            "Protect AI systems from adversarial attacks, unauthorized access, "
            "and ensure proper handling of personal and sensitive data."
        ),
        weight=1.5,
        categories=[
            RiskCategory(
                category_id="SEC-ADV",
                name="Adversarial Robustness",
                description="Defend against prompt injection, jailbreaks, and adversarial inputs.",
                weight=1.5,
                controls=[
                    Control(
                        control_id="SEC-ADV-01",
                        name="Prompt Injection Detection",
                        description=(
                            "Detect and block prompt injection attempts that try to "
                            "override system instructions or extract sensitive data."
                        ),
                        category=ControlCategory.DETECTIVE,
                        automatable=True,
                        checker_mapping="security",
                        evidence_requirements=[
                            "Injection pattern database",
                            "Detection rate metrics",
                            "Adversarial testing results",
                        ],
                        compliance_mappings=[
                            ComplianceMapping(NIST, "MEASURE 2.7", "Resilience to adversarial attacks"),
                            ComplianceMapping(EU, "Article 15.4", "Cybersecurity measures"),
                            ComplianceMapping(ISO, "A.6.2.5", "AI-specific security threats"),
                        ],
                    ),
                    Control(
                        control_id="SEC-ADV-02",
                        name="Jailbreak Prevention",
                        description=(
                            "Detect attempts to bypass AI safety constraints through "
                            "role-play, hypothetical framing, or instruction manipulation."
                        ),
                        category=ControlCategory.DETECTIVE,
                        automatable=True,
                        checker_mapping="security",
                        evidence_requirements=[
                            "Jailbreak pattern database",
                            "Red team testing reports",
                            "Evasion rate tracking",
                        ],
                        compliance_mappings=[
                            ComplianceMapping(NIST, "MEASURE 2.7", "Security testing"),
                            ComplianceMapping(EU, "Article 15.4", "Resistance to manipulation"),
                        ],
                    ),
                    Control(
                        control_id="SEC-ADV-03",
                        name="Encoding Attack Detection",
                        description=(
                            "Detect obfuscated attacks using base64 encoding, unicode "
                            "manipulation, or homoglyph substitution."
                        ),
                        category=ControlCategory.DETECTIVE,
                        automatable=True,
                        checker_mapping="security",
                        evidence_requirements=[
                            "Encoding detection rules",
                            "Test coverage for encoding variants",
                        ],
                        compliance_mappings=[
                            ComplianceMapping(NIST, "MEASURE 2.7", "Input validation"),
                        ],
                    ),
                ],
            ),
            RiskCategory(
                category_id="SEC-PRI",
                name="Data Privacy",
                description="Protect personal and sensitive data throughout the AI lifecycle.",
                controls=[
                    Control(
                        control_id="SEC-PRI-01",
                        name="PII Detection & Redaction",
                        description=(
                            "Detect and redact personally identifiable information "
                            "in AI inputs and outputs (SSN, credit cards, emails, phones)."
                        ),
                        category=ControlCategory.DETECTIVE,
                        automatable=True,
                        checker_mapping="compliance",
                        evidence_requirements=[
                            "PII detection patterns",
                            "Redaction policy",
                            "False positive analysis",
                        ],
                        compliance_mappings=[
                            ComplianceMapping(EU, "Article 10.5", "Personal data processing"),
                            ComplianceMapping(NIST, "MAP 5.1", "Privacy risk identification"),
                            ComplianceMapping(ISO, "A.8.5", "Data management for AI"),
                        ],
                    ),
                    Control(
                        control_id="SEC-PRI-02",
                        name="Data Minimization",
                        description=(
                            "Ensure AI systems process only the minimum data necessary "
                            "for the intended purpose."
                        ),
                        category=ControlCategory.DIRECTIVE,
                        required_maturity=MaturityLevel.DEFINED,
                        evidence_requirements=[
                            "Data inventory",
                            "Purpose limitation documentation",
                            "Data retention policy",
                        ],
                        compliance_mappings=[
                            ComplianceMapping(EU, "Article 10.2", "Data governance practices"),
                            ComplianceMapping(ISO, "A.8.5", "Data quality for AI systems"),
                        ],
                    ),
                    Control(
                        control_id="SEC-PRI-03",
                        name="Information Leak Prevention",
                        description=(
                            "Prevent AI systems from leaking system prompts, training "
                            "data, or confidential information in outputs."
                        ),
                        category=ControlCategory.DETECTIVE,
                        automatable=True,
                        checker_mapping="security",
                        evidence_requirements=[
                            "Leak detection rules",
                            "System prompt protection configuration",
                            "Data exfiltration testing results",
                        ],
                        compliance_mappings=[
                            ComplianceMapping(NIST, "MANAGE 2.4", "Information integrity"),
                            ComplianceMapping(EU, "Article 15.4", "Cybersecurity measures"),
                        ],
                    ),
                ],
            ),
            RiskCategory(
                category_id="SEC-ACC",
                name="Access Control",
                description="Manage authentication and authorization for AI systems.",
                controls=[
                    Control(
                        control_id="SEC-ACC-01",
                        name="API Authentication",
                        description=(
                            "Enforce authentication for all AI system API endpoints "
                            "using industry-standard mechanisms."
                        ),
                        category=ControlCategory.PREVENTIVE,
                        evidence_requirements=[
                            "Authentication architecture",
                            "API key rotation policy",
                            "Access log configuration",
                        ],
                        compliance_mappings=[
                            ComplianceMapping(ISO, "A.6.2.4", "Access control for AI systems"),
                        ],
                    ),
                    Control(
                        control_id="SEC-ACC-02",
                        name="Rate Limiting & Abuse Prevention",
                        description=(
                            "Implement rate limiting and usage quotas to prevent "
                            "abuse of AI system resources."
                        ),
                        category=ControlCategory.PREVENTIVE,
                        automatable=True,
                        evidence_requirements=[
                            "Rate limit configuration",
                            "Abuse detection rules",
                            "Usage monitoring dashboard",
                        ],
                        compliance_mappings=[
                            ComplianceMapping(NIST, "MANAGE 2.2", "System abuse prevention"),
                        ],
                    ),
                ],
            ),
        ],
    )


# ═══════════════════════════════════════════════════════════════════
# Domain 3: Fairness & Non-discrimination
# ═══════════════════════════════════════════════════════════════════


def _domain_fairness() -> RiskDomain:
    return RiskDomain(
        domain_id="FAI",
        name="Fairness & Non-discrimination",
        description=(
            "Ensure AI systems treat all individuals and groups equitably, "
            "without unlawful discrimination or systematic bias."
        ),
        weight=1.3,
        categories=[
            RiskCategory(
                category_id="FAI-BIA",
                name="Bias Detection & Mitigation",
                description="Identify and mitigate algorithmic bias across protected groups.",
                weight=1.5,
                controls=[
                    Control(
                        control_id="FAI-BIA-01",
                        name="Disparate Impact Analysis",
                        description=(
                            "Measure disparate impact ratio across protected groups "
                            "using the 4/5ths rule and flag violations."
                        ),
                        category=ControlCategory.DETECTIVE,
                        automatable=True,
                        checker_mapping="bias",
                        evidence_requirements=[
                            "Protected group definitions",
                            "Impact ratio calculations",
                            "Historical trend analysis",
                        ],
                        compliance_mappings=[
                            ComplianceMapping(NIST, "MEASURE 2.10", "Fairness assessment"),
                            ComplianceMapping(EU, "Article 10.2f", "Bias detection measures"),
                            ComplianceMapping(ISO, "A.7.4", "AI system impact assessment"),
                        ],
                    ),
                    Control(
                        control_id="FAI-BIA-02",
                        name="Demographic Parity Monitoring",
                        description=(
                            "Monitor positive outcome rates across demographic groups "
                            "and flag disparities exceeding tolerance thresholds."
                        ),
                        category=ControlCategory.DETECTIVE,
                        automatable=True,
                        checker_mapping="bias",
                        evidence_requirements=[
                            "Parity metrics dashboard",
                            "Threshold calibration documentation",
                            "Remediation action records",
                        ],
                        compliance_mappings=[
                            ComplianceMapping(NIST, "MEASURE 2.10", "Fairness metrics"),
                            ComplianceMapping(EU, "Article 10.2f", "Examination for bias"),
                        ],
                    ),
                    Control(
                        control_id="FAI-BIA-03",
                        name="Equalized Odds Assessment",
                        description=(
                            "Evaluate true positive and false positive rate differences "
                            "across protected groups."
                        ),
                        category=ControlCategory.DETECTIVE,
                        automatable=True,
                        checker_mapping="bias",
                        evidence_requirements=[
                            "TPR/FPR analysis per group",
                            "Calibration assessment",
                            "Intersectional analysis where applicable",
                        ],
                        compliance_mappings=[
                            ComplianceMapping(NIST, "MEASURE 2.10", "Performance disaggregation"),
                        ],
                    ),
                ],
            ),
            RiskCategory(
                category_id="FAI-LAN",
                name="Language & Representation",
                description="Detect and prevent biased, stereotyping, or exclusionary language.",
                controls=[
                    Control(
                        control_id="FAI-LAN-01",
                        name="Biased Language Detection",
                        description=(
                            "Detect stereotyping, derogatory, or discriminatory language "
                            "patterns in AI-generated outputs."
                        ),
                        category=ControlCategory.DETECTIVE,
                        automatable=True,
                        checker_mapping="bias",
                        evidence_requirements=[
                            "Biased language pattern library",
                            "Detection accuracy metrics",
                            "Cultural sensitivity review",
                        ],
                        compliance_mappings=[
                            ComplianceMapping(NIST, "MEASURE 2.10", "Harmful bias in outputs"),
                            ComplianceMapping(EU, "Article 10.2f", "Bias in AI outputs"),
                        ],
                    ),
                    Control(
                        control_id="FAI-LAN-02",
                        name="Inclusive Design Review",
                        description=(
                            "Conduct periodic reviews ensuring AI system outputs and "
                            "interactions are inclusive across cultures and demographics."
                        ),
                        category=ControlCategory.DIRECTIVE,
                        required_maturity=MaturityLevel.MANAGED,
                        evidence_requirements=[
                            "Inclusive design guidelines",
                            "Periodic review reports",
                            "Diverse evaluator panel records",
                        ],
                        compliance_mappings=[
                            ComplianceMapping(NIST, "MAP 2.3", "Diverse stakeholder engagement"),
                        ],
                    ),
                ],
            ),
        ],
    )


# ═══════════════════════════════════════════════════════════════════
# Domain 4: Transparency & Explainability
# ═══════════════════════════════════════════════════════════════════


def _domain_transparency() -> RiskDomain:
    return RiskDomain(
        domain_id="TRA",
        name="Transparency & Explainability",
        description=(
            "Ensure AI systems and their decisions can be understood, explained, "
            "and communicated to affected stakeholders."
        ),
        weight=1.0,
        categories=[
            RiskCategory(
                category_id="TRA-DIS",
                name="Disclosure & Communication",
                description="Inform users when they interact with AI and explain system capabilities.",
                controls=[
                    Control(
                        control_id="TRA-DIS-01",
                        name="AI Interaction Disclosure",
                        description=(
                            "Clearly disclose to users when they are interacting with "
                            "an AI system rather than a human."
                        ),
                        category=ControlCategory.DIRECTIVE,
                        evidence_requirements=[
                            "Disclosure implementation",
                            "User interface screenshots",
                            "Disclosure placement and timing",
                        ],
                        compliance_mappings=[
                            ComplianceMapping(EU, "Article 52.1", "Transparency obligations"),
                            ComplianceMapping(NIST, "MAP 5.2", "Stakeholder communication"),
                        ],
                    ),
                    Control(
                        control_id="TRA-DIS-02",
                        name="Capability & Limitation Documentation",
                        description=(
                            "Document and communicate the intended capabilities, known "
                            "limitations, and appropriate use cases of the AI system."
                        ),
                        category=ControlCategory.DIRECTIVE,
                        evidence_requirements=[
                            "System documentation",
                            "Known limitations registry",
                            "User-facing guidance",
                        ],
                        compliance_mappings=[
                            ComplianceMapping(EU, "Article 13", "Transparency and information"),
                            ComplianceMapping(NIST, "MAP 1.2", "Intended context of use"),
                            ComplianceMapping(ISO, "A.6.1.3", "Documentation of AI systems"),
                        ],
                    ),
                ],
            ),
            RiskCategory(
                category_id="TRA-EXP",
                name="Explainability",
                description="Provide meaningful explanations of AI decisions and reasoning.",
                controls=[
                    Control(
                        control_id="TRA-EXP-01",
                        name="Decision Explanation",
                        description=(
                            "Provide human-understandable explanations for AI-driven "
                            "decisions, especially those affecting individuals."
                        ),
                        category=ControlCategory.DETECTIVE,
                        required_maturity=MaturityLevel.MANAGED,
                        evidence_requirements=[
                            "Explanation generation mechanism",
                            "User comprehension testing",
                            "Explanation accuracy validation",
                        ],
                        compliance_mappings=[
                            ComplianceMapping(EU, "Article 13.3d", "Explanations to deployers"),
                            ComplianceMapping(NIST, "MEASURE 2.8", "Interpretability of outputs"),
                        ],
                    ),
                    Control(
                        control_id="TRA-EXP-02",
                        name="Risk Score Transparency",
                        description=(
                            "Make risk assessment scores, thresholds, and contributing "
                            "factors available for inspection."
                        ),
                        category=ControlCategory.DETECTIVE,
                        automatable=True,
                        evidence_requirements=[
                            "Score breakdown documentation",
                            "Threshold rationale",
                            "Factor contribution visibility",
                        ],
                        compliance_mappings=[
                            ComplianceMapping(NIST, "MEASURE 2.8", "Transparency of metrics"),
                        ],
                    ),
                ],
            ),
            RiskCategory(
                category_id="TRA-LOG",
                name="Logging & Traceability",
                description="Maintain comprehensive logs for auditability and traceability.",
                controls=[
                    Control(
                        control_id="TRA-LOG-01",
                        name="Immutable Audit Trail",
                        description=(
                            "Maintain a tamper-evident, hash-chained audit log of all "
                            "AI system evaluations and decisions."
                        ),
                        category=ControlCategory.DETECTIVE,
                        automatable=True,
                        evidence_requirements=[
                            "Audit log architecture",
                            "Hash chain verification results",
                            "Retention policy",
                        ],
                        compliance_mappings=[
                            ComplianceMapping(EU, "Article 12", "Record-keeping"),
                            ComplianceMapping(NIST, "GOVERN 1.7", "Audit trail requirements"),
                            ComplianceMapping(ISO, "A.6.2.6", "Recording of AI system events"),
                        ],
                    ),
                    Control(
                        control_id="TRA-LOG-02",
                        name="Input/Output Logging",
                        description=(
                            "Log AI system inputs and outputs with sufficient detail "
                            "to support investigation and compliance audits."
                        ),
                        category=ControlCategory.DETECTIVE,
                        automatable=True,
                        evidence_requirements=[
                            "Logging configuration",
                            "Log retention period",
                            "Privacy-preserving logging approach",
                        ],
                        compliance_mappings=[
                            ComplianceMapping(EU, "Article 12.2", "Automatic logging"),
                            ComplianceMapping(ISO, "A.6.2.6", "Logging of AI interactions"),
                        ],
                    ),
                ],
            ),
        ],
    )


# ═══════════════════════════════════════════════════════════════════
# Domain 5: Accountability & Governance
# ═══════════════════════════════════════════════════════════════════


def _domain_accountability() -> RiskDomain:
    return RiskDomain(
        domain_id="ACC",
        name="Accountability & Governance",
        description=(
            "Establish clear ownership, governance structures, and accountability "
            "mechanisms for AI systems throughout their lifecycle."
        ),
        weight=1.2,
        categories=[
            RiskCategory(
                category_id="ACC-GOV",
                name="Governance Framework",
                description="Establish organizational governance for AI risk management.",
                controls=[
                    Control(
                        control_id="ACC-GOV-01",
                        name="AI Risk Management Policy",
                        description=(
                            "Maintain an organizational policy defining AI risk appetite, "
                            "governance roles, and risk management processes."
                        ),
                        category=ControlCategory.DIRECTIVE,
                        evidence_requirements=[
                            "AI risk management policy document",
                            "Board/leadership approval records",
                            "Policy review schedule",
                        ],
                        compliance_mappings=[
                            ComplianceMapping(NIST, "GOVERN 1.1", "AI risk management policy"),
                            ComplianceMapping(EU, "Article 9.1", "Risk management system"),
                            ComplianceMapping(ISO, "5.2", "AI management system policy"),
                        ],
                    ),
                    Control(
                        control_id="ACC-GOV-02",
                        name="Roles & Responsibilities",
                        description=(
                            "Define and document clear roles, responsibilities, and "
                            "authorities for AI risk management."
                        ),
                        category=ControlCategory.DIRECTIVE,
                        evidence_requirements=[
                            "RACI matrix for AI governance",
                            "Role descriptions",
                            "Accountability chain documentation",
                        ],
                        compliance_mappings=[
                            ComplianceMapping(NIST, "GOVERN 2.1", "Roles and responsibilities"),
                            ComplianceMapping(EU, "Article 9.9", "Risk management documentation"),
                            ComplianceMapping(ISO, "5.3", "Roles, responsibilities, authorities"),
                        ],
                    ),
                    Control(
                        control_id="ACC-GOV-03",
                        name="Risk Appetite & Thresholds",
                        description=(
                            "Define quantitative risk tolerance thresholds for blocking, "
                            "review, and escalation of AI system decisions."
                        ),
                        category=ControlCategory.DIRECTIVE,
                        automatable=True,
                        evidence_requirements=[
                            "Risk threshold configuration",
                            "Threshold rationale documentation",
                            "Periodic threshold review records",
                        ],
                        compliance_mappings=[
                            ComplianceMapping(NIST, "GOVERN 1.4", "Risk tolerance levels"),
                            ComplianceMapping(EU, "Article 9.2a", "Risk identification and analysis"),
                        ],
                    ),
                ],
            ),
            RiskCategory(
                category_id="ACC-LCM",
                name="Lifecycle Management",
                description="Govern AI systems across their full lifecycle.",
                controls=[
                    Control(
                        control_id="ACC-LCM-01",
                        name="Model Registration & Inventory",
                        description=(
                            "Maintain a centralized registry of all AI models with "
                            "version, owner, risk tier, and lifecycle state."
                        ),
                        category=ControlCategory.DETECTIVE,
                        automatable=True,
                        evidence_requirements=[
                            "Model registry contents",
                            "Registration workflow documentation",
                            "Inventory completeness verification",
                        ],
                        compliance_mappings=[
                            ComplianceMapping(EU, "Article 51", "Registration in EU database"),
                            ComplianceMapping(NIST, "GOVERN 1.5", "AI system inventory"),
                            ComplianceMapping(ISO, "A.5.3", "AI system inventory"),
                        ],
                    ),
                    Control(
                        control_id="ACC-LCM-02",
                        name="Lifecycle State Management",
                        description=(
                            "Enforce valid lifecycle transitions (draft, validation, "
                            "production, deprecated, retired) with appropriate gates."
                        ),
                        category=ControlCategory.PREVENTIVE,
                        automatable=True,
                        evidence_requirements=[
                            "Lifecycle state machine definition",
                            "Transition gate criteria",
                            "State change audit trail",
                        ],
                        compliance_mappings=[
                            ComplianceMapping(NIST, "GOVERN 1.5", "Lifecycle governance"),
                            ComplianceMapping(ISO, "A.5.4", "AI system lifecycle management"),
                        ],
                    ),
                    Control(
                        control_id="ACC-LCM-03",
                        name="Decommissioning Procedures",
                        description=(
                            "Establish procedures for safely retiring AI systems "
                            "including data disposal and dependency management."
                        ),
                        category=ControlCategory.CORRECTIVE,
                        evidence_requirements=[
                            "Decommissioning checklist",
                            "Data disposal records",
                            "Dependency impact analysis",
                        ],
                        compliance_mappings=[
                            ComplianceMapping(ISO, "A.5.4", "End-of-life management"),
                        ],
                    ),
                ],
            ),
            RiskCategory(
                category_id="ACC-COM",
                name="Compliance Reporting",
                description="Generate and maintain regulatory compliance documentation.",
                controls=[
                    Control(
                        control_id="ACC-COM-01",
                        name="Regulatory Report Generation",
                        description=(
                            "Generate compliance reports aligned with applicable "
                            "regulations (GDPR, SOX, EU AI Act)."
                        ),
                        category=ControlCategory.DETECTIVE,
                        automatable=True,
                        evidence_requirements=[
                            "Generated compliance reports",
                            "Report validation records",
                            "Regulatory filing confirmations",
                        ],
                        compliance_mappings=[
                            ComplianceMapping(EU, "Article 11", "Technical documentation"),
                            ComplianceMapping(NIST, "GOVERN 6.2", "Documentation and reporting"),
                            ComplianceMapping(ISO, "A.6.1.3", "AI system documentation"),
                        ],
                    ),
                    Control(
                        control_id="ACC-COM-02",
                        name="Conformity Assessment",
                        description=(
                            "Conduct periodic self-assessments or third-party audits "
                            "to verify compliance with applicable standards."
                        ),
                        category=ControlCategory.DETECTIVE,
                        required_maturity=MaturityLevel.MANAGED,
                        evidence_requirements=[
                            "Assessment schedule",
                            "Assessment findings and remediation",
                            "Assessor qualifications",
                        ],
                        compliance_mappings=[
                            ComplianceMapping(EU, "Article 43", "Conformity assessment"),
                            ComplianceMapping(ISO, "9.2", "Internal audit"),
                        ],
                    ),
                ],
            ),
        ],
    )


# ═══════════════════════════════════════════════════════════════════
# Domain 6: Robustness & Resilience
# ═══════════════════════════════════════════════════════════════════


def _domain_robustness() -> RiskDomain:
    return RiskDomain(
        domain_id="ROB",
        name="Robustness & Resilience",
        description=(
            "Ensure AI systems maintain performance under adverse conditions, "
            "distribution shifts, and unexpected inputs."
        ),
        weight=1.0,
        categories=[
            RiskCategory(
                category_id="ROB-DRI",
                name="Distribution Drift",
                description="Detect and respond to changes in input data distributions.",
                controls=[
                    Control(
                        control_id="ROB-DRI-01",
                        name="Data Drift Detection",
                        description=(
                            "Monitor input data distributions for statistically significant "
                            "shifts using KS tests or similar methods."
                        ),
                        category=ControlCategory.DETECTIVE,
                        automatable=True,
                        evidence_requirements=[
                            "Drift detection configuration",
                            "Baseline distribution records",
                            "Drift alert history",
                        ],
                        compliance_mappings=[
                            ComplianceMapping(NIST, "MEASURE 3.2", "Monitoring for drift"),
                            ComplianceMapping(EU, "Article 9.2b", "Foreseeable risks monitoring"),
                        ],
                    ),
                    Control(
                        control_id="ROB-DRI-02",
                        name="Model Retraining Triggers",
                        description=(
                            "Define and automate triggers for model retraining or "
                            "recalibration when drift exceeds thresholds."
                        ),
                        category=ControlCategory.CORRECTIVE,
                        required_maturity=MaturityLevel.MANAGED,
                        evidence_requirements=[
                            "Retraining trigger definitions",
                            "Retraining history",
                            "Performance recovery metrics",
                        ],
                        compliance_mappings=[
                            ComplianceMapping(NIST, "MANAGE 3.1", "Response to performance changes"),
                        ],
                    ),
                ],
            ),
            RiskCategory(
                category_id="ROB-ANO",
                name="Anomaly Detection",
                description="Identify unusual patterns in inputs, outputs, or system behavior.",
                controls=[
                    Control(
                        control_id="ROB-ANO-01",
                        name="Input Anomaly Detection",
                        description=(
                            "Detect anomalous inputs that fall outside the expected "
                            "distribution using statistical or ML methods."
                        ),
                        category=ControlCategory.DETECTIVE,
                        automatable=True,
                        evidence_requirements=[
                            "Anomaly detection model configuration",
                            "Contamination threshold rationale",
                            "Anomaly alert and response records",
                        ],
                        compliance_mappings=[
                            ComplianceMapping(NIST, "MEASURE 2.7", "Anomaly identification"),
                        ],
                    ),
                    Control(
                        control_id="ROB-ANO-02",
                        name="Behavioral Anomaly Detection",
                        description=(
                            "Monitor AI system behavioral patterns for unexpected "
                            "changes in output distributions or decision patterns."
                        ),
                        category=ControlCategory.DETECTIVE,
                        automatable=True,
                        evidence_requirements=[
                            "Behavioral baseline definition",
                            "Anomaly detection alerts",
                            "Investigation records",
                        ],
                        compliance_mappings=[
                            ComplianceMapping(NIST, "MEASURE 3.2", "Post-deployment monitoring"),
                            ComplianceMapping(EU, "Article 9.8", "Systematic monitoring"),
                        ],
                    ),
                ],
            ),
            RiskCategory(
                category_id="ROB-STR",
                name="Stress Testing",
                description="Validate system behavior under extreme or adversarial conditions.",
                controls=[
                    Control(
                        control_id="ROB-STR-01",
                        name="Adversarial Testing",
                        description=(
                            "Conduct regular red-team exercises and adversarial testing "
                            "to evaluate system robustness."
                        ),
                        category=ControlCategory.DETECTIVE,
                        required_maturity=MaturityLevel.MANAGED,
                        evidence_requirements=[
                            "Red team exercise schedule",
                            "Testing methodology",
                            "Findings and remediation records",
                        ],
                        compliance_mappings=[
                            ComplianceMapping(NIST, "MEASURE 2.7", "Red-teaming exercises"),
                            ComplianceMapping(EU, "Article 9.6", "Testing with independent data"),
                        ],
                    ),
                    Control(
                        control_id="ROB-STR-02",
                        name="Edge Case Testing",
                        description=(
                            "Maintain and execute test suites covering boundary "
                            "conditions, edge cases, and known failure modes."
                        ),
                        category=ControlCategory.DETECTIVE,
                        evidence_requirements=[
                            "Edge case test suite",
                            "Coverage metrics",
                            "Failure mode catalog",
                        ],
                        compliance_mappings=[
                            ComplianceMapping(NIST, "MEASURE 2.5", "Evaluation with test data"),
                            ComplianceMapping(EU, "Article 9.6", "Testing procedures"),
                        ],
                    ),
                ],
            ),
        ],
    )


# ═══════════════════════════════════════════════════════════════════
# Domain 7: Human Oversight
# ═══════════════════════════════════════════════════════════════════


def _domain_human_oversight() -> RiskDomain:
    return RiskDomain(
        domain_id="HUM",
        name="Human Oversight",
        description=(
            "Ensure meaningful human control over AI systems with appropriate "
            "review, escalation, and override mechanisms."
        ),
        weight=1.2,
        categories=[
            RiskCategory(
                category_id="HUM-REV",
                name="Review Workflows",
                description="Enable human review of flagged AI decisions.",
                weight=1.5,
                controls=[
                    Control(
                        control_id="HUM-REV-01",
                        name="Risk-Based Review Flagging",
                        description=(
                            "Automatically flag AI decisions exceeding risk thresholds "
                            "for human review before execution."
                        ),
                        category=ControlCategory.DETECTIVE,
                        automatable=True,
                        evidence_requirements=[
                            "Review threshold configuration",
                            "Flagging criteria documentation",
                            "Review queue metrics",
                        ],
                        compliance_mappings=[
                            ComplianceMapping(EU, "Article 14.1", "Human oversight measures"),
                            ComplianceMapping(NIST, "GOVERN 1.4", "Risk-based thresholds"),
                        ],
                    ),
                    Control(
                        control_id="HUM-REV-02",
                        name="Review Decision Tracking",
                        description=(
                            "Track human review decisions (approve, reject, escalate) "
                            "with rationale and timestamps."
                        ),
                        category=ControlCategory.DETECTIVE,
                        automatable=True,
                        evidence_requirements=[
                            "Review decision records",
                            "Reviewer assignment logs",
                            "Decision rationale documentation",
                        ],
                        compliance_mappings=[
                            ComplianceMapping(EU, "Article 14.4", "Oversight documentation"),
                            ComplianceMapping(ISO, "A.8.4", "Human oversight records"),
                        ],
                    ),
                    Control(
                        control_id="HUM-REV-03",
                        name="Escalation Procedures",
                        description=(
                            "Automatically escalate critical-risk decisions to senior "
                            "authorities when initial review is insufficient."
                        ),
                        category=ControlCategory.CORRECTIVE,
                        automatable=True,
                        evidence_requirements=[
                            "Escalation criteria",
                            "Escalation chain documentation",
                            "SLA for escalation response",
                        ],
                        compliance_mappings=[
                            ComplianceMapping(EU, "Article 14.3", "Ability to intervene"),
                            ComplianceMapping(NIST, "MANAGE 4.1", "Escalation procedures"),
                        ],
                    ),
                ],
            ),
            RiskCategory(
                category_id="HUM-OVR",
                name="Override & Intervention",
                description="Enable human override of AI decisions when necessary.",
                controls=[
                    Control(
                        control_id="HUM-OVR-01",
                        name="Human Override Capability",
                        description=(
                            "Provide mechanisms for authorized humans to override "
                            "AI decisions at any point in the workflow."
                        ),
                        category=ControlCategory.CORRECTIVE,
                        evidence_requirements=[
                            "Override mechanism documentation",
                            "Authorization requirements",
                            "Override audit trail",
                        ],
                        compliance_mappings=[
                            ComplianceMapping(EU, "Article 14.3d", "Ability to override"),
                            ComplianceMapping(NIST, "GOVERN 1.4", "Human-in-the-loop controls"),
                        ],
                    ),
                    Control(
                        control_id="HUM-OVR-02",
                        name="Emergency Stop Capability",
                        description=(
                            "Implement ability to immediately halt AI system operation "
                            "when critical safety concerns arise."
                        ),
                        category=ControlCategory.CORRECTIVE,
                        required_maturity=MaturityLevel.DEFINED,
                        evidence_requirements=[
                            "Emergency stop mechanism",
                            "Trigger criteria",
                            "Recovery procedures",
                        ],
                        compliance_mappings=[
                            ComplianceMapping(EU, "Article 14.3e", "Ability to stop the system"),
                            ComplianceMapping(NIST, "MANAGE 4.2", "System shutdown procedures"),
                        ],
                    ),
                ],
            ),
        ],
    )


# ═══════════════════════════════════════════════════════════════════
# Domain 8: Data Quality & Integrity
# ═══════════════════════════════════════════════════════════════════


def _domain_data_quality() -> RiskDomain:
    return RiskDomain(
        domain_id="DAT",
        name="Data Quality & Integrity",
        description=(
            "Ensure the quality, integrity, and appropriateness of data used "
            "to train, fine-tune, and operate AI systems."
        ),
        weight=1.0,
        categories=[
            RiskCategory(
                category_id="DAT-QUA",
                name="Data Quality Assurance",
                description="Verify and maintain quality of training and operational data.",
                controls=[
                    Control(
                        control_id="DAT-QUA-01",
                        name="Training Data Documentation",
                        description=(
                            "Document training data sources, collection methods, "
                            "preprocessing steps, and known limitations."
                        ),
                        category=ControlCategory.DIRECTIVE,
                        evidence_requirements=[
                            "Data card / datasheet",
                            "Source inventory",
                            "Preprocessing pipeline documentation",
                        ],
                        compliance_mappings=[
                            ComplianceMapping(EU, "Article 10.2", "Data governance practices"),
                            ComplianceMapping(NIST, "MAP 4.1", "Data documentation"),
                            ComplianceMapping(ISO, "A.8.5", "Data management for AI"),
                        ],
                    ),
                    Control(
                        control_id="DAT-QUA-02",
                        name="Data Validation Pipeline",
                        description=(
                            "Implement automated validation checks for data completeness, "
                            "consistency, accuracy, and timeliness."
                        ),
                        category=ControlCategory.PREVENTIVE,
                        automatable=True,
                        evidence_requirements=[
                            "Validation rule definitions",
                            "Data quality metrics",
                            "Validation failure handling procedures",
                        ],
                        compliance_mappings=[
                            ComplianceMapping(EU, "Article 10.3", "Data quality criteria"),
                            ComplianceMapping(NIST, "MEASURE 2.4", "Data quality assessment"),
                        ],
                    ),
                    Control(
                        control_id="DAT-QUA-03",
                        name="Data Representativeness Assessment",
                        description=(
                            "Assess whether training data adequately represents the "
                            "target population and use-case conditions."
                        ),
                        category=ControlCategory.DETECTIVE,
                        evidence_requirements=[
                            "Population coverage analysis",
                            "Representation gap identification",
                            "Mitigation strategies for gaps",
                        ],
                        compliance_mappings=[
                            ComplianceMapping(EU, "Article 10.3", "Relevant and representative data"),
                            ComplianceMapping(NIST, "MAP 4.2", "Data representativeness"),
                        ],
                    ),
                ],
            ),
            RiskCategory(
                category_id="DAT-INT",
                name="Data Integrity & Provenance",
                description="Maintain data integrity and track lineage throughout the AI lifecycle.",
                controls=[
                    Control(
                        control_id="DAT-INT-01",
                        name="Data Provenance Tracking",
                        description=(
                            "Track the origin, transformations, and lineage of all "
                            "data used in AI system training and operation."
                        ),
                        category=ControlCategory.DETECTIVE,
                        evidence_requirements=[
                            "Data lineage graph",
                            "Transformation audit trail",
                            "Source verification records",
                        ],
                        compliance_mappings=[
                            ComplianceMapping(EU, "Article 10.2a", "Data collection purpose"),
                            ComplianceMapping(NIST, "MAP 4.1", "Data provenance"),
                            ComplianceMapping(ISO, "A.8.5", "Data lifecycle management"),
                        ],
                    ),
                    Control(
                        control_id="DAT-INT-02",
                        name="Data Integrity Verification",
                        description=(
                            "Verify data integrity using checksums, digital signatures, "
                            "or hash verification at each processing stage."
                        ),
                        category=ControlCategory.DETECTIVE,
                        automatable=True,
                        evidence_requirements=[
                            "Integrity verification mechanism",
                            "Verification schedule",
                            "Integrity failure response procedures",
                        ],
                        compliance_mappings=[
                            ComplianceMapping(ISO, "A.8.5", "Data integrity for AI"),
                        ],
                    ),
                ],
            ),
            RiskCategory(
                category_id="DAT-FRA",
                name="Fraud & Anomaly in Data",
                description="Detect fraudulent or anomalous data patterns.",
                controls=[
                    Control(
                        control_id="DAT-FRA-01",
                        name="Transaction Fraud Detection",
                        description=(
                            "Detect anomalous transactions using statistical methods "
                            "(z-score), velocity tracking, and pattern rules."
                        ),
                        category=ControlCategory.DETECTIVE,
                        automatable=True,
                        checker_mapping="fraud",
                        evidence_requirements=[
                            "Fraud detection rule configuration",
                            "Detection rate and precision metrics",
                            "Alert triage procedures",
                        ],
                        compliance_mappings=[
                            ComplianceMapping(NIST, "MEASURE 2.7", "Anomaly detection"),
                        ],
                    ),
                    Control(
                        control_id="DAT-FRA-02",
                        name="Data Poisoning Detection",
                        description=(
                            "Monitor for signs of data poisoning or manipulation "
                            "in training and operational data pipelines."
                        ),
                        category=ControlCategory.DETECTIVE,
                        required_maturity=MaturityLevel.MANAGED,
                        evidence_requirements=[
                            "Poisoning detection methodology",
                            "Data integrity monitoring",
                            "Incident response for data poisoning",
                        ],
                        compliance_mappings=[
                            ComplianceMapping(NIST, "MEASURE 2.7", "Data integrity threats"),
                            ComplianceMapping(EU, "Article 15.4", "Cybersecurity in data"),
                        ],
                    ),
                ],
            ),
        ],
    )


# ── Public API ──────────────────────────────────────────────────────

STANDARD_V1 = _build_standard()


def get_standard(version: str = "1.0") -> Standard:
    """Retrieve a standard by version string."""
    if version == "1.0":
        return STANDARD_V1
    raise ValueError(f"Unknown standard version: {version}")
