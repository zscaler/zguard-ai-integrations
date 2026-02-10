# Zscaler AI Guard Integrations

Enterprise-grade AI security integrations for various AI platforms using Zscaler AI Guard.

## Overview

This repository contains integrations that enable runtime AI security by routing AI traffic through Zscaler AI Guard for inspection. AI Guard provides comprehensive protection against:

- **Prompt Injection** - Malicious attempts to manipulate AI behavior
- **Data Loss Prevention (DLP)** - Sensitive data exposure (PII, secrets, credentials)
- **Toxicity** - Harmful or inappropriate content
- **Malicious URLs** - Links to phishing, malware, or blocked domains
- **Code Injection** - Unwanted or malicious code patterns

## Available Integrations

| Platform | Description | Status |
|----------|-------------|--------|
| [Claude Code](./claude-code-aiguard/) | Security hooks for Claude Code CLI | ✅ Available |
| Cursor IDE | Security hooks for Cursor | 🚧 Planned |
| LiteLLM | LLM gateway integration | 🚧 Planned |

## Quick Start

### Claude Code

```bash
# 1. Install SDK
pip install git+https://github.com/zscaler/zscaler-sdk-python.git

# 2. Copy hooks
mkdir -p ~/.claude/hooks/aiguard
cp Anthropic/claude-code-aiguard/hooks/*.py ~/.claude/hooks/aiguard/

# 3. Configure environment (choose one option)

# Option A: Using .env file (recommended)
cp Anthropic/claude-code-aiguard/.env.example ~/.claude/hooks/aiguard/.env
# Edit ~/.claude/hooks/aiguard/.env with your credentials

# Option B: Using shell environment variables
export AIGUARD_API_KEY="your-api-key"
export AIGUARD_CLOUD="us1"
export AIGUARD_POLICY_ID="760"

# 4. Configure Claude Code
cp Anthropic/claude-code-aiguard/settings.json ~/.claude/settings.json
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    AI Guard Integration Flow                     │
│                                                                  │
│   AI Application          Hook/Integration         AI Guard     │
│   (Claude Code)                                    API          │
│        │                        │                    │          │
│        │ ── User Prompt ──────► │                    │          │
│        │                        │ ── Scan (IN) ────► │          │
│        │                        │ ◄── ALLOW/BLOCK ── │          │
│        │ ◄── Allow/Block ────── │                    │          │
│        │                        │                    │          │
│        │ ── Tool Response ────► │                    │          │
│        │                        │ ── Scan (OUT) ───► │          │
│        │                        │ ◄── ALLOW/BLOCK ── │          │
│        │ ◄── Allow/Block ────── │                    │          │
└─────────────────────────────────────────────────────────────────┘
```

## License

Part of the Zscaler MCP Server repository.
