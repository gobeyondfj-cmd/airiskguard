# Getting Started

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

## Guarding LLM Calls

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

## RAG Pipeline Safety

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

```python
guard = RiskGuard()

planner_report = await guard.evaluate(
    input_data=task, output_data=plan,
    model_id="planner-agent",
)

coder_report = await guard.evaluate(
    input_data=plan, output_data=code,
    model_id="coder-agent",
)

planner_stats = await guard.dashboard.get_summary(model_id="planner-agent")
coder_stats = await guard.dashboard.get_summary(model_id="coder-agent")
```

## FastAPI Middleware

```python
from fastapi import FastAPI
from airiskguard.integrations.fastapi import add_risk_guard

app = FastAPI()
add_risk_guard(app, config={"enabled_checkers": ["security", "compliance"]})
```

## Custom Checkers

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

## Assessing Against the Standard

```python
from airiskguard.standards import STANDARD_V1, StandardAssessor

assessor = StandardAssessor(STANDARD_V1)
assessor.set_control_status("ACC-GOV-01", implemented=True, maturity=3)
assessor.apply_checker_results(report)
result = assessor.assess(model_id="my-model")
print(result.summary())
```
