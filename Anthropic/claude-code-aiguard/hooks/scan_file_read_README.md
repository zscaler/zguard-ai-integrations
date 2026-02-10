# scan_file_read.py - File Read Security Scanner

## Overview

`scan_file_read.py` is a Claude Code security hook that scans file contents **before** Claude reads them, preventing exposure of sensitive data like credentials, API keys, and private keys.

## What It Does

1. **Intercepts file read operations** - Triggers when Claude is about to read a file
2. **Pattern-based detection** - Checks if the filename matches sensitive patterns (credentials, keys, secrets, etc.)
3. **Content scanning** - If sensitive, reads the file and scans it through AI Guard
4. **Blocks on policy violations** - If AI Guard detects credentials, PII, or other violations, the read is blocked

## Installation

### 1. Copy the hook script

```bash
cp hooks/scan_file_read.py ~/.claude/hooks/aiguard/scan_file_read.py
chmod +x ~/.claude/hooks/aiguard/scan_file_read.py
```

### 2. Update `~/.claude/settings.json`

Add the Read tool matcher to `PreToolUse`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Read",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/aiguard/scan_file_read.py"
          }
        ]
      }
    ]
  }
}
```

### 3. Restart Claude Code

Close and reopen Cursor/Claude Code for the hook to take effect.

## How It Works

### Sensitive File Pattern Detection

The hook checks if the file path matches any of these patterns:

| Pattern | Description | Example |
|---------|-------------|---------|
| `*credentials*.json` | Credentials files | `aws-credentials.json` |
| `*.pem` | PEM certificates/keys | `private-key.pem` |
| `*.key` | Key files | `api.key` |
| `*.ppk` | PuTTY private keys | `server.ppk` |
| `*secret*` | Files with "secret" | `api-secrets.txt` |
| `*.env` | Environment files | `.env`, `.env.production` |
| `*password*` | Files with "password" | `passwords.txt` |
| `*id_rsa*` | SSH private keys | `id_rsa`, `id_rsa.pub` |
| `~/.aws/credentials` | AWS credentials | AWS config |
| `~/.ssh/*` | SSH keys/config | SSH directory |
| `*.p12`, `*.pfx` | Certificates | PKCS#12 files |
| `*config.json` | Config files | `config.json` |
| `*auth*.json` | Auth files | `auth-config.json` |
| `*token*` | Token files | `github-token.txt` |
| `*api*key*` | API key files | `api_key.txt` |

### AI Guard Scanning

If a file matches a sensitive pattern:

1. **Read file content** (up to 50KB by default)
2. **Send to AI Guard** with `direction: IN`
3. **Evaluate detectors**:
   - Credentials (AWS keys, API tokens, passwords)
   - PII (SSN, credit cards, emails)
   - Toxicity or harmful content
   - Custom policy rules
4. **Block or allow** based on verdict

### Flow Diagram

```
User asks Claude to read file
         ↓
PreToolUse event fires
         ↓
scan_file_read.py runs
         ↓
Is filename sensitive? ──No──> ALLOW
         ↓ Yes
Read file content (50KB)
         ↓
Send to AI Guard (direction: IN)
         ↓
    AI Guard scans
         ↓
   ┌─────┴─────┐
   │   Verdict │
   └─────┬─────┘
         │
    ┌────┴────┐
    │         │
  BLOCK     ALLOW
    │         │
    v         v
Exit 2    Exit 0
(blocked) (allowed)
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AIGUARD_API_KEY` | (required) | AI Guard API key |
| `AIGUARD_CLOUD` | `us1` | AI Guard cloud region |
| `AIGUARD_POLICY_ID` | (optional) | Specific policy ID to use |
| `AIGUARD_TIMEOUT` | `30` | API timeout in seconds |
| `AIGUARD_MAX_FILE_SCAN_SIZE` | `51200` | Max file size to scan (bytes) |
| `SECURITY_LOG_PATH` | `~/.claude/hooks/aiguard/security.log` | Log file path |

### Adjusting File Size Limit

To scan larger files, set the environment variable:

```bash
export AIGUARD_MAX_FILE_SCAN_SIZE=102400  # 100KB
```

Or add to `~/.claude/hooks/aiguard/.env`:

```
AIGUARD_MAX_FILE_SCAN_SIZE=102400
```

## Testing

### Test 1: Create a fake credentials file

```bash
# Create a test credentials file
cat > /tmp/test-credentials.json <<EOF
{
  "aws_access_key_id": "AKIAIOSFODNN7EXAMPLE",
  "aws_secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
}
EOF
```

In Claude Code, ask:

```
Read the file /tmp/test-credentials.json
```

**Expected:** The hook should detect the sensitive filename pattern and scan the content. If AI Guard has credential detection enabled, it should **BLOCK** the read with a message like:

```
Blocked by Zscaler AI Guard: File '/tmp/test-credentials.json' contains policy violations
Triggered detectors: credentials
Severity: HIGH | Transaction ID: abc123...
```

### Test 2: Create a safe file

```bash
# Create a safe file
cat > /tmp/README.md <<EOF
# README

This is a safe readme file with no sensitive data.
EOF
```

In Claude Code, ask:

```
Read the file /tmp/README.md
```

**Expected:** The filename doesn't match sensitive patterns, so the hook allows the read without scanning. Log shows:

```
[2026-02-04 12:00:00] FILE READ (not sensitive pattern): /tmp/README.md
```

### Test 3: SSH private key

```bash
# Create a fake SSH private key
cat > /tmp/id_rsa <<EOF
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtz
c2gtZWQyNTUxOQAAACDGKfY+qmGTvTTVQKPzVZ9Gz8CZ7Bz5J0I2Sj0yTYHRXgAA
-----END OPENSSH PRIVATE KEY-----
EOF
```

In Claude Code, ask:

```
Read the file /tmp/id_rsa
```

**Expected:** The hook detects the sensitive pattern (`*id_rsa*`), scans the content, and if AI Guard detects a private key pattern, it **BLOCKS** with:

```
Blocked by Zscaler AI Guard: File '/tmp/id_rsa' contains policy violations
Triggered detectors: credentials
```

### Test 4: Check logs

```bash
tail -20 ~/.claude/hooks/aiguard/security.log
```

Look for entries like:

```
[2026-02-04 12:00:00] Scanning sensitive file read: /tmp/test-credentials.json (type: credentials file)
[2026-02-04 12:00:01] FILE READ: Scanning 150 bytes from /tmp/test-credentials.json
[2026-02-04 12:00:02] BLOCKED FILE READ /tmp/test-credentials.json: severity=HIGH policy=auto-resolved detectors=[credentials] (txn:abc123...)
```

## Logs

All file read security events are logged to `~/.claude/hooks/aiguard/security.log`:

```
[2026-02-04 12:00:00] Scanning sensitive file read: /path/to/credentials.json (type: credentials file)
[2026-02-04 12:00:01] FILE READ: Scanning 256 bytes from /path/to/credentials.json
[2026-02-04 12:00:02] BLOCKED FILE READ /path/to/credentials.json: severity=HIGH policy=policy_123 detectors=[credentials] (txn:xyz789...)
```

Log message types:

- `FILE READ (not sensitive pattern)` - File doesn't match patterns, allowed without scanning
- `Scanning sensitive file read` - File matches pattern, content will be scanned
- `BLOCKED FILE READ` - AI Guard blocked the file read
- `ALLOWED FILE READ` - AI Guard allowed the file read
- `WARNING FILE READ` - AI Guard detected violations but action is DETECT (not BLOCK)
- `ERROR` - Issues during scanning

## Troubleshooting

### Hook not triggering

1. **Check settings.json** - Ensure the Read matcher is configured
2. **Restart Claude Code** - Close and reopen Cursor
3. **Check permissions** - Ensure the script is executable: `chmod +x ~/.claude/hooks/aiguard/scan_file_read.py`

### All reads are allowed

1. **Check filename patterns** - Your file might not match any sensitive patterns
2. **Check AI Guard policy** - Ensure your policy has credential detection enabled
3. **Check API key** - Ensure `AIGUARD_API_KEY` is set in `~/.claude/hooks/aiguard/.env`

### Errors in logs

Check the security log for ERROR messages:

```bash
grep ERROR ~/.claude/hooks/aiguard/security.log
```

Common issues:
- `AIGUARD_API_KEY not set` - Add API key to .env file
- `Failed to read file` - File permissions issue
- `AI Guard API error` - Network or API issue

## Security Considerations

### Fail-Open Behavior

The hook is designed to **fail-open** on errors:

- If AI Guard API is unreachable → allow read
- If file can't be read → allow (Claude will handle the error)
- If API key is missing → allow (with error log)

This prevents the hook from breaking Claude Code functionality if AI Guard is temporarily unavailable.

### File Size Limit

By default, only the first 50KB of a file is scanned for performance. For very large files:

- Credentials are typically in the first few KB
- Increase `AIGUARD_MAX_FILE_SCAN_SIZE` if needed
- Consider using file hash scanning for large binary files (future enhancement)

### Performance Impact

- **Pattern match only**: ~1ms (most files skip scanning)
- **Pattern match + scan**: 100-300ms (only sensitive files)
- **Network latency**: Depends on AI Guard cloud region

## Customization

### Add custom file patterns

Edit `scan_file_read.py` and add to `SENSITIVE_FILE_PATTERNS`:

```python
SENSITIVE_FILE_PATTERNS = [
    # ... existing patterns ...
    (r'.*my-custom-secret.*', "custom secret file"),
    (r'.*/secrets/.*', "files in secrets directory"),
]
```

### Disable scanning for specific patterns

Remove or comment out patterns you don't want to scan:

```python
SENSITIVE_FILE_PATTERNS = [
    # (r'.*config\.json$', "configuration file"),  # Disabled
    (r'.*credentials.*\.json$', "credentials file"),  # Active
]
```

### Use a specific policy

Set `AIGUARD_POLICY_ID` in your `.env`:

```
AIGUARD_POLICY_ID=12345
```

This uses policy ID 12345 instead of auto-resolved policy.

## Related Hooks

- `scan_user_input.py` - Scans user prompts
- `scan_mcp_request.py` - Scans MCP tool parameters
- `scan_response.py` - Scans tool responses
- `scan_url.py` - Scans URLs before fetch

## Future Enhancements

- [ ] Binary file support (scan metadata, hashes)
- [ ] Directory scanning (recursively scan all files)
- [ ] File hash allowlist (skip known-safe files)
- [ ] Redaction mode (allow read but redact sensitive content)
- [ ] Integration with file write scanning (prevent write → read loops)
