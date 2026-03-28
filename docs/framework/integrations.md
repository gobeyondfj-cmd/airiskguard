# Integrations

airiskguard integrates natively with the most popular LLM frameworks. Add risk governance to your existing stack with minimal code changes.

## LangChain

Install:

```bash
pip install airiskguard[langchain]
```

Use `RiskGuardCallbackHandler` with any LangChain LLM, chain, or agent:

```python
from airiskguard import RiskGuard
from airiskguard.integrations.langchain import RiskGuardCallbackHandler

guard = RiskGuard()
handler = RiskGuardCallbackHandler(
    guard,
    model_id="my-app",
    input_checks=["security", "compliance"],
    output_checks=["hallucination", "compliance"],
)

# Attach to any LLM
from langchain_openai import ChatOpenAI
llm = ChatOpenAI(callbacks=[handler])

# Or pass at invocation time
result = await chain.ainvoke({"question": "..."}, config={"callbacks": [handler]})
```

The handler evaluates:

- **LLM inputs** — on `on_llm_start` / `on_llm_start_async`
- **LLM outputs** — on `on_llm_end` / `on_llm_end_async`
- **Tool inputs** — on `on_tool_start` (blocks dangerous tool calls)
- **Tool outputs** — on `on_tool_end`

Raises `RiskBlockedError` when blocked, halting the chain. Set `raise_on_block=False` to log and continue instead.

---

## LlamaIndex

Install:

```bash
pip install airiskguard[llamaindex]
```

### QueryEngine wrapper (recommended)

Wraps any query engine with pre/post risk checks. Zero changes to your existing pipeline:

```python
from airiskguard import RiskGuard
from airiskguard.integrations.llamaindex import RiskGuardQueryEngineWrapper

guard = RiskGuard()

base_engine = index.as_query_engine()
engine = RiskGuardQueryEngineWrapper(
    base_engine,
    guard,
    model_id="rag-app",
)

# Sync
response = engine.query("What is the refund policy?")

# Async
response = await engine.aquery("What is the refund policy?")
```

Source URLs are automatically extracted from `source_nodes` and passed to the hallucination checker as `known_urls` — fabricated citations are caught automatically.

### CallbackManager handler

For deeper event-level tracing (LLM calls, retrievals):

```python
from llama_index.core import Settings
from llama_index.core.callbacks import CallbackManager
from airiskguard.integrations.llamaindex import RiskGuardCallbackHandler

handler = RiskGuardCallbackHandler(guard, model_id="rag-app")
Settings.callback_manager = CallbackManager([handler])

# All LLM calls and retrievals are now automatically evaluated
engine = index.as_query_engine()
response = engine.query("What is the refund policy?")
```

---

## OpenAI SDK

Install:

```bash
pip install airiskguard[openai]
```

Drop-in replacements for `AsyncOpenAI` and `OpenAI` — one line change:

```python
# Before
from openai import AsyncOpenAI
client = AsyncOpenAI()

# After
from airiskguard.integrations.openai import GuardedAsyncOpenAI
client = GuardedAsyncOpenAI(guard, model_id="my-app")

# Everything else stays the same
response = await client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello"}],
)
```

Sync version:

```python
from airiskguard.integrations.openai import GuardedOpenAI
client = GuardedOpenAI(guard, model_id="my-app")
response = client.chat.completions.create(...)
```

All `openai.AsyncOpenAI` / `openai.OpenAI` constructor arguments (`api_key`, `base_url`, `timeout`, etc.) are forwarded transparently.

---

## FastAPI

Install:

```bash
pip install airiskguard[fastapi]
```

```python
from fastapi import FastAPI
from airiskguard import RiskGuard
from airiskguard.integrations.fastapi import add_risk_guard

app = FastAPI()
guard = RiskGuard()

# Automatic middleware — adds x-risk-score and x-risk-level headers
add_risk_guard(app, config={"enabled_checkers": ["security", "compliance"]})
```

---

## Flask

Install:

```bash
pip install airiskguard[flask]
```

```python
from flask import Flask
from airiskguard import RiskGuard
from airiskguard.integrations.flask import add_risk_guard

app = Flask(__name__)
guard = RiskGuard()
add_risk_guard(app, guard)
```

---

## Production Storage

For multi-instance deployments, use PostgreSQL or Redis instead of the default in-memory backend:

```python
# PostgreSQL
guard = RiskGuard(config={
    "storage_backend": "postgres",
    "storage_path": "postgresql://user:pass@host/dbname",
    "storage_pool_max_size": 20,
})

# Redis
guard = RiskGuard(config={
    "storage_backend": "redis",
    "storage_path": "redis://localhost:6379",
})
```

Install the extras:

```bash
pip install airiskguard[postgres]
pip install airiskguard[redis]
```
