# Portkey Integration with Zscaler AI Guard

This directory contains the integration between the [Portkey AI Gateway](https://portkey.ai/) and Zscaler AI Guard. The integration enables real-time security scanning of LLM inputs and outputs routed through Portkey.

---

> **Zscaler AI Guard is now a native Portkey guardrail.** Portkey has published a first-party integration on their SaaS platform — configure it directly from the Portkey Admin Settings with no custom code.
>
> **Official documentation:** [portkey.ai/docs/integrations/guardrails/zscaler](https://portkey.ai/docs/integrations/guardrails/zscaler)
>
> The native plugin supports `beforeRequestHook` (input scanning) and `afterRequestHook` (output scanning), configurable Policy ID and timeout, and works with all Portkey-managed LLM providers.

---

## Two Integration Approaches

### Option A: Native Portkey Plugin (Recommended for Portkey SaaS)

Use the built-in Zscaler AI Guard guardrail on the Portkey SaaS platform. No custom code, no SDK installation.

1. Navigate to **Admin Settings > Plugins** in Portkey
2. Add your **Zscaler AI Guard API Key**
3. Go to **Guardrails > Create**, search for "Zscaler AI Guard"
4. Configure **Policy ID** and **Timeout**
5. Add the Guardrail ID to your Portkey Config:

```json
{
  "input_guardrails": ["guardrails-id-xxx"],
  "output_guardrails": ["guardrails-id-xxx"]
}
```

**Advantages:**
- Zero custom code — native UI configuration
- Server-side scanning inside the Portkey gateway
- Works with all Portkey-managed providers
- Configurable per-request via Portkey Config

See the [official docs](https://portkey.ai/docs/integrations/guardrails/zscaler) for full setup.

### Option B: SDK-Based Client-Side Scanning

Use the `zscaler-sdk-python` SDK to scan prompts and responses client-side, before and after they pass through a self-hosted Portkey gateway.

**Advantages:**
- Works with the self-hosted Portkey gateway (no SaaS dependency)
- Uses `zscaler-sdk-python` (`LegacyZGuardClientHelper`)
- Automatic policy resolution via `resolve-and-execute-policy` (no explicit Policy ID)
- Full control over scan logic and error handling

**Requires:**
- Self-hosted Portkey gateway via Docker
- Python 3.10+ with `zscaler-sdk-python`

See the [examples/](examples/) directory for working scripts.

---

## How It Works (SDK Approach)

```
User Prompt
    │
    ▼
┌──────────────────────────┐
│  AI Guard Pre-Scan (IN)  │ ◄── SDK scans prompt
│  action=ALLOW → proceed  │
│  action=BLOCK → stop     │
└──────────┬───────────────┘
           │
           ▼
┌──────────────────────────┐
│  Portkey Gateway         │ ◄── Routes to any LLM provider
│  (Anthropic, AWS, Azure, │
│   Vertex AI, etc.)       │
└──────────┬───────────────┘
           │
           ▼
┌──────────────────────────┐
│  AI Guard Post-Scan (OUT)│ ◄── SDK scans LLM response
│  action=ALLOW → return   │
│  action=BLOCK → suppress │
└──────────────────────────┘
```

The SDK calls the AI Guard DAS API (`resolve-and-execute-policy`) which automatically resolves the appropriate policy — no profile name or policy ID needed at the gateway level.

## Quick Start (SDK Approach)

```bash
cd examples
python start_portkey.py            # start gateway on port 8787
pip install -r requirements.txt
cp env.example .env                # add your credentials
python test_anthropic.py "What is 2+2?"
```

See [`examples/README.md`](examples/README.md) for all provider scripts.

## Prerequisites

- An active Zscaler AI Guard license and API key

For the native plugin (Option A):
- A Portkey SaaS account

For the SDK approach (Option B):
- Docker (for the self-hosted Portkey gateway)
- Python 3.10+
- Credentials for at least one LLM provider (Anthropic, AWS, Azure, or GCP)

## Comparison

| Feature | Native Plugin | SDK Client-Side |
|---------|:---:|:---:|
| Custom code | Not required | Python scripts |
| Scanning location | Server-side (Portkey SaaS) | Client-side (Python) |
| Policy selection | Explicit Policy ID | Auto-resolution |
| Self-hosted gateway | Not supported | Supported |
| Provider support | All Portkey-managed | All via gateway |
| SDK | Direct API (built-in) | `zscaler-sdk-python` |

## Links

- [Portkey Zscaler AI Guard Docs](https://portkey.ai/docs/integrations/guardrails/zscaler) (native plugin)
- [Portkey Gateway Repo](https://github.com/Portkey-AI/gateway)
- [Portkey Docs](https://portkey.ai/docs/)
- [zscaler-sdk-python](https://github.com/zscaler/zscaler-sdk-python)
- [Zscaler AI Guard](https://www.zscaler.com/products/ai-guard)
