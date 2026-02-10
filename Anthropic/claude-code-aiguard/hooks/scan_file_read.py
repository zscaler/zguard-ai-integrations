#!/usr/bin/env python3
"""
Zscaler AI Guard - File Read Security Scanner Hook for Claude Code

Scans file contents BEFORE Claude reads them to prevent exposure of:
- Credentials (API keys, tokens, passwords)
- SSH/TLS private keys
- Environment files with secrets
- Sensitive configuration files

Usage: Configured as a Claude Code hook for PreToolUse events on Read tool.
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path


# Load environment variables from .env file if present
def load_env():
    """Load environment variables from .env file."""
    env_file = Path(__file__).parent / ".env"
    if not env_file.exists():
        env_file = Path(__file__).parent.parent / ".env"
    if not env_file.exists():
        return
    try:
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    if key and value and key not in os.environ:
                        os.environ[key] = value
    except Exception:
        pass


load_env()

from zscaler.oneapi_client import LegacyZGuardClient


def get_log_file() -> Path:
    """Get the log file path."""
    log_path = os.environ.get(
        "SECURITY_LOG_PATH", os.path.expanduser("~/.claude/hooks/aiguard/security.log")
    )
    log_file = Path(log_path)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    return log_file


def log_message(message: str) -> None:
    """Write a message to the security log."""
    log_file = get_log_file()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a") as f:
        f.write(f"[{timestamp}] {message}\n")


def get_client_config() -> dict:
    """Build client configuration from environment variables."""
    return {
        "api_key": os.environ.get("AIGUARD_API_KEY"),
        "cloud": os.environ.get("AIGUARD_CLOUD", "us1"),
        "timeout": int(os.environ.get("AIGUARD_TIMEOUT", "30")),
        "auto_retry_on_rate_limit": True,
        "max_rate_limit_retries": 3,
    }


def get_policy_id():
    """Get policy ID from environment variables."""
    policy_id = os.environ.get("AIGUARD_POLICY_ID")
    return int(policy_id) if policy_id else None


def get_triggered_detectors(detector_responses: dict) -> list:
    """Extract list of triggered detector names."""
    triggered = []
    if detector_responses:
        for name, response in detector_responses.items():
            if hasattr(response, "triggered") and response.triggered:
                triggered.append(name)
    return triggered


# Sensitive file patterns (filename-based detection)
SENSITIVE_FILE_PATTERNS = [
    (r".*credentials.*\.json$", "credentials file"),
    (r".*\.pem$", "PEM certificate/key"),
    (r".*\.key$", "key file"),
    (r".*\.ppk$", "PuTTY private key"),
    (r".*secret.*", "file with 'secret' in name"),
    (r".*\.env$", "environment file"),
    (r".*\.env\..*$", "environment file"),
    (r".*password.*", "file with 'password' in name"),
    (r".*id_rsa.*", "SSH private key"),
    (r".*id_dsa.*", "SSH private key"),
    (r".*id_ecdsa.*", "SSH private key"),
    (r".*id_ed25519.*", "SSH private key"),
    (r".*/\.aws/credentials$", "AWS credentials"),
    (r".*/\.ssh/.*", "SSH configuration/keys"),
    (r".*\.p12$", "PKCS#12 certificate"),
    (r".*\.pfx$", "PFX certificate"),
    (r".*config\.json$", "configuration file"),
    (r".*auth.*\.json$", "authentication file"),
    (r".*token.*", "file with 'token' in name"),
    (r".*api.?key.*", "API key file"),
]


def is_sensitive_file(filepath: str) -> tuple:
    """
    Check if file path matches sensitive file patterns.

    Returns:
        (is_sensitive: bool, reason: str)
    """
    for pattern, description in SENSITIVE_FILE_PATTERNS:
        if re.search(pattern, filepath, re.IGNORECASE):
            return True, description
    return False, None


def scan_file_content(filepath: str, content: str, policy_id: int = None) -> tuple:
    """
    Scan file content through AI Guard.

    Args:
        filepath: Path to the file being read
        content: File content to scan
        policy_id: Optional specific policy ID

    Returns:
        Tuple of (should_block: bool, message: str, details: dict)
    """
    config = get_client_config()

    if not config["api_key"]:
        log_message(f"ERROR: AIGUARD_API_KEY not set - allowing file read: {filepath}")
        return False, None, {}  # Fail-open for misconfiguration

    try:
        with LegacyZGuardClient(config) as client:
            if policy_id:
                result, response, error = client.zguard.policy_detection.execute_policy(
                    content=content, direction="IN", policy_id=policy_id
                )
            else:
                result, response, error = (
                    client.zguard.policy_detection.resolve_and_execute_policy(
                        content=content, direction="IN"
                    )
                )

            if error:
                log_message(f"ERROR: AI Guard API error for {filepath}: {error}")
                return False, None, {}  # Fail-open on API errors

            # Extract response details
            action = result.action or "ALLOW"
            severity = result.severity or "NONE"
            transaction_id = result.transaction_id or "unknown"
            policy_name = getattr(result, "policy_name", None) or (
                f"policy_{policy_id}" if policy_id else "auto-resolved"
            )

            # Get triggered detectors
            triggered = get_triggered_detectors(result.detector_responses)
            detectors_str = ",".join(triggered) if triggered else ""

            details = {
                "action": action,
                "severity": severity,
                "transaction_id": transaction_id,
                "policy_name": policy_name,
                "triggered_detectors": triggered,
            }

            if action == "BLOCK":
                if detectors_str:
                    log_message(
                        f"BLOCKED FILE READ {filepath}: severity={severity} policy={policy_name} detectors=[{detectors_str}] (txn:{transaction_id})"
                    )
                    message = f"Blocked by Zscaler AI Guard: File '{filepath}' contains policy violations\nTriggered detectors: {detectors_str}\nSeverity: {severity} | Transaction ID: {transaction_id}"
                else:
                    log_message(
                        f"BLOCKED FILE READ {filepath}: severity={severity} policy={policy_name} (txn:{transaction_id})"
                    )
                    message = f"Blocked by Zscaler AI Guard: File '{filepath}' contains policy violations\nSeverity: {severity} | Transaction ID: {transaction_id}"
                return True, message, details

            elif action == "DETECT":
                if detectors_str:
                    log_message(
                        f"WARNING FILE READ {filepath}: severity={severity} policy={policy_name} detectors=[{detectors_str}] (txn:{transaction_id})"
                    )
                else:
                    log_message(
                        f"WARNING FILE READ {filepath}: severity={severity} policy={policy_name} (txn:{transaction_id})"
                    )
                # Allow with warning
                return False, None, details

            else:
                # ALLOW
                if detectors_str:
                    log_message(
                        f"ALLOWED FILE READ {filepath}: detectors=[{detectors_str}] (txn:{transaction_id})"
                    )
                else:
                    log_message(f"ALLOWED FILE READ {filepath} (txn:{transaction_id})")
                return False, None, details

    except Exception as e:
        log_message(f"ERROR: Exception during file scan for {filepath}: {str(e)}")
        return False, None, {}  # Fail-open on exceptions


def main():
    """Main entry point for the hook."""
    # Read JSON input from stdin
    try:
        input_json = json.load(sys.stdin)
    except json.JSONDecodeError:
        # If no valid JSON, allow
        sys.exit(0)

    # Extract the file path from Read tool input
    tool_input = input_json.get("tool_input", {})
    filepath = tool_input.get("path", "")

    if not filepath:
        # No file path, nothing to scan
        sys.exit(0)

    # Check if this is a sensitive file by name
    is_sensitive, file_type = is_sensitive_file(filepath)

    if not is_sensitive:
        # Not a sensitive file pattern, allow without scanning
        log_message(f"FILE READ (not sensitive pattern): {filepath}")
        sys.exit(0)

    log_message(f"Scanning sensitive file read: {filepath} (type: {file_type})")

    # Read file content to scan
    try:
        file_path = Path(filepath)

        # Check if file exists and is readable
        if not file_path.exists():
            log_message(f"FILE READ: File does not exist: {filepath}")
            sys.exit(0)  # Let Claude handle the error

        if not file_path.is_file():
            log_message(f"FILE READ: Not a regular file: {filepath}")
            sys.exit(0)  # Let Claude handle

        # Read file content (limit to first 50KB for performance)
        max_scan_size = int(
            os.environ.get("AIGUARD_MAX_FILE_SCAN_SIZE", "51200")
        )  # 50KB default
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read(max_scan_size)

        if len(content) < 5:
            log_message(f"FILE READ: File too small to scan: {filepath}")
            sys.exit(0)

        log_message(f"FILE READ: Scanning {len(content)} bytes from {filepath}")

    except Exception as e:
        log_message(f"ERROR: Failed to read file {filepath}: {str(e)}")
        sys.exit(0)  # Fail-open - let Claude try to read it

    # Get policy ID from env or config file
    policy_id = get_policy_id()

    # Perform scan
    should_block, message, details = scan_file_content(filepath, content, policy_id)

    if should_block:
        # Output block response as JSON to stdout (visible to user)
        block_response = {
            "continue": False,
            "stopReason": "Zscaler AI Guard blocked file read",
            "systemMessage": message,
            "hookSpecificOutput": {"hookEventName": "PreToolUse"},
        }
        print(json.dumps(block_response))
        sys.exit(0)  # Exit 0 with JSON response (not exit 2)

    sys.exit(0)  # Allow


if __name__ == "__main__":
    main()
