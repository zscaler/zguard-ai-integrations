#!/usr/bin/env python3
"""
Zscaler AI Guard - MCP Request Security Scanner Hook for Claude Code
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
    log_path = os.environ.get(
        "SECURITY_LOG_PATH", os.path.expanduser("~/.claude/hooks/aiguard/security.log")
    )
    log_file = Path(log_path)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    return log_file


def log_message(message: str) -> None:
    log_file = get_log_file()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a") as f:
        f.write(f"[{timestamp}] {message}\n")


def get_client_config() -> dict:
    return {
        "api_key": os.environ.get("AIGUARD_API_KEY"),
        "cloud": os.environ.get("AIGUARD_CLOUD", "us1"),
        "timeout": int(os.environ.get("AIGUARD_TIMEOUT", "30")),
        "auto_retry_on_rate_limit": True,
        "max_rate_limit_retries": 3,
    }


def get_policy_id():
    policy_id = os.environ.get("AIGUARD_POLICY_ID")
    return int(policy_id) if policy_id else None


def get_triggered_detectors(detector_responses: dict) -> list:
    triggered = []
    if detector_responses:
        for name, response in detector_responses.items():
            if hasattr(response, "triggered") and response.triggered:
                triggered.append(name)
    return triggered


def extract_content_from_tool_input(tool_input: dict) -> str:
    if not tool_input or not isinstance(tool_input, dict):
        return ""
    content_fields = [
        "query",
        "message",
        "prompt",
        "text",
        "content",
        "request",
        "input",
        "data",
        "body",
        "url",
        "path",
    ]
    for field in content_fields:
        if field in tool_input and tool_input[field]:
            value = tool_input[field]
            if isinstance(value, str):
                return value
            elif isinstance(value, (dict, list)):
                return json.dumps(value)
    strings = []

    def extract_strings(obj, depth=0):
        if depth > 5:
            return
        if isinstance(obj, str):
            strings.append(obj)
        elif isinstance(obj, dict):
            for v in obj.values():
                extract_strings(v, depth + 1)
        elif isinstance(obj, list):
            for item in obj[:10]:
                extract_strings(item, depth + 1)

    extract_strings(tool_input)
    return " ".join(strings[:10])


def scan_mcp_request(tool_name: str, content: str, policy_id: int = None) -> tuple:
    config = get_client_config()
    if not config["api_key"]:
        log_message("ERROR: AIGUARD_API_KEY not set")
        return False, None, {}
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
                log_message(f"ERROR: AI Guard API error for {tool_name}: {error}")
                return False, None, {}
            action = result.action or "ALLOW"
            severity = result.severity or "NONE"
            transaction_id = result.transaction_id or "unknown"
            policy_name = getattr(result, "policy_name", None) or (
                f"policy_{policy_id}" if policy_id else "auto-resolved"
            )
            triggered = get_triggered_detectors(result.detector_responses)
            detectors_str = ",".join(triggered) if triggered else ""
            if action == "BLOCK":
                if detectors_str:
                    log_message(
                        f"BLOCKED MCP REQUEST {tool_name}: severity={severity} policy={policy_name} detectors=[{detectors_str}] (txn:{transaction_id})"
                    )
                    message = f"Blocked by Zscaler AI Guard: MCP request to {tool_name} blocked\nTriggered detectors: {detectors_str}\nSeverity: {severity}"
                else:
                    log_message(
                        f"BLOCKED MCP REQUEST {tool_name}: severity={severity} policy={policy_name} (txn:{transaction_id})"
                    )
                    message = f"Blocked by Zscaler AI Guard: MCP request to {tool_name} blocked\nSeverity: {severity}"
                return True, message, {}
            else:
                log_message(f"ALLOWED MCP REQUEST {tool_name} (txn:{transaction_id})")
                return False, None, {}
    except Exception as e:
        log_message(f"ERROR: Exception during MCP scan for {tool_name}: {str(e)}")
        return False, None, {}


def main():
    try:
        input_json = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)
    tool_name = input_json.get("tool_name", "unknown")
    tool_input = input_json.get("tool_input", {})
    content = extract_content_from_tool_input(tool_input)

    # Log MCP request even if content is minimal
    if not content or len(content) < 5:
        log_message(
            f"MCP REQUEST {tool_name}: no significant content to scan (params: {str(tool_input)[:100]})"
        )
        sys.exit(0)

    log_message(f"Scanning {tool_name} request: {content[:100]}...")
    policy_id = get_policy_id()
    should_block, message, details = scan_mcp_request(tool_name, content, policy_id)
    if should_block:
        # Output block response as JSON to stdout (visible to user)
        block_response = {
            "continue": False,
            "stopReason": "Zscaler AI Guard blocked MCP request",
            "systemMessage": message,
            "hookSpecificOutput": {"hookEventName": "PreToolUse"},
        }
        print(json.dumps(block_response))
        sys.exit(0)  # Exit 0 with JSON response
    sys.exit(0)


if __name__ == "__main__":
    main()
