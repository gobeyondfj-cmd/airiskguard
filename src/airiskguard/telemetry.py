"""OpenTelemetry integration for airiskguard.

Emits traces and metrics for every RiskGuard evaluation.

Traces:
  - Span per evaluate() call with checker results as attributes
  - Child spans per checker

Metrics:
  - airiskguard.evaluations.total      (counter)
  - airiskguard.evaluations.blocked    (counter)
  - airiskguard.risk_score             (histogram)
  - airiskguard.checker.score          (histogram, per checker)
  - airiskguard.checker.flagged        (counter, per checker)

Usage::

    from opentelemetry import trace, metrics
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.metrics import MeterProvider

    # Set up your OTel providers (Jaeger, OTLP, Datadog, etc.)
    trace.set_tracer_provider(TracerProvider())
    metrics.set_meter_provider(MeterProvider())

    from airiskguard import RiskGuard
    from airiskguard.telemetry import TelemetryExporter

    guard = RiskGuard()
    guard.telemetry = TelemetryExporter()          # attach after init
    # or pass at construction:
    guard = RiskGuard(telemetry=TelemetryExporter())
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from airiskguard.types import RiskReport

_INSTRUMENTATION_NAME = "airiskguard"
_INSTRUMENTATION_VERSION = "0.3.0"


class TelemetryExporter:
    """Exports airiskguard evaluation data as OpenTelemetry traces and metrics.

    Gracefully no-ops if ``opentelemetry-api`` is not installed.

    Args:
        service_name: Service name tag added to all spans/metrics.
        record_input_hash: Include input_hash as a span attribute (default True).
        record_checker_spans: Emit a child span per checker (default False — adds overhead).
    """

    def __init__(
        self,
        service_name: str = "airiskguard",
        record_input_hash: bool = True,
        record_checker_spans: bool = False,
    ) -> None:
        self.service_name = service_name
        self.record_input_hash = record_input_hash
        self.record_checker_spans = record_checker_spans
        self._tracer = None
        self._meter = None
        self._metrics: dict[str, Any] = {}
        self._enabled = self._init_otel()

    def _init_otel(self) -> bool:
        try:
            from opentelemetry import trace, metrics as otel_metrics

            self._tracer = trace.get_tracer(
                _INSTRUMENTATION_NAME, _INSTRUMENTATION_VERSION
            )
            meter = otel_metrics.get_meter(
                _INSTRUMENTATION_NAME, _INSTRUMENTATION_VERSION
            )

            self._metrics["evaluations_total"] = meter.create_counter(
                name="airiskguard.evaluations.total",
                description="Total number of RiskGuard evaluations",
                unit="1",
            )
            self._metrics["evaluations_blocked"] = meter.create_counter(
                name="airiskguard.evaluations.blocked",
                description="Number of evaluations that were blocked",
                unit="1",
            )
            self._metrics["risk_score"] = meter.create_histogram(
                name="airiskguard.risk_score",
                description="Overall risk score distribution",
                unit="1",
            )
            self._metrics["checker_score"] = meter.create_histogram(
                name="airiskguard.checker.score",
                description="Per-checker risk score distribution",
                unit="1",
            )
            self._metrics["checker_flagged"] = meter.create_counter(
                name="airiskguard.checker.flagged",
                description="Number of times each checker flagged content",
                unit="1",
            )
            return True
        except ImportError:
            return False

    @property
    def enabled(self) -> bool:
        return self._enabled

    def record_evaluation(self, report: "RiskReport", model_id: str) -> None:
        """Record a completed evaluation. Call after evaluate() returns."""
        if not self._enabled:
            return

        attrs = {
            "model_id": model_id,
            "overall_risk": report.overall_risk.value,
            "blocked": str(report.blocked).lower(),
            "service.name": self.service_name,
        }

        # Metrics
        self._metrics["evaluations_total"].add(1, attrs)
        self._metrics["risk_score"].record(report.overall_score, attrs)
        if report.blocked:
            self._metrics["evaluations_blocked"].add(1, attrs)

        for result in report.check_results:
            checker_attrs = {**attrs, "checker": result.checker_name}
            self._metrics["checker_score"].record(result.score, checker_attrs)
            if not result.passed:
                self._metrics["checker_flagged"].add(1, checker_attrs)

    def start_evaluation_span(self, model_id: str, checks: list[str]) -> Any:
        """Start a trace span for an evaluation. Returns the span (or None)."""
        if not self._enabled or self._tracer is None:
            return None
        from opentelemetry.trace import SpanKind
        span = self._tracer.start_span(
            name="airiskguard.evaluate",
            kind=SpanKind.INTERNAL,
            attributes={
                "model_id": model_id,
                "checks": ",".join(checks),
                "service.name": self.service_name,
            },
        )
        return span

    def finish_evaluation_span(self, span: Any, report: "RiskReport") -> None:
        """Finish a trace span with evaluation results."""
        if not self._enabled or span is None:
            return
        try:
            from opentelemetry.trace import StatusCode
            span.set_attribute("overall_risk", report.overall_risk.value)
            span.set_attribute("overall_score", report.overall_score)
            span.set_attribute("blocked", report.blocked)
            span.set_attribute("passed", report.passed)
            for result in report.check_results:
                prefix = f"checker.{result.checker_name}"
                span.set_attribute(f"{prefix}.score", result.score)
                span.set_attribute(f"{prefix}.risk", result.risk_level.value)
                span.set_attribute(f"{prefix}.passed", result.passed)
            if report.blocked:
                span.set_status(StatusCode.ERROR, "evaluation blocked")
            else:
                span.set_status(StatusCode.OK)
        finally:
            span.end()

    def record_exception(self, span: Any, exc: Exception) -> None:
        """Record an exception on the span."""
        if not self._enabled or span is None:
            return
        try:
            span.record_exception(exc)
            from opentelemetry.trace import StatusCode
            span.set_status(StatusCode.ERROR, str(exc))
        finally:
            span.end()
