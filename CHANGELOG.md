# Zscaler AI Guard Integrations Changelog

## 0.1.0 (March 28, 2026)

### Notes

- Python Versions: **v3.11, v3.12, v3.13**
- Initial integration set: pull request [#1][pr1].

### Features

- [PR #6](https://github.com/zscaler/zguard-ai-integrations/pull/6) - **Anthropic (Claude Code)** — Python hooks for pre/post prompt and tool-use scanning via the AI Guard DAS API.
- [PR #6](https://github.com/zscaler/zguard-ai-integrations/pull/6) - **Azure API Management** — Gateway policy patterns to scan AI requests and responses at the edge.
- [PR #6](https://github.com/zscaler/zguard-ai-integrations/pull/6) **Cursor IDE** — Project hooks for prompts, MCP, tool use, and agent responses.
- [PR #6](https://github.com/zscaler/zguard-ai-integrations/pull/6) **Cline (VS Code)** — Extension hook scripts and shared utilities for UserPromptSubmit, PreToolUse, PostToolUse, and TaskComplete.
- [PR #6](https://github.com/zscaler/zguard-ai-integrations/pull/6) **Windsurf** — Cascade hooks for pre/post user prompts, shell commands, MCP, and cascade completion.
- [PR #6](https://github.com/zscaler/zguard-ai-integrations/pull/6) **Google (Apigee + Vertex AI)** — Apigee proxy and Vertex-oriented configuration for scanning proxied LLM traffic.
- [PR #6](https://github.com/zscaler/zguard-ai-integrations/pull/6) **Kong Gateway** — Self-managed Lua plugin and Konnect request-callout examples for inline policy enforcement.
- [PR #6](https://github.com/zscaler/zguard-ai-integrations/pull/6) **LiteLLM** — Proxy custom callback using `zscaler-sdk-python` for IN/OUT scanning.
- [PR #6](https://github.com/zscaler/zguard-ai-integrations/pull/6) **NVIDIA NeMo Guardrails** — Custom action and library plugin wiring AI Guard into guardrails flows.
- [PR #6](https://github.com/zscaler/zguard-ai-integrations/pull/6) **Portkey AI Gateway** — Client-side SDK scanning and gateway-oriented examples.
- [PR #6](https://github.com/zscaler/zguard-ai-integrations/pull/6) **TrueFoundry** — FastAPI guardrail server that delegates scans to AI Guard.
- [PR #6](https://github.com/zscaler/zguard-ai-integrations/pull/6) **GitHub Actions** — CI/CD policy validation pipeline (`scan_policy.py`, test prompts, workflow samples).
- [PR #6](https://github.com/zscaler/zguard-ai-integrations/pull/6) **Jenkins** — Declarative pipeline parity with GitHub Actions for policy validation.
- [PR #6](https://github.com/zscaler/zguard-ai-integrations/pull/6)**n8n** — Custom workflow node (TypeScript) and example workflows for automation.