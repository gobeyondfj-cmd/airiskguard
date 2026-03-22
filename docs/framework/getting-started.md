# Getting Started

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

## Guarding LLM Calls

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

## RAG Pipeline Safety

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

## Multi-Agent Systems

Use a shared `RiskGuard` instance across agents for unified audit trails:

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

## FastAPI Middleware

Add risk governance to a chat API with one-line middleware:

```python
from fastapi import FastAPI
from airiskguard import RiskGuard
from airiskguard.integrations.fastapi import add_risk_guard

app = FastAPI()
guard = RiskGuard()

# Automatic middleware (adds x-risk-score, x-risk-level headers)
add_risk_guard(app, config={
    "enabled_checkers": ["security", "compliance"]
})
```

## Custom Checkers

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
        toxicity_score = await detect_toxicity(output_data)
        risk = RiskLevel.HIGH if toxicity_score >= self.threshold else RiskLevel.LOW
        return CheckResult(
            checker_name=self.name,
            risk_level=risk,
            passed=toxicity_score < self.threshold,
            score=toxicity_score,
        )

register_checker("toxicity", ToxicityChecker)
```

## Assessing Against the Standard

Evaluate your AI system against AIRMS v1.0:

```python
from airiskguard.standards import STANDARD_V1, StandardAssessor

assessor = StandardAssessor(STANDARD_V1)

# Record manually verified controls
assessor.set_control_status("ACC-GOV-01", implemented=True, maturity=3)
assessor.set_control_status("TRA-DIS-01", implemented=True, maturity=4)

# Integrate automated checker results
assessor.apply_checker_results(report)

# Run full assessment
result = assessor.assess(model_id="my-model")
print(result.summary())
```
