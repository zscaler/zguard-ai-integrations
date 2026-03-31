# Zscaler AI Guard Integrations Changelog

## 0.1.1 (March 31, 2026)

### Notes

- Python Versions: **v3.11, v3.12, v3.13**

### Bug Fixes

- [PR #8](https://github.com/zscaler/zguard-ai-integrations/pull/8) - Fixed LiteLLM and Port Key Documentation to point to official plugin registry pages.

## 0.1.0 (March 31, 2026)

### Notes

- Python Versions: **v3.11, v3.12, v3.13**

### Features

- [PR #7](https://github.com/zscaler/zguard-ai-integrations/pull/7) - **Anthropic (Claude Code)** — Python hooks for pre/post prompt and tool-use scanning via the AI Guard DAS API.
- [PR #7](https://github.com/zscaler/zguard-ai-integrations/pull/7) - **Azure API Management** — Gateway policy patterns to scan AI requests and responses at the edge.
- [PR #7](https://github.com/zscaler/zguard-ai-integrations/pull/7) **Cursor IDE** — Project hooks for prompts, MCP, tool use, and agent responses.
- [PR #7](https://github.com/zscaler/zguard-ai-integrations/pull/7) **Cline (VS Code)** — Extension hook scripts and shared utilities for UserPromptSubmit, PreToolUse, PostToolUse, and TaskComplete.
- [PR #7](https://github.com/zscaler/zguard-ai-integrations/pull/7) **Windsurf** — Cascade hooks for pre/post user prompts, shell commands, MCP, and cascade completion.
- [PR #7](https://github.com/zscaler/zguard-ai-integrations/pull/7) **Google (Apigee + Vertex AI)** — Apigee proxy and Vertex-oriented configuration for scanning proxied LLM traffic.
- [PR #7](https://github.com/zscaler/zguard-ai-integrations/pull/7) **Kong Gateway** — Self-managed Lua plugin and Konnect request-callout examples for inline policy enforcement.
- [PR #7](https://github.com/zscaler/zguard-ai-integrations/pull/7) **LiteLLM** — Proxy custom callback using `zscaler-sdk-python` for IN/OUT scanning.
- [PR #7](https://github.com/zscaler/zguard-ai-integrations/pull/7) **NVIDIA NeMo Guardrails** — Custom action and library plugin wiring AI Guard into guardrails flows.
- [PR #7](https://github.com/zscaler/zguard-ai-integrations/pull/7) **Portkey AI Gateway** — Client-side SDK scanning and gateway-oriented examples.
- [PR #7](https://github.com/zscaler/zguard-ai-integrations/pull/7) **TrueFoundry** — FastAPI guardrail server that delegates scans to AI Guard.
- [PR #7](https://github.com/zscaler/zguard-ai-integrations/pull/7) **GitHub Actions** — CI/CD policy validation pipeline (`scan_policy.py`, test prompts, workflow samples).
- [PR #7](https://github.com/zscaler/zguard-ai-integrations/pull/7) **Jenkins** — Declarative pipeline parity with GitHub Actions for policy validation.
- [PR #7](https://github.com/zscaler/zguard-ai-integrations/pull/7)**n8n** — Custom workflow node (TypeScript) and example workflows for automation.