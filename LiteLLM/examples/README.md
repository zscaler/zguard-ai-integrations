# LiteLLM Examples

> **Recommended:** LiteLLM now includes a native Zscaler AI Guard guardrail — no custom code needed.
> See [config-native-guardrail.yaml](config-native-guardrail.yaml) or the [official docs](https://docs.litellm.ai/docs/proxy/guardrails/zscaler_ai_guard).

The examples below use the **SDK-based custom callback** approach, which provides automatic policy resolution via `resolve-and-execute-policy`.

## Quick Start (Anthropic)

```bash
# 1. Set your keys
export ANTHROPIC_API_KEY="your-anthropic-key"
export AIGUARD_API_KEY="your-aiguard-key"

# 2. Start the proxy
python start_anthropic.py

# 3. Test
python test_anthropic.py "What is 2+2?"
```

## Quick Start (All Providers)

```bash
# 1. Set your keys (or use .env file)
export AZURE_OPENAI_API_KEY="your-azure-key"
export AZURE_RESOURCE="your-azure-resource"
export AWS_ACCESS_KEY_ID="your-aws-key"
export AWS_SECRET_ACCESS_KEY="your-aws-secret"
export AWS_REGION="us-east-1"
export AIGUARD_API_KEY="your-aiguard-key"

# 2. Start the proxy
python start_all.py

# 3. Test each provider
python test_azure.py "What is 2+2?"
python test_aws.py "Tell me a joke"
```

## Files

| File | Purpose |
|------|---------|
| `aiguard_guardrail.py` | AI Guard SDK callback — scans prompts and responses via `zscaler-sdk-python` |
| `config-native-guardrail.yaml` | Native guardrail config (recommended, no custom code) |
| `config-anthropic.yaml` | SDK callback config for Anthropic |
| `config-all.yaml` | SDK callback config for Azure + AWS |
| `config-azure.yaml` | SDK callback config for Azure OpenAI |
| `config-aws.yaml` | SDK callback config for AWS Bedrock |
| `start_anthropic.py` | Start proxy with Anthropic + AI Guard |
| `start_all.py` | Start proxy with Azure + AWS + AI Guard |
| `test_anthropic.py` | Test with Anthropic Claude |
| `test_azure.py` | Test with Azure OpenAI |
| `test_aws.py` | Test with AWS Bedrock |
| `docker-compose.yml` | Container configuration |
| `Dockerfile` | Extends LiteLLM image with `zscaler-sdk-python` |
| `env.example` | Template for environment variables |

## Environment Variables

Set directly or put in a `.env` file (copy from `env.example`):

| Variable | Required For | Description |
|----------|-------------|-------------|
| `AIGUARD_API_KEY` | SDK callback | Zscaler AI Guard API key |
| `AIGUARD_CLOUD` | SDK callback | Cloud region (default: `us1`) |
| `ZSCALER_AI_GUARD_API_KEY` | Native plugin | Zscaler AI Guard API key |
| `ZSCALER_AI_GUARD_POLICY_ID` | Native plugin | Policy ID (optional) |
| `ANTHROPIC_API_KEY` | Anthropic | Anthropic API key |
| `AZURE_OPENAI_API_KEY` | Azure | Azure OpenAI API key |
| `AZURE_RESOURCE` | Azure | Azure resource name |
| `AWS_ACCESS_KEY_ID` | AWS | AWS access key |
| `AWS_SECRET_ACCESS_KEY` | AWS | AWS secret key |
| `AWS_REGION` | AWS | AWS region |

## How It Works (SDK Callback)

```
Client → LiteLLM Proxy → AI Guard scan (IN) → LLM → AI Guard scan (OUT) → Client
```

1. LiteLLM starts as an OpenAI-compatible proxy
2. Every request hits `aiguard_guardrail.py` pre_call hook → AI Guard `resolve-and-execute-policy` (direction=IN)
3. If `action=ALLOW` → request goes to the LLM
4. If `action=BLOCK` → request rejected with 403
5. LLM response hits post_call hook → AI Guard `resolve-and-execute-policy` (direction=OUT)
6. If `action=BLOCK` → response rejected before reaching client

## Managing the Proxy

```bash
docker compose logs -f     # stream logs
docker compose ps          # check status
docker compose down        # stop
```

---

For more information, see the main [README.md](../README.md).
