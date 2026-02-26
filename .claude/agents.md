# Agent Instructions

Instructions for sub-agents working in this repository.

**Read `/CLAUDE.md` first** — it contains the full project context, structure, conventions, and API details.

## Project Context

This repo integrates **Zscaler AI Guard** with third-party AI gateways and platforms. The core API is `resolve-and-execute-policy` from the AI Guard DAS service. The preferred client is `zscaler-sdk-python` (`LegacyZGuardClientHelper`).

## Key Constraints

### Security (non-negotiable)
- NEVER include real API keys, tokens, or credentials in code or docs
- Use environment variables: `AIGUARD_API_KEY`, `AIGUARD_CLOUD`
- Provide `env.example` files with placeholder values

### SDK Usage
- Use `zscaler-sdk-python` (`from zscaler.zaiguard.legacy import LegacyZGuardClientHelper`) wherever Python is available
- Do NOT use raw `httpx` / `requests` / `aiohttp` calls to the AI Guard API — use the SDK
- Wrap synchronous SDK calls with `asyncio.to_thread()` in async contexts
- Initialize the SDK client lazily (on first use, not at module import)

### Fail-Closed Logic
- If the API call fails, errors out, or returns unexpected data: **block the content**
- Only allow content when the API explicitly returns `action: ALLOW`

### Block Messages
- Include detailed context: action, severity, policy name, transaction ID, blocking detectors
- Parse `detectorResponses` to identify which specific detectors triggered the block

### Code Style
- Python preferred over shell scripts for all tooling, test scripts, and server management
- Use `python-dotenv` for environment variable loading
- Provide `requirements.txt` for Python projects, `package.json` for TypeScript
- Docker Compose for anything that runs as a server

## Integration Directory Structure

Each integration should follow this pattern:

```
PlatformName/
├── README.md              # Overview, prerequisites, quick start
└── examples/
    ├── README.md          # Detailed usage instructions
    ├── env.example        # Environment variable template
    ├── requirements.txt   # Python dependencies (if applicable)
    ├── docker-compose.yml # Docker setup (if applicable)
    ├── Dockerfile         # Container definition (if applicable)
    ├── main.py            # Core integration code
    ├── start_*.py         # Server/service management scripts
    └── test_*.py          # Test/validation scripts
```

## Before Completing Work

- [ ] Integration uses `zscaler-sdk-python` (not raw HTTP) when Python is available
- [ ] Fail-closed logic is implemented
- [ ] Block messages include detector details
- [ ] No real credentials included anywhere
- [ ] `env.example` provided with placeholder values
- [ ] Code examples are syntactically correct and tested
- [ ] README includes: Overview, Prerequisites, Quick Start, Configuration

## Commit Messages

```
feat: add [Platform] integration
fix: correct [Platform] configuration
docs: update [Platform] README
test: add validation scripts for [Platform]
```

## Existing Integrations Reference

| Integration | Entry Point | Key Files |
|-------------|-------------|-----------|
| LiteLLM | `LiteLLM/examples/aiguard_guardrail.py` | Custom callback via `CustomLogger` |
| NemoGuardrails | `NemoGuardrails/config/actions/zs-ai-guard.py` | NeMo `@action` decorator |
| Portkey | `Portkey/examples/aiguard_scanner.py` | Shared scanner module for test scripts |
| TrueFoundry | `TrueFoundry/examples/main.py` | FastAPI guardrail server |
| Kong | `Kong/custom-plugin/handler.lua` | Lua plugin (no SDK, raw HTTP) |
| n8n | `n8n/nodes/AIGuard/AIGuard.node.ts` | TypeScript n8n node |
| Anthropic | `Anthropic/claude-code-aiguard/hooks/` | Claude Code hooks system |