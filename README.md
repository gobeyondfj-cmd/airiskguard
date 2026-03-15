# airiskguard

AI Risk Governance Framework — model registry, audit logs, risk dashboards, anomaly detection, regulatory reports, and human review workflows for AI applications.

## Installation

```bash
pip install airiskguard
```

With optional extras:

```bash
pip install airiskguard[fastapi]    # FastAPI integration
pip install airiskguard[flask]      # Flask integration
pip install airiskguard[transformers]  # ML-based hallucination/security detection
pip install airiskguard[dev]        # Development tools
```

## Quick Start

### Decorator Pattern

```python
from airiskguard import risk_guard

@risk_guard(checks=["fraud", "compliance"], model_id="payment-v2")
async def process_payment(tx: dict) -> dict:
    return await engine.process(tx)
```

### Middleware Pattern

```python
from fastapi import FastAPI
from airiskguard.integrations.fastapi import add_risk_guard

app = FastAPI()
add_risk_guard(app, config="airiskguard.yaml")
```

### Direct API

```python
from airiskguard import RiskGuard

guard = RiskGuard()
await guard.initialize()

report = await guard.evaluate(
    input_data={"amount": 500, "user_id": "u123"},
    output_data={"approved": True},
    model_id="my-model",
)
print(report.overall_risk, report.overall_score)
```

## Features

- **Model Registry** — register, version, and manage model lifecycles
- **Audit Log** — immutable SHA-256 hash-chain audit trail
- **Risk Dashboard** — aggregate metrics, trends, and JSON export
- **Anomaly Detection** — IsolationForest + KS drift detection
- **Regulatory Reports** — GDPR, SOX, EU AI Act reports in JSON + HTML
- **Human Review** — threshold-based flagging, approve/reject/escalate workflows
- **Risk Checkers** — fraud, hallucination, compliance, bias, security
- **Framework Integration** — FastAPI, Flask, ASGI, WSGI middleware

## Risk Checkers

| Checker | Detects |
|---------|---------|
| `fraud` | Amount anomaly (z-score), velocity abuse, suspicious patterns |
| `hallucination` | Fabricated URLs, unverifiable citations, contradictions, NLI |
| `compliance` | PII (SSN, email, CC, phone), prohibited content, custom rules |
| `bias` | Disparate impact (4/5ths rule), demographic parity, equalized odds |
| `security` | Prompt injection (~30 patterns), jailbreak (~20 patterns), encoding attacks |

## License

MIT
