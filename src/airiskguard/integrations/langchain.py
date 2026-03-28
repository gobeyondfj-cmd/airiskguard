"""LangChain integration for airiskguard.

Usage::

    from airiskguard import RiskGuard
    from airiskguard.integrations.langchain import RiskGuardCallbackHandler

    guard = RiskGuard()
    handler = RiskGuardCallbackHandler(guard, model_id="my-chain")

    llm = ChatOpenAI(callbacks=[handler])
    chain = LLMChain(llm=llm, prompt=prompt, callbacks=[handler])
"""

from __future__ import annotations

import asyncio
from typing import Any
from uuid import UUID

try:
    from langchain_core.callbacks.base import BaseCallbackHandler
    from langchain_core.outputs import LLMResult
except ImportError as e:
    raise ImportError(
        "LangChain integration requires langchain-core. "
        "Install with: pip install airiskguard[langchain]"
    ) from e

from airiskguard.exceptions import RiskBlockedError
from airiskguard.types import RiskReport


class RiskGuardCallbackHandler(BaseCallbackHandler):
    """LangChain callback handler that evaluates inputs/outputs with RiskGuard.

    Raises :class:`~airiskguard.exceptions.RiskBlockedError` when a blocked
    risk report is produced, halting the chain.

    Args:
        guard: An initialized (or auto-initializing) :class:`~airiskguard.RiskGuard` instance.
        model_id: Identifier used for audit logs and dashboard metrics.
        input_checks: Checkers to run on LLM inputs. Defaults to ``["security", "compliance"]``.
        output_checks: Checkers to run on LLM outputs. Defaults to ``["hallucination", "compliance"]``.
        tool_checks: Checkers to run on tool inputs. Defaults to ``["security"]``.
        raise_on_block: If ``True`` (default), raise :class:`RiskBlockedError` when blocked.
            Set to ``False`` to log and continue.
        context: Extra context forwarded to every checker call.
    """

    raise_error = True  # BaseCallbackHandler flag — propagate exceptions

    def __init__(
        self,
        guard: Any,
        model_id: str = "langchain",
        input_checks: list[str] | None = None,
        output_checks: list[str] | None = None,
        tool_checks: list[str] | None = None,
        raise_on_block: bool = True,
        context: dict[str, Any] | None = None,
    ) -> None:
        super().__init__()
        self.guard = guard
        self.model_id = model_id
        self.input_checks = input_checks or ["security", "compliance"]
        self.output_checks = output_checks or ["hallucination", "compliance"]
        self.tool_checks = tool_checks or ["security"]
        self.raise_on_block = raise_on_block
        self.context = context or {}
        # run_id → input text, for pairing with on_llm_end
        self._pending_inputs: dict[UUID, str] = {}

    def _run(self, coro: Any) -> Any:
        """Run a coroutine from a sync callback."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(coro)
        # Already inside an event loop (e.g. Jupyter) — run in thread
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as pool:
            return pool.submit(asyncio.run, coro).result()

    def _handle_report(self, report: RiskReport, phase: str) -> None:
        if report.blocked and self.raise_on_block:
            raise RiskBlockedError(
                f"[airiskguard] {phase} blocked by {self.model_id} "
                f"(risk={report.overall_risk.value}, score={report.overall_score:.2f})",
                report=report,
            )

    # --- LLM callbacks ---

    def on_llm_start(
        self,
        serialized: dict[str, Any],
        prompts: list[str],
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        input_text = "\n".join(prompts)
        self._pending_inputs[run_id] = input_text
        report = self._run(
            self.guard.evaluate(
                input_data=input_text,
                output_data="",
                model_id=self.model_id,
                checks=self.input_checks,
                context=self.context,
            )
        )
        self._handle_report(report, "LLM input")

    def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        input_text = self._pending_inputs.pop(run_id, "")
        output_text = "\n".join(
            gen.text
            for gens in response.generations
            for gen in gens
            if hasattr(gen, "text")
        )
        report = self._run(
            self.guard.evaluate(
                input_data=input_text,
                output_data=output_text,
                model_id=self.model_id,
                checks=self.output_checks,
                context=self.context,
            )
        )
        self._handle_report(report, "LLM output")

    def on_llm_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        self._pending_inputs.pop(run_id, None)

    # --- Chain callbacks ---

    def on_chain_start(
        self,
        serialized: dict[str, Any],
        inputs: dict[str, Any],
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        input_text = str(inputs)
        self._pending_inputs[run_id] = input_text

    def on_chain_end(
        self,
        outputs: dict[str, Any],
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        self._pending_inputs.pop(run_id, None)

    def on_chain_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        self._pending_inputs.pop(run_id, None)

    # --- Tool callbacks ---

    def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        tool_name = serialized.get("name", "unknown_tool")
        report = self._run(
            self.guard.evaluate(
                input_data={"tool": tool_name, "input": input_str},
                output_data="",
                model_id=self.model_id,
                checks=self.tool_checks,
                context=self.context,
            )
        )
        self._handle_report(report, f"tool input ({tool_name})")

    def on_tool_end(
        self,
        output: str,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        report = self._run(
            self.guard.evaluate(
                input_data="",
                output_data=output,
                model_id=self.model_id,
                checks=self.output_checks,
                context=self.context,
            )
        )
        self._handle_report(report, "tool output")

    def on_tool_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        pass

    # --- Async variants (used when chain runs async) ---

    async def on_llm_start_async(  # type: ignore[override]
        self,
        serialized: dict[str, Any],
        prompts: list[str],
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        input_text = "\n".join(prompts)
        self._pending_inputs[run_id] = input_text
        report = await self.guard.evaluate(
            input_data=input_text,
            output_data="",
            model_id=self.model_id,
            checks=self.input_checks,
            context=self.context,
        )
        self._handle_report(report, "LLM input")

    async def on_llm_end_async(  # type: ignore[override]
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        input_text = self._pending_inputs.pop(run_id, "")
        output_text = "\n".join(
            gen.text
            for gens in response.generations
            for gen in gens
            if hasattr(gen, "text")
        )
        report = await self.guard.evaluate(
            input_data=input_text,
            output_data=output_text,
            model_id=self.model_id,
            checks=self.output_checks,
            context=self.context,
        )
        self._handle_report(report, "LLM output")

    async def on_tool_start_async(  # type: ignore[override]
        self,
        serialized: dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        tool_name = serialized.get("name", "unknown_tool")
        report = await self.guard.evaluate(
            input_data={"tool": tool_name, "input": input_str},
            output_data="",
            model_id=self.model_id,
            checks=self.tool_checks,
            context=self.context,
        )
        self._handle_report(report, f"tool input ({tool_name})")

    async def on_tool_end_async(  # type: ignore[override]
        self,
        output: str,
        *,
        run_id: UUID,
        **kwargs: Any,
    ) -> None:
        report = await self.guard.evaluate(
            input_data="",
            output_data=output,
            model_id=self.model_id,
            checks=self.output_checks,
            context=self.context,
        )
        self._handle_report(report, "tool output")
