---
hide:
  - navigation
  - toc
---

<style>
.md-content__button { display: none; }

/* Hero */
.hero { text-align: center; padding: 2rem 0 3rem; }
.hero h1 { font-size: 2.8rem; font-weight: 800; margin-bottom: 0.5rem; }
.hero h1 .headerlink, .hero h1 a.headerlink { display: none !important; }
.hero h2 .headerlink, .hero h2 a.headerlink { display: none !important; }
.section-title h2 .headerlink, .section-title h2 a.headerlink { display: none !important; }
.hero .tagline { font-size: 1.3rem; color: var(--md-default-fg-color--light); margin-bottom: 2rem; }
.hero .buttons { display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap; }
.hero .buttons a {
  display: inline-block; padding: 0.8rem 2rem; border-radius: 8px;
  font-weight: 600; text-decoration: none; font-size: 1rem;
}
.hero .btn-primary { background: var(--md-primary-fg-color); color: white; }
.hero .btn-secondary { border: 2px solid var(--md-primary-fg-color); color: var(--md-primary-fg-color); }

/* Gateway banner */
.gateway-banner {
  background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 100%);
  color: white;
  border-radius: 12px;
  padding: 2.5rem 2rem;
  margin: 2rem 0;
  text-align: center;
}
.gateway-banner h2 { color: white; font-size: 1.8rem; margin-bottom: 0.5rem; border: none; }
.gateway-banner p { color: #94a3b8; margin-bottom: 1.5rem; font-size: 1.05rem; }
.gateway-banner .btn-gw {
  display: inline-block; padding: 0.75rem 2rem; border-radius: 8px;
  font-weight: 600; text-decoration: none; font-size: 1rem;
  background: #3b82f6; color: white; margin: 0.25rem;
}
.gateway-banner .btn-gw-outline {
  display: inline-block; padding: 0.75rem 2rem; border-radius: 8px;
  font-weight: 600; text-decoration: none; font-size: 1rem;
  border: 2px solid #3b82f6; color: #93c5fd; margin: 0.25rem;
}

/* Pricing */
.pricing-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 1.5rem;
  padding: 2rem 0;
}
.pricing-card {
  border-radius: 12px;
  border: 1px solid var(--md-default-fg-color--lightest);
  padding: 2rem 1.5rem;
  position: relative;
}
.pricing-card.featured {
  border: 2px solid var(--md-primary-fg-color);
}
.pricing-card .badge {
  position: absolute;
  top: -12px;
  left: 50%;
  transform: translateX(-50%);
  background: var(--md-primary-fg-color);
  color: white;
  font-size: 0.75rem;
  font-weight: 700;
  padding: 2px 12px;
  border-radius: 999px;
  white-space: nowrap;
}
.pricing-card h3 { margin-top: 0; font-size: 1.3rem; }
.pricing-card .price { font-size: 2rem; font-weight: 800; color: var(--md-primary-fg-color); margin: 0.5rem 0; }
.pricing-card .price span { font-size: 1rem; font-weight: 400; color: var(--md-default-fg-color--light); }
.pricing-card ul { padding-left: 1.2rem; margin: 1rem 0; }
.pricing-card ul li { margin-bottom: 0.4rem; font-size: 0.9rem; }
.pricing-card .cta {
  display: block; text-align: center; padding: 0.7rem 1rem; border-radius: 8px;
  font-weight: 600; text-decoration: none; margin-top: 1.5rem; font-size: 0.95rem;
}
.pricing-card .cta-primary { background: var(--md-primary-fg-color); color: white; }
.pricing-card .cta-outline { border: 2px solid var(--md-primary-fg-color); color: var(--md-primary-fg-color); }

/* Features */
.features { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1.5rem; padding: 2rem 0; }
.feature-card { padding: 1.5rem; border-radius: 12px; border: 1px solid var(--md-default-fg-color--lightest); }
.feature-card h3 { margin-top: 0.5rem; }

/* Stats */
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
AI Risk Governance for LLM applications, AI agents, and developer AI coding tools.
</p>

<div class="buttons">
<a href="gateway/index.md" class="btn-primary">Enterprise Gateway</a>
<a href="framework/getting-started.md" class="btn-secondary">Get Started Free</a>
</div>

</div>

---

<div class="gateway-banner" markdown>

## Enterprise AI Coding Gateway — Now Available

Stop secrets, PII, and proprietary code from leaving your network via Claude Code, Codex CLI, and Cursor. One env var for developers. Full visibility for your security team.

```
Claude Code ──► airiskguard-gateway ──► Anthropic API
Codex CLI   ──►   [inspects both]   ──► OpenAI API
            ◄── [blocked if secret / vuln detected]
```

<a href="gateway/index.md" class="btn-gw">View Gateway Docs</a>
<a href="pricing.md" class="btn-gw-outline">See Pricing</a>

</div>

---

<div class="section-title" markdown>

## Three editions. One platform.

</div>

<div class="pricing-grid" markdown>

<div class="pricing-card" markdown>

