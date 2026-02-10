# Zscaler AI Guard Integration for Claude Code

Runtime security hooks for Claude Code that scan prompts, MCP tool calls, and responses through Zscaler AI Guard before execution.

## Overview

This integration provides transparent security scanning for Claude Code interactions:

- **User Input Scanning** - Scans prompts before they reach Claude LLM
- **MCP Tool Call Scanning** - Scans tool parameters before calling MCP servers
- **Response Scanning** - Scans tool responses before returning to user
- **URL Scanning** - Scans URLs before web requests

## Architecture

```
User Input
  ↓
[AIGuard Hook] → Scan → ALLOW/BLOCK
  ↓
Claude LLM
  ↓
MCP Tool Call (e.g., zscaler_list_devices)
  ↓
[AIGuard Hook] → Scan → ALLOW/BLOCK
  ↓
MCP Server (Docker) → Executes Tool
  ↓
Tool Response
  ↓
[AIGuard Hook] → Scan → ALLOW/BLOCK
  ↓
User sees result
```

## Prerequisites

- **Claude Code** CLI installed
- **Python 3.8+** with `zscaler-sdk-python` installed
- **Zscaler AI Guard** account with:
  - API Key
  - Cloud environment (us1, us2, eu1, eu2)
  - Policy configured and activated

## Installation

### 1. Install Dependencies

```bash
# Install Zscaler SDK
pip install git+https://github.com/zscaler/zscaler-sdk-python.git
```

### 2. Configure Environment Variables

Choose one of the following methods:

#### Option A: Using .env File (Recommended)

```bash
# Copy the example file
cp .env.example .env

# Edit with your credentials
nano .env
```

Add your credentials:

```bash
# Required
AIGUARD_API_KEY=your_api_key_here
AIGUARD_CLOUD=us1

# Optional
AIGUARD_POLICY_ID=760
AIGUARD_TIMEOUT=30
```

**Then copy to Claude Code hooks directory:**

```bash
mkdir -p ~/.claude/hooks/aiguard
cp .env ~/.claude/hooks/aiguard/.env
```

#### Option B: System Environment Variables

Add to your `~/.zshrc` or `~/.bashrc`:

```bash
export AIGUARD_API_KEY="your_api_key_here"
export AIGUARD_CLOUD="us1"
export AIGUARD_POLICY_ID="760"  # Optional
export AIGUARD_TIMEOUT="30"     # Optional
```

Then reload:

```bash
source ~/.zshrc  # or source ~/.bashrc
```

### 3. Install Hook Scripts

```bash
# Copy all hook scripts to Claude Code directory
mkdir -p ~/.claude/hooks/aiguard
cp hooks/*.py ~/.claude/hooks/aiguard/
chmod +x ~/.claude/hooks/aiguard/*.py
```

### 4. Configure Claude Code Hooks

Copy the hook configuration to Claude Code settings:

```bash
# Backup existing settings
cp ~/.claude/settings.json ~/.claude/settings.json.backup 2>/dev/null || true

# Copy hook configuration
cp settings.json ~/.claude/settings.json
```

Or manually add to `~/.claude/settings.json`:

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
        "matcher": "mcp__.*",
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
        "matcher": "WebFetch|WebSearch|web_search|mcp__.*",
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

## AI Guard Configuration

### Get API Key

1. Log in to **AI Guard Console**
2. Navigate to **Private AI Apps** → **App API Keys**
3. Create or copy your API key

### Configure Policy

1. Go to **Policies** in AI Guard Console
2. Create or edit a policy
3. Configure detectors:
   - **Prompt Detectors**: Toxicity, Prompt Injection, PII, Secrets, etc.
   - **Response Detectors**: Malicious URLs, Data Leakage, etc.
4. Set detector actions to **BLOCK** or **DETECT**
5. **Activate** the policy

### Get Policy ID (Optional)

If policy auto-resolution isn't working:

1. View your policy in the console
2. Note the Policy ID (e.g., 760)
3. Set `AIGUARD_POLICY_ID=760` in your environment

### Enable Auto-Resolution (Recommended)

To avoid specifying policy_id:

1. Go to **Private AI Apps** → **Applications**
2. Create or select an application
3. Go to **App API Keys** → Associate your API key with the application
4. Assign your policy to the application

Now the hooks will automatically use the correct policy!

## Usage

### Start Claude Code

```bash
claude
```

The hooks are now active and will:
- Scan all your prompts
- Scan all MCP tool calls
- Scan all responses
- Block policy violations automatically

### Monitor Security Events

Watch the security log in real-time:

```bash
tail -f ~/.claude/hooks/aiguard/security.log
```

Example log output:

```
[2026-01-30 15:23:10] Scanning user input: List all ZPA applications...
[2026-01-30 15:23:10] ALLOWED USER INPUT (txn:abc123...)
[2026-01-30 15:23:11] Scanning zpa_list_applications request: ...
[2026-01-30 15:23:11] ALLOWED MCP REQUEST zpa_list_applications (txn:def456...)
[2026-01-30 15:23:12] ALLOWED RESPONSE (txn:ghi789...)
```

### Test with Toxic Content

