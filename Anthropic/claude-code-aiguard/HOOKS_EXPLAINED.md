# Claude Code Hooks + AI Guard: How It Works

This document explains how Claude Code's hook system integrates with Zscaler AI Guard to provide runtime security scanning for AI interactions.

## Overview

Claude Code has a **hook system** that fires events at specific points in the conversation lifecycle. Our AI Guard integration registers Python scripts to run at these hook points, scanning content through AI Guard's detection policies.

**Key insight:** AI Guard only knows about content policies (toxicity, PII, malware, etc.). It doesn't know if content came from an MCP request, user prompt, or tool response. The hooks are the **orchestration layer** that decides when to call AI Guard, what content to extract, and how to interpret the verdict.

---

## Claude Code Event Types

Claude Code fires these events during a conversation:

| Event | When It Fires | Description |
|-------|---------------|-------------|
| `UserPromptSubmit` | User presses Enter on their prompt | Before Claude sees the user's message |
| `PreToolUse` | Claude is **about to call** a tool | Before any tool execution |
| `PostToolUse` | A tool has **returned** its response | After tool execution completes |

---

## Hook Configuration: `settings.json`

The hooks are configured in `~/.claude/settings.json`:

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/aiguard/scan_user_input.py"
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "WebFetch|WebSearch|web_search",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/aiguard/scan_url.py"
          }
        ]
      },
      {
        "matcher": "mcp__.*__read.*|mcp__.*__resource.*|mcp__.*",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/aiguard/scan_mcp_request.py"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "WebFetch|WebSearch|web_search",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/aiguard/scan_response.py"
          }
        ]
      },
      {
        "matcher": "mcp__.*__read.*|mcp__.*__resource.*|mcp__.*",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/aiguard/scan_response.py"
          }
        ]
      }
    ]
  }
}
```

---

## How Matchers Work

The **matcher** is a regex pattern that matches the **tool name**. When an event fires, Claude Code checks:

1. **Event fires** (e.g., `PreToolUse`)
2. **Tool name** (e.g., `mcp__zscaler-mcp-server__zpa_list_applications`)
3. **Does the tool name match any registered matcher?**

### Matcher Examples

| Tool Name | Matcher | Result |
|-----------|---------|--------|
| `mcp__zscaler-mcp-server__zpa_list_applications` | `mcp__.*` | ✅ Match → run `scan_mcp_request.py` |
| `mcp__github__list_repos` | `mcp__.*` | ✅ Match → run `scan_mcp_request.py` |
| `WebFetch` | `WebFetch\|WebSearch` | ✅ Match → run `scan_url.py` |
| `Read` | `mcp__.*` | ❌ No match → skip hook |
| `Bash` | `mcp__.*` | ❌ No match → skip hook |

### Special Case: `UserPromptSubmit`

The `UserPromptSubmit` event has **no matcher** — it fires for ALL user prompts. Every message the user types goes through `scan_user_input.py`.

---

## The Hook Scripts

### 1. `scan_user_input.py`

**Triggered by:** `UserPromptSubmit` (all user prompts)

**What it does:**
1. Reads JSON from stdin: `{"prompt": "List ZPA applications"}`
2. Extracts the `prompt` field
3. Calls AI Guard with `direction: IN`
4. If AI Guard returns `BLOCK` → exit code 2 (blocks the prompt)
5. If AI Guard returns `ALLOW` → exit code 0 (allows the prompt)

**Content extracted:** `input_json["prompt"]`

### 2. `scan_mcp_request.py`

**Triggered by:** `PreToolUse` when tool name matches `mcp__.*`

**What it does:**
1. Reads JSON from stdin: `{"tool_name": "mcp__zscaler__zpa_create_segment_group", "tool_input": {"name": "test", "description": "..."}}`
2. Extracts content from `tool_input` (looks for fields like `query`, `message`, `content`, etc.)
3. Calls AI Guard with `direction: IN`
4. If AI Guard returns `BLOCK` → exit code 2 (blocks the MCP call)
5. If AI Guard returns `ALLOW` → exit code 0 (allows the MCP call)

**Content extracted:** `input_json["tool_input"]` (the MCP tool parameters)

### 3. `scan_url.py`

**Triggered by:** `PreToolUse` when tool name matches `WebFetch|WebSearch|web_search`

**What it does:**
1. Reads JSON from stdin with the URL to be fetched
2. Extracts the URL
3. Calls AI Guard with `direction: IN`
4. Blocks malicious or policy-violating URLs

**Content extracted:** URL from tool input

### 4. `scan_response.py`

**Triggered by:** `PostToolUse` when tool name matches configured patterns

**What it does:**
1. Reads JSON from stdin: `{"tool_name": "...", "tool_response": {...}}`
2. Extracts content from `tool_response`
3. Calls AI Guard with `direction: OUT`
4. If AI Guard returns `BLOCK` → outputs block response JSON
5. If AI Guard returns `ALLOW` → exit code 0

**Content extracted:** `input_json["tool_response"]` (the data returned by the tool)

---

## Direction: IN vs OUT

AI Guard policies can be configured differently for inbound vs outbound traffic:

| Direction | Meaning | Used By |
|-----------|---------|---------|
| `IN` | Data coming **into** the system | User prompts, MCP tool parameters |
| `OUT` | Data going **out** of the system | Tool responses, data returned to user |

This allows you to have different policies for:
- **Inbound:** Block prompt injection, malicious commands, toxic user input
- **Outbound:** Block PII leakage, sensitive data exposure, malicious content in responses

---

## Complete Flow: Example

When a user asks "List ZPA applications", here's what happens:

```mermaid
flowchart TD
    subgraph User Input
        A[User: "List ZPA applications"] --> B{EVENT: UserPromptSubmit}
    end

    subgraph Hook: scan_user_input.py
        B --> C[Extract: prompt]
        C --> D[AI Guard Scan<br/>direction: IN]
        D --> E{Verdict?}
        E -->|BLOCK| F[Exit 2<br/>Prompt Blocked]
        E -->|ALLOW| G[Exit 0<br/>Continue]
    end

    subgraph Claude Processing
        G --> H[Claude thinks...]
        H --> I[Decides to call:<br/>mcp__zscaler__zpa_list_applications]
    end

    subgraph Hook: scan_mcp_request.py
        I --> J{EVENT: PreToolUse}
        J --> K[Matcher: mcp__.* ✓]
        K --> L[Extract: tool_input]
        L --> M[AI Guard Scan<br/>direction: IN]
        M --> N{Verdict?}
        N -->|BLOCK| O[Exit 2<br/>MCP Call Blocked]
        N -->|ALLOW| P[Exit 0<br/>Continue]
    end

    subgraph MCP Execution
        P --> Q[MCP Server Executes Tool]
        Q --> R[Returns: list of applications]
    end

    subgraph Hook: scan_response.py
        R --> S{EVENT: PostToolUse}
        S --> T[Matcher: mcp__.* ✓]
        T --> U[Extract: tool_response]
        U --> V[AI Guard Scan<br/>direction: OUT]
        V --> W{Verdict?}
        W -->|BLOCK| X[Response Blocked<br/>Data not shown]
        W -->|ALLOW| Y[Exit 0<br/>Continue]
    end

    subgraph Result
        Y --> Z[Claude shows result to user]
    end

    style F fill:#ff6b6b,color:#fff
    style O fill:#ff6b6b,color:#fff
    style X fill:#ff6b6b,color:#fff
    style Z fill:#51cf66,color:#fff
