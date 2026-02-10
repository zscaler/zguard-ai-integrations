# UI Silent Block Limitation

## Issue Summary

The AI Guard security hooks work correctly and block malicious content, but **error messages are only visible in Claude Code CLI, not in the Cursor UI** (Composer/Chat).

## Observed Behavior

| Interface | Hook Execution | Error Message Displayed | User Experience |
|-----------|---------------|------------------------|-----------------|
| **Claude Code CLI** | ✅ Works | ✅ Shows message | ✅ Good - user sees why blocked |
| **Cursor UI (Composer)** | ✅ Works | ❌ Silent | ❌ Poor - user confused |
| **Security Logs** | ✅ Always logged | ✅ Full details | ⚠️ Requires checking logs |

### Example

**User action:** "Read /tmp/aiguard-test/.env"

**CLI output:**
```
Operation stopped by hook: Zscaler AI Guard blocked your input
```

**UI output:**
```
(nothing - silent block, agent stops responding)
```

**Security log:**
```
[2026-02-03 21:47:37] BLOCKED USER INPUT: severity=CRITICAL policy=policy_760 (txn:405b4456...)
```

## Root Cause

**Cursor's UI doesn't forward hook stderr/stdout to the user interface.**

The hooks output error messages via:
1. `stderr` - CLI displays this, UI ignores it
2. JSON to `stdout` - CLI shows "Operation stopped by hook", UI ignores the message content

This is a **limitation of how Cursor implements hook integration**, not an issue with our hooks.

## Impact

- ✅ **Security still works** - blocks happen correctly
- ❌ **UX is poor** - users don't know why they're blocked
- ⚠️ **Trust issues** - users may think the system is broken when it's actually protecting them

## Workarounds

### Workaround 1: Check Security Logs (Current)

Users can monitor the log file:

```bash
# Watch logs in real-time
tail -f ~/.claude/hooks/aiguard/security.log

# Check last 20 entries
tail -20 ~/.claude/hooks/aiguard/security.log | grep BLOCKED
```

**Pros:**
- Works now
- Full details available

**Cons:**
- Requires terminal knowledge
- Not user-friendly
- Requires separate window

### Workaround 2: Use Claude Code CLI (Current)

Run Claude Code from terminal instead of Cursor UI:

```bash
claude
```

**Pros:**
- Error messages show properly
- Same AI Guard protection
- All hooks work with visible feedback

**Cons:**
- Different workflow than Cursor UI
- No visual IDE integration
- Users must use terminal

### Workaround 3: Desktop Notifications (Proposed)

Add OS-level notifications when blocks occur.

**Implementation:**

```python
# Add to hooks after blocking
def send_notification(title: str, message: str):
    """Send desktop notification (macOS example)"""
    import subprocess
    import platform
    
    if platform.system() == "Darwin":  # macOS
        subprocess.run([
            "osascript", "-e",
            f'display notification "{message}" with title "{title}"'
        ])
    elif platform.system() == "Linux":
        subprocess.run(["notify-send", title, message])
    # Windows: use win10toast or similar

# In scan_user_input.py
if should_block:
    send_notification(
        "🛑 Zscaler AI Guard",
        f"Blocked: {severity} violation detected"
    )
```

**Pros:**
- Works in both UI and CLI
- Clear visual feedback
- Non-intrusive

**Cons:**
- Requires OS permissions
- Notifications might be missed
- Extra dependency

### Workaround 4: Write Block Reason to File (Proposed)

Create a temporary file with block reason that Cursor might display:

```python
# In hooks
if should_block:
    block_file = Path.home() / ".claude" / "last_block.txt"
    with open(block_file, "w") as f:
        f.write(f"🛑 BLOCKED BY ZSCALER AI GUARD\n\n{message}")
```

Users could then read the file if confused:

```
cat ~/.claude/last_block.txt
```

**Pros:**
- Simple to implement
- Persistent reason
- No OS dependencies

**Cons:**
- Still requires user action
- File might be stale
- Not real-time

