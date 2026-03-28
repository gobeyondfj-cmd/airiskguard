"""LlamaIndex integration for airiskguard.

Two integration points:

1. **RiskGuardQueryEngineWrapper** — wraps any QueryEngine with pre/post risk checks.
   Zero changes to your existing pipeline.

2. **RiskGuardCallbackHandler** — plugs into LlamaIndex's CallbackManager for
   event-level tracing (LLM calls, retrievals, embeddings).

Usage::

    from airiskguard import RiskGuard
    from airiskguard.integrations.llamaindex import (
        RiskGuardQueryEngineWrapper,
        RiskGuardCallbackHandler,
    )

    guard = RiskGuard()

    # Option 1: wrap your query engine
    base_engine = index.as_query_engine()
    engine = RiskGuardQueryEngineWrapper(base_engine, guard, model_id="rag-app")
    response = engine.query("What is the refund policy?")

    # Option 2: callback manager (deeper tracing)
    from llama_index.core.callbacks import CallbackManager
    handler = RiskGuardCallbackHandler(guard, model_id="rag-app")
    Settings.callback_manager = CallbackManager([handler])
"""

from __future__ import annotations

import asyncio
from typing import Any

try:
    from llama_index.core.callbacks.base_handler import BaseCallbackHandler as LlamaBaseCallbackHandler
    from llama_index.core.callbacks.schema import CBEventType, EventPayload
except ImportError as e:
    raise ImportError(
        "LlamaIndex integration requires llama-index-core. "
        "Install with: pip install airiskguard[llamaindex]"
    ) from e

from airiskguard.exceptions import RiskBlockedError
from airiskguard.types import RiskReport


