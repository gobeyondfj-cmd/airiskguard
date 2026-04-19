# AI Risk Trends

*Updated monthly by the airiskguard team. Last update: **April 2026**.*

This page tracks the global AI risk landscape — incident volumes, emerging threat vectors, regulatory milestones, and what they mean for teams building and deploying AI systems.

---

## April 2026 snapshot

### Incident volume

| Metric | 2024 | 2025 | Change |
|---|---|---|---|
| AI incidents (AI Incident Database) | 233 | 362 | +55% YoY |
| Foundation Model Transparency Index | 58 | 40 | -31% |
| Orgs with formal AI governance framework | — | 36% | — |
| Orgs reporting unsanctioned AI tool usage | — | 98% | — |

### Top threat vectors this month

1. **Agentic AI exploitation** — autonomous agents with tool access are the new attack surface. A March 2026 breach saw a SQL injection via an AI agent expose millions of records within two hours of deployment.
2. **Multi-turn jailbreaks** — single-turn safety filters are being bypassed via 3–5 message sequences that gradually shift model behaviour.
3. **Prompt injection via tool outputs** — malicious content in tool responses (web search results, database rows) hijacks agent instructions.
4. **Credential enumeration** — agents with broad permissions are being probed to enumerate API keys, secrets, and database credentials.
5. **Model transparency collapse** — the Foundation Model Transparency Index dropped 31% in one year, making third-party risk assessment harder.

### Regulatory milestones

| Date | Event |
|---|---|
| Feb 2026 | EU AI Act GPAI transparency obligations in force |
| **Aug 2, 2026** | EU AI Act high-risk system deadline (7% revenue penalty) |
| 2026 ongoing | Illinois HB 3773 — bias testing for employment AI |
| 2026 ongoing | India — 2-hour deepfake takedown mandate |
| 2026 ongoing | Colorado, Texas, Virginia — state-level AI bias laws |

### Key findings from recent reports

- **Stanford HAI 2026**: Safety benchmarks are reported for fewer models than capability benchmarks — teams can compare reasoning but not safety.
- **MIT AI Governance Audit**: Socioeconomic risks (economic devaluation, power centralization) and multi-agent risks receive the least governance attention.
- **FINRA 2026**: Financial sector now requires structured audit trails for every AI-generated recommendation.
- **helpnetsecurity.com**: Most models are released via restricted APIs, preventing independent safety validation.

---

## March 2026 snapshot

### Top threats

1. Prompt injection attacks up 40% vs Q4 2025
2. PII leakage in RAG pipelines — retrieval returning sensitive documents to unauthorized users
3. Hallucination in financial summaries — incorrect figures cited as fact in analyst reports

### Regulatory milestones

| Date | Event |
|---|---|
| Mar 2026 | EU AI Office begins accepting GPAI model documentation |
| Mar 2026 | NIST AI RMF 1.1 draft published for comment |

---

## How to use this data

These trends directly inform airiskguard's checker priorities and benchmark datasets. When a new threat vector appears here, it gets added to:

- The **benchmark dataset** (`airiskguard-benchmark --checkers agent`)
- The **agent checker** patterns (`src/airiskguard/checkers/agent.py`)
- The **standard** (`docs/standard/ai-risk-management-standard-v1.md`)

If you spot a trend we've missed, [open an issue](https://github.com/gobeyondfj-cmd/airiskguard/issues) or email [research@airiskguard.ai](mailto:research@airiskguard.ai).

---

## Sources

- [AI Adoption Outpacing Safeguards — helpnetsecurity.com](https://www.helpnetsecurity.com/2026/04/14/ai-adoption-safety-transparency-report/)
- [AI Governance Regulatory Deadline & Security Breaches — thenextgentechinsider.com](https://www.thenextgentechinsider.com/pulse/ai-governance-faces-urgent-regulatory-deadline-amid-security-breaches)
- [MIT AI Governance Landscape Audit — airisk.mit.edu](https://airisk.mit.edu/blog/mapping-the-ai-governance-landscape-april-2026-update)
- [AI Compliance Checklist 2026 — neuraltrust.ai](https://neuraltrust.ai/blog/ai-compliance-checklist-2026)
- [EU AI Act 2026 Compliance — secureprivacy.io](https://secureprivacy.io/blog/eu-ai-act-2026-compliance)
- [Stanford HAI AI Index 2026 — The Register](https://www.theregister.com/2026/04/14/ai_report_2026_stanford_hai/)
