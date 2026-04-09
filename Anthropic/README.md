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

| Integration | Type | Description | Status |
|-------------|------|-------------|--------|
| [Claude Code Hooks](./claude-code-aiguard/) | Hooks | Automatic pre/post scanning via Claude Code hooks system | ✅ Available |
| [Claude Code Skill](./claude-code-skill/) | Skill | On-demand scanning via `/aiguard` slash command | ✅ Available |

### Integration Comparison

| Feature | Hooks | Skill |
|---------|:-----:|:-----:|
| Automatic scanning | ✅ | Semi (auto-invoke rules) |
| On-demand scanning | ❌ | ✅ (`/aiguard`) |
| Pre/Post tool scanning | ✅ | ❌ |
| Requires separate process | ❌ | ❌ |
| Uses zscaler-sdk-python | ✅ | ✅ |

## Quick Start

### Option 1: Claude Code Hooks (Automatic Scanning)

```bash
# 1. Install SDK
pip install zscaler-sdk-python

# 2. Copy hooks
mkdir -p ~/.claude/hooks/aiguard
cp claude-code-aiguard/hooks/*.py ~/.claude/hooks/aiguard/

# 3. Configure environment
export AIGUARD_API_KEY="your-api-key"
export AIGUARD_CLOUD="us1"

# 4. Configure Claude Code
cp claude-code-aiguard/settings.json ~/.claude/settings.json
```

### Option 2: Claude Code Skill (On-Demand Scanning)

```bash
# 1. Install SDK
pip install zscaler-sdk-python

# 2. Copy skill
mkdir -p ~/.claude/skills
cp -r claude-code-skill ~/.claude/skills/aiguard

# 3. Configure environment
export AIGUARD_API_KEY="your-api-key"
export AIGUARD_CLOUD="us1"

# 4. Use in Claude Code via /aiguard or by asking Claude to scan content
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
