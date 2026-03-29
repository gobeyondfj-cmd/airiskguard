"""Benchmark runner and metrics for airiskguard checkers."""

from __future__ import annotations

import asyncio
import json
import time
from dataclasses import asdict, dataclass
from typing import Any

from airiskguard.benchmark.datasets import ALL_DATASETS, BenchmarkSample


@dataclass
class CheckerMetrics:
    checker: str
    total: int
    tp: int  # true positives  (flagged, should be flagged)
    fp: int  # false positives (flagged, should pass)
    tn: int  # true negatives  (passed, should pass)
    fn: int  # false negatives (passed, should be flagged)

    @property
    def precision(self) -> float:
        return self.tp / (self.tp + self.fp) if (self.tp + self.fp) > 0 else 0.0

    @property
    def recall(self) -> float:
        return self.tp / (self.tp + self.fn) if (self.tp + self.fn) > 0 else 0.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if (p + r) > 0 else 0.0

    @property
    def accuracy(self) -> float:
        return (self.tp + self.tn) / self.total if self.total > 0 else 0.0

    @property
    def false_positive_rate(self) -> float:
        return self.fp / (self.fp + self.tn) if (self.fp + self.tn) > 0 else 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "checker": self.checker,
            "total": self.total,
            "tp": self.tp, "fp": self.fp, "tn": self.tn, "fn": self.fn,
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
            "f1": round(self.f1, 4),
            "accuracy": round(self.accuracy, 4),
            "false_positive_rate": round(self.false_positive_rate, 4),
        }


@dataclass
class BenchmarkResult:
    version: str
    timestamp: str
    duration_seconds: float
    metrics: list[CheckerMetrics]

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "timestamp": self.timestamp,
            "duration_seconds": round(self.duration_seconds, 2),
            "metrics": [m.to_dict() for m in self.metrics],
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    def print_table(self) -> None:
        header = f"{'Checker':<16} {'Precision':>10} {'Recall':>8} {'F1':>8} {'Accuracy':>10} {'FPR':>8} {'TP':>5} {'FP':>5} {'TN':>5} {'FN':>5}"
        sep = "-" * len(header)
        print(f"\nairiskguard v{self.version} Benchmark Results")
        print(f"Ran in {self.duration_seconds:.2f}s  |  {self.timestamp}")
        print(sep)
        print(header)
        print(sep)
        for m in self.metrics:
            print(
                f"{m.checker:<16} "
                f"{m.precision:>10.1%} "
                f"{m.recall:>8.1%} "
                f"{m.f1:>8.1%} "
                f"{m.accuracy:>10.1%} "
                f"{m.false_positive_rate:>8.1%} "
                f"{m.tp:>5} {m.fp:>5} {m.tn:>5} {m.fn:>5}"
            )
        print(sep)


async def _run_checker(
    checker_name: str,
    samples: list[BenchmarkSample],
    checker_config: dict[str, Any] | None = None,
) -> CheckerMetrics:
    from airiskguard.checkers.registry import get_checker

    checker = get_checker(checker_name, checker_config or {})
    tp = fp = tn = fn = 0

    for sample in samples:
        try:
            result = await checker.check(
                input_data=sample.input_data,
                output_data=sample.output_data,
                context=sample.context,
            )
            flagged = not result.passed
        except Exception:
            flagged = False

        if flagged and sample.label:
            tp += 1
        elif flagged and not sample.label:
            fp += 1
        elif not flagged and not sample.label:
            tn += 1
        else:
            fn += 1

    return CheckerMetrics(
        checker=checker_name,
        total=len(samples),
        tp=tp, fp=fp, tn=tn, fn=fn,
    )


async def run_benchmark(
    checkers: list[str] | None = None,
    checker_configs: dict[str, dict[str, Any]] | None = None,
) -> BenchmarkResult:
    """Run the benchmark suite and return results.

    Args:
        checkers: List of checker names to benchmark. Defaults to all available.
        checker_configs: Per-checker configuration overrides.
    """
    from airiskguard._version import __version__
    from airiskguard.utils.time_utils import utc_now_iso

    available = list(ALL_DATASETS.keys())
    checkers_to_run = [c for c in (checkers or available) if c in ALL_DATASETS]
    checker_configs = checker_configs or {}

    start = time.monotonic()
    tasks = [
        _run_checker(name, ALL_DATASETS[name], checker_configs.get(name))
        for name in checkers_to_run
    ]
    metrics = await asyncio.gather(*tasks)
    duration = time.monotonic() - start

    return BenchmarkResult(
        version=__version__,
        timestamp=utc_now_iso(),
        duration_seconds=duration,
        metrics=list(metrics),
    )


def run_benchmark_sync(
    checkers: list[str] | None = None,
    checker_configs: dict[str, dict[str, Any]] | None = None,
) -> BenchmarkResult:
    """Synchronous wrapper for :func:`run_benchmark`."""
    return asyncio.run(run_benchmark(checkers, checker_configs))
