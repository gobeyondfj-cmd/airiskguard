# airiskguard

AI Risk Governance Framework for LLM applications, AI agents, and ML systems — and now an **Enterprise AI Coding Gateway** that protects companies when employees use Claude Code, Codex CLI, Cursor, and Copilot.

## What's New: Enterprise AI Coding Gateway

Companies deploying AI coding assistants face a critical risk: **employee prompts containing source code, secrets, customer data, and proprietary IP are sent to external AI APIs with zero visibility or control.**

airiskguard now ships a drop-in HTTPS proxy that sits between your developers and the AI provider. Zero config change for developers — just set one env var.

```
Developer machine           Corporate network          External
─────────────────           ─────────────────          ────────
Claude Code  ──► airiskguard-gateway ──► Anthropic API
Codex CLI    ──►    (localhost:8080)  ──► OpenAI API
Cursor       ──►    [inspects both]   ──► Azure OpenAI
             ◄── [blocked if secret / vuln detected]
```

```bash
# Install
pip install "airiskguard[gateway]"

# Start gateway
airiskguard-gateway --config gateway.yaml --port 8080

# Developer sets one env var — Claude Code, Codex, Cursor work unchanged
export ANTHROPIC_BASE_URL=http://localhost:8080
export OPENAI_BASE_URL=http://localhost:8080
```

**What gets intercepted:**

| Risk | Prompt (outbound) | Completion (inbound) |
|---|---|---|
| API keys / tokens in code | Block / redact | — |
| AWS credentials, private keys | Block / redact | — |
| Database connection strings | Block / redact | — |
| PII / customer data | Block / redact | — |
| SQL injection in generated code | — | Block |
| `shell=True`, `os.system()` | — | Block |
| Hardcoded passwords in AI output | — | Block |
| Weak crypto (MD5/SHA1) | — | Flag |
| Prompt injection via completions | — | Block |

