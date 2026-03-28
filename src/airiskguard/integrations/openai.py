"""OpenAI SDK integration for airiskguard.

Drop-in replacements for ``openai.AsyncOpenAI`` and ``openai.OpenAI`` that
automatically evaluate inputs and outputs with RiskGuard.

Usage::

    # Before
    from openai import AsyncOpenAI
    client = AsyncOpenAI()

    # After — one line change
    from airiskguard.integrations.openai import GuardedAsyncOpenAI
    client = GuardedAsyncOpenAI(guard, model_id="my-app")

    # Everything else stays the same
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "Hello"}],
    )
"""

from __future__ import annotations

import asyncio
from typing import Any, AsyncIterator, Iterator

try:
    import openai
    from openai import AsyncOpenAI, OpenAI
    from openai.types.chat import ChatCompletion, ChatCompletionChunk
except ImportError as e:
    raise ImportError(
        "OpenAI integration requires openai. "
        "Install with: pip install airiskguard[openai]"
    ) from e

from airiskguard.exceptions import RiskBlockedError
from airiskguard.types import RiskReport


def _messages_to_text(messages: list[dict[str, Any]]) -> str:
    """Flatten a messages list to a single string for evaluation."""
    parts = []
    for m in messages:
        role = m.get("role", "")
        content = m.get("content", "")
        if isinstance(content, list):
            # Multi-modal: extract text parts only
            content = " ".join(
                p.get("text", "") for p in content if isinstance(p, dict) and p.get("type") == "text"
            )
        parts.append(f"{role}: {content}")
    return "\n".join(parts)


def _completion_to_text(completion: ChatCompletion) -> str:
    """Extract assistant text from a ChatCompletion response."""
    texts = []
    for choice in completion.choices:
        msg = choice.message
        if msg and msg.content:
            texts.append(msg.content)
    return "\n".join(texts)


class _GuardedCompletions:
    """Proxy for client.chat.completions with risk evaluation."""

    def __init__(
        self,
        completions: Any,
        guard: Any,
        model_id: str,
        input_checks: list[str],
        output_checks: list[str],
        raise_on_block: bool,
        context: dict[str, Any],
        is_async: bool,
    ) -> None:
        self._completions = completions
        self.guard = guard
        self.model_id = model_id
        self.input_checks = input_checks
        self.output_checks = output_checks
        self.raise_on_block = raise_on_block
        self.context = context
        self.is_async = is_async

    def _handle_report(self, report: RiskReport, phase: str) -> None:
        if report.blocked and self.raise_on_block:
            raise RiskBlockedError(
                f"[airiskguard] {phase} blocked by {self.model_id} "
                f"(risk={report.overall_risk.value}, score={report.overall_score:.2f})",
                report=report,
            )

    async def _acreate(self, **kwargs: Any) -> ChatCompletion:
        messages = kwargs.get("messages", [])
        input_text = _messages_to_text(messages)

        report = await self.guard.evaluate(
            input_data=input_text,
            output_data="",
            model_id=self.model_id,
            checks=self.input_checks,
            context=self.context,
        )
        self._handle_report(report, "chat input")

        completion: ChatCompletion = await self._completions.create(**kwargs)

        output_text = _completion_to_text(completion)
        report = await self.guard.evaluate(
            input_data=input_text,
            output_data=output_text,
            model_id=self.model_id,
            checks=self.output_checks,
            context=self.context,
        )
        self._handle_report(report, "chat output")
        return completion

    def _sync_create(self, **kwargs: Any) -> ChatCompletion:
        messages = kwargs.get("messages", [])
        input_text = _messages_to_text(messages)

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        def _run(coro: Any) -> Any:
            if loop and loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    return pool.submit(asyncio.run, coro).result()
            return asyncio.run(coro)

        report = _run(self.guard.evaluate(
            input_data=input_text,
            output_data="",
            model_id=self.model_id,
            checks=self.input_checks,
            context=self.context,
        ))
        self._handle_report(report, "chat input")

        completion: ChatCompletion = self._completions.create(**kwargs)

        output_text = _completion_to_text(completion)
        report = _run(self.guard.evaluate(
            input_data=input_text,
            output_data=output_text,
            model_id=self.model_id,
            checks=self.output_checks,
            context=self.context,
        ))
        self._handle_report(report, "chat output")
        return completion

    def create(self, **kwargs: Any) -> Any:
        if self.is_async:
            return self._acreate(**kwargs)
        return self._sync_create(**kwargs)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._completions, name)


