#!/usr/bin/env python3
"""
Zscaler AI Guard - User Input Security Scanner Hook for Claude Code

Scans user prompts BEFORE they reach Claude using Zscaler AI Guard API.
Provides first-line defense against prompt injection, PII exposure, and
malicious content in user inputs.

Usage: Configured as a Claude Code hook for UserPromptSubmit events.
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path


# Load environment variables from .env file if present
def load_env():
    """Load environment variables from .env file."""
    env_file = Path(__file__).parent / ".env"
    if not env_file.exists():
        # Try parent directory
        env_file = Path(__file__).parent.parent / ".env"

    if not env_file.exists():
        return  # No .env file, use system environment variables

    try:
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if not line or line.startswith("#"):
                    continue
                # Parse KEY=VALUE
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip()
                    # Only set if not already in environment
                    if key and value and key not in os.environ:
                        os.environ[key] = value
    except Exception:
        pass  # Fail silently, use system environment variables


# Load .env file at import time
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
    config = {
        "api_key": os.environ.get("AIGUARD_API_KEY"),
        "cloud": os.environ.get("AIGUARD_CLOUD", "us1"),
        "timeout": int(os.environ.get("AIGUARD_TIMEOUT", "30")),
        "auto_retry_on_rate_limit": True,
        "max_rate_limit_retries": 3,
    }
    return config


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


def scan_user_input(content: str, policy_id: int = None) -> tuple:
    """
    Scan user input content through AI Guard.

    Args:
        content: The user prompt to scan
        policy_id: Optional specific policy ID

    Returns:
        Tuple of (should_block: bool, message: str, details: dict)
    """
    config = get_client_config()

    if not config["api_key"]:
        log_message("ERROR: AIGUARD_API_KEY environment variable not set")
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
                log_message(f"ERROR: AI Guard API error: {error}")
                return False, None, {}  # Fail-open on API errors

            # Extract response details
            action = result.action or "ALLOW"
            severity = result.severity or "NONE"
            transaction_id = result.transaction_id or "unknown"
            # Use policy_id if provided, otherwise check if API returned policy name
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
                        f"BLOCKED USER INPUT: severity={severity} policy={policy_name} detectors=[{detectors_str}] (txn:{transaction_id})"
                    )
                    message = f"Blocked by Zscaler AI Guard: Your input was blocked due to policy violation\nTriggered detectors: {detectors_str}\nSeverity: {severity} | Transaction ID: {transaction_id}"
                else:
                    log_message(
                        f"BLOCKED USER INPUT: severity={severity} policy={policy_name} (txn:{transaction_id})"
                    )
                    message = f"Blocked by Zscaler AI Guard: Your input was blocked due to policy violation\nSeverity: {severity} | Transaction ID: {transaction_id}"
                return True, message, details

            elif action == "DETECT":
                if detectors_str:
                    log_message(
                        f"WARNING USER INPUT: severity={severity} policy={policy_name} detectors=[{detectors_str}] (txn:{transaction_id})"
                    )
                else:
                    log_message(
                        f"WARNING USER INPUT: severity={severity} policy={policy_name} (txn:{transaction_id})"
                    )
                # Allow with warning
                return False, None, details

            else:
                # ALLOW
                if detectors_str:
                    log_message(
                        f"ALLOWED USER INPUT: detectors=[{detectors_str}] (txn:{transaction_id})"
                    )
                else:
                    log_message(f"ALLOWED USER INPUT (txn:{transaction_id})")
                return False, None, details

    except Exception as e:
        log_message(f"ERROR: Exception during scan: {str(e)}")
        return False, None, {}  # Fail-open on exceptions


def main():
    """Main entry point for the hook."""
    # Read JSON input from stdin
    try:
        input_json = json.load(sys.stdin)
    except json.JSONDecodeError:
        # If no valid JSON, allow
        sys.exit(0)

    # Extract the user prompt
    user_message = input_json.get("prompt", "")

    if not user_message:
        sys.exit(0)  # Nothing to scan

    # Log scan initiation
    log_message(f"Scanning user input: {user_message[:100]}...")

    # Get policy ID from env or config file
    policy_id = get_policy_id()

    # Perform scan
    should_block, message, details = scan_user_input(user_message, policy_id)

    if should_block:
        # Output to stderr for visibility
        print("\n" + "=" * 60, file=sys.stderr)
        print("🛑 BLOCKED BY ZSCALER AI GUARD", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        print(message, file=sys.stderr)
        print("=" * 60 + "\n", file=sys.stderr)

        # Output JSON response
        block_response = {
            "continue": False,
            "stopReason": "Zscaler AI Guard blocked your input",
            "systemMessage": message,
            "hookSpecificOutput": {"hookEventName": "UserPromptSubmit"},
        }
        print(json.dumps(block_response))
        sys.exit(2)  # Exit 2 to signal block

    sys.exit(0)  # Allow


if __name__ == "__main__":
    main()
