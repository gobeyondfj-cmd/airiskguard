---
hide:
  - navigation
  - toc
---

<style>
.md-content__button { display: none; }
.md-header { background: rgba(15, 23, 42, 0.97); }

/* Hero */
.hero {
  text-align: center;
  padding: 3rem 1rem 4rem;
  max-width: 800px;
  margin: 0 auto;
}
.hero h1 { font-size: 2.8rem; font-weight: 800; margin-bottom: 0.5rem; line-height: 1.15; }
.hero h1 .headerlink { display: none !important; }
.hero h2 .headerlink { display: none !important; }
.section-title h2 .headerlink { display: none !important; }
.hero .tagline { font-size: 1.2rem; color: var(--md-default-fg-color--light); margin-bottom: 2rem; max-width: 600px; margin-left: auto; margin-right: auto; }

.urgency-badge {
  display: inline-block;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  color: #dc2626;
  padding: 0.4rem 1.2rem;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 500;
  margin-bottom: 1.5rem;
}
[data-md-color-scheme="slate"] .urgency-badge {
  background: rgba(239, 68, 68, 0.15);
  color: #fca5a5;
}

.hero .buttons { display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap; }
.hero .buttons a {
  display: inline-block; padding: 0.9rem 2.2rem; border-radius: 8px;
  font-weight: 700; text-decoration: none; font-size: 1.05rem;
  transition: transform 0.2s, box-shadow 0.2s;
}
.hero .btn-primary {
  background: #2563eb; color: white;
  box-shadow: 0 4px 15px rgba(37, 99, 235, 0.3);
}
.hero .btn-primary:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(37, 99, 235, 0.4); }
.hero .btn-secondary { border: 2px solid #2563eb; color: #2563eb; }
[data-md-color-scheme="slate"] .hero .btn-secondary { color: #60a5fa; border-color: #60a5fa; }
.hero .sub-cta { margin-top: 1rem; font-size: 0.9rem; color: var(--md-default-fg-color--light); }
.hero .sub-cta a { color: #2563eb; }

/* Trust bar */
.trust-bar {
  text-align: center;
  padding: 1.2rem;
  background: var(--md-code-bg-color);
  border-radius: 8px;
  margin: 0 auto 2rem;
  max-width: 800px;
  font-size: 0.85rem;
  color: var(--md-default-fg-color--light);
  letter-spacing: 0.3px;
}
.trust-bar strong { color: var(--md-primary-fg-color); }

/* Deliverables */
.deliverables-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.5rem;
  padding: 1rem 0 2rem;
}
.deliverable-card {
  padding: 1.5rem;
  border-radius: 12px;
  border: 1px solid var(--md-default-fg-color--lightest);
  transition: box-shadow 0.2s;
}
.deliverable-card:hover { box-shadow: 0 4px 15px rgba(0,0,0,0.08); }
.deliverable-card h3 { margin-top: 0.5rem; font-size: 1.05rem; }
.deliverable-card p { font-size: 0.9rem; color: var(--md-default-fg-color--light); }

/* Steps */
.steps-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 2rem;
  padding: 1rem 0 2rem;
  text-align: center;
}
.step-num {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 2.5rem;
  height: 2.5rem;
  background: rgba(37, 99, 235, 0.1);
  color: #2563eb;
  border-radius: 50%;
  font-size: 1.1rem;
  font-weight: 700;
  margin-bottom: 0.75rem;
}
[data-md-color-scheme="slate"] .step-num { background: rgba(96, 165, 250, 0.15); color: #60a5fa; }
.step h3 { font-size: 1rem; margin-bottom: 0.3rem; }
.step p { font-size: 0.85rem; color: var(--md-default-fg-color--light); }

/* Pricing */
.pricing-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.5rem;
  padding: 1rem 0 2rem;
}
.pricing-card {
  border-radius: 12px;
  border: 1px solid var(--md-default-fg-color--lightest);
  padding: 2rem 1.5rem;
  position: relative;
  text-align: center;
}
.pricing-card.featured { border: 2px solid #2563eb; }
.pricing-card .badge {
  position: absolute; top: -12px; left: 50%; transform: translateX(-50%);
  background: #2563eb; color: white; font-size: 0.7rem; font-weight: 700;
  padding: 3px 12px; border-radius: 999px; text-transform: uppercase; letter-spacing: 0.5px;
}
.pricing-card h3 { margin-top: 0; font-size: 1.2rem; }
.pricing-card .price { font-size: 2.2rem; font-weight: 800; color: var(--md-default-fg-color); margin: 0.5rem 0 0.2rem; }
.pricing-card .price-note { font-size: 0.85rem; color: var(--md-default-fg-color--light); margin-bottom: 1.2rem; }
.pricing-card ul { text-align: left; padding-left: 0; list-style: none; margin: 1rem 0 1.5rem; }
.pricing-card ul li { padding: 0.3rem 0; font-size: 0.9rem; padding-left: 1.5rem; position: relative; }
.pricing-card ul li::before { content: "✓"; position: absolute; left: 0; color: #16a34a; font-weight: 700; }
.pricing-card .cta {
  display: block; text-align: center; padding: 0.75rem 1.5rem; border-radius: 8px;
  font-weight: 600; text-decoration: none; font-size: 0.95rem; transition: all 0.2s;
}
.pricing-card .cta-primary { background: #2563eb; color: white; }
.pricing-card .cta-primary:hover { background: #1d4ed8; }
.pricing-card .cta-outline { border: 2px solid #2563eb; color: #2563eb; }
[data-md-color-scheme="slate"] .pricing-card .cta-outline { color: #60a5fa; border-color: #60a5fa; }

/* Report mockup */
.report-mockup {
  max-width: 650px;
  margin: 1rem auto 2rem;
  border: 1px solid var(--md-default-fg-color--lightest);
  border-radius: 12px;
  padding: 1.5rem 2rem;
  box-shadow: 0 10px 40px rgba(0,0,0,0.08);
}
.report-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 1rem;
  margin-bottom: 1rem;
  border-bottom: 2px solid #2563eb;
}
.report-grade {
  display: inline-flex; align-items: center; justify-content: center;
  width: 3.5rem; height: 3.5rem; border-radius: 50%;
  background: #dc2626; color: white; font-size: 1.8rem; font-weight: 800;
}
.report-findings {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.6rem;
}
.report-finding {
  background: var(--md-code-bg-color);
  padding: 0.5rem 0.75rem;
  border-radius: 4px;
  font-size: 0.8rem;
  border-left: 3px solid #dc2626;
}
.report-finding.high { border-left-color: #ea580c; }
.report-finding.medium { border-left-color: #ca8a04; }

/* Compliance */
.compliance-row {
  display: flex;
  justify-content: center;
  gap: 3rem;
  flex-wrap: wrap;
  padding: 1rem 0 2rem;
  text-align: center;
}
.compliance-item strong { display: block; font-size: 1rem; }
.compliance-item span { font-size: 0.8rem; color: var(--md-default-fg-color--light); }

/* Final CTA */
.final-cta {
  background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 100%);
  color: white;
  border-radius: 12px;
  padding: 3rem 2rem;
  text-align: center;
  margin: 2rem 0;
}
.final-cta h2 { color: white; font-size: 1.8rem; margin-bottom: 0.5rem; border: none; }
.final-cta p { color: #94a3b8; font-size: 1.05rem; margin-bottom: 1.5rem; }
.final-cta .btn-gw {
  display: inline-block; padding: 0.8rem 2rem; border-radius: 8px;
  font-weight: 600; text-decoration: none; font-size: 1rem;
  background: #2563eb; color: white; margin: 0.25rem;
}
.final-cta .btn-gw-outline {
  display: inline-block; padding: 0.8rem 2rem; border-radius: 8px;
  font-weight: 600; text-decoration: none; font-size: 1rem;
  border: 2px solid #60a5fa; color: #93c5fd; margin: 0.25rem;
}

.section-title { text-align: center; padding: 2rem 0 0.5rem; }
.section-title h2 { font-size: 1.8rem; }
.section-subtitle { text-align: center; color: var(--md-default-fg-color--light); font-size: 1rem; max-width: 550px; margin: 0 auto 1.5rem; }

@media (max-width: 768px) {
  .steps-grid { grid-template-columns: 1fr; }
  .report-findings { grid-template-columns: 1fr; }
  .hero h1 { font-size: 2rem; }
}
</style>

<div class="hero" markdown>

<div class="urgency-badge">⚠ EU AI Act enforcement deadline approaching — fines up to €35M</div>

# Is your AI application secure and compliant?

<p class="tagline">
Get a comprehensive AI Risk Assessment with EU AI Act compliance mapping. 30-page report delivered in 5 business days.
</p>

<div class="buttons">
<a href="mailto:sales@airiskguard.ai?subject=AI%20Risk%20Assessment" class="btn-primary">Get Your Assessment — $2,500</a>
<a href="mailto:sales@airiskguard.ai?subject=Quick%20Question" class="btn-secondary">Book a Call</a>
</div>

<p class="sub-cta">or email <a href="mailto:sales@airiskguard.ai">sales@airiskguard.ai</a> to discuss your needs</p>

</div>

<div class="trust-bar">
<strong>53 security controls</strong> · NIST AI RMF · EU AI Act · ISO/IEC 42001 · <strong>OWASP Top 10 for LLMs</strong>
</div>

---

<div class="section-title" markdown>

## What You Get

</div>

<p class="section-subtitle">A professional security assessment that satisfies auditors, boards, and regulators.</p>

<div class="deliverables-grid" markdown>

<div class="deliverable-card" markdown>

### 🛡️ Security Grade (A–F)

Clear, board-ready score based on 53 automated checks across prompt injection, PII leakage, hallucination risk, and more.

</div>

<div class="deliverable-card" markdown>

### 📋 Detailed Findings Report

Every vulnerability documented with evidence, severity rating, and step-by-step remediation instructions.

</div>

<div class="deliverable-card" markdown>

### ⚖️ EU AI Act Compliance Map

Article-by-article mapping showing your compliance status. Traffic-light indicators for each requirement.

</div>

<div class="deliverable-card" markdown>

### 🗺️ Remediation Roadmap

Prioritized action plan (P1/P2/P3) so your team knows exactly what to fix first and how.

</div>

<div class="deliverable-card" markdown>

### 🔍 Live Endpoint Testing

Adversarial prompts sent to your AI endpoints to test for real-world injection, bypass, and leakage attacks.

</div>

<div class="deliverable-card" markdown>

### 📊 Static Code Analysis

Your AI integration code scanned for hardcoded secrets, unsafe prompt construction, and missing guardrails.

</div>

</div>

---

<div class="section-title" markdown>

## Sample Report Preview

</div>

<p class="section-subtitle">This is what a $2,500 assessment delivers. Professional, actionable, board-ready.</p>

<div class="report-mockup">
  <div class="report-header">
    <div>
      <strong style="font-size: 1.1rem;">AI Risk Assessment Report</strong><br>
      <span style="font-size: 0.85rem; color: var(--md-default-fg-color--light);">Acme AI Corp · May 2026</span>
    </div>
    <div class="report-grade">D</div>
  </div>
  <div class="report-findings">
    <div class="report-finding">CRITICAL: Prompt injection via f-string</div>
    <div class="report-finding high">HIGH: PII exposed in prompt context</div>
    <div class="report-finding high">HIGH: Hardcoded API key in source</div>
    <div class="report-finding medium">MEDIUM: No input validation on endpoint</div>
    <div class="report-finding medium">MEDIUM: Temperature 0.9 without guardrails</div>
    <div class="report-finding high">HIGH: No error handling on LLM calls</div>
  </div>
  <p style="margin-top: 1rem; font-size: 0.8rem; color: var(--md-default-fg-color--light); text-align: center;">
    + EU AI Act compliance mapping · Remediation roadmap · Executive summary
  </p>
</div>

---

<div class="section-title" markdown>

## How It Works

</div>

<p class="section-subtitle">From kickoff to report in 5 business days. No lengthy onboarding.</p>

<div class="steps-grid">
  <div class="step">
    <div class="step-num">1</div>
    <h3>Share Access</h3>
    <p>Give us your AI endpoint URL, code repository, or both. We handle the rest.</p>
  </div>
  <div class="step">
    <div class="step-num">2</div>
    <h3>We Scan + Analyze</h3>
    <p>53 automated security checks plus expert review. Live adversarial testing and static code analysis.</p>
  </div>
  <div class="step">
    <div class="step-num">3</div>
    <h3>Get Your Report</h3>
    <p>30-page branded PDF with grade, findings, compliance mapping, and prioritized remediation plan.</p>
  </div>
</div>

---

<div class="section-title" markdown>

## Pricing

</div>

<p class="section-subtitle">Transparent pricing. No surprise fees. No long-term contracts required.</p>

<div class="pricing-grid" markdown>

<div class="pricing-card" markdown>

### AI Risk Assessment
<div class="price">$2,500</div>
<div class="price-note">One-time · Delivered in 5 days</div>

- 30-page branded PDF report
- A–F security grade
- Live endpoint + static code scan
- EU AI Act compliance mapping
- Prioritized remediation roadmap
- 30-minute debrief call

<a href="mailto:sales@airiskguard.ai?subject=AI%20Risk%20Assessment" class="cta cta-outline">Get Started</a>

</div>

<div class="pricing-card featured" markdown>

<span class="badge">Most Popular</span>

### Compliance Package
<div class="price">$7,500</div>
<div class="price-note">One-time · Delivered in 2 weeks</div>

- Everything in Assessment, plus:
- Full policy document suite
- Board-ready risk register
- Incident response playbook
- Regulatory filing support docs
- 2 hours of advisory calls

<a href="mailto:sales@airiskguard.ai?subject=Compliance%20Package" class="cta cta-primary">Get Started</a>

</div>

<div class="pricing-card" markdown>

### Continuous Monitoring
<div class="price">$1,500</div>
<div class="price-note">Per month · Cancel anytime</div>

- Monthly automated re-scan
- Updated compliance report
- Slack alerts on new vulnerabilities
- Quarterly advisory call
- Priority remediation support
- Audit-ready documentation

<a href="mailto:sales@airiskguard.ai?subject=Continuous%20Monitoring" class="cta cta-outline">Get Started</a>

</div>

</div>

---

<div class="section-title" markdown>

## Mapped to the Standards That Matter

</div>

<p class="section-subtitle">Our assessment framework aligns with major AI governance standards so your report satisfies auditors.</p>

<div class="compliance-row">
  <div class="compliance-item"><strong>EU AI Act</strong><span>Articles 9, 10, 13, 14, 15</span></div>
  <div class="compliance-item"><strong>NIST AI RMF</strong><span>Govern · Map · Measure · Manage</span></div>
  <div class="compliance-item"><strong>ISO/IEC 42001</strong><span>AI Management System</span></div>
  <div class="compliance-item"><strong>OWASP LLM Top 10</strong><span>2025 Edition</span></div>
  <div class="compliance-item"><strong>SOC 2</strong><span>Trust Service Criteria</span></div>
</div>

---

<div class="final-cta">
  <h2>Don't wait for a breach or a fine.</h2>
  <p>One AI security incident costs $4.5M on average. One assessment costs $2,500. The math is simple.</p>
  <a href="mailto:sales@airiskguard.ai?subject=AI%20Risk%20Assessment" class="btn-gw">Get Your Assessment</a>
  <a href="mailto:sales@airiskguard.ai?subject=Quick%20Question" class="btn-gw-outline">Book a Call</a>
</div>

---

<div style="text-align: center; padding: 1rem 0; font-size: 0.85rem; color: var(--md-default-fg-color--light);">

**Open Source Tools:** [Framework Docs](framework/getting-started.md) · [AI Coding Gateway](gateway/index.md) · [AI Risk Standard](standard/ai-risk-management-standard-v1/index.md) · [GitHub](https://github.com/gobeyondfj-cmd/airiskguard)

</div>