```

---

## Why Separate Hooks?

Even though AI Guard runs the same policy engine, having separate hooks provides:

### 1. **Different Content Extraction**
Each hook knows how to extract the relevant content:
- User prompts are in `prompt`
- MCP params are in `tool_input`
- Responses are in `tool_response`

### 2. **Different Directions**
- `IN` for incoming data (user prompts, MCP params)
- `OUT` for outgoing data (tool responses)

### 3. **Selective Scanning via Matchers**
- Only scan MCP tools, not local file reads
- Only scan web responses, not internal tools
- Skip scanning for tools that don't need it

### 4. **Better Logging and Debugging**
Each hook logs its specific context:
```
[2026-01-30 15:22:01] Scanning user input: List ZPA applications...
[2026-01-30 15:22:02] ALLOWED USER INPUT (txn:abc123...)
[2026-01-30 15:22:03] Scanning mcp__zscaler__zpa_list_applications request...
[2026-01-30 15:22:04] ALLOWED MCP REQUEST zpa_list_applications (txn:def456...)
[2026-01-30 15:22:05] Scanning mcp__zscaler__zpa_list_applications response...
[2026-01-30 15:22:06] ALLOWED mcp__zscaler__zpa_list_applications response (txn:ghi789...)
```

---

## AI Guard's Role

**AI Guard only knows about content policies.** It doesn't know:
- If the content came from an MCP request
- If it's a user prompt or tool response
- What tool is being called

AI Guard receives:
1. **Content** (text to scan)
2. **Direction** (`IN` or `OUT`)
3. **Policy ID** (optional, for specific policy)

AI Guard returns:
1. **Action** (`ALLOW`, `BLOCK`, or `DETECT`)
2. **Severity** (if triggered)
3. **Triggered detectors** (toxicity, PII, malware, etc.)
4. **Transaction ID** (for audit trail)

The **hooks interpret this verdict** and take action (block or allow).

---

## Summary Table

| Component | Role |
|-----------|------|
| **Claude Code** | Fires events (`UserPromptSubmit`, `PreToolUse`, `PostToolUse`) |
| **settings.json** | Maps events + matchers → hook scripts |
| **Matchers** | Regex patterns that determine which tools trigger which hooks |
| **Hook scripts** | Extract content, call AI Guard, interpret verdict, block/allow |
| **AI Guard** | Scans content against policies — doesn't know the source |

---

## Files Reference

| File | Purpose |
|------|---------|
| `~/.claude/settings.json` | Hook configuration (events, matchers, commands) |
| `~/.claude/hooks/aiguard/scan_user_input.py` | Scans user prompts |
| `~/.claude/hooks/aiguard/scan_mcp_request.py` | Scans MCP tool parameters |
| `~/.claude/hooks/aiguard/scan_url.py` | Scans URLs before web requests |
| `~/.claude/hooks/aiguard/scan_response.py` | Scans tool responses |
| `~/.claude/hooks/aiguard/.env` | AI Guard credentials and config |
| `~/.claude/hooks/aiguard/security.log` | Security event log |
