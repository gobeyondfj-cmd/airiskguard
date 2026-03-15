# airiskguard

AI Risk Governance Framework for LLM applications, AI agents, and ML systems. Provides risk checkers, audit logs, model registry, dashboards, anomaly detection, regulatory reports, and human review workflows.

## Installation

```bash
pip install airiskguard
```

With optional extras:

```bash
pip install airiskguard[fastapi]         # FastAPI integration
pip install airiskguard[flask]           # Flask integration
pip install airiskguard[transformers]    # ML-based hallucination detection (NLI)
pip install airiskguard[dev]             # Development tools
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

### Guarding LLM Calls

Wrap any LLM API call (OpenAI, Anthropic, etc.) with pre- and post-evaluation:

```python
from airiskguard import RiskGuard

guard = RiskGuard(config={
    "enabled_checkers": ["security", "compliance", "hallucination"],
    "block_threshold": "high",
})

async def chat(user_message: str) -> str:
    # Pre-check: block prompt injection, PII leakage, jailbreaks
    pre = await guard.evaluate(
        input_data=user_message,
        output_data="",
        model_id="chatbot-v1",
        checks=["security", "compliance"],
    )
    if pre.blocked:
        return "Your message was flagged for safety reasons."

    # Call your LLM
    llm_response = await call_openai(user_message)

    # Post-check: catch hallucinations, compliance violations
    post = await guard.evaluate(
        input_data=user_message,
        output_data=llm_response,
        model_id="chatbot-v1",
        checks=["hallucination", "compliance"],
    )
    if post.blocked:
        return "I'm unable to provide that response."

    return llm_response
```

See [`examples/llm_openai_chat.py`](examples/llm_openai_chat.py) for a complete example.

### RAG Pipeline Safety

Check both retrieved context and generated responses:

```python
# Check retrieved documents for compliance (PII, prohibited content)
doc_check = await guard.evaluate(
    input_data=query,
    output_data="\n".join(retrieved_docs),
    model_id="rag-pipeline",
    checks=["compliance"],
)

# Check generated answer for hallucination with source URLs
answer_check = await guard.evaluate(
    input_data=query,
    output_data=generated_answer,
    model_id="rag-pipeline",
    checks=["hallucination"],
    context={"known_urls": source_urls},
)
```

The hallucination checker uses `known_urls` in the context to distinguish real source URLs from fabricated ones. See [`examples/rag_pipeline.py`](examples/rag_pipeline.py).

### Multi-Agent Systems

Use a shared `RiskGuard` instance across agents for unified audit trails and dashboards:

```python
guard = RiskGuard()

# Each agent uses its own model_id for tracking
planner_report = await guard.evaluate(
    input_data=task, output_data=plan,
    model_id="planner-agent",
)

coder_report = await guard.evaluate(
    input_data=plan, output_data=code,
    model_id="coder-agent",
)

# Per-agent dashboards
planner_stats = await guard.dashboard.get_summary(model_id="planner-agent")
coder_stats = await guard.dashboard.get_summary(model_id="coder-agent")
```

Escalate when accumulated risk across an agent chain is too high. See [`examples/multi_agent.py`](examples/multi_agent.py).

### Tool-Calling Agents

Validate tool inputs before execution and check outputs before returning to the LLM:

```python
from airiskguard import RiskGuard
from airiskguard.checkers.base import BaseChecker
from airiskguard.checkers.registry import register_checker
from airiskguard.types import CheckResult, RiskLevel

# Custom checker for dangerous tool patterns
class ToolSafetyChecker(BaseChecker):
    name = "tool_safety"

    async def check(self, input_data, output_data, context=None):
        tool_name = input_data.get("tool", "") if isinstance(input_data, dict) else ""
        flags = []
        score = 0.0
        blocked_tools = {"rm", "delete_file", "drop_table", "exec_raw_sql"}
        if tool_name in blocked_tools:
            flags.append(f"blocked_tool: {tool_name}")
            score = 0.95
        risk = RiskLevel.CRITICAL if score >= 0.8 else RiskLevel.LOW
        return CheckResult(
            checker_name=self.name, risk_level=risk,
            passed=score < 0.5, score=score, details={"flags": flags},
        )

register_checker("tool_safety", ToolSafetyChecker)

guard = RiskGuard(config={"enabled_checkers": ["tool_safety", "security", "compliance"]})
```

See [`examples/tool_calling_agent.py`](examples/tool_calling_agent.py) for a complete agent loop.

### Chatbot Middleware (FastAPI)

Add risk governance to a chat API with one-line middleware or explicit evaluation:

```python
from fastapi import FastAPI
from airiskguard import RiskGuard
from airiskguard.integrations.fastapi import add_risk_guard