def _run(coro: Any) -> Any:
    """Run a coroutine from a sync context."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor() as pool:
        return pool.submit(asyncio.run, coro).result()


class RiskGuardQueryEngineWrapper:
    """Wraps any LlamaIndex QueryEngine with pre/post risk evaluation.

    Args:
        engine: Any LlamaIndex query engine (sync or async).
        guard: A :class:`~airiskguard.RiskGuard` instance.
        model_id: Identifier for audit logs and dashboard metrics.
        input_checks: Checkers to run on the query. Defaults to ``["security", "compliance"]``.
        output_checks: Checkers to run on the response. Defaults to ``["hallucination", "compliance"]``.
        raise_on_block: Raise :class:`RiskBlockedError` when blocked (default ``True``).
        context: Extra context forwarded to checkers (e.g. ``known_urls`` for hallucination).
    """

    def __init__(
        self,
        engine: Any,
        guard: Any,
        model_id: str = "llamaindex",
        input_checks: list[str] | None = None,
        output_checks: list[str] | None = None,
        raise_on_block: bool = True,
        context: dict[str, Any] | None = None,
    ) -> None:
        self._engine = engine
        self.guard = guard
        self.model_id = model_id
        self.input_checks = input_checks or ["security", "compliance"]
        self.output_checks = output_checks or ["hallucination", "compliance"]
        self.raise_on_block = raise_on_block
        self.context = context or {}

    def _handle_report(self, report: RiskReport, phase: str) -> None:
        if report.blocked and self.raise_on_block:
            raise RiskBlockedError(
                f"[airiskguard] {phase} blocked by {self.model_id} "
                f"(risk={report.overall_risk.value}, score={report.overall_score:.2f})",
                report=report,
            )

    def query(self, query_str: str, **kwargs: Any) -> Any:
        """Evaluate query, call engine, evaluate response."""
        report = _run(self.guard.evaluate(
            input_data=query_str,
            output_data="",
            model_id=self.model_id,
            checks=self.input_checks,
            context=self.context,
        ))
        self._handle_report(report, "query input")

        response = self._engine.query(query_str, **kwargs)

        response_text = str(response)
        source_urls = _extract_source_urls(response)
        ctx = {**self.context, "known_urls": source_urls}

        report = _run(self.guard.evaluate(
            input_data=query_str,
            output_data=response_text,
            model_id=self.model_id,
            checks=self.output_checks,
            context=ctx,
        ))
        self._handle_report(report, "query response")
        return response

    async def aquery(self, query_str: str, **kwargs: Any) -> Any:
        """Async version of :meth:`query`."""
        report = await self.guard.evaluate(
            input_data=query_str,
            output_data="",
            model_id=self.model_id,
            checks=self.input_checks,
            context=self.context,
        )
        self._handle_report(report, "query input")

        response = await self._engine.aquery(query_str, **kwargs)

        response_text = str(response)
        source_urls = _extract_source_urls(response)
        ctx = {**self.context, "known_urls": source_urls}

        report = await self.guard.evaluate(
            input_data=query_str,
            output_data=response_text,
            model_id=self.model_id,
            checks=self.output_checks,
            context=ctx,
        )
        self._handle_report(report, "query response")
        return response

    def __getattr__(self, name: str) -> Any:
        """Proxy any other engine attributes transparently."""
        return getattr(self._engine, name)


class RiskGuardCallbackHandler(LlamaBaseCallbackHandler):
    """LlamaIndex CallbackManager handler for event-level risk tracing.

    Hooks into LLM start/end and retrieval events. Use alongside
    :class:`RiskGuardQueryEngineWrapper` for full coverage, or standalone
    for lighter-weight tracing.

    Args:
        guard: A :class:`~airiskguard.RiskGuard` instance.
        model_id: Identifier for audit logs and dashboard metrics.
        llm_input_checks: Checkers for LLM inputs.
        llm_output_checks: Checkers for LLM outputs.
        raise_on_block: Raise :class:`RiskBlockedError` when blocked.
    """

    def __init__(
        self,
        guard: Any,
        model_id: str = "llamaindex",
        llm_input_checks: list[str] | None = None,
        llm_output_checks: list[str] | None = None,
        raise_on_block: bool = True,
    ) -> None:
        super().__init__(
            event_starts_to_ignore=[],
            event_ends_to_ignore=[],
        )
        self.guard = guard
        self.model_id = model_id
        self.llm_input_checks = llm_input_checks or ["security", "compliance"]
        self.llm_output_checks = llm_output_checks or ["hallucination", "compliance"]
        self.raise_on_block = raise_on_block
        self._event_inputs: dict[str, str] = {}

    def _handle_report(self, report: RiskReport, phase: str) -> None:
        if report.blocked and self.raise_on_block:
            raise RiskBlockedError(
                f"[airiskguard] {phase} blocked by {self.model_id} "
                f"(risk={report.overall_risk.value}, score={report.overall_score:.2f})",
                report=report,
            )

    def on_event_start(
        self,
        event_type: CBEventType,
        payload: dict[str, Any] | None = None,
        event_id: str = "",
        parent_id: str = "",
        **kwargs: Any,
    ) -> str:
        if event_type == CBEventType.LLM and payload:
            messages = payload.get(EventPayload.MESSAGES, [])
            prompt = payload.get(EventPayload.PROMPT, "")
            input_text = prompt or " ".join(str(m) for m in messages)
            self._event_inputs[event_id] = input_text
            report = _run(self.guard.evaluate(
                input_data=input_text,
                output_data="",
                model_id=self.model_id,
                checks=self.llm_input_checks,
            ))
            self._handle_report(report, "LLM input")
        return event_id

    def on_event_end(
        self,
        event_type: CBEventType,
        payload: dict[str, Any] | None = None,
        event_id: str = "",
        **kwargs: Any,
    ) -> None:
        if event_type == CBEventType.LLM and payload:
            input_text = self._event_inputs.pop(event_id, "")
            response = payload.get(EventPayload.RESPONSE, "")
            completion = payload.get(EventPayload.COMPLETION, "")
            output_text = str(response or completion)
            report = _run(self.guard.evaluate(
                input_data=input_text,
                output_data=output_text,
                model_id=self.model_id,
                checks=self.llm_output_checks,
            ))
            self._handle_report(report, "LLM output")
        elif event_type == CBEventType.RETRIEVE and payload:
            nodes = payload.get(EventPayload.NODES, [])
            retrieved_text = "\n".join(
                getattr(n, "text", str(n)) for n in nodes
            )
            if retrieved_text:
                report = _run(self.guard.evaluate(
                    input_data="",
                    output_data=retrieved_text,
                    model_id=self.model_id,
                    checks=["compliance"],
                ))
                self._handle_report(report, "retrieved context")

    def start_trace(self, trace_id: str | None = None) -> None:
        pass

    def end_trace(
        self,
        trace_id: str | None = None,
        trace_map: dict[str, list[str]] | None = None,
    ) -> None:
        pass


def _extract_source_urls(response: Any) -> list[str]:
    """Pull source URLs from a LlamaIndex response's source nodes."""
    urls: list[str] = []
    source_nodes = getattr(response, "source_nodes", [])
    for node in source_nodes:
        metadata = getattr(getattr(node, "node", node), "metadata", {})
        url = metadata.get("url") or metadata.get("source") or metadata.get("file_path")
        if url:
            urls.append(str(url))
    return urls
