# NeMo Guardrails Integration with Zscaler AI Guard

This directory contains the integration between [NVIDIA NeMo Guardrails](https://github.com/NVIDIA-NeMo/Guardrails) and Zscaler AI Guard. It provides input and output rails that scan LLM prompts and responses for security threats using the `zscaler-sdk-python` SDK.

## Overview

NeMo Guardrails is an open-source toolkit for adding programmable guardrails to LLM applications. This integration registers a custom action that calls the AI Guard DAS API to scan content for PII leakage, secrets exposure, toxicity, prompt injections, and policy violations.

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Your Application                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    NeMo Guardrails                              │
│  ┌───────────────┐    ┌───────────────┐    ┌───────────────┐    │
│  │  Input Rails  │───▶│   LLM Call    │───▶│ Output Rails  │    │
│  └───────────────┘    └───────────────┘    └───────────────┘    │
│         │                                          │            │
│         ▼                                          ▼            │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │       Zscaler AI Guard Action (zscaler-sdk-python)      │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              Zscaler AI Guard DAS API                            │
│           (resolve-and-execute-policy)                           │
└─────────────────────────────────────────────────────────────────┘
```

## Contents

### `config/` — Ready-to-Use Custom Config

A standalone NeMo Guardrails configuration with the AI Guard action. Copy this into your NeMo Guardrails project to get started immediately.

| File | Description |
|---|---|
| `config.yml` | NeMo Guardrails config referencing the action and flows |
| `actions/zs-ai-guard.py` | Custom action using `zscaler-sdk-python` |
| `rails/rails.co` | Colang flow definitions for input/output scanning |

**Quick start:**

```bash
pip install nemoguardrails zscaler-sdk-python python-dotenv
export AIGUARD_API_KEY=your-api-key
export AIGUARD_CLOUD=us1

# Copy config/ to your NeMo Guardrails project
nemoguardrails chat --config=config/
```

### `library-plugin/` — For Contributing to NeMo Guardrails

A library-format plugin (`zscaler_aiguard/`) ready to submit as a PR to [NVIDIA-NeMo/Guardrails](https://github.com/NVIDIA-NeMo/Guardrails). Once merged, users can reference the flows without copying any files.

See [`library-plugin/README.md`](library-plugin/README.md) for submission instructions.

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `AIGUARD_API_KEY` | Yes | — | Zscaler AI Guard API key |
| `AIGUARD_CLOUD` | No | `us1` | Cloud region (us1, us2, eu1, etc.) |

### config.yml

```yaml
models:
  - type: main
    engine: openai
    model: gpt-4o-mini

actions:
  - type: custom
    name: CallZscalerAiGuardAction
    path: actions/zs-ai-guard.py

rails:
  input:
    flows:
      - zscaler aiguard inspect prompt
  output:
    flows:
      - zscaler aiguard inspect response
```

### Colang Flows

The action returns a dict with `blocked` (bool), `triggered_by` (list of detectors), `transaction_id`, and `policy_name`. The flows check `blocked` and stop the conversation if content is denied.

```colang
define flow zscaler aiguard inspect prompt
  $result = execute CallZscalerAiGuardAction(prompt=$user_message)
  if $result[blocked]
    bot refuse to respond
    stop
```

## Behavior

- **Fail-closed**: If the API call fails or returns an unexpected response, content is blocked by default.
- **Automatic policy resolution**: No profile name or policy ID needed — policies are resolved based on your Zscaler tenant configuration.
- **Async-safe**: The SDK's synchronous calls are wrapped with `asyncio.to_thread` for compatibility with NeMo Guardrails' async runtime.

## Prerequisites

- Python 3.10+
- NVIDIA NeMo Guardrails 0.18.0+
- Zscaler AI Guard subscription with API access
- `zscaler-sdk-python` package

## Links

- [NeMo Guardrails](https://github.com/NVIDIA-NeMo/Guardrails)
- [NeMo Guardrails Docs](https://docs.nvidia.com/nemo/guardrails/latest/index.html)
- [Zscaler AI Guard](https://www.zscaler.com/products/ai-guard)
