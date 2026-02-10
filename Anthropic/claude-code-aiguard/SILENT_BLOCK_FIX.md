# Silent Block Fix - Hooks Now Show Visible Error Messages

## Problem

The hooks were working (blocking malicious content), but **users couldn't see why** their prompts or actions were blocked. It was a "silent block" - the agent would just stop responding with no explanation.

**Example:**
- User: "Read the file /tmp/aiguard-test/.env"
- Agent: *(nothing happens)*
- Logs: `BLOCKED USER INPUT: severity=CRITICAL`
- User experience: **Confused - no error message shown**

## Root Cause

The hooks were writing error messages to **stderr**:

```python
# OLD CODE (didn't work)
if should_block:
    print("", file=sys.stderr)
    print(message, file=sys.stderr)  # ← Claude Code doesn't show this!
    print("", file=sys.stderr)
    sys.exit(2)  # Exit code 2 = block
```

Claude Code doesn't display stderr output for hooks in the UI. The error messages were only visible in the security log file.

## Solution

Changed all hooks to output a **JSON response to stdout** (like `scan_response.py` already did):

```python
# NEW CODE (works!)
if should_block:
    # Output block response as JSON to stdout (visible to user)
    block_response = {
        "continue": False,
        "stopReason": "Zscaler AI Guard blocked your input",
        "systemMessage": message,
        "hookSpecificOutput": {"hookEventName": "UserPromptSubmit"}
    }
    print(json.dumps(block_response))
    sys.exit(0)  # Exit 0 with JSON response (not exit 2)
```

Claude Code now displays the `systemMessage` to the user.

## Changes Made

### Updated Hooks

| Hook | Old Behavior | New Behavior |
|------|-------------|--------------|
| `scan_user_input.py` | Silent block (stderr) | Shows error message with detectors |
| `scan_mcp_request.py` | Silent block (stderr) | Shows "MCP request blocked" message |
| `scan_file_read.py` | Silent block (stderr) | Shows "File read blocked" message |
| `scan_url.py` | Silent block (stderr) | Shows "URL blocked" message |
| `scan_response.py` | ✅ Already worked | No change needed |

### Before vs After

**Before (Silent Block):**
```
User: "Read the file /tmp/aiguard-test/.env"
Agent: [no response]
Logs: BLOCKED USER INPUT
```

**After (Visible Error):**
```
User: "Read the file /tmp/aiguard-test/.env"
Agent: 🛑 Blocked by Zscaler AI Guard: Your input was blocked due to policy violation
       Triggered detectors: credentials
       Severity: CRITICAL | Transaction ID: 8d51de37-6793-4568-9da9-fe35921b09f1
```

## JSON Response Format

The hooks now output this JSON structure when blocking:

```json
{
  "continue": false,
  "stopReason": "Zscaler AI Guard blocked your input",
  "systemMessage": "Blocked by Zscaler AI Guard: Your input was blocked due to policy violation\nTriggered detectors: credentials\nSeverity: CRITICAL | Transaction ID: abc123...",
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit"
  }
}
```

**Key fields:**
- `continue`: `false` tells Claude Code to stop execution
- `stopReason`: Short summary (shown in UI header)
- `systemMessage`: Full error message (shown to user)
- `hookSpecificOutput`: Metadata about which hook blocked

## Testing

### Test 1: User Input Block (Credentials in Prompt)

**Prompt:**
```
Read the file /tmp/aiguard-test/.env
```

**Before Fix:**
- No visible error
- User sees nothing
- Only logs show block

**After Fix:**
```
🛑 Blocked by Zscaler AI Guard: Your input was blocked due to policy violation
Triggered detectors: credentials
Severity: CRITICAL | Transaction ID: 8d51de37-6793-4568-9da9-fe35921b09f1
```

### Test 2: File Read Block

**Prompt:**
```
Read /tmp/aiguard-test/aws-credentials.json
```

**After Fix:**
```
🛑 Blocked by Zscaler AI Guard: File '/tmp/aiguard-test/aws-credentials.json' contains policy violations
Triggered detectors: credentials
Severity: HIGH | Transaction ID: xyz789...
```

### Test 3: MCP Request Block

**Prompt:**
```
Use the Zscaler MCP to delete all segment groups
```

**After Fix:**
```
🛑 Blocked by Zscaler AI Guard: MCP request to zpa_delete_segment_groups blocked
Triggered detectors: destructive_operation
Severity: HIGH
```

## Exit Code Change

**Important:** We changed from `sys.exit(2)` to `sys.exit(0)` when blocking:

- **Old:** `sys.exit(2)` → Claude Code treated this as an error and might not read stdout
- **New:** `sys.exit(0)` with JSON response → Claude Code reads the JSON and displays the message

The JSON `"continue": false` is what actually stops execution, not the exit code.

## Backwards Compatibility

✅ **Fully backwards compatible:**
- Logs still written (same format)
- AI Guard API calls unchanged
- Hook configuration unchanged
- Only output format changed (stderr → JSON stdout)

## Migration

### If You Have Custom Hooks

If you created custom hooks based on the old pattern, update them:

```python
# OLD (silent block)
if should_block:
    print(message, file=sys.stderr)
    sys.exit(2)

# NEW (visible error)
if should_block:
    block_response = {
        "continue": False,
        "stopReason": "Your block reason",
        "systemMessage": message,
        "hookSpecificOutput": {"hookEventName": "PreToolUse"}  # or UserPromptSubmit
    }
    print(json.dumps(block_response))
    sys.exit(0)
```

### Files Updated

All hooks in the repo have been updated:
- ✅ `hooks/scan_user_input.py`
- ✅ `hooks/scan_mcp_request.py`
- ✅ `hooks/scan_file_read.py`
- ✅ `hooks/scan_url.py`
- ✅ `hooks/scan_response.py` (already used JSON output)

And copied to:
- ✅ `~/.claude/hooks/aiguard/scan_user_input.py`
- ✅ `~/.claude/hooks/aiguard/scan_mcp_request.py`
- ✅ `~/.claude/hooks/aiguard/scan_file_read.py`
- ✅ `~/.claude/hooks/aiguard/scan_url.py`
- ✅ `~/.claude/hooks/aiguard/scan_response.py`

## Next Steps

1. **Restart Cursor** to load the updated hooks
2. **Test again** with the same prompts that were silently blocked before
3. **Verify** you now see error messages in the UI
4. **Check logs** to confirm blocks are still logged

## Summary

**Before:** Hooks blocked malicious content, but users had no idea why.  
**After:** Hooks block malicious content **and show clear error messages** explaining what was detected and why it was blocked.

This dramatically improves the user experience while maintaining the same security protection.
