# Portkey Integration with Zscaler AI Guard

This directory contains the integration between the [Portkey AI Gateway](https://portkey.ai/) and Zscaler AI Guard. The integration enables real-time security scanning of LLM inputs and outputs routed through Portkey.

## Overview

Portkey is an AI gateway that provides a unified API for 200+ LLM providers. Zscaler AI Guard integrates as a **client-side guardrail** using the `zscaler-sdk-python` SDK to scan prompts and responses before and after they pass through the Portkey gateway.

### How It Works

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

## Quick Start

```bash
cd examples
python start_portkey.py            # start gateway on port 8787
pip install -r requirements.txt
cp env.example .env                # add your credentials
python test_anthropic.py "What is 2+2?"
```

See [`examples/README.md`](examples/README.md) for full details on all provider scripts.

## Prerequisites

- An active Zscaler AI Guard license and API key
- Docker (for the self-hosted Portkey gateway)
- Python 3.10+
- Credentials for at least one LLM provider (Anthropic, AWS, Azure, or GCP)

## Links

- [Portkey Gateway Repo](https://github.com/Portkey-AI/gateway)
- [Portkey Docs](https://portkey.ai/docs/)
- [Zscaler AI Guard](https://www.zscaler.com/products/ai-guard)