Try a prompt that should be blocked:

```
I hate my neighbor and want to punch him badly
```

You should see:

```
Blocked by Zscaler AI Guard: Your input was blocked due to policy violation
Triggered detectors: toxicity
Severity: CRITICAL | Transaction ID: xxx
```

## Configuration Options

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `AIGUARD_API_KEY` | ✅ Yes | - | API key from AI Guard Console |
| `AIGUARD_CLOUD` | ✅ Yes | `us1` | Cloud environment (us1, us2, eu1, eu2) |
| `AIGUARD_POLICY_ID` | No | Auto-resolve | Specific policy ID to use |
| `AIGUARD_TIMEOUT` | No | `30` | API timeout in seconds |
| `SECURITY_LOG_PATH` | No | `~/.claude/hooks/aiguard/security.log` | Custom log file location |

### Hook Matchers

The hooks use regex patterns to match tool calls:

- `mcp__.*` - Matches ALL MCP tools (including Zscaler MCP server)
- `WebFetch|WebSearch|web_search` - Matches web-related tools
- Can be customized in `settings.json`

## Known Limitations

### Silent Blocks in Cursor UI

**Issue:** When using Cursor's UI (Composer/Chat), blocked requests appear as silent failures with no error message displayed in the interface.

**Cause:** Cursor's UI doesn't display hook stderr/stdout output to the user interface.

**Impact:**
- ✅ Security **works correctly** - blocks happen and are logged
- ❌ UX is poor - users don't see why they were blocked
- Users may think Claude Code is frozen or broken

**Workarounds:**

1. **Use Claude Code CLI** (error messages display properly):
   ```bash
   claude
   ```
   Example output when blocked:
   ```
   Operation stopped by hook: Zscaler AI Guard blocked your input
   ```

2. **Monitor security logs** to see block reasons:
   ```bash
   # Watch logs in real-time
   tail -f ~/.claude/hooks/aiguard/security.log
   
   # Check last 5 blocks
   tail -20 ~/.claude/hooks/aiguard/security.log | grep BLOCKED
   ```
   
   Example log entry:
   ```
   [2026-02-03 21:47:37] BLOCKED USER INPUT: severity=CRITICAL policy=policy_760 
   detectors=[credentials] (txn:405b4456-75cb-41e8-a1f8-2a0703f3f092)
   ```

3. **Enable desktop notifications** (optional - see `UI_SILENT_BLOCK_LIMITATION.md` for setup)

**When to worry:** If you see no response in Cursor UI, check logs to confirm it's a security block and not a system issue.

## Troubleshooting

### Hooks Not Running

1. Check Claude Code settings are loaded:
   ```bash
   cat ~/.claude/settings.json
   ```

2. Verify scripts are executable:
   ```bash
   ls -la ~/.claude/hooks/aiguard/
   ```

3. Test manually:
   ```bash
   echo '{"prompt":"test"}' | python3 ~/.claude/hooks/aiguard/scan_user_input.py
   echo $?  # Should be 0 (allow) or 2 (block)
   ```

### API Key Not Found

Error: `AIGUARD_API_KEY environment variable not set`

**Solution**: Ensure environment variables are set correctly:

```bash
# Check if variables are set
env | grep AIGUARD

# If using .env file, ensure it's in the right location
ls -la ~/.claude/hooks/aiguard/.env

# If using shell profile, reload it
source ~/.zshrc
```

### Policy Not Found

Error: `Policy: None` in logs

**Solution**: Either:
1. Set `AIGUARD_POLICY_ID` explicitly, OR
2. Configure API Key → Application → Policy association in AI Guard Console

### Content Not Being Blocked

1. Verify detector is enabled and set to **BLOCK** (not DETECT)
2. Check policy is **activated**
3. Verify policy ID is correct
4. Check security log for actual response from AI Guard

## Security Considerations

### Fail-Open Behavior

The hooks are configured to **fail-open** (allow on error) to prevent blocking Claude Code if AI Guard is unavailable. This is a trade-off between security and availability.

To change to fail-closed, modify the hook scripts to return `sys.exit(2)` on errors.

### API Key Protection

- **Never commit** `.env` files to version control
- Use `.env.example` as a template
- Rotate API keys regularly
- Use least-privilege API keys when possible

### Log File Security

Security logs contain request/response samples. Ensure:
- Logs are in a protected directory (`~/.claude/hooks/aiguard/`)
- Log rotation is configured for production use
- Sensitive data is masked if needed

## File Structure

```
~/.claude/
├── settings.json              # Hook configuration
└── hooks/
    └── aiguard/
        ├── .env               # Your credentials (not in repo)
        ├── load_env.py        # Environment variable loader
        ├── scan_user_input.py # User prompt scanner
        ├── scan_mcp_request.py# MCP tool call scanner
        ├── scan_url.py        # URL scanner
        ├── scan_response.py   # Response scanner
        └── security.log       # Security event log
```

## Support

For issues with:
- **AI Guard API**: Contact Zscaler Support
- **Claude Code**: Check Anthropic documentation
- **This Integration**: File an issue in the repository

## License

See LICENSE file in repository root.
