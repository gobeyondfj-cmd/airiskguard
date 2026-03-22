# Risk Checkers

airiskguard includes five built-in risk checkers that run in real-time on AI inputs and outputs.

## Overview

| Checker | Detects |
|---------|---------|
| `security` | Prompt injection, jailbreak attempts, encoding attacks, system prompt leakage |
| `compliance` | PII (SSN, email, credit card, phone), prohibited content, custom regex rules |
| `hallucination` | Fabricated URLs, unverifiable citations, contradictions, overconfident language |
| `bias` | Disparate impact, demographic parity violations, equalized odds, biased language |
| `fraud` | Amount anomaly (z-score), velocity abuse, suspicious transaction patterns |

## Security Checker

Detects adversarial inputs targeting AI systems.

**Detection capabilities:**

- **Prompt injection** (~30 patterns) — "ignore previous instructions", system prompt markers, roleplay attacks
- **Jailbreak attempts** (~20 patterns) — "DAN mode", "unrestricted mode", hypothetical framing
- **Encoding attacks** — base64-encoded injections, unicode manipulation, homoglyph substitution
- **Information leakage** — system prompt markers appearing in LLM output

**Risk scoring:**

| Threat | Score | Risk Level |
|--------|-------|------------|
| Injection detected | 0.85 | HIGH |
| Jailbreak detected | 0.80 | HIGH |
| Encoding attack | 0.90 | CRITICAL |
| Info leak in output | 0.70 | HIGH |

## Compliance Checker

Scans for PII and prohibited content in both inputs and outputs.

**PII patterns and weights:**

| PII Type | Pattern | Weight |
|----------|---------|--------|
| SSN | `XXX-XX-XXXX` | 0.9 |
| Credit card | `XXXX-XXXX-XXXX-XXXX` | 0.9 |
| Email | Standard email format | 0.4 |
| Phone | US phone formats | 0.5 |
| IP address | IPv4 format | 0.3 |

**Prohibited content detection:**

| Content Type | Score |
|-------------|-------|
| Violence instructions | 0.95 |
| Illegal activity | 0.95 |
| Self-harm instructions | 0.95 |

**Custom rules** — Add regex-based detection patterns via configuration:

```yaml
checker_configs:
  compliance:
    custom_rules:
      - name: api_key_pattern
        pattern: '(?:sk|pk)[-_][a-zA-Z0-9]{32,}'
```

## Hallucination Checker

Detects fabricated information in AI outputs.

**Heuristic mode** (default):

| Check | Condition | Score |
|-------|-----------|-------|
| Fabricated URLs | URL not in `context["known_urls"]` | 0.4 |
| Unverifiable citations | Pattern: "Author (YYYY)" | 0.3 |
| Overconfident language | 2+ markers: "100%", "guaranteed", "definitely" | 0.3 |
| Internal contradictions | "always/never" pairs | 0.5 |

**NLI mode** (optional, requires `pip install airiskguard[transformers]`):

Uses `cross-encoder/nli-deberta-v3-small` for semantic contradiction detection between premise and hypothesis.

```yaml
checker_configs:
  hallucination:
    use_nli: true
```

## Bias Checker

Evaluates algorithmic fairness using four metrics.

**Metrics:**

| Metric | Threshold | Data Required |
|--------|-----------|---------------|
| Disparate Impact Ratio | < 0.8 (4/5ths rule) | `context["group_outcomes"]` |
| Demographic Parity | > 0.1 difference | `context["group_outcomes"]` |
| Equalized Odds (TPR) | > 0.1 difference | `context["predictions"]`, `context["labels"]` |
| Equalized Odds (FPR) | > 0.1 difference | `context["predictions"]`, `context["labels"]` |
| Biased Language | Pattern match | Output text |

## Fraud Checker

Transaction-focused fraud detection.

**Detection methods:**

| Method | Trigger | Score |
|--------|---------|-------|
| Amount anomaly | z-score > 3.0 | `min(z / (threshold * 2), 1.0)` |
| Velocity abuse | > 5 transactions per user | `min(count / (max * 3), 1.0)` |
| Round large amounts | > $1,000 as integer | 0.6 |
| Currency mismatch | Country/currency inconsistency | 0.6 |

## Universal Risk Scoring

All checkers use the same risk level mapping:

| Score Range | Risk Level |
|-------------|------------|
| `>= 0.8` | CRITICAL |
| `0.5 – 0.8` | HIGH |
| `0.3 – 0.5` | MEDIUM |
| `< 0.3` | LOW |
