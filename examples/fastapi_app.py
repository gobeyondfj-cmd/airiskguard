"""FastAPI chat API with airiskguard risk governance.

Demonstrates:
- /chat endpoint wrapping LLM calls with pre/post risk checks
- /chat/stream endpoint with accumulated response checking
- Risk headers on all responses
- Dashboard and audit endpoints

Requires: pip install fastapi uvicorn airiskguard
Run: uvicorn examples.fastapi_app:app --reload
"""

from __future__ import annotations

import asyncio
import json
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse

from airiskguard import RiskGuard
from airiskguard.integrations.fastapi import add_risk_guard

app = FastAPI(title="AI Chat Service")

# Automatic middleware: adds x-risk-score, x-risk-level headers to all responses
add_risk_guard(app, config={"enabled_checkers": ["security", "compliance"]})

# Direct guard for explicit evaluation in endpoints
guard = RiskGuard(config={
    "enabled_checkers": ["security", "compliance", "hallucination"],
    "block_threshold": "high",
    "review_threshold": "medium",
    "storage_backend": "memory",
})


# --- Simulated LLM ---

async def call_llm(messages: list[dict[str, str]]) -> str:
    """Simulate an LLM call. Replace with OpenAI/Anthropic client."""
    user_msg = messages[-1]["content"]
    return f"I'd be happy to help with: {user_msg}"


async def stream_llm(messages: list[dict[str, str]]) -> AsyncIterator[str]:
    """Simulate streaming LLM response."""
    response = await call_llm(messages)
    words = response.split()
    for word in words:
        await asyncio.sleep(0.05)
        yield word + " "


# --- Startup ---

@app.on_event("startup")
async def startup() -> None:
    await guard.initialize()
    await guard.registry.register(
        name="chat-model", version="1.0",
        owner="ml-team", model_id="chatbot-v1",
    )


# --- Chat endpoint ---

@app.post("/chat")
async def chat(request: Request) -> JSONResponse:
    """Chat endpoint with pre/post risk evaluation."""
    data = await request.json()
    user_message = data.get("message", "")
    conversation = data.get("messages", [{"role": "user", "content": user_message}])

    # Pre-check: security and compliance on user input
    pre_report = await guard.evaluate(
        input_data=user_message,
        output_data="",
        model_id="chatbot-v1",
        checks=["security", "compliance"],
    )

    if pre_report.blocked:
        return JSONResponse(
            status_code=403,
            content={
                "error": "Message blocked by safety check",
                "risk_level": pre_report.overall_risk.value,
                "risk_score": pre_report.overall_score,
            },
            headers={
                "x-risk-level": pre_report.overall_risk.value,
                "x-risk-score": str(pre_report.overall_score),
            },
        )

    # Call LLM
    llm_response = await call_llm(conversation)

    # Post-check: hallucination and compliance on LLM response
    post_report = await guard.evaluate(
        input_data=user_message,
        output_data=llm_response,
        model_id="chatbot-v1",
        checks=["hallucination", "compliance"],
    )

    if post_report.blocked:
        return JSONResponse(
            status_code=422,
            content={
                "error": "Response filtered for safety",
                "risk_level": post_report.overall_risk.value,
            },
            headers={
                "x-risk-level": post_report.overall_risk.value,
                "x-risk-score": str(post_report.overall_score),
            },
        )

    return JSONResponse(
        content={
            "response": llm_response,
            "risk_level": post_report.overall_risk.value,
            "risk_score": post_report.overall_score,
        },
        headers={
            "x-risk-level": post_report.overall_risk.value,
            "x-risk-score": str(post_report.overall_score),
        },
    )


# --- Streaming chat endpoint ---

@app.post("/chat/stream")
async def chat_stream(request: Request) -> StreamingResponse:
    """Streaming chat endpoint. Accumulates chunks and checks after generation."""
    data = await request.json()
    user_message = data.get("message", "")
    conversation = data.get("messages", [{"role": "user", "content": user_message}])

    # Pre-check on user input
    pre_report = await guard.evaluate(
        input_data=user_message,
        output_data="",
        model_id="chatbot-v1",
        checks=["security", "compliance"],
    )

    if pre_report.blocked:
        async def blocked_stream() -> AsyncIterator[str]:
            yield json.dumps({
                "error": "Message blocked by safety check",
                "risk_level": pre_report.overall_risk.value,
            })

        return StreamingResponse(
            blocked_stream(),
            media_type="text/event-stream",
            headers={"x-risk-level": pre_report.overall_risk.value},
        )

    # Stream response, accumulate for post-check
    async def checked_stream() -> AsyncIterator[str]:
        chunks: list[str] = []
        async for chunk in stream_llm(conversation):
            chunks.append(chunk)
            yield f"data: {json.dumps({'text': chunk})}\n\n"

        # Post-check the full accumulated response
        full_response = "".join(chunks)
        post_report = await guard.evaluate(
            input_data=user_message,
            output_data=full_response,
            model_id="chatbot-v1",
            checks=["hallucination", "compliance"],
        )

        # Send risk metadata as final SSE event
        yield f"data: {json.dumps({'done': True, 'risk_level': post_report.overall_risk.value, 'risk_score': post_report.overall_score})}\n\n"

        if post_report.blocked:
            yield f"data: {json.dumps({'warning': 'Response flagged for review', 'risk_level': post_report.overall_risk.value})}\n\n"
            await guard.review.flag_for_review("chatbot-v1", post_report)

    return StreamingResponse(
        checked_stream(),
        media_type="text/event-stream",
    )


# --- Dashboard and audit endpoints ---

@app.get("/risk/dashboard")
async def dashboard() -> JSONResponse:
    """Risk dashboard with aggregate metrics."""
    summary = await guard.dashboard.get_summary(model_id="chatbot-v1")
    breakdown = await guard.dashboard.get_checker_breakdown(model_id="chatbot-v1")
    return JSONResponse(content={
        "summary": summary,
        "checker_breakdown": breakdown,
    })


@app.get("/risk/audit")
async def audit_trail() -> JSONResponse:
    """Recent audit trail entries."""
    entries = await guard.audit.query(model_id="chatbot-v1", limit=50)
    return JSONResponse(content=[
        {
            "entry_id": e.entry_id,
            "action": e.action,
            "risk_level": e.risk_level.value,
            "score": e.score,
            "timestamp": e.timestamp,
        }
        for e in entries
    ])


@app.get("/risk/review-queue")
async def review_queue() -> JSONResponse:
    """Pending review items."""
    queue = await guard.review.get_queue()
    return JSONResponse(content=[
        {
            "review_id": item.review_id,
            "model_id": item.model_id,
            "status": item.status.value,
            "risk_level": item.risk_report.overall_risk.value,
            "created_at": item.created_at,
        }
        for item in queue
    ])
