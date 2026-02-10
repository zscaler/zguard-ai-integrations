# notification_helper.py

## Status: Not Integrated

This script is **available but not currently integrated** into the hooks.

It was created as a potential solution for the "silent block" issue in Cursor UI, but has been kept as a standalone script for future reference.

## What It Does

Sends OS-level desktop notifications when AI Guard blocks a request.

**Supported platforms:**
- macOS (via osascript)
- Linux (via notify-send)
- Windows (via PowerShell)

## Example Usage

If you wanted to integrate it manually, you could:

```python
# In your hook
from notification_helper import notify_block

if should_block:
    # ... existing logging and blocking code ...
    
    # Optional: Send notification
    notify_block(
        severity="CRITICAL",
        detectors=["credentials", "pii"],
        transaction_id="abc123..."
    )
```

## Testing

Test if notifications work on your system:

```bash
cd ~/.claude/hooks/aiguard
python3 notification_helper.py test
```

Or test manually:

```bash
# macOS
osascript -e 'display notification "Test" with title "Test"'

# Linux
notify-send "Test" "Test message"
```

## Why It's Not Integrated

- Desktop notifications can be intrusive
- Not all users want them
- Adds OS-specific dependencies
- The CLI already shows error messages
- Logs provide full details

The script remains available if anyone wants to integrate it themselves in the future.
