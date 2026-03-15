"""Example: RAG pipeline with airiskguard safety checks.

Demonstrates:
- Checking retrieved documents for compliance (PII, prohibited content)
- Checking generated answers for hallucination
- Passing known_urls context to the hallucination checker
- Full audit trail for the pipeline

Requires: pip install airiskguard
"""

from __future__ import annotations

import asyncio
from typing import Any

from airiskguard import RiskGuard


# --- Simulated RAG components ---

DOCUMENT_STORE = {
    "doc1": {
        "content": "Paris is the capital of France. Population: 2.1 million.",
        "url": "https://en.wikipedia.org/wiki/Paris",
    },
    "doc2": {
        "content": "The Eiffel Tower was built in 1889 for the World's Fair.",
        "url": "https://en.wikipedia.org/wiki/Eiffel_Tower",
    },
    "doc3": {
        "content": (
            "Patient John Smith (SSN: 123-45-6789) was diagnosed with hypertension. "
            "Contact: john.smith@hospital.example.com"
        ),
        "url": "https://internal.hospital.example.com/records/123",
    },
}


async def retrieve(query: str) -> list[dict[str, Any]]:
    """Simulate retrieval — returns matching documents."""
    results = []
    for doc_id, doc in DOCUMENT_STORE.items():
        if any(word in doc["content"].lower() for word in query.lower().split()):
            results.append({"id": doc_id, **doc})
    return results or [DOCUMENT_STORE["doc1"]]  # fallback


async def generate(query: str, context_docs: list[dict[str, Any]]) -> str:
    """Simulate LLM generation from retrieved context."""
    context_text = "\n".join(d["content"] for d in context_docs)

    if "capital" in query.lower():
        return "Based on the sources, Paris is the capital of France with a population of 2.1 million."

    if "patient" in query.lower() or "medical" in query.lower():
        return (
            "According to the records, John Smith (SSN: 123-45-6789) has hypertension. "
            "I'm 100% certain this is accurate."
        )

    # Simulate hallucinated response with fabricated URL
    return (
        "The Eiffel Tower is 330 meters tall and was definitely visited by "
        "50 million people last year. See https://fabricated-stats.example.com/eiffel "
        "for the full statistics."
    )


# --- Guarded RAG pipeline ---

async def rag_query(guard: RiskGuard, query: str) -> dict[str, Any]:
    """Execute a RAG query with safety checks at each stage."""
    print(f"\nQuery: {query}")
    result: dict[str, Any] = {"query": query, "status": "ok"}

    # Step 1: Retrieve documents
    docs = await retrieve(query)
    doc_contents = "\n---\n".join(d["content"] for d in docs)
    source_urls = [d["url"] for d in docs]
    print(f"  Retrieved {len(docs)} documents")

    # Step 2: Check retrieved documents for compliance issues
    doc_report = await guard.evaluate(
        input_data=query,
        output_data=doc_contents,
        model_id="rag-retriever",
        checks=["compliance"],
    )

    if not doc_report.passed:
        print(f"  WARNING: Retrieved docs flagged — "
              f"risk={doc_report.overall_risk.value}")
        for r in doc_report.check_results:
            if not r.passed:
                print(f"    {r.checker_name}: {r.details}")

        if doc_report.blocked:
            result["status"] = "blocked"
            result["reason"] = "Retrieved documents contain sensitive content"
            print(f"  BLOCKED: Sensitive content in retrieved documents")
            return result

    # Step 3: Generate answer
    answer = await generate(query, docs)
    print(f"  Generated: {answer[:80]}...")

    # Step 4: Check generated answer for hallucination and compliance
    answer_report = await guard.evaluate(
        input_data=query,
        output_data=answer,
        model_id="rag-generator",
        checks=["hallucination", "compliance"],
        context={"known_urls": source_urls},
    )

    result["risk_level"] = answer_report.overall_risk.value
    result["risk_score"] = answer_report.overall_score

    if answer_report.blocked:
        result["status"] = "blocked"
        result["reason"] = "Generated answer failed safety checks"
        print(f"  BLOCKED: risk={answer_report.overall_risk.value}, "
              f"score={answer_report.overall_score:.2f}")
        for r in answer_report.check_results:
            if not r.passed:
                print(f"    {r.checker_name}: {r.details}")
        return result

    if not answer_report.passed:
        print(f"  WARNING: risk={answer_report.overall_risk.value}, "
              f"score={answer_report.overall_score:.2f}")
        for r in answer_report.check_results:
            if not r.passed:
                print(f"    {r.checker_name}: {r.details}")

    result["answer"] = answer
    result["sources"] = source_urls
    return result


async def main() -> None:
    guard = RiskGuard(config={
        "enabled_checkers": ["compliance", "hallucination"],
        "block_threshold": "high",
        "storage_backend": "memory",
    })
    await guard.initialize()

    # Register pipeline components
    await guard.registry.register(
        name="rag-retriever", version="1.0", owner="search-team",
        model_id="rag-retriever",
    )
    await guard.registry.register(
        name="rag-generator", version="1.0", owner="llm-team",
        model_id="rag-generator",
    )

    # Run test queries
    queries = [
        "What is the capital of France?",
        "Tell me about patient medical records",
        "How tall is the Eiffel Tower?",
    ]

    print("=" * 60)
    print("RAG Pipeline with Safety Checks")
    print("=" * 60)

    for query in queries:
        result = await rag_query(guard, query)
        print(f"  Result: status={result['status']}")

    # Pipeline audit trail
    print(f"\n{'='*60}")
    print("Audit Trail:")

    for component in ["rag-retriever", "rag-generator"]:
        entries = await guard.audit.query(model_id=component)
        print(f"\n  {component}: {len(entries)} evaluations")
        for entry in entries:
            print(f"    [{entry.action}] risk={entry.risk_level.value} "
                  f"score={entry.score:.2f}")

    # Per-component dashboard
    print(f"\n{'='*60}")
    print("Dashboard:")
    for component in ["rag-retriever", "rag-generator"]:
        summary = await guard.dashboard.get_summary(model_id=component)
        print(f"  {component}: {summary['total_evaluations']} evals, "
              f"avg_score={summary['avg_score']:.2f}")

    await guard.close()


if __name__ == "__main__":
    asyncio.run(main())