See the [Gateway docs](https://www.airiskguard.ai/gateway/) for full configuration.

---

## Installation

```bash
pip install airiskguard
```

With optional extras:

```bash
pip install "airiskguard[gateway]"        # Enterprise AI coding gateway
pip install "airiskguard[fastapi]"        # FastAPI integration
pip install "airiskguard[flask]"          # Flask integration
pip install "airiskguard[langchain]"      # LangChain integration
pip install "airiskguard[llamaindex]"     # LlamaIndex integration
pip install "airiskguard[openai]"         # OpenAI SDK drop-in wrapper
pip install "airiskguard[postgres]"       # PostgreSQL storage backend
pip install "airiskguard[redis]"          # Redis storage backend
pip install "airiskguard[opentelemetry]"  # OTel traces + metrics
pip install "airiskguard[transformers]"   # ML-based hallucination detection
pip install "airiskguard[dev]"            # Development tools
```

## Quick Start

Guard an LLM call in three lines:

```python
from airiskguard import RiskGuard

guard = RiskGuard()

# Check user prompt before sending to LLM
pre = await guard.evaluate(
    input_data=user_message,
    output_data="",
    model_id="gpt-4",
    checks=["security", "compliance"],
)
if pre.blocked:
    return "Sorry, I can't process that request."

# ... call your LLM ...

# Check LLM response before returning to user
post = await guard.evaluate(
    input_data=user_message,
    output_data=llm_response,
    model_id="gpt-4",
    checks=["hallucination", "compliance"],
)
if post.blocked:
    return "Response filtered for safety."
```

For synchronous code, use `guard.evaluate_sync(...)` instead.

## Usage Guide

### Enterprise AI Coding Gateway

Stop secrets, PII, and proprietary code from leaving your network via AI coding tools:

```yaml
# gateway.yaml
upstream:
  anthropic: https://api.anthropic.com
  openai: https://api.openai.com

checks:
  outbound: [secrets, compliance, agent]   # scan prompts before sending
  inbound:  [vuln, agent]                  # scan completions before returning

policies:
  - name: block_secrets
    condition: {checker: secrets, risk: ">= high"}
    action: block
  - name: block_vuln_code
    condition: {checker: vuln, risk: ">= high"}
    action: block

teams:
  contractors:
    model_allowlist: [claude-haiku-4-5]    # restrict to cheaper model
    outbound_checks: [secrets, compliance, agent]
    api_keys: [gw-contractor-key-abc]
  engineers:
    model_allowlist: [claude-sonnet-4-6, gpt-4o]
    outbound_checks: [secrets, compliance]
    api_keys: [gw-engineer-key-xyz]

notifications:
  slack: https://hooks.slack.com/services/...

redact_secrets: true   # sanitise secrets before forwarding, don't just block
```

```bash
airiskguard-gateway --config gateway.yaml
```

### Guarding LLM Calls (SDK)

Wrap any LLM API call with pre- and post-evaluation:

```python
from airiskguard import RiskGuard

guard = RiskGuard(config={
    "enabled_checkers": ["security", "compliance", "hallucination"],
    "block_threshold": "high",
})

async def chat(user_message: str) -> str:
    pre = await guard.evaluate(
        input_data=user_message, output_data="",
        model_id="chatbot-v1", checks=["security", "compliance"],
    )
    if pre.blocked:
        return "Your message was flagged for safety reasons."

    llm_response = await call_openai(user_message)

    post = await guard.evaluate(
        input_data=user_message, output_data=llm_response,
        model_id="chatbot-v1", checks=["hallucination", "compliance"],
    )
    if post.blocked:
        return "I'm unable to provide that response."

    return llm_response
```

### Incident Notifications

Get alerted on Slack, webhook, PagerDuty, or email when evaluations are blocked:

```python
from airiskguard import RiskGuard
from airiskguard.notifications import NotificationManager, SlackChannel, PagerDutyChannel

guard = RiskGuard(
    notifications=NotificationManager([
        SlackChannel(webhook_url="https://hooks.slack.com/services/..."),
        PagerDutyChannel(routing_key="your-pd-key"),
    ])
)
```

### Policy-as-Code

Define governance rules in YAML — no Python required:

```yaml
# policies.yaml
policies:
  - name: block_high_security
    condition: {checker: security, risk: ">= high"}
    action: block

  - name: flag_pii_output
    condition: {checker: compliance, contains_flag: "pii_"}
    action: review

  - name: block_multiple_risks
    condition: {checkers_above: {risk: ">= high", count: ">= 2"}}
    action: block
```

```python
guard = RiskGuard(policies="policies.yaml")
```

### RAG Pipeline Safety

```python
# Check retrieved documents for PII
doc_check = await guard.evaluate(
    input_data=query,
    output_data="\n".join(retrieved_docs),
    model_id="rag-pipeline",
    checks=["compliance"],
)

# Check generated answer for hallucination
answer_check = await guard.evaluate(
    input_data=query,
    output_data=generated_answer,
    model_id="rag-pipeline",
    checks=["hallucination"],
    context={"known_urls": source_urls},
)
```

### FastAPI Middleware

```python
from fastapi import FastAPI
from airiskguard.integrations.fastapi import add_risk_guard

app = FastAPI()
add_risk_guard(app, config={"enabled_checkers": ["security", "compliance"]})
```

### Custom Checkers

```python
from airiskguard.checkers.base import BaseChecker
from airiskguard.checkers.registry import register_checker
from airiskguard.types import CheckResult, RiskLevel

class MyChecker(BaseChecker):
    name = "my_checker"

    async def check(self, input_data, output_data, context=None):
        score = await my_detection_logic(output_data)
        return CheckResult(
            checker_name=self.name,
            risk_level=RiskLevel.HIGH if score >= 0.7 else RiskLevel.LOW,
            passed=score < 0.7,
            score=score,
        )

register_checker("my_checker", MyChecker)
```

## Risk Checkers

| Checker | Use case | Key detections |
|---|---|---|
| `secrets` | Coding gateway, code review | API keys, AWS/GCP/Azure creds, private keys, DB URLs, JWTs — 18 types |
| `vuln` | Coding gateway, code review | SQL injection, shell injection, weak crypto, pickle, path traversal — 11 categories |
| `agent` | Agentic AI, tool calls | SQL injection in tool inputs, data exfiltration, prompt injection via tool outputs |
| `security` | Chatbots, LLM APIs | Prompt injection (~30 patterns), jailbreak (~20 patterns), encoding attacks |
| `compliance` | All deployments | PII (SSN, email, CC, phone), prohibited content, custom regex rules |
| `hallucination` | RAG, factual AI | Fabricated URLs, unverifiable citations, contradictions, overconfident language |
| `bias` | HR/lending/insurance AI | Disparate impact (4/5ths rule), demographic parity, equalized odds |
| `toxicity` | Consumer chatbots | Threats, hate speech, insults, profanity — pattern + ML backends |
| `fraud` | Fintech, transactions | Amount anomaly (z-score), velocity abuse, suspicious patterns |

## Configuration

```yaml
# airiskguard.yaml
storage_backend: sqlite          # memory | sqlite | json | postgres | redis
storage_path: ./airiskguard.db

block_threshold: high            # low | medium | high | critical
review_threshold: medium
score_block_threshold: 0.85

enabled_checkers:
  - security
  - compliance
  - hallucination
  - bias
  - secrets
  - vuln

audit_enabled: true
review_enabled: true
dashboard_enabled: true
```

## Architecture

```
airiskguard-gateway (HTTPS proxy)
├── SecretsChecker  — blocks 18 secret types before they leave the network
├── VulnChecker     — blocks insecure code before it reaches the developer
├── AgentChecker    — blocks SQL injection / exfiltration in tool calls
└── PolicyEngine    — per-team YAML rules (model allowlist, checker sets)

RiskGuard (SDK orchestrator)
├── Checkers: secrets, vuln, agent, security, compliance,
│            hallucination, bias, toxicity, fraud, [custom]
├── AuditLog        — immutable SHA-256 hash-chain per decision
├── RiskDashboard   — per-model metrics, trends, checker breakdowns
├── ModelRegistry   — lifecycle management (DRAFT → PRODUCTION → RETIRED)
├── ReviewWorkflow  — flag → approve/reject/escalate with callbacks
├── PolicyEngine    — declarative YAML rules (block / review / log)
├── NotificationManager — Slack, webhook, PagerDuty, email
├── TelemetryExporter — OpenTelemetry traces + metrics
└── Storage         — Memory | SQLite | JSON | PostgreSQL | Redis
```

## Benchmark Results (v0.3.0)

| Checker | Precision | Recall | F1 | FPR |
|---|---|---|---|---|
| security | 100% | 85.7% | 91.9% | 0% |
| compliance | 100% | 66.7% | 80.0% | 0% |
| hallucination | 100% | 88.9% | 94.1% | 14.3% |
| bias | 100% | 100% | 100% | 0% |
| toxicity | 100% | 66.7% | 80.0% | 0% |

## Examples

| Example | Description |
|---|---|
| [`opentelemetry_tracing.py`](examples/opentelemetry_tracing.py) | OTel traces + metrics for every evaluation |
| [`policy_as_code.py`](examples/policy_as_code.py) | Declarative YAML governance rules |
| [`langchain_integration.py`](examples/langchain_integration.py) | LangChain callback handler |
| [`llamaindex_integration.py`](examples/llamaindex_integration.py) | LlamaIndex query engine wrapper |
| [`openai_guarded.py`](examples/openai_guarded.py) | Drop-in OpenAI SDK replacement |
| [`llm_openai_chat.py`](examples/llm_openai_chat.py) | Wrapping OpenAI chat with pre/post checks |
| [`rag_pipeline.py`](examples/rag_pipeline.py) | RAG pipeline with hallucination checking |
| [`multi_agent.py`](examples/multi_agent.py) | Multi-agent with per-agent tracking |
| [`fastapi_app.py`](examples/fastapi_app.py) | FastAPI chat API with risk headers |

## Editions

airiskguard is open-core. The community edition (this repo) is free and open-source. Team and Enterprise editions add centralized management, compliance reporting, and enterprise integrations.

| Feature | Community | Team | Enterprise |
|---|:---:|:---:|:---:|
| Local HTTPS proxy | ✓ | ✓ | ✓ |
| Secret detection (18 types) | ✓ | ✓ | ✓ |
| OWASP Top 10 inbound scanning | ✓ | ✓ | ✓ |
| Local YAML config | ✓ | ✓ | ✓ |
| Model allowlist | ✓ | ✓ | ✓ |
| **Centralized policy server** | — | ✓ | ✓ |
| **Per-team policies + gateway-issued keys** | — | ✓ | ✓ |
| **Dashboard (web UI)** | — | ✓ | ✓ |
| **ML-based PII detection** | — | ✓ | ✓ |
| **30-day audit log (centralized, searchable)** | — | ✓ | ✓ |
| **SSO (SAML / OIDC)** | — | ✓ | ✓ |
| **Slack / PagerDuty / webhook notifications** | — | ✓ | ✓ |
| **Custom scanning rules** | — | — | ✓ |
| **Compliance reports (EU AI Act, SOC 2, ISO 42001)** | — | — | ✓ |
| **Unlimited audit log + SIEM export** | — | — | ✓ |
| **RBAC (admin / policy-author / viewer)** | — | — | ✓ |
| **Self-hosted / air-gapped deployment** | — | — | ✓ |
| **SLA + dedicated support** | — | — | ✓ |
| **Incident response playbooks** | — | — | ✓ |
| **Pricing** | Free | Per seat / month | Annual contract |

**[Contact us](mailto:sales@airiskguard.ai) for Team and Enterprise access.**

## License

MIT — Community Edition only. Team and Enterprise editions are distributed under a commercial license. See [airiskguard.ai/pricing](https://www.airiskguard.ai/pricing/) for details.