### Workaround 5: Custom Cursor Extension (Future)

Create a Cursor extension that:
1. Monitors the security log
2. Shows notifications in Cursor UI
3. Displays block reasons in a panel

**Pros:**
- Best UX - integrated into Cursor
- Real-time feedback in UI
- Can show history

**Cons:**
- Requires Cursor extension development
- More complex to maintain
- Cursor extension API may be limited

## Recommended Approach

**Short-term (Current):**
1. ✅ Document the limitation clearly in README
2. ✅ Provide instructions for checking logs
3. ✅ Recommend CLI for users who want visible feedback

**Medium-term (1-2 weeks):**
4. ⚠️ Add desktop notifications as opt-in feature
5. ⚠️ Create a helper script that tails logs and shows notifications

**Long-term (Future):**
6. 🔮 Investigate Cursor extension for better UI integration
7. 🔮 Contact Cursor team about hook output visibility

## Documentation Updates

### README.md - Add "Known Limitations" Section

```markdown
## Known Limitations

### UI Silent Blocks

**Issue:** When using Cursor's UI (Composer/Chat), blocked requests appear as silent failures with no error message.

**Cause:** Cursor's UI doesn't display hook stderr/stdout output.

**Workaround:** 
- **Option 1:** Use Claude Code CLI (`claude` command) - error messages display properly
- **Option 2:** Monitor logs: `tail -f ~/.claude/hooks/aiguard/security.log`
- **Option 3:** Check last block: `tail -5 ~/.claude/hooks/aiguard/security.log | grep BLOCKED`

**When this matters:** You'll see blocks in logs but no UI feedback. Your security is still protected.
```

### User Communication Template

When a user reports "Claude stopped responding":

```
Your request was blocked by Zscaler AI Guard for security reasons.

Due to a Cursor UI limitation, the error message isn't displayed in the interface.

To see why it was blocked:
1. Check logs: `tail -5 ~/.claude/hooks/aiguard/security.log | grep BLOCKED`
2. Or use CLI: `claude` (shows error messages)

Example log entry:
[2026-02-03 21:47:37] BLOCKED USER INPUT: severity=CRITICAL policy=policy_760 detectors=[credentials]

This means AI Guard detected credentials in your prompt and blocked it to protect sensitive data.
```

## Testing Matrix

| Test Case | CLI Expected | UI Expected | Actual CLI | Actual UI |
|-----------|-------------|-------------|-----------|----------|
| Block user input | Show error | Show error | ✅ Shows | ❌ Silent |
| Block file read | Show error | Show error | ✅ Shows | ❌ Silent |
| Block MCP call | Show error | Show error | ✅ Shows | ❌ Silent |
| Block URL | Show error | Show error | ✅ Shows | ❌ Silent |
| Block response | Show error | Show error | ✅ Shows | ❌ Silent |
| Allow operation | Continue | Continue | ✅ Works | ✅ Works |

## Related Issues

- Hooks execute correctly (confirmed in logs)
- JSON output format is correct (works in CLI)
- stderr output is correct (works in CLI)
- Issue is specific to Cursor UI rendering of hook output

## Future Improvement: Hook Status Indicator

Ideal solution would be a Cursor UI status indicator:

```
┌─────────────────────────────────────┐
│ 🛡️ AI Guard Active                  │
│                                     │
│ Last scan: 2 seconds ago            │
│ Status: ✅ ALLOWED                  │
│                                     │
│ Session stats:                      │
│ - Scans: 15                         │
│ - Blocks: 2                         │
│ - Last block: credentials detected  │
└─────────────────────────────────────┘
```

This would require a Cursor extension or plugin.

## Conclusion

The security functionality **works correctly** - blocks happen and are logged. The limitation is purely **cosmetic/UX** - users in the Cursor UI don't see why they were blocked.

For now, users should:
1. **Use CLI if they want visible feedback**
2. **Check logs if confused about silent blocks**
3. **Know that silence = security working** (though not ideal UX)
