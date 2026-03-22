# Architecture

## System Overview

```
RiskGuard (orchestrator)
├── Checkers: security, compliance, hallucination, bias, fraud, [custom]
├── AuditLog: immutable hash-chain (SHA-256) per decision
├── RiskDashboard: per-model metrics, trends, checker breakdowns
├── ModelRegistry: lifecycle management (DRAFT → PRODUCTION → RETIRED)
├── ReviewWorkflow: flag → approve/reject/escalate with callbacks
├── AnomalyDetector: IsolationForest + KS drift
├── ReportGenerator: GDPR, SOX, EU AI Act
├── StandardAssessor: AIRMS v1.0 compliance assessment
└── Storage: MemoryStorage | SQLiteStorage | JSONFileStorage
```

Each `evaluate()` call runs selected checkers, aggregates risk, logs to the audit trail, records dashboard metrics, and optionally flags for human review — all in a single async call.

## Core Components

| Component | Purpose |
|-----------|---------|
| **RiskGuard** | Main orchestrator wiring storage, checkers, and core features |
| **AuditLog** | Immutable SHA-256 hash-chain audit trail with tamper verification |
| **ModelRegistry** | Model registration, versioning, lifecycle state management |
| **RiskDashboard** | Metrics aggregation, trends, per-checker breakdowns, JSON export |
| **ReviewWorkflow** | Threshold-based flagging with approve/reject/escalate and callbacks |
| **AnomalyDetector** | IsolationForest for outliers, KS test for distribution drift |
| **ReportGenerator** | GDPR, SOX, EU AI Act compliance reports |
| **StandardAssessor** | AIRMS v1.0 assessment engine with maturity scoring |

## Model Lifecycle

```
DRAFT → VALIDATION → PRODUCTION → DEPRECATED → RETIRED
  │         │                          │
  └─────────┘── can return ───────────┘
              to DRAFT               to PRODUCTION
```

Valid transitions are enforced by the ModelRegistry.

## Storage Backends

| Backend | Use Case |
|---------|----------|
| **MemoryStorage** | Development and testing |
| **SQLiteStorage** | Production single-node deployment |
| **JSONFileStorage** | Simple file-based persistence |

All backends implement the same `StorageBackend` interface with four tables: audit entries, models, review items, and metrics.

## Integration Points

| Integration | Method |
|-------------|--------|
| **FastAPI** | `add_risk_guard(app)` middleware |
| **Flask** | Flask integration middleware |
| **ASGI** | ASGI middleware |
| **WSGI** | WSGI middleware |
| **Decorator** | `@risk_guard()` for any sync/async function |
| **Custom checkers** | Extend `BaseChecker` and `register_checker()` |
