#!/usr/bin/env python3
"""
Zscaler AI Guard - Response Security Scanner Hook for Claude Code
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


def extract_response_content(input_json: dict) -> str:
    tool_response = input_json.get("tool_response", "")
    if isinstance(tool_response, str):
        return tool_response
    if isinstance(tool_response, dict):
        for field in [
            "result",
            "content",
            "text",
            "body",
            "message",
            "data",
            "output",
            "response",
            "value",
        ]:
            if field in tool_response:
                value = tool_response[field]
                if isinstance(value, str):
                    return value
                elif value is not None:
                    return json.dumps(value)
        return json.dumps(tool_response)
    if isinstance(tool_response, list):
        parts = []
        for item in tool_response[:10]:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                for field in ["text", "content", "value", "result"]:
                    if field in item and isinstance(item[field], str):
                        parts.append(item[field])
                        break
                else:
                    parts.append(json.dumps(item))
        return "\n".join(parts)
    return str(tool_response) if tool_response else ""


def scan_content(content: str, direction: str, policy_id: int = None) -> tuple:
    config = get_client_config()
    if not config["api_key"]:
        return "ALLOW", None, None, [], "AIGUARD_API_KEY not set"
    try:
        with LegacyZGuardClient(config) as client:
            if policy_id:
                result, response, error = client.zguard.policy_detection.execute_policy(
                    content=content, direction=direction, policy_id=policy_id
                )
            else:
                result, response, error = (
                    client.zguard.policy_detection.resolve_and_execute_policy(
                        content=content, direction=direction
                    )
                )
            if error:
                return "ALLOW", None, None, [], None, str(error)
            action = result.action or "ALLOW"
            severity = result.severity
            transaction_id = result.transaction_id
            triggered = get_triggered_detectors(result.detector_responses)
            policy_name = f"policy_{policy_id}" if policy_id else "auto-resolved"
            return action, severity, transaction_id, triggered, policy_name, None
    except Exception as e:
        return "ALLOW", None, None, [], None, str(e)


def output_block_response(reason: str, message: str):
    response = {
        "continue": False,
        "stopReason": reason,
        "systemMessage": message,
        "hookSpecificOutput": {"hookEventName": "PostToolUse"},
    }
    print(json.dumps(response))


def main():
    try:
        input_json = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)
    tool_name = input_json.get("tool_name", "unknown")
    log_message(f"Scanning {tool_name} response...")
    content = extract_response_content(input_json)
    if not content or len(content) < 5:
        log_message(f"{tool_name}: Skipping - insufficient content")
        sys.exit(0)
    log_message(f"{tool_name}: Extracted content length: {len(content)}")
    policy_id = get_policy_id()
    truncated_content = content[:5000]
    if len(truncated_content) >= 10:
        action, severity, txn_id, triggered, policy_name, error = scan_content(
            truncated_content, "OUT", policy_id
        )
        detectors_str = ",".join(triggered) if triggered else ""
        if error:
            log_message(f"ERROR: Content scan failed for {tool_name}: {error}")
            sys.exit(0)
        if action == "BLOCK":
            if detectors_str:
                log_message(
                    f"BLOCKED {tool_name} response: severity={severity} policy={policy_name} detectors=[{detectors_str}] (txn:{txn_id})"
                )
                block_msg = f"Blocked by Zscaler AI Guard: {tool_name} response contained policy violations (detectors: {detectors_str})"
            else:
                log_message(
                    f"BLOCKED {tool_name} response: severity={severity} policy={policy_name} (txn:{txn_id})"
                )
                block_msg = f"Blocked by Zscaler AI Guard: {tool_name} response contained policy violations"
            print("", file=sys.stderr)
            print(block_msg, file=sys.stderr)
            print("", file=sys.stderr)
            output_block_response(
                "Zscaler AI Guard blocked tool response",
                "Operation blocked by Zscaler AI Guard security policy",
            )
            sys.exit(0)
        else:
            log_message(f"ALLOWED {tool_name} response (txn:{txn_id})")
    sys.exit(0)


if __name__ == "__main__":
    main()
