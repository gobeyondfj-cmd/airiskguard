"""Example: Tool-calling agent with airiskguard safety checks.

Demonstrates:
- Validating tool call arguments before execution
- Checking tool outputs before returning to the LLM
- Blocking dangerous tool patterns (file deletion, raw SQL, network access)
- Custom checker for tool-specific risks

Requires: pip install airiskguard
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from airiskguard import RiskGuard, RiskLevel
from airiskguard.checkers.base import BaseChecker
from airiskguard.checkers.registry import register_checker
from airiskguard.types import CheckResult


# --- Custom tool safety checker ---

class ToolSafetyChecker(BaseChecker):
    """Checks tool calls for dangerous patterns."""

    name = "tool_safety"

    BLOCKED_TOOLS = {"delete_file", "rm_rf", "drop_table", "exec_raw_sql", "shutdown"}
    SENSITIVE_TOOLS = {"send_email", "write_file", "execute_code", "http_request"}

    def __init__(self, blocked_tools: list[str] | None = None) -> None:
        if blocked_tools:
            self.BLOCKED_TOOLS = set(blocked_tools)

    async def check(
        self,
        input_data: Any,
        output_data: Any,
        context: dict[str, Any] | None = None,
    ) -> CheckResult:
        flags: list[str] = []
        score = 0.0

        # Extract tool info from input_data
        tool_name = ""
        tool_args = {}
        if isinstance(input_data, dict):
            tool_name = input_data.get("tool", input_data.get("function", ""))
            tool_args = input_data.get("arguments", input_data.get("args", {}))
        elif isinstance(input_data, str):
            tool_name = input_data

        # Check for blocked tools
        if tool_name in self.BLOCKED_TOOLS:
            flags.append(f"blocked_tool: {tool_name}")
            score = max(score, 0.95)

        # Check for sensitive tools (elevated but not blocked)
        if tool_name in self.SENSITIVE_TOOLS:
            flags.append(f"sensitive_tool: {tool_name}")
            score = max(score, 0.4)

        # Check for dangerous arguments
        if isinstance(tool_args, dict):
            args_str = json.dumps(tool_args).lower()

            # SQL injection in arguments
            sql_patterns = ["drop ", "delete from", "truncate ", "; --", "' or '1'='1"]
            for pattern in sql_patterns:
                if pattern in args_str:
                    flags.append(f"sql_injection_in_args: {pattern}")
                    score = max(score, 0.9)

            # Path traversal
            if "../" in args_str or "~/" in args_str:
                flags.append("path_traversal_in_args")
                score = max(score, 0.8)

            # Sensitive file paths
            sensitive_paths = ["/etc/passwd", "/etc/shadow", ".env", "credentials"]
            for path in sensitive_paths:
                if path in args_str:
                    flags.append(f"sensitive_path: {path}")
                    score = max(score, 0.85)

        # Check tool output for sensitive data leakage
        output_str = str(output_data).lower() if output_data else ""
        if any(marker in output_str for marker in ["password:", "secret:", "api_key:"]):
            flags.append("sensitive_data_in_output")
            score = max(score, 0.7)

        # Determine risk level
        if score >= 0.8:
            risk = RiskLevel.CRITICAL
        elif score >= 0.5:
            risk = RiskLevel.HIGH
        elif score >= 0.3:
            risk = RiskLevel.MEDIUM
        else:
            risk = RiskLevel.LOW

        return CheckResult(
            checker_name=self.name,
            risk_level=risk,
            passed=score < 0.5,
            score=score,
            details={"flags": flags, "tool": tool_name},
        )


# Register the custom checker
register_checker("tool_safety", ToolSafetyChecker)


# --- Simulated tools ---

TOOLS = {
    "search_web": lambda args: f"Search results for '{args.get('query', '')}': "
                                f"Found 3 relevant articles about {args.get('query', '')}.",
    "read_file": lambda args: f"Contents of {args.get('path', '')}: "
                               f"This is sample file content.",
    "write_file": lambda args: f"Written {len(args.get('content', ''))} bytes "
                                f"to {args.get('path', '')}.",
    "execute_code": lambda args: f"Code output: {args.get('code', 'print(42)')} => 42",
    "delete_file": lambda args: f"Deleted {args.get('path', '')}.",
    "database_query": lambda args: "Results: [{'id': 1, 'name': 'Alice'}, "
                                    "{'id': 2, 'name': 'Bob'}]",
}


async def execute_tool(tool_name: str, arguments: dict[str, Any]) -> str:
    """Execute a tool (simulated)."""
    fn = TOOLS.get(tool_name)
    if fn:
        return fn(arguments)
    return f"Unknown tool: {tool_name}"


# --- Agent loop ---

async def agent_step(
    guard: RiskGuard,
    tool_call: dict[str, Any],
) -> dict[str, Any]:
    """Process a single tool call with safety checks."""
    tool_name = tool_call["tool"]
    arguments = tool_call.get("arguments", {})

    print(f"\n  Tool call: {tool_name}({json.dumps(arguments)})")

    # Step 1: Validate tool call BEFORE execution
    pre_report = await guard.evaluate(
        input_data={"tool": tool_name, "arguments": arguments},
        output_data="",
        model_id="tool-agent",
        checks=["tool_safety", "security"],
    )

    if pre_report.blocked:
        print(f"  BLOCKED (pre-execution): {pre_report.overall_risk.value}")
        for r in pre_report.check_results:
            if not r.passed:
                print(f"    {r.checker_name}: {r.details}")
        return {
            "tool": tool_name,
            "status": "blocked",
            "reason": "Tool call blocked by safety check",
            "risk_level": pre_report.overall_risk.value,
        }

    # Step 2: Execute the tool
    output = await execute_tool(tool_name, arguments)
    print(f"  Output: {output[:80]}")

    # Step 3: Check tool output BEFORE returning to LLM
    post_report = await guard.evaluate(
        input_data={"tool": tool_name, "arguments": arguments},
        output_data=output,
        model_id="tool-agent",
        checks=["tool_safety", "compliance"],
    )

    if post_report.blocked:
        print(f"  BLOCKED (post-execution): output filtered")
        return {
            "tool": tool_name,
            "status": "filtered",
            "reason": "Tool output contained sensitive content",
        }

    return {
        "tool": tool_name,
        "status": "ok",
        "output": output,
        "risk_score": post_report.overall_score,
    }


async def main() -> None:
    guard = RiskGuard(config={
        "enabled_checkers": ["tool_safety", "security", "compliance"],
        "block_threshold": "high",
        "storage_backend": "memory",
    })
    await guard.initialize()

    await guard.registry.register(
        name="tool-calling-agent", version="1.0",
        owner="agent-team", model_id="tool-agent",
    )

    # Simulate a sequence of tool calls from an LLM agent
    tool_calls = [
        # Safe: web search
        {"tool": "search_web", "arguments": {"query": "Python best practices"}},
        # Safe: read a file
        {"tool": "read_file", "arguments": {"path": "/app/data/report.txt"}},
        # Dangerous: delete a file
        {"tool": "delete_file", "arguments": {"path": "/app/data/users.db"}},
        # Dangerous: path traversal
        {"tool": "read_file", "arguments": {"path": "../../../etc/passwd"}},
        # Dangerous: SQL injection in args
        {"tool": "database_query", "arguments": {"sql": "SELECT * FROM users; DROP TABLE users; --"}},
        # Sensitive but allowed: write file
        {"tool": "write_file", "arguments": {"path": "/app/output.txt", "content": "Report data"}},
    ]

    print("=" * 60)
    print("Tool-Calling Agent with Safety Checks")
    print("=" * 60)

    results = []
    for tool_call in tool_calls:
        result = await agent_step(guard, tool_call)
        results.append(result)

    # Summary
    print(f"\n{'='*60}")
    print("Summary:")
    allowed = sum(1 for r in results if r["status"] == "ok")
    blocked = sum(1 for r in results if r["status"] == "blocked")
    filtered = sum(1 for r in results if r["status"] == "filtered")
    print(f"  Allowed: {allowed}, Blocked: {blocked}, Filtered: {filtered}")

    # Dashboard
    summary = await guard.dashboard.get_summary(model_id="tool-agent")
    print(f"\n  Total evaluations: {summary['total_evaluations']}")
    print(f"  Avg risk score: {summary['avg_score']:.2f}")
    print(f"  Risk distribution: {summary['risk_distribution']}")

    await guard.close()


if __name__ == "__main__":
    asyncio.run(main())