class _GuardedChat:
    def __init__(self, chat: Any, completions: _GuardedCompletions) -> None:
        self._chat = chat
        self.completions = completions

    def __getattr__(self, name: str) -> Any:
        return getattr(self._chat, name)


class GuardedAsyncOpenAI:
    """Drop-in replacement for ``openai.AsyncOpenAI`` with built-in risk evaluation.

    Args:
        guard: A :class:`~airiskguard.RiskGuard` instance.
        model_id: Identifier for audit logs and dashboard metrics.
        input_checks: Checkers for chat inputs. Defaults to ``["security", "compliance"]``.
        output_checks: Checkers for chat outputs. Defaults to ``["hallucination", "compliance"]``.
        raise_on_block: Raise :class:`RiskBlockedError` when blocked (default ``True``).
        context: Extra context forwarded to checkers.
        **openai_kwargs: Forwarded to ``openai.AsyncOpenAI`` (api_key, base_url, etc.).
    """

    def __init__(
        self,
        guard: Any,
        model_id: str = "openai",
        input_checks: list[str] | None = None,
        output_checks: list[str] | None = None,
        raise_on_block: bool = True,
        context: dict[str, Any] | None = None,
        **openai_kwargs: Any,
    ) -> None:
        self._client = AsyncOpenAI(**openai_kwargs)
        self.guard = guard
        self.model_id = model_id
        self.chat = _GuardedChat(
            self._client.chat,
            _GuardedCompletions(
                completions=self._client.chat.completions,
                guard=guard,
                model_id=model_id,
                input_checks=input_checks or ["security", "compliance"],
                output_checks=output_checks or ["hallucination", "compliance"],
                raise_on_block=raise_on_block,
                context=context or {},
                is_async=True,
            ),
        )

    def __getattr__(self, name: str) -> Any:
        return getattr(self._client, name)


class GuardedOpenAI:
    """Drop-in replacement for ``openai.OpenAI`` with built-in risk evaluation.

    Args:
        guard: A :class:`~airiskguard.RiskGuard` instance.
        model_id: Identifier for audit logs and dashboard metrics.
        input_checks: Checkers for chat inputs. Defaults to ``["security", "compliance"]``.
        output_checks: Checkers for chat outputs. Defaults to ``["hallucination", "compliance"]``.
        raise_on_block: Raise :class:`RiskBlockedError` when blocked (default ``True``).
        context: Extra context forwarded to checkers.
        **openai_kwargs: Forwarded to ``openai.OpenAI`` (api_key, base_url, etc.).
    """

    def __init__(
        self,
        guard: Any,
        model_id: str = "openai",
        input_checks: list[str] | None = None,
        output_checks: list[str] | None = None,
        raise_on_block: bool = True,
        context: dict[str, Any] | None = None,
        **openai_kwargs: Any,
    ) -> None:
        self._client = OpenAI(**openai_kwargs)
        self.guard = guard
        self.model_id = model_id
        self.chat = _GuardedChat(
            self._client.chat,
            _GuardedCompletions(
                completions=self._client.chat.completions,
                guard=guard,
                model_id=model_id,
                input_checks=input_checks or ["security", "compliance"],
                output_checks=output_checks or ["hallucination", "compliance"],
                raise_on_block=raise_on_block,
                context=context or {},
                is_async=False,
            ),
        )

    def __getattr__(self, name: str) -> Any:
        return getattr(self._client, name)
