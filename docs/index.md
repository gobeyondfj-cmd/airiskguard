---
hide:
  - navigation
  - toc
---

<style>
.md-content__button { display: none; }
.hero { text-align: center; padding: 2rem 0 3rem; }
.hero h1 { font-size: 2.8rem; font-weight: 800; margin-bottom: 0.5rem; }
.hero .tagline { font-size: 1.3rem; color: var(--md-default-fg-color--light); margin-bottom: 2rem; }
.hero .buttons { display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap; }
.hero .buttons a {
  display: inline-block; padding: 0.8rem 2rem; border-radius: 8px;
  font-weight: 600; text-decoration: none; font-size: 1rem;
}
.hero .btn-primary {
  background: var(--md-primary-fg-color); color: white;
}
.hero .btn-secondary {
  border: 2px solid var(--md-primary-fg-color); color: var(--md-primary-fg-color);
}
.features { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.5rem; padding: 2rem 0; }
.feature-card { padding: 1.5rem; border-radius: 12px; border: 1px solid var(--md-default-fg-color--lightest); }
.feature-card h3 { margin-top: 0.5rem; }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 1rem; padding: 2rem 0; text-align: center; }
.stat { padding: 1.5rem; }
.stat .number { font-size: 2.5rem; font-weight: 800; color: var(--md-primary-fg-color); }
.stat .label { font-size: 0.9rem; color: var(--md-default-fg-color--light); }
.section-title { text-align: center; padding: 2rem 0 1rem; }
.section-title h2 { font-size: 2rem; }
</style>

<div class="hero" markdown>

# airiskguard

<p class="tagline">
AI Risk Governance Framework — standards, guardrails, and compliance for AI systems.
</p>

<div class="buttons">
<a href="standard/ai-risk-management-standard-v1/" class="btn-primary">Read the Standard</a>
<a href="framework/getting-started/" class="btn-secondary">Get Started</a>
</div>

</div>

---

<div class="section-title" markdown>

## The first machine-enforceable AI risk standard

AIRMS v1.0 defines 53 controls across 8 risk domains — each one both human-readable and programmatically assessable. Map your compliance across NIST AI RMF, EU AI Act, and ISO/IEC 42001 from a single framework.

</div>

<div class="stats" markdown>

<div class="stat">
<div class="number">53</div>
<div class="label">Controls</div>
</div>

<div class="stat">
<div class="number">8</div>
<div class="label">Risk Domains</div>
</div>

<div class="stat">
<div class="number">3</div>
<div class="label">Framework Mappings</div>
</div>

<div class="stat">
<div class="number">58%</div>
<div class="label">Automatable</div>
</div>

</div>

---

<div class="section-title" markdown>

## What airiskguard does

</div>

<div class="features" markdown>

<div class="feature-card" markdown>

### Risk Guardrails

Detect prompt injection, jailbreaks, PII leakage, hallucinations, bias, and fraud in real-time. Pre-check inputs, post-check outputs.

</div>

<div class="feature-card" markdown>

### Standards-Based Assessment

Assess AI systems against AIRMS v1.0 with structured maturity scoring, gap analysis, and prioritized recommendations.

</div>

<div class="feature-card" markdown>

### Compliance Mapping

Map controls to NIST AI RMF (46 mappings), EU AI Act (38 mappings), and ISO/IEC 42001 (21 mappings) automatically.

</div>

<div class="feature-card" markdown>

### Immutable Audit Trail

SHA-256 hash-chained audit log for every AI decision. Tamper-evident, verifiable, and ready for regulatory review.

</div>

<div class="feature-card" markdown>

### Human Oversight

Risk-based flagging, review workflows, escalation procedures, and override capabilities built in.

</div>

<div class="feature-card" markdown>

### Framework Integration

Drop-in middleware for FastAPI, Flask, ASGI, and WSGI. Decorator pattern for any Python function.

</div>

</div>

---

<div class="section-title" markdown>

## Quick Start

</div>

Install from PyPI:

```bash
pip install airiskguard
```

Guard an LLM call:

```python
from airiskguard import RiskGuard

guard = RiskGuard()

# Pre-check user input
pre = await guard.evaluate(
    input_data=user_message,
    output_data="",
    model_id="gpt-4",
    checks=["security", "compliance"],
)
if pre.blocked:
    return "Sorry, I can't process that request."

# ... call your LLM ...

# Post-check AI output
post = await guard.evaluate(
    input_data=user_message,
    output_data=llm_response,
    model_id="gpt-4",
    checks=["hallucination", "compliance"],
)
```

Assess against the standard:

```python
from airiskguard.standards import STANDARD_V1, StandardAssessor

assessor = StandardAssessor(STANDARD_V1)
assessor.set_control_status("ACC-GOV-01", implemented=True, maturity=3)
assessor.apply_checker_results(report)

result = assessor.assess(model_id="my-model")
print(result.summary())
```

<div style="text-align: center; padding: 2rem 0;" markdown>

[Read the Full Standard](standard/ai-risk-management-standard-v1.md){ .md-button .md-button--primary }
[View on GitHub](https://github.com/gobeyondfj-cmd/airiskguard){ .md-button }
[Install from PyPI](https://pypi.org/project/airiskguard/){ .md-button }

</div>
