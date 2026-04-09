# Zscaler AI Guard Integrations Changelog

## 0.1.2 (April 9, 2026)

### Notes

- Python Versions: **v3.11, v3.12, v3.13**

### Features

- [PR #8](https://github.com/zscaler/zguard-ai-integrations/pull/8) - Added Anthropic Claude Code Skill integration with on-demand `/aiguard` scanning via `scan.py`
- [PR #8](https://github.com/zscaler/zguard-ai-integrations/pull/8) - Added complete AI Guard detector reference (`threat-categories.md`) covering 19 prompt and 21 response detectors

### Enhancements

- [PR #8](https://github.com/zscaler/zguard-ai-integrations/pull/8) - Enhanced SKILL.md auto-invoke triggers for brand safety, competitor mentions, intellectual property, invisible text, and language/topic policies
- [PR #8](https://github.com/zscaler/zguard-ai-integrations/pull/8) - Updated `CLAUDE.md` with Claude Code skill entry, integration patterns, per-integration details, and key files reference
- [PR #8](https://github.com/zscaler/zguard-ai-integrations/pull/8) - Fixed Malicious URL detector categorization from Content Moderation to Security in SKILL.md

### Bug Fixes

- [PR #8](https://github.com/zscaler/zguard-ai-integrations/pull/8) - Fixed `CLAUDE.md` directory reference from `Azure/` to `Microsoft/`
- [PR #8](https://github.com/zscaler/zguard-ai-integrations/pull/8) - Removed stale "Planned" entries for Cursor and LiteLLM from `Anthropic/README.md`

## 0.1.1 (March 31, 2026)

### Notes

- Python Versions: **v3.11, v3.12, v3.13**

### Enhancements

- [PR #8](https://github.com/zscaler/zguard-ai-integrations/pull/8) - Added LiteLLM output scanning (`async_post_call_success_hook`) to SDK-based custom callback
- [PR #8](https://github.com/zscaler/zguard-ai-integrations/pull/8) - Added LiteLLM native guardrail configuration example (`config-native-guardrail.yaml`)
- [PR #8](https://github.com/zscaler/zguard-ai-integrations/pull/8) - Updated root `README.md` with official docs links for LiteLLM and Portkey native integrations

### Bug Fixes

- [PR #8](https://github.com/zscaler/zguard-ai-integrations/pull/8) - Updated LiteLLM `README.md` with callout to official Zscaler AI Guard plugin page
- [PR #8](https://github.com/zscaler/zguard-ai-integrations/pull/8) - Updated Portkey `README.md` with callout to official Zscaler AI Guard integration page
- [PR #8](https://github.com/zscaler/zguard-ai-integrations/pull/8) - Updated Portkey `examples/README.md` directing users to native plugin as recommended approach

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