app = FastAPI()
guard = RiskGuard()

# Option 1: automatic middleware (adds x-risk-score, x-risk-level headers)
add_risk_guard(app, config={"enabled_checkers": ["security", "compliance"]})

# Option 2: explicit evaluation in endpoints
@app.post("/chat")
async def chat(request: dict):
    report = await guard.evaluate(
        input_data=request["message"],
        output_data="",
        model_id="chatbot",
        checks=["security"],
    )
    if report.blocked:
        return {"error": "Message blocked", "risk_level": report.overall_risk.value}
    # ... generate response ...
```

See [`examples/fastapi_app.py`](examples/fastapi_app.py) for a full chat API with streaming.

### Streaming Responses

For streaming LLM responses, accumulate chunks and check after generation completes:

```python
chunks = []
async for chunk in llm_stream(user_message):
    chunks.append(chunk)
    yield chunk  # stream to user

full_response = "".join(chunks)

# Post-check the complete response
report = await guard.evaluate(
    input_data=user_message,
    output_data=full_response,
    model_id="chatbot-v1",
    checks=["hallucination", "compliance"],
)
if report.blocked:
    # Log for review; response already streamed
    await guard.review.flag_for_review("chatbot-v1", report)
```

### Custom Checkers

Write domain-specific checkers by extending `BaseChecker`:

```python
from airiskguard.checkers.base import BaseChecker
from airiskguard.checkers.registry import register_checker
from airiskguard.types import CheckResult, RiskLevel

class ToxicityChecker(BaseChecker):
    name = "toxicity"

    def __init__(self, threshold: float = 0.7):
        self.threshold = threshold

    async def check(self, input_data, output_data, context=None):
        # Your detection logic here (call an API, run a model, etc.)
        toxicity_score = await detect_toxicity(output_data)

        if toxicity_score >= self.threshold:
            risk = RiskLevel.HIGH
            passed = False
        else:
            risk = RiskLevel.LOW
            passed = True

        return CheckResult(
            checker_name=self.name,
            risk_level=risk,
            passed=passed,
            score=toxicity_score,
            details={"toxicity_score": toxicity_score},
        )

# Register so RiskGuard can load it by name
register_checker("toxicity", ToxicityChecker)

# Use it
guard = RiskGuard(config={
    "enabled_checkers": ["toxicity", "security"],
    "checker_configs": {"toxicity": {"threshold": 0.6}},
})
```

## Configuration

### YAML Configuration

```yaml
# airiskguard.yaml
storage_backend: sqlite          # memory | sqlite | json
storage_path: ./airiskguard.db

block_threshold: high            # low | medium | high | critical
review_threshold: medium
score_block_threshold: 0.85

enabled_checkers:
  - security
  - compliance
  - hallucination
  - bias

checker_configs:
  compliance:
    detect_pii: true
    detect_prohibited: true
    custom_rules:
      - name: api_key_pattern
        pattern: '(?:sk|pk)[-_][a-zA-Z0-9]{32,}'
  hallucination:
    use_nli: false               # true requires transformers extra
  security:
    check_encoding: true

audit_enabled: true
review_enabled: true
review_auto_escalate: true       # auto-escalate CRITICAL to review
dashboard_enabled: true
```

Load via path or dict:

```python
guard = RiskGuard(config="airiskguard.yaml")
# or
guard = RiskGuard(config={"block_threshold": "high", "enabled_checkers": ["security"]})
```

### Configuration Reference

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `storage_backend` | str | `"memory"` | `"memory"`, `"sqlite"`, or `"json"` |
| `storage_path` | str | `""` | Path for sqlite/json backends |
| `block_threshold` | str | `"critical"` | Auto-block if risk >= this level |
| `review_threshold` | str | `"high"` | Flag for human review if risk >= this |
| `score_block_threshold` | float | `0.9` | Block if numeric score >= this |
| `enabled_checkers` | list | all five | Which checkers to load |
| `checker_configs` | dict | `{}` | Per-checker configuration |
| `audit_enabled` | bool | `true` | Enable immutable audit trail |
| `review_enabled` | bool | `true` | Enable human review workflow |
| `review_auto_escalate` | bool | `true` | Auto-escalate CRITICAL items |
| `dashboard_enabled` | bool | `true` | Record evaluation metrics |
| `anomaly_contamination` | float | `0.1` | IsolationForest contamination param |
| `drift_significance` | float | `0.05` | KS test p-value threshold |

## Risk Checkers

| Checker | Detects |
|---------|---------|
| `security` | Prompt injection (~30 patterns), jailbreak (~20 patterns), encoding attacks, system prompt leakage |
| `compliance` | PII (SSN, email, credit card, phone), prohibited content, custom regex rules |
| `hallucination` | Fabricated URLs, unverifiable citations, contradictions, overconfident language, NLI-based contradiction |
| `bias` | Disparate impact (4/5ths rule), demographic parity, equalized odds, biased language |
| `fraud` | Amount anomaly (z-score), velocity abuse, suspicious patterns (round amounts, currency mismatch) |

### Checker Details

**Security** — Detects prompt injection attempts ("ignore previous instructions", system prompt markers, roleplay attacks), jailbreak patterns ("DAN mode", "unrestricted mode"), and encoding attacks (base64-encoded injections, homoglyphs). Also checks LLM output for system prompt leakage.

**Compliance** — Scans both input and output for PII (SSN: weight 0.9, credit card: 0.9, email: 0.4, phone: 0.5, IP: 0.3). Detects prohibited content (violence instructions, illegal activity, self-harm: score 0.95). Supports custom regex rules.

**Hallucination** — Heuristic mode detects fabricated URLs (not in `context["known_urls"]`), suspicious citations ("According to Author (YYYY)"), overconfident language ("100%", "guaranteed"), and internal contradictions (always/never pairs). Optional NLI mode uses `cross-encoder/nli-deberta-v3-small` for semantic contradiction detection.

**Bias** — Computes disparate impact ratio against the 4/5ths rule threshold using `context["group_outcomes"]`. Checks demographic parity gap, equalized odds (TPR/FPR differences using `context["predictions"]` and `context["labels"]`), and biased language patterns.

**Fraud** — Transaction-focused: z-score anomaly on amounts, per-user velocity tracking, pattern rules (round large amounts, currency/country mismatch).

## Features

- **Model Registry** — register, version, and manage model lifecycles (draft, validation, production, deprecated, retired)
- **Audit Log** — immutable SHA-256 hash-chain audit trail with tamper verification
- **Risk Dashboard** — aggregate metrics, trends, per-checker breakdowns, JSON export
- **Anomaly Detection** — IsolationForest for anomalies, Kolmogorov-Smirnov test for drift
- **Regulatory Reports** — GDPR, SOX, EU AI Act compliance reports (JSON + HTML)
- **Human Review** — threshold-based flagging with approve/reject/escalate workflows and async callbacks
- **Framework Integration** — FastAPI, Flask, ASGI, WSGI middleware with automatic risk headers
- **Decorator Pattern** — `@risk_guard()` for wrapping any sync/async function
- **Custom Checkers** — extend `BaseChecker` and register for domain-specific risk detection

## Architecture

```
RiskGuard (orchestrator)
├── Checkers: security, compliance, hallucination, bias, fraud, [custom]
├── AuditLog: immutable hash-chain (SHA-256) per decision
├── RiskDashboard: per-model metrics, trends, checker breakdowns
├── ModelRegistry: lifecycle management (DRAFT → PRODUCTION → RETIRED)
├── ReviewWorkflow: flag → approve/reject/escalate with callbacks
├── AnomalyDetector: IsolationForest + KS drift
├── ReportGenerator: GDPR, SOX, EU AI Act
└── Storage: MemoryStorage | SQLiteStorage | JSONFileStorage
```

Each `evaluate()` call runs selected checkers, aggregates risk, logs to audit trail, records dashboard metrics, and optionally flags for human review — all in a single async call.

## Examples

| Example | Description |
|---------|-------------|
| [`llm_openai_chat.py`](examples/llm_openai_chat.py) | Wrapping OpenAI chat completions with pre/post risk checks |
| [`rag_pipeline.py`](examples/rag_pipeline.py) | RAG pipeline with document compliance + hallucination checking |
| [`multi_agent.py`](examples/multi_agent.py) | Multi-agent orchestrator with per-agent tracking and escalation |
| [`tool_calling_agent.py`](examples/tool_calling_agent.py) | Tool-calling agent with input/output validation and custom checker |
| [`fastapi_app.py`](examples/fastapi_app.py) | FastAPI chat API with streaming and risk headers |
| [`flask_app.py`](examples/flask_app.py) | Flask integration with synchronous evaluation |
| [`standalone_usage.py`](examples/standalone_usage.py) | Direct API usage with all core features |

## License

MIT
