# Enterprise AI Coding Gateway

The airiskguard gateway is a **local HTTPS reverse proxy** that intercepts traffic between your developers' AI coding tools (Claude Code, Codex CLI, Cursor, GitHub Copilot) and the upstream AI provider APIs.

Developers change **one environment variable**. Everything else works exactly as before — but now your organisation has full visibility, control, and an audit trail over what's being sent to and received from external AI APIs.

## The Problem

When your employees use AI coding assistants:

- Source code containing **hardcoded secrets, API keys, private keys** is pasted into prompts
- **Customer PII and internal data** leaks into AI provider logs
- **Proprietary algorithms and IP** are sent to external servers
- AI-generated code containing **SQL injection, shell injection, weak crypto** reaches production
- There is **no audit trail** of what was sent or generated

## Architecture

```
Developer machine             Corporate network              External
─────────────────             ─────────────────              ────────
Claude Code  ──► airiskguard-gateway  (port 8080) ──► Anthropic API
Codex CLI    ──►    Inspects outbound prompts      ──► OpenAI API
Cursor       ──►    Inspects inbound completions   ──► Azure OpenAI
             ◄── Returns cleaned/blocked response
```

Every request is inspected **before** leaving your network. Every completion is inspected **before** reaching the developer's editor. Blocked requests return a clear error — the external API is never called.

## Install

```bash
pip install "airiskguard[gateway]"
```

## Quick Start

**Step 1** — Create `gateway.yaml`:

```yaml
upstream:
  anthropic: https://api.anthropic.com
  openai: https://api.openai.com

checks:
  outbound: [secrets, compliance, agent]
  inbound:  [vuln, agent]

policies:
  - name: block_secrets
    condition: {checker: secrets, risk: ">= high"}
    action: block
  - name: block_vuln_code
    condition: {checker: vuln, risk: ">= high"}
    action: block

redact_secrets: true
```

**Step 2** — Start the gateway:

```bash
airiskguard-gateway --config gateway.yaml --port 8080
```

**Step 3** — Developers set one environment variable:

```bash
# For Claude Code
export ANTHROPIC_BASE_URL=http://localhost:8080

# For Codex CLI / OpenAI tools
export OPENAI_BASE_URL=http://localhost:8080
```

That's it. Claude Code, Codex CLI, and Cursor all work exactly as before — with every prompt and completion now inspected.

## What Gets Intercepted

### Outbound (prompt → API)

The gateway scans the prompt **before** forwarding to the upstream provider:

| Detection | Checker | Action |
|---|---|---|
| Anthropic / OpenAI / HuggingFace API keys | `secrets` | Block or redact |
| AWS access keys / secret keys | `secrets` | Block or redact |
| GCP service account JSON | `secrets` | Block or redact |
| Azure connection strings | `secrets` | Block or redact |
| GitHub / GitLab tokens | `secrets` | Block or redact |
| Private keys (RSA, EC, OPENSSH) | `secrets` | Block or redact |
| Database connection strings with passwords | `secrets` | Block or redact |
| JWT tokens | `secrets` | Block or redact |
| Hardcoded passwords in code | `secrets` | Block or redact |
| PII (SSN, email, credit cards) | `compliance` | Block or redact |
| SQL injection in tool inputs | `agent` | Block |
| Prompt injection attempts | `security` | Block |

### Inbound (completion → developer)

The gateway scans the AI-generated code **before** it appears in the developer's editor:

| Detection | Checker | Action |
|---|---|---|
| SQL injection (`cursor.execute(f"...{var}...")`) | `vuln` | Block |
| Command injection (`shell=True`, `os.system()`) | `vuln` | Block |
| Insecure deserialization (`pickle.loads()`) | `vuln` | Block |
| Weak cryptography (`hashlib.md5()`, `hashlib.sha1()`) | `vuln` | Flag |
| Insecure random (`random.randint()` for secrets) | `vuln` | Flag |
| Hardcoded credentials in generated code | `vuln` | Block |
| Path traversal (`open(request.args['file'])`) | `vuln` | Block |
| Debug flags in production (`DEBUG=True`) | `vuln` | Flag |
| Insecure CORS (`Access-Control-Allow-Origin: *`) | `vuln` | Flag |
| Prompt injection via tool outputs | `agent` | Block |

## Secret Redaction

With `redact_secrets: true`, detected secrets are **replaced** before the prompt is forwarded upstream — rather than simply blocking the request. This means developers can still get help with code structure even when a file contains a secret.

```
ORIGINAL:  DATABASE_URL=postgresql://admin:MyP@ssw0rd@prod.db.company.com/app
FORWARDED: DATABASE_URL=[REDACTED:DB_CONNECTION_STRING]
```

## Per-Team Policies

Different teams can have different rules, model restrictions, and checker sets:

```yaml
teams:
  contractors:
    # Restricted to cheaper model only
    model_allowlist: [claude-haiku-4-5]
    # Stricter scanning
    outbound_checks: [secrets, compliance, agent, security]
    inbound_checks: [vuln, agent]
    # Gateway API keys for this team (employees never see real provider keys)
    api_keys:
      - gw-contractor-team-key-abc123

  engineers:
    model_allowlist: [claude-sonnet-4-6, claude-opus-4-6, gpt-4o]
    outbound_checks: [secrets, compliance]
    inbound_checks: [vuln]
    api_keys:
      - gw-engineering-team-key-xyz789

  data-scientists:
    model_allowlist: [claude-sonnet-4-6, gpt-4o]
    outbound_checks: [secrets, pii]
    inbound_checks: [vuln]
    api_keys:
      - gw-data-science-key-def456
```

Employees are issued **gateway API keys** — they never see the real provider API keys, which are stored only in the gateway config.

## Notifications

Get alerted when sensitive data is blocked:

```yaml
notifications:
  slack: https://hooks.slack.com/services/T.../B.../...
  webhook: https://siem.company.com/api/events
  pagerduty_key: your-pd-routing-key
```

Every blocked evaluation sends a rich Slack message with:

- Which model was called
- Which checker triggered
- Risk level and score
- Timestamp

## Full Configuration Reference

```yaml
# gateway.yaml

upstream:
  anthropic: https://api.anthropic.com   # Anthropic API base URL
  openai: https://api.openai.com         # OpenAI API base URL

# TLS (recommended for production)
tls:
  cert: /etc/gateway/fullchain.pem
  key: /etc/gateway/privkey.pem

# Default checkers (can be overridden per team)
checks:
  outbound: [secrets, compliance, agent]
  inbound:  [vuln, agent]

# Policy-as-code rules (same syntax as airiskguard PolicyEngine)
policies:
  - name: block_any_secret
    condition: {checker: secrets, risk: ">= medium"}
    action: block
  - name: block_critical_vuln
    condition: {checker: vuln, risk: ">= critical"}
    action: block
  - name: flag_medium_vuln
    condition: {checker: vuln, risk: ">= medium"}
    action: review

# Per-team policies
teams:
  contractors:
    model_allowlist: [claude-haiku-4-5]
    outbound_checks: [secrets, compliance, agent, security]
    inbound_checks: [vuln, agent]
    api_keys: [gw-contractor-key]
  engineers:
    model_allowlist: [claude-sonnet-4-6, gpt-4o]
    outbound_checks: [secrets, compliance]
    inbound_checks: [vuln]
    api_keys: [gw-engineer-key]

notifications:
  slack: https://hooks.slack.com/services/...
  webhook: https://siem.company.com/events
  pagerduty_key: your-routing-key

# Behaviour
block_on_secrets: true      # Block (not just log) when secrets detected
redact_secrets: true        # Replace secrets before forwarding (vs hard block)
audit_enabled: true         # Log every evaluation to audit trail

# Server
host: 0.0.0.0
port: 8080
log_level: info             # debug | info | warning | error
```

## CLI Reference

```bash
airiskguard-gateway [OPTIONS]

Options:
  --config, -c PATH          Path to gateway YAML config file
  --host TEXT                Bind host (default: 0.0.0.0)
  --port, -p INTEGER         Bind port (default: 8080)
  --log-level TEXT           Log level: debug|info|warning|error
  --outbound-checks CHECKER  Override outbound checkers
  --inbound-checks CHECKER   Override inbound checkers
  --no-tls                   Disable TLS
```

## Python API

You can also embed the gateway in your own ASGI application:

```python
from airiskguard.gateway import GatewayApp, GatewayConfig

config = GatewayConfig.load("gateway.yaml")
app = GatewayApp(config)

# Run with uvicorn
import uvicorn
uvicorn.run(app, host="0.0.0.0", port=8080)
```

## Production Deployment

For production, run behind a reverse proxy with TLS:

```yaml
# docker-compose.yml
services:
  gateway:
    image: python:3.11-slim
    command: >
      bash -c "pip install 'airiskguard[gateway]' &&
               airiskguard-gateway --config /config/gateway.yaml"
    volumes:
      - ./gateway.yaml:/config/gateway.yaml
      - ./certs:/etc/certs
    ports:
      - "8080:8080"
    environment:
      - LOG_LEVEL=info
```

**Recommended architecture:**

```
Internet → Nginx (TLS termination) → airiskguard-gateway → AI provider APIs
                                            ↓
                                     SQLite/PostgreSQL (audit log)
                                            ↓
                                     Slack/PagerDuty (alerts)
```

## Security Notes

- Gateway API keys are short strings you assign — store them in your secrets manager (Vault, AWS Secrets Manager, etc.)
- The real provider API keys are stored only in `gateway.yaml` — never shared with developers
- Audit logs record prompt hashes (not plaintext) by default — full logging is opt-in
- The gateway makes no outbound connections except to the configured upstream URLs and notification webhooks
