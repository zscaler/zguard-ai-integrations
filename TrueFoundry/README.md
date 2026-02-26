# TrueFoundry Integration with Zscaler AI Guard

This directory contains the integration between [TrueFoundry AI Gateway](https://truefoundry.com/) and Zscaler AI Guard. The integration provides a custom guardrail server that TrueFoundry calls to scan LLM inputs and outputs for security threats.

## Overview

TrueFoundry supports **custom guardrails** via external FastAPI servers. This integration provides a guardrail server that calls the Zscaler AI Guard DAS API to scan content for PII leakage, secrets exposure, toxicity, prompt injections, and policy violations.

### How It Works

```
User Prompt
    │
    ▼
┌───────────────────────┐
│  TrueFoundry Gateway  │
│  (routes to guardrail)│
└──────────┬────────────┘
           │
           ▼
┌───────────────────────────────┐
│  AI Guard Guardrail Server    │
│  POST /input-scan             │ ◄── Scans prompt (direction=IN)
│  POST /output-scan            │ ◄── Scans response (direction=OUT)
│                               │
│  Uses zscaler-sdk-python      │
│  → resolve-and-execute-policy │
└──────────┬────────────────────┘
           │
           ▼
  null = ALLOW  |  HTTP 400 = BLOCK
```

TrueFoundry's guardrail hooks:

| Hook | Endpoint | Description |
|---|---|---|
| LLM Input | `POST /input-scan` | Scans prompts before they reach the LLM |
| LLM Output | `POST /output-scan` | Scans responses before returning to the user |

AI Guard uses automatic policy resolution — no profile name or policy ID is needed.

## Quick Start

```bash
cd examples
cp env.example .env              # add your AIGUARD_API_KEY
python start_server.py           # builds and starts on port 8000
python test_input.py "What is 2+2?"
python test_output.py "The answer is 4."
```

See [`examples/README.md`](examples/README.md) for full details.

## Registering in TrueFoundry Dashboard

Once the guardrail server is running and accessible, register it in TrueFoundry:

1. Go to **AI Gateway > Guardrails** in the TrueFoundry dashboard.
2. Click **Add New Guardrails Group**.
3. Configure the custom guardrail:

   | Field | Value |
   |---|---|
   | **Name** | `zscaler-aiguard` |
   | **URL** | `http://<your-server>:8000/input-scan` (for input guardrails) |
   | **Operation** | `Validate` |
   | **Auth Data** | None (or add if you secure the server) |
   | **Config** | `{}` |

4. Repeat for the output endpoint (`/output-scan`).
5. Create guardrail rules to apply them to specific models, users, or MCP tools.

### Example YAML Configuration

```yaml
name: guardrails-control
type: gateway-guardrails-config
rules:
  - id: aiguard-all-traffic
    when: {}
    llm_input_guardrails:
      - my-guardrails-group/zscaler-aiguard-input
    llm_output_guardrails:
      - my-guardrails-group/zscaler-aiguard-output
    mcp_tool_pre_invoke_guardrails: []
    mcp_tool_post_invoke_guardrails: []
```

## Response Behavior

- **Content allowed:** Returns `null` (HTTP 200) — TrueFoundry proceeds normally.
- **Content blocked:** Returns HTTP 400 with detailed JSON:

```json
{
  "detail": {
    "message": "Request blocked by Zscaler AI Guard",
    "action": "BLOCK",
    "severity": "CRITICAL",
    "direction": "IN",
    "policy_name": "PolicyApp01",
    "policy_id": 900,
    "transaction_id": "abc-123",
    "blocking_detectors": ["pii", "secrets"],
    "detectors": {
      "toxicity": {"action": "ALLOW", "triggered": false},
      "pii": {"action": "BLOCK", "triggered": true},
      "secrets": {"action": "BLOCK", "triggered": false}
    }
  }
}
```

## Prerequisites

- An active Zscaler AI Guard license and API key
- Docker (for running the guardrail server)
- Python 3.10+
- TrueFoundry platform access

## Links

- [TrueFoundry Custom Guardrails Docs](https://truefoundry.com/docs/ai-gateway/custom-guardrails)
- [TrueFoundry Guardrails Configuration](https://truefoundry.com/docs/ai-gateway/guardrails-configuration)
- [Custom Guardrails Template Repo](https://github.com/truefoundry/custom-guardrails-template)
- [Zscaler AI Guard](https://www.zscaler.com/products/ai-guard)