### Community
<div class="price">Free <span>forever</span></div>

Open-source. Single developer. Local only.

- Local HTTPS proxy
- 18-type secret detection
- OWASP Top 10 vuln scanning
- Local YAML config
- Model allowlist
- MIT license

<a href="framework/getting-started/" class="cta cta-outline">Get Started</a>

</div>

<div class="pricing-card featured" markdown>

<span class="badge">Most Popular</span>

### Team
<div class="price">Per seat <span>/ month</span></div>

For engineering teams of 5–50 developers.

- Everything in Community
- **Centralized policy server**
- **Per-team policies + gateway keys**
- **Web dashboard** (usage, violations, audit)
- **ML-based PII detection** (Presidio NER)
- **SSO** (SAML / OIDC)
- **30-day audit log** (centralized)
- Slack / PagerDuty / webhook alerts

<a href="mailto:sales@airiskguard.ai" class="cta cta-primary">Contact Sales</a>

</div>

<div class="pricing-card" markdown>

### Enterprise
<div class="price">Annual <span>contract</span></div>

For 50+ developers and regulated industries.

- Everything in Team
- **EU AI Act / SOC 2 / ISO 42001 reports**
- **RBAC** (admin / author / viewer / auditor)
- **SIEM integration** (Splunk, Elastic, Datadog)
- **Custom scanning rules** (org-specific YAML)
- **Incident response playbooks**
- **Unlimited audit retention + export**
- **Self-hosted / air-gapped deployment**
- SLA + dedicated support

<a href="mailto:sales@airiskguard.ai" class="cta cta-outline">Contact Sales</a>

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
<div class="number">9</div>
<div class="label">Risk Checkers</div>
</div>

</div>

---

<div class="section-title" markdown>

## What airiskguard does

</div>

<div class="features" markdown>

<div class="feature-card" markdown>

### 🛡️ AI Coding Gateway

Intercept Claude Code, Codex CLI, and Cursor traffic. Block secrets, PII, and vulnerable AI-generated code before it leaves your network or reaches your developers.

</div>

<div class="feature-card" markdown>

### 🔍 Risk Guardrails

Detect prompt injection, jailbreaks, PII leakage, hallucinations, bias, and fraud in real-time. Pre-check inputs, post-check outputs.

</div>

<div class="feature-card" markdown>

### 📋 Standards-Based Assessment

Assess AI systems against AIRMS v1.0 with structured maturity scoring, gap analysis, and prioritized recommendations.

</div>

<div class="feature-card" markdown>

### 🗂️ Compliance Mapping

Map controls to NIST AI RMF, EU AI Act, and ISO/IEC 42001 automatically. Generate evidence reports for auditors.

</div>

<div class="feature-card" markdown>

### 📜 Immutable Audit Trail

SHA-256 hash-chained audit log for every AI decision. Tamper-evident, verifiable, and ready for regulatory review.

</div>

<div class="feature-card" markdown>

### 🔌 Framework Integration

Drop-in middleware for FastAPI, Flask, LangChain, LlamaIndex, and OpenAI SDK. Works with any Python LLM stack.

</div>

</div>

---

<div class="section-title" markdown>

## Quick Start

</div>

Install from PyPI:

```bash
pip install airiskguard                    # Community Edition
pip install "airiskguard[gateway]"         # + Enterprise Gateway
```

Guard an LLM call:

```python
from airiskguard import RiskGuard

guard = RiskGuard()

pre = await guard.evaluate(
    input_data=user_message, output_data="",
    model_id="gpt-4", checks=["security", "compliance"],
)
if pre.blocked:
    return "Sorry, I can't process that request."
```

Start the coding gateway:

```bash
airiskguard-gateway --config gateway.yaml --port 8080
export ANTHROPIC_BASE_URL=http://localhost:8080   # Claude Code now protected
```

<div style="text-align: center; padding: 2rem 0;" markdown>

[Gateway Docs](gateway/index.md){ .md-button .md-button--primary }
[Framework Docs](framework/getting-started.md){ .md-button }
[View on GitHub](https://github.com/gobeyondfj-cmd/airiskguard){ .md-button }

</div>

---

<div class="section-title" markdown>

## Services & Contact

</div>

Need help deploying airiskguard or preparing for EU AI Act compliance?

<div class="features" markdown>

<div class="feature-card" markdown>

### Consulting

AI risk assessments, regulatory readiness (EU AI Act, NIST, ISO 42001), framework design, and policy development.

</div>

<div class="feature-card" markdown>

### Implementation

Gateway deployment, custom checker development, CI/CD integration, and dashboard configuration.

</div>

<div class="feature-card" markdown>

### Enterprise & Partnerships

Team and Enterprise licensing, platform integrations, research collaboration, and training programs.

</div>

</div>

<div style="text-align: center; padding: 2rem 0;" markdown>

[Get in Touch](services.md){ .md-button .md-button--primary }
[sales@airiskguard.ai](mailto:sales@airiskguard.ai){ .md-button }

</div>
