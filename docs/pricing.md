---
hide:
  - toc
---

<style>
.md-content__button { display: none; }

.pricing-hero { text-align: center; padding: 2rem 0 3rem; }
.pricing-hero h1 { font-size: 2.4rem; font-weight: 800; }
.pricing-hero p { font-size: 1.15rem; color: var(--md-default-fg-color--light); max-width: 600px; margin: 0 auto 1rem; }

.pricing-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.5rem;
  padding: 2rem 0;
  align-items: start;
}
.pricing-card {
  border-radius: 12px;
  border: 1px solid var(--md-default-fg-color--lightest);
  padding: 2rem 1.5rem;
  position: relative;
}
.pricing-card.featured {
  border: 2px solid var(--md-primary-fg-color);
  box-shadow: 0 4px 24px rgba(0,150,136,0.12);
}
.pricing-card .badge {
  position: absolute;
  top: -13px;
  left: 50%;
  transform: translateX(-50%);
  background: var(--md-primary-fg-color);
  color: white;
  font-size: 0.72rem;
  font-weight: 700;
  padding: 3px 14px;
  border-radius: 999px;
  white-space: nowrap;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}
.pricing-card .tier { font-size: 0.8rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: var(--md-primary-fg-color); margin-bottom: 0.5rem; }
.pricing-card h2 { font-size: 1.6rem; margin: 0 0 0.25rem; }
.pricing-card .price { font-size: 2.2rem; font-weight: 800; color: var(--md-primary-fg-color); margin: 0.75rem 0 0.25rem; }
.pricing-card .price-note { font-size: 0.85rem; color: var(--md-default-fg-color--light); margin-bottom: 1.25rem; }
.pricing-card .desc { font-size: 0.9rem; color: var(--md-default-fg-color--light); margin-bottom: 1.5rem; border-bottom: 1px solid var(--md-default-fg-color--lightest); padding-bottom: 1.25rem; }
.pricing-card ul { list-style: none; padding: 0; margin: 0 0 1.5rem; }
.pricing-card ul li { font-size: 0.9rem; padding: 0.3rem 0 0.3rem 1.5rem; position: relative; }
.pricing-card ul li::before { content: "✓"; position: absolute; left: 0; color: #22c55e; font-weight: 700; }
.pricing-card ul li.section-label { font-weight: 700; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.06em; color: var(--md-default-fg-color--light); padding-left: 0; margin-top: 1rem; }
.pricing-card ul li.section-label::before { content: ""; }
.pricing-card .cta {
  display: block; text-align: center; padding: 0.75rem 1rem; border-radius: 8px;
  font-weight: 600; text-decoration: none; font-size: 0.95rem;
}
.pricing-card .cta-primary { background: var(--md-primary-fg-color); color: white; }
.pricing-card .cta-outline { border: 2px solid var(--md-primary-fg-color); color: var(--md-primary-fg-color); }

.compare-table { width: 100%; border-collapse: collapse; margin: 2rem 0; font-size: 0.9rem; }
.compare-table th { background: var(--md-primary-fg-color); color: white; padding: 0.75rem 1rem; text-align: left; }
.compare-table th:not(:first-child) { text-align: center; }
.compare-table td { padding: 0.65rem 1rem; border-bottom: 1px solid var(--md-default-fg-color--lightest); }
.compare-table td:not(:first-child) { text-align: center; }
.compare-table tr:nth-child(even) { background: var(--md-code-bg-color); }
.compare-table .section-row td { font-weight: 700; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.06em; color: var(--md-default-fg-color--light); background: var(--md-default-fg-color--lightest); padding: 0.4rem 1rem; }
.check { color: #22c55e; font-weight: 700; font-size: 1.1rem; }
.dash { color: var(--md-default-fg-color--light); }

.faq { max-width: 720px; margin: 0 auto; }
.faq details { border: 1px solid var(--md-default-fg-color--lightest); border-radius: 8px; padding: 1rem 1.25rem; margin-bottom: 0.75rem; }
.faq summary { font-weight: 600; cursor: pointer; }
.faq p { margin-top: 0.75rem; font-size: 0.9rem; color: var(--md-default-fg-color--light); }

.section-title { text-align: center; padding: 2.5rem 0 1rem; }
.section-title h2 { font-size: 1.9rem; }
</style>

<div class="pricing-hero" markdown>

# Pricing

Simple, transparent pricing. Start free. Scale when you need centralized control.

</div>

<div class="pricing-grid" markdown>

<div class="pricing-card" markdown>

<div class="tier">Community</div>

## Free

<div class="price">$0</div>
<div class="price-note">Forever. No credit card required.</div>
<div class="desc">For individual developers and open-source projects.</div>

<ul>
<li class="section-label">Gateway</li>
<li>Local HTTPS reverse proxy</li>
<li>18-type secret detection (regex + entropy)</li>
<li>OWASP Top 10 inbound vuln scanning</li>
<li>Local YAML config</li>
<li>Model allowlist</li>
<li class="section-label">SDK</li>
<li>All 9 risk checkers</li>
<li>Policy-as-code engine</li>
<li>Local audit log</li>
<li>FastAPI / Flask / LangChain integrations</li>
<li class="section-label">Support</li>
<li>GitHub Issues</li>
<li>MIT license</li>
</ul>

<a href="../framework/getting-started/" class="cta cta-outline">Get Started</a>

</div>

<div class="pricing-card featured" markdown>

<span class="badge">Most Popular</span>

<div class="tier">Team</div>

## Contact Us

<div class="price">Per seat</div>
<div class="price-note">Monthly or annual billing. Volume discounts available.</div>
<div class="desc">For engineering teams of 5–50 developers who need centralized control.</div>

<ul>
<li class="section-label">Everything in Community, plus:</li>
<li>Centralized policy server</li>
<li>Push policies to all developer machines</li>
<li>Per-team model allowlists and checker sets</li>
<li>Gateway-issued API keys (real keys stay server-side)</li>
<li class="section-label">Visibility</li>
<li>Web dashboard — usage, violations, audit log</li>
<li>30-day centralized audit log (searchable)</li>
<li>Slack / PagerDuty / webhook alerts</li>
<li class="section-label">Security</li>
<li>ML-based PII detection (Presidio NER)</li>
<li>Session quarantine for offending keys</li>
<li>SSO — SAML 2.0 and OIDC</li>
<li class="section-label">Support</li>
<li>Email support (next business day)</li>
<li>Commercial license</li>
</ul>

<a href="mailto:sales@airiskguard.ai" class="cta cta-primary">Contact Sales</a>

</div>

<div class="pricing-card" markdown>

<div class="tier">Enterprise</div>

## Contact Us

<div class="price">Annual</div>
<div class="price-note">Custom contract. Includes SLA and dedicated support.</div>
<div class="desc">For 50+ developers, regulated industries, and Fortune 500.</div>

<ul>
<li class="section-label">Everything in Team, plus:</li>
<li>EU AI Act evidence reports</li>
<li>SOC 2 Type II evidence generation</li>
<li>ISO 42001 / NIST RMF reports</li>
<li>PDF compliance report export</li>
<li class="section-label">Security & Control</li>
<li>RBAC — admin / policy-author / viewer / auditor</li>
<li>Custom scanning rules (org-specific YAML)</li>
<li>Incident response playbooks</li>
<li>SIEM integration (Splunk, Elastic, Datadog)</li>
<li>Unlimited audit log retention + SIEM export</li>
<li class="section-label">Deployment</li>
<li>Self-hosted / air-gapped deployment</li>
<li>Docker Compose + Kubernetes manifests</li>
<li class="section-label">Support</li>
<li>4-hour SLA response time</li>
<li>Dedicated customer success manager</li>
<li>Commercial license</li>
</ul>

<a href="mailto:sales@airiskguard.ai" class="cta cta-outline">Contact Sales</a>

</div>

</div>

---

<div class="section-title" markdown>

## Full Feature Comparison

</div>

<table class="compare-table">
<thead>
<tr>
<th>Feature</th>
<th>Community</th>
<th>Team</th>
<th>Enterprise</th>
</tr>
</thead>
<tbody>

<tr class="section-row"><td colspan="4">Gateway — Core</td></tr>
<tr><td>Local HTTPS reverse proxy</td><td class="check">✓</td><td class="check">✓</td><td class="check">✓</td></tr>
<tr><td>Secret detection (18 types + entropy)</td><td class="check">✓</td><td class="check">✓</td><td class="check">✓</td></tr>
<tr><td>OWASP Top 10 inbound scanning</td><td class="check">✓</td><td class="check">✓</td><td class="check">✓</td></tr>
<tr><td>Secret redaction (vs hard block)</td><td class="check">✓</td><td class="check">✓</td><td class="check">✓</td></tr>
<tr><td>Model allowlist</td><td class="check">✓</td><td class="check">✓</td><td class="check">✓</td></tr>
<tr><td>Local YAML config</td><td class="check">✓</td><td class="check">✓</td><td class="check">✓</td></tr>

<tr class="section-row"><td colspan="4">Gateway — Team</td></tr>
<tr><td>Centralized policy server</td><td class="dash">—</td><td class="check">✓</td><td class="check">✓</td></tr>
<tr><td>Policy hot-reload (polling)</td><td class="dash">—</td><td class="check">✓</td><td class="check">✓</td></tr>
<tr><td>Per-team policies</td><td class="dash">—</td><td class="check">✓</td><td class="check">✓</td></tr>
<tr><td>Gateway-issued API keys</td><td class="dash">—</td><td class="check">✓</td><td class="check">✓</td></tr>
<tr><td>Session quarantine</td><td class="dash">—</td><td class="check">✓</td><td class="check">✓</td></tr>
<tr><td>SSO (SAML / OIDC)</td><td class="dash">—</td><td class="check">✓</td><td class="check">✓</td></tr>

<tr class="section-row"><td colspan="4">Visibility & Audit</td></tr>
<tr><td>Local stdout/stderr logging</td><td class="check">✓</td><td class="check">✓</td><td class="check">✓</td></tr>
<tr><td>Web dashboard</td><td class="dash">—</td><td class="check">✓</td><td class="check">✓</td></tr>
<tr><td>Centralized audit log</td><td class="dash">—</td><td>30 days</td><td>Unlimited</td></tr>
<tr><td>Slack / PagerDuty / webhook alerts</td><td class="dash">—</td><td class="check">✓</td><td class="check">✓</td></tr>
<tr><td>SIEM integration (Splunk, Elastic)</td><td class="dash">—</td><td class="dash">—</td><td class="check">✓</td></tr>
<tr><td>Audit log export</td><td class="dash">—</td><td class="dash">—</td><td class="check">✓</td></tr>

<tr class="section-row"><td colspan="4">Detection</td></tr>
<tr><td>Regex-based PII detection</td><td class="check">✓</td><td class="check">✓</td><td class="check">✓</td></tr>
<tr><td>ML-based PII detection (Presidio NER)</td><td class="dash">—</td><td class="check">✓</td><td class="check">✓</td></tr>
<tr><td>Custom org-specific scanning rules</td><td class="dash">—</td><td class="dash">—</td><td class="check">✓</td></tr>

<tr class="section-row"><td colspan="4">Compliance & Reporting</td></tr>
<tr><td>EU AI Act evidence reports</td><td class="dash">—</td><td class="dash">—</td><td class="check">✓</td></tr>
<tr><td>SOC 2 Type II evidence</td><td class="dash">—</td><td class="dash">—</td><td class="check">✓</td></tr>
<tr><td>ISO 42001 / NIST RMF reports</td><td class="dash">—</td><td class="dash">—</td><td class="check">✓</td></tr>
<tr><td>PDF report export</td><td class="dash">—</td><td class="dash">—</td><td class="check">✓</td></tr>

<tr class="section-row"><td colspan="4">Access Control</td></tr>
<tr><td>RBAC (admin / author / viewer / auditor)</td><td class="dash">—</td><td class="dash">—</td><td class="check">✓</td></tr>
<tr><td>Incident response playbooks</td><td class="dash">—</td><td class="dash">—</td><td class="check">✓</td></tr>

<tr class="section-row"><td colspan="4">Deployment</td></tr>
<tr><td>Single machine (local)</td><td class="check">✓</td><td class="check">✓</td><td class="check">✓</td></tr>
<tr><td>Docker Compose</td><td class="dash">—</td><td class="check">✓</td><td class="check">✓</td></tr>
<tr><td>Kubernetes manifests</td><td class="dash">—</td><td class="dash">—</td><td class="check">✓</td></tr>
<tr><td>Self-hosted / air-gapped</td><td class="dash">—</td><td class="dash">—</td><td class="check">✓</td></tr>

<tr class="section-row"><td colspan="4">Support</td></tr>
<tr><td>GitHub Issues</td><td class="check">✓</td><td class="check">✓</td><td class="check">✓</td></tr>
<tr><td>Email support</td><td class="dash">—</td><td>Next business day</td><td>4-hour SLA</td></tr>
<tr><td>Dedicated customer success</td><td class="dash">—</td><td class="dash">—</td><td class="check">✓</td></tr>
<tr><td>License</td><td>MIT</td><td>Commercial</td><td>Commercial</td></tr>

</tbody>
</table>

---

<div class="section-title" markdown>

## Frequently Asked Questions

</div>

<div class="faq" markdown>

<details>
<summary>Is the Community Edition really free forever?</summary>
<p>Yes. The Community Edition is open-source (MIT license) and will always be free. It includes the full local gateway proxy, all 9 risk checkers, and the SDK. There are no usage limits or expiry dates.</p>
</details>

<details>
<summary>How does the Team Edition licensing work?</summary>
<p>Team Edition is licensed per developer seat per month. A "seat" is a developer who has the gateway running on their machine or who accesses the policy server. Contact <a href="mailto:sales@airiskguard.ai">sales@airiskguard.ai</a> for current pricing and volume discounts.</p>
</details>

<details>
<summary>Can I self-host the Team Edition?</summary>
<p>Yes. The Team policy server and dashboard are designed to run on your own infrastructure. We provide Docker Compose configs for Team and Kubernetes manifests for Enterprise. No data ever leaves your network.</p>
</details>

<details>
<summary>What's the difference between Team and Enterprise for compliance?</summary>
<p>Team Edition gives you the audit log and violation history needed for internal governance. Enterprise Edition adds structured compliance evidence reports (EU AI Act, SOC 2, ISO 42001, NIST RMF) in PDF, Markdown, and JSON formats — ready to hand to auditors.</p>
</details>

<details>
<summary>Do developer API keys ever leave our network?</summary>
<p>No. With Team or Enterprise, developers are issued gateway API keys. The real Anthropic/OpenAI provider keys are stored only in the policy server config and never shared with developers or sent to external services.</p>
</details>

<details>
<summary>Can I upgrade from Community to Team later?</summary>
<p>Yes. The Team Edition is a separate package (<code>airiskguard-team</code>) that installs on top of the Community Edition. Your existing gateway config and audit data are preserved.</p>
</details>

<details>
<summary>Is there a trial for Team or Enterprise?</summary>
<p>Yes — contact <a href="mailto:sales@airiskguard.ai">sales@airiskguard.ai</a> to arrange a 30-day trial with full Team or Enterprise features.</p>
</details>

</div>

---

<div style="text-align: center; padding: 2rem 0;" markdown>

**Ready to get started?**

[Get Community Free](../framework/getting-started.md){ .md-button .md-button--primary }
[Contact Sales](mailto:sales@airiskguard.ai){ .md-button }

</div>
