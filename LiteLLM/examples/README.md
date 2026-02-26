# LiteLLM Examples

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
| `aiguard_guardrail.py` | AI Guard callback — scans prompts via `zscaler-sdk-python` |
| `start_anthropic.py` | Start proxy with Anthropic + AI Guard |
| `start_all.py` | Start proxy with Azure + AWS + AI Guard |
| `test_anthropic.py` | Test with Anthropic Claude |
| `test_azure.py` | Test with Azure OpenAI |
| `test_aws.py` | Test with AWS Bedrock |
| `docker-compose.yml` | Container configuration |
| `Dockerfile` | Extends LiteLLM image with `zscaler-sdk-python` |
| `config-anthropic.yaml` | LiteLLM config for Anthropic |
| `config-all.yaml` | LiteLLM config for Azure + AWS |
| `env.example` | Template for environment variables |

## Environment Variables

Set directly or put in a `.env` file (copy from `env.example`):

| Variable | Required For | Description |
|----------|-------------|-------------|
| `AIGUARD_API_KEY` | All | Zscaler AI Guard API key |
| `AIGUARD_CLOUD` | All | Cloud region (default: `us1`) |
| `ANTHROPIC_API_KEY` | Anthropic | Anthropic API key |
| `AZURE_OPENAI_API_KEY` | Azure | Azure OpenAI API key |
| `AZURE_RESOURCE` | Azure | Azure resource name |
| `AWS_ACCESS_KEY_ID` | AWS | AWS access key |
| `AWS_SECRET_ACCESS_KEY` | AWS | AWS secret key |
| `AWS_REGION` | AWS | AWS region |

## How It Works

```
Client → LiteLLM Proxy → AI Guard scan → LLM (if allowed)
```

1. LiteLLM starts as an OpenAI-compatible proxy
2. Every request hits `aiguard_guardrail.py` which calls AI Guard `resolve-and-execute-policy`
3. If `action=ALLOW` → request goes to the LLM
4. If `action=BLOCK` → request rejected with error

## Managing the Proxy

```bash
docker compose logs -f     # stream logs
docker compose ps          # check status
docker compose down        # stop
```

---

For more information, see the main [README.md](../README.md).
