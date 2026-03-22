# Configuration

## YAML Configuration

```yaml
# airiskguard.yaml
storage_backend: sqlite          # memory | sqlite | json
storage_path: ./airiskguard.db

block_threshold: high            # low | medium | high | critical
review_threshold: medium
score_block_threshold: 0.85

enabled_checkers:
  - security
  - compliance
  - hallucination
  - bias

checker_configs:
  compliance:
    detect_pii: true
    detect_prohibited: true
    custom_rules:
      - name: api_key_pattern
        pattern: '(?:sk|pk)[-_][a-zA-Z0-9]{32,}'
  hallucination:
    use_nli: false               # true requires transformers extra
  security:
    check_encoding: true

audit_enabled: true
review_enabled: true
review_auto_escalate: true       # auto-escalate CRITICAL to review
dashboard_enabled: true
```

Load via path or dict:

```python
guard = RiskGuard(config="airiskguard.yaml")
# or
guard = RiskGuard(config={
    "block_threshold": "high",
    "enabled_checkers": ["security"],
})
```

## Reference

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `storage_backend` | str | `"memory"` | `"memory"`, `"sqlite"`, or `"json"` |
| `storage_path` | str | `""` | Path for sqlite/json backends |
| `block_threshold` | str | `"critical"` | Auto-block if risk >= this level |
| `review_threshold` | str | `"high"` | Flag for human review if risk >= this |
| `score_block_threshold` | float | `0.9` | Block if numeric score >= this |
| `enabled_checkers` | list | all five | Which checkers to load |
| `checker_configs` | dict | `{}` | Per-checker configuration |
| `audit_enabled` | bool | `true` | Enable immutable audit trail |
| `review_enabled` | bool | `true` | Enable human review workflow |
| `review_auto_escalate` | bool | `true` | Auto-escalate CRITICAL items |
| `dashboard_enabled` | bool | `true` | Record evaluation metrics |
| `anomaly_contamination` | float | `0.1` | IsolationForest contamination param |
| `drift_significance` | float | `0.05` | KS test p-value threshold |
