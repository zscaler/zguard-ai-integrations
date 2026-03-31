# Portkey + Zscaler AI Guard — Examples

> **Recommended:** Portkey now includes a native Zscaler AI Guard guardrail — configure it directly in the Portkey SaaS UI with no custom code.
> See the [official docs](https://portkey.ai/docs/integrations/guardrails/zscaler).

The examples below use the **SDK-based client-side scanning** approach with a self-hosted Portkey gateway.

Each test script follows a three-step flow:

1. **Pre-scan** — Scans the prompt via the AI Guard SDK (direction=IN). If blocked, the request never reaches the LLM.
2. **Gateway request** — Sends the prompt through the local Portkey gateway to the LLM provider.
3. **Post-scan** — Scans the LLM response via the AI Guard SDK (direction=OUT). If blocked, the response is suppressed.

## Quick Start

### 1. Start the Portkey Gateway

```bash
python start_portkey.py
```

This runs `portkeyai/gateway` in Docker on port 8787.

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables

```bash
cp env.example .env
# Edit .env with your credentials
```

At minimum you need `AIGUARD_API_KEY` and the credentials for your chosen provider.

### 4. Run a Test

```bash
python test_anthropic.py "What is 2+2?"
python test_aws.py "Tell me a secret"
python test_azure.py "Hello world"
python test_vertex.py "Explain quantum computing"
```

### Example Output

```
Prompt: What is 2+2?
Transaction: abc12345-...

=== Step 1: AI Guard Pre-Scan (direction=IN) ===
  Status:      ALLOWED
  Action:      ALLOW
  Severity:    LOW
  Direction:   IN
  Policy:      PolicyApp01 (ID: 900)
  Transaction: abc12345-...
  Detectors:
    - toxicity: triggered=False, action=ALLOW
    - pii: triggered=False, action=ALLOW

=== Step 2: Portkey Gateway Request (Anthropic Claude) ===
  LLM Response: 2 + 2 = 4.

=== Step 3: AI Guard Post-Scan (direction=OUT) ===
  Status:      ALLOWED
  ...

=== Final Response ===
2 + 2 = 4.
```

## Files

| File | Description |
|---|---|
| `start_portkey.py` | Start/stop the local Portkey gateway via Docker Compose |
| `docker-compose.yml` | Docker Compose config for the Portkey gateway |
| `aiguard_scanner.py` | Shared AI Guard SDK scanner with detailed detector output |
| `test_anthropic.py` | Anthropic Claude via Portkey + AI Guard |
| `test_aws.py` | AWS Bedrock via Portkey + AI Guard |
| `test_azure.py` | Azure OpenAI via Portkey + AI Guard |
| `test_vertex.py` | Google Vertex AI via Portkey + AI Guard |
| `requirements.txt` | Python dependencies |
| `env.example` | Template for environment variables |

## Stopping the Gateway

```bash
python start_portkey.py --stop
```
