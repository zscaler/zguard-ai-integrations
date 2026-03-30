# Zscaler AI Guard Integrations

Integration repository for connecting **Zscaler AI Guard** with third-party AI gateways, LLM platforms, and automation tools. Each integration scans prompts and LLM responses via the AI Guard DAS API (`resolve-and-execute-policy`) to enforce DLP, content safety, PII detection, secrets scanning, and compliance policies.

## Repository Purpose

Working code, configuration examples, and documentation for deploying Zscaler AI Guard across the AI ecosystem. Where possible, integrations use **`zscaler-sdk-python`** (`LegacyZGuardClientHelper`) for direct SDK-based API calls rather than raw HTTP.

## Structure

```
├── Anthropic/          # Claude Code hooks (pre/post scan via hooks system)
├── Azure/              # Azure API Management policy integration
├── Cursor/             # Cursor IDE hooks (beforeSubmitPrompt, beforeMCPExecution, postToolUse, afterAgentResponse)
├── Cline/              # Cline VS Code hooks (UserPromptSubmit, PreToolUse, PostToolUse, TaskComplete)
├── Windsurf/           # Windsurf Cascade hooks (pre/post prompt, command, MCP, cascade response)
├── Google/             # Google Apigee + Vertex AI proxy
├── Kong/               # Kong Gateway — Lua custom plugin & Konnect request callout
├── LiteLLM/            # LiteLLM proxy — Python custom callback (zscaler-sdk-python)
├── NemoGuardrails/     # NVIDIA NeMo Guardrails — custom action + library plugin (zscaler-sdk-python)
├── Portkey/            # Portkey AI Gateway — client-side SDK scanning (zscaler-sdk-python)
├── TrueFoundry/        # TrueFoundry — custom guardrail server via FastAPI (zscaler-sdk-python)
├── github-actions/     # GitHub Actions CI/CD — policy validation pipeline (zscaler-sdk-python)
├── Jenkins/            # Jenkins Declarative Pipeline — policy validation (zscaler-sdk-python)
├── n8n/                # n8n workflow automation — custom TypeScript node
```

### Integration Patterns

| Pattern | Language | Used By |
|---------|----------|---------|
| Python SDK callback/action | Python | LiteLLM, NemoGuardrails, Portkey, TrueFoundry |
| Lua gateway plugin | Lua | Kong (self-managed) |
| Lua request callout config | Lua/YAML | Kong (Konnect SaaS) |
| TypeScript gateway plugin | TypeScript | n8n, Portkey (native plugin) |
| FastAPI guardrail server | Python | TrueFoundry |
| Claude Code hooks | Python | Anthropic |
| Cursor IDE hooks | Python | Cursor |
| Cline IDE hooks | Python | Cline |
| Windsurf Cascade hooks | Python | Windsurf |
| CI/CD policy validation | Python | GitHub Actions, Jenkins |
| API Management policy | XML/config | Azure APIM, Google Apigee |

### Per-Integration Details

| Integration | SDK | Docker | Test Scripts | Native Plugin |
|-------------|:---:|:------:|:------------:|:-------------:|
| Anthropic | ✅ | — | — | — |
| Azure | — | — | — | — |
| Cursor | ✅ | — | ✅ | Python hooks |
| Cline | ✅ | — | — | Python hooks |
| Windsurf | ✅ | — | — | Python hooks |
| Google | ✅ | — | ✅ | — |
| Kong | — | ✅ | ✅ | Lua plugin |
| LiteLLM | ✅ | ✅ | ✅ | Callback |
| NemoGuardrails | ✅ | — | — | Library plugin (PR-ready) |
| Portkey | ✅ | ✅ | ✅ | TS plugin (PR-ready) |
| TrueFoundry | ✅ | ✅ | ✅ | FastAPI server |
| GitHub Actions | ✅ | — | ✅ | Policy validation |
| Jenkins | ✅ | — | ✅ | Policy validation |
| n8n | — | ✅ | — | TS node |

