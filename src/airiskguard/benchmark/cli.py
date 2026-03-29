"""CLI entry point for airiskguard benchmark."""

from __future__ import annotations

import argparse
import json
import sys


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="airiskguard-benchmark",
        description="Benchmark airiskguard checkers and report precision/recall/F1.",
    )
    parser.add_argument(
        "--checkers",
        nargs="+",
        metavar="CHECKER",
        help="Checkers to benchmark (default: all). Choices: security, compliance, hallucination, bias",
    )
    parser.add_argument(
        "--output",
        metavar="FILE",
        help="Save results to a JSON file.",
    )
    parser.add_argument(
        "--format",
        choices=["table", "json"],
        default="table",
        help="Output format (default: table).",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress progress output.",
    )
    args = parser.parse_args()

    if not args.quiet:
        print("Running airiskguard benchmark...", file=sys.stderr)

    from airiskguard.benchmark.runner import run_benchmark_sync
    result = run_benchmark_sync(checkers=args.checkers)

    if args.format == "json":
        print(result.to_json())
    else:
        result.print_table()

    if args.output:
        with open(args.output, "w") as f:
            f.write(result.to_json())
        if not args.quiet:
            print(f"\nResults saved to {args.output}", file=sys.stderr)

    # Exit 1 if any checker has F1 < 0.5 (useful for CI)
    if any(m.f1 < 0.5 for m in result.metrics):
        sys.exit(1)


if __name__ == "__main__":
    main()
