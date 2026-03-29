# OpenTelemetry Observability

airiskguard ships a built-in `TelemetryExporter` that emits **traces** and **metrics** for every evaluation — no extra code required beyond wiring up your OTel providers.

## Install

```bash
pip install "airiskguard[opentelemetry]"
```

## Quick start

Configure your OTel providers **before** creating `RiskGuard`, then pass a `TelemetryExporter`:

```python
from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.metrics import MeterProvider

# Traces → OTLP (Jaeger, Grafana Tempo, Datadog, …)
tracer_provider = TracerProvider()
tracer_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
trace.set_tracer_provider(tracer_provider)

metrics.set_meter_provider(MeterProvider())

from airiskguard import RiskGuard
from airiskguard.telemetry import TelemetryExporter

guard = RiskGuard(
    telemetry=TelemetryExporter(service_name="my-ai-app"),
)
```

Every `guard.evaluate()` call now emits a span and increments metrics automatically.

## Emitted signals

### Traces

| Span name | Kind | Key attributes |
|---|---|---|
| `airiskguard.evaluate` | INTERNAL | `model_id`, `checks`, `overall_risk`, `overall_score`, `blocked`, `passed`, `checker.<name>.score`, `checker.<name>.risk`, `checker.<name>.passed` |

Span status is set to `ERROR` when the evaluation is blocked, `OK` otherwise.

### Metrics

| Metric | Type | Description |
|---|---|---|
| `airiskguard.evaluations.total` | Counter | Total evaluations |
| `airiskguard.evaluations.blocked` | Counter | Evaluations that were blocked |
| `airiskguard.risk_score` | Histogram | Overall risk score distribution |
| `airiskguard.checker.score` | Histogram | Per-checker score (label: `checker`) |
| `airiskguard.checker.flagged` | Counter | Times each checker flagged content |

All signals carry `model_id`, `overall_risk`, `blocked`, and `service.name` attributes.

## Configuration options

```python
TelemetryExporter(
    service_name="my-ai-app",       # added to all spans/metrics
    record_input_hash=True,         # include SHA-256 of input as span attribute
    record_checker_spans=False,     # emit child span per checker (adds overhead)
)
```

## Graceful no-op

If `opentelemetry-api` is not installed, `TelemetryExporter` silently no-ops — no errors, no performance impact. This means you can ship the same code to environments with and without OTel configured.

```python
exporter = TelemetryExporter()
print(exporter.enabled)  # False if opentelemetry-api not installed
```

## Grafana dashboard

A sample Grafana dashboard JSON is available in `examples/grafana_dashboard.json` (coming soon). Key panels to build:

- **Blocked rate** — `rate(airiskguard_evaluations_blocked_total[5m]) / rate(airiskguard_evaluations_total[5m])`
- **Risk score p95** — histogram quantile on `airiskguard_risk_score`
- **Top flagging checkers** — `topk(5, airiskguard_checker_flagged_total)`

## Backends

`TelemetryExporter` works with any OTel-compatible backend:

| Backend | Export package |
|---|---|
| Jaeger | `opentelemetry-exporter-jaeger` |
| Grafana Tempo / OTLP | `opentelemetry-exporter-otlp-proto-grpc` |
| Datadog | `opentelemetry-exporter-datadog` |
| Prometheus (metrics) | `opentelemetry-exporter-prometheus` |
| Stdout (dev) | `opentelemetry-sdk` (built-in) |