## Zscaler AI Guard API

All integrations call the same underlying API:

- **Endpoint**: `https://api.{cloud}.zseclipse.net/v1/detection/resolve-and-execute-policy`
- **Auth**: `Authorization: Bearer {AIGUARD_API_KEY}`
- **Payload**: `{"direction": "IN"|"OUT", "content": "text to scan"}`
- **Response fields**: `action` (ALLOW/BLOCK/DETECT), `severity`, `policyName`, `transactionId`, `detectorResponses`

### SDK Usage (preferred)

```python
from zscaler.zaiguard.legacy import LegacyZGuardClientHelper

client = LegacyZGuardClientHelper(cloud="us1")
result, response, error = client.policy_detection.resolve_and_execute_policy(
    content="text to scan",
    direction="IN",
)
```

### Environment Variables

| Variable | Required | Default | Description |
|----------|:--------:|---------|-------------|
| `AIGUARD_API_KEY` | Yes | — | Zscaler AI Guard API key (Bearer token) |
| `AIGUARD_CLOUD` | No | `us1` | Cloud region: us1, us2, eu1, etc. |

## Working in This Repo

### Adding New Integrations

1. Create directory: `PlatformName/`
2. Include a `README.md` with: Overview, Prerequisites, Quick Start, Configuration
3. Add `examples/` with working code, `env.example`, `requirements.txt` (Python) or `package.json` (TypeScript)
4. Use `zscaler-sdk-python` when the integration supports Python
5. Provide Docker Compose for anything that needs a running server
6. Update root `README.md` with the new integration

### Technical Requirements

All integrations MUST:
1. Use `zscaler-sdk-python` (`LegacyZGuardClientHelper`) when Python is available
2. Implement fail-closed logic — block when the API call fails or returns unexpected data
3. Support both `direction=IN` (prompt scanning) and `direction=OUT` (response scanning)
4. Never include real credentials — use `AIGUARD_API_KEY`, `AIGUARD_CLOUD` environment variables
5. Provide detailed block messages including: action, severity, policy name, transaction ID, blocking detectors

### Commit Convention

```
feat: add [Platform] integration
fix: correct [Platform] configuration
docs: update [Platform] README
test: add validation scripts for [Platform]
```

## Key Files

| File | Purpose |
|------|---------|
| `README.md` | Integration index and overview |
| `Makefile` | Local `make test-compile`, policy scans, hook sample scripts |
| `.github/workflows/weekly-integrations.yml` | Weekly Monday CI: compile + dual policy scan |
| `CLAUDE.md` | This file — project context for AI agents |
| `.claude/agents.md` | Sub-agent instructions |
| `local_dev/` | Development artifacts, plugin staging, internal docs |

## Upstream Plugin Submissions

Some integrations have native plugins ready for PR to upstream repos:

| Platform | Upstream Repo | Plugin Location | Branch |
|----------|---------------|-----------------|--------|
| NemoGuardrails | `NVIDIA-NeMo/Guardrails` | `nemoguardrails/library/zscaler_aiguard/` | `feat/zscaler-aiguard-integration` |
| Portkey | `Portkey-AI/gateway` | `plugins/zscaler-aiguard/` | `feat/zscaler-aiguard-guardrail` |

Local copies of these plugins are kept in `NemoGuardrails/library-plugin/` and `local_dev/gateway-plugin/`.

## External Resources

- [Zscaler AI Guard](https://www.zscaler.com/products/ai-guard)
- [zscaler-sdk-python](https://github.com/zscaler/zscaler-sdk-python) — `zscaler.zaiguard.legacy.LegacyZGuardClientHelper`
- [NVIDIA NeMo Guardrails](https://github.com/NVIDIA-NeMo/Guardrails)
- [Portkey AI Gateway](https://github.com/Portkey-AI/gateway)
- [LiteLLM](https://github.com/BerriAI/litellm)
- Design reference: `PaloAltoNetworks/prisma-airs-integrations`