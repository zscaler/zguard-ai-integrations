"""
Zscaler AI Guard - Shared Utilities for Claude Code Hooks

Common functions used across all hook scripts.
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from zscaler.oneapi_client import LegacyZGuardClient


# Path to config file (fallback when env vars not available)
CONFIG_FILE = Path(__file__).parent / "config.json"


def load_config() -> dict:
    """Load configuration from config.json file."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def get_log_file() -> Path:
    """Get the log file path from environment or default."""
    log_path = os.environ.get(
        "SECURITY_LOG_PATH", os.path.expanduser("~/.claude/hooks/aiguard/security.log")
    )
    log_file = Path(log_path)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    return log_file


def log_message(message: str) -> None:
    """Write a timestamped message to the security log."""
    log_file = get_log_file()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a") as f:
        f.write(f"[{timestamp}] {message}\n")


def get_client_config() -> dict:
    """Build LegacyZGuardClient configuration from environment or config file."""
    # Load from config file as fallback
    file_config = load_config()

    return {
        "api_key": os.environ.get("AIGUARD_API_KEY") or file_config.get("api_key"),
        "cloud": os.environ.get("AIGUARD_CLOUD") or file_config.get("cloud", "us1"),
        "timeout": int(
            os.environ.get("AIGUARD_TIMEOUT") or file_config.get("timeout", 30)
        ),
        "auto_retry_on_rate_limit": True,
        "max_rate_limit_retries": 3,
    }


def get_policy_id() -> Optional[int]:
    """Get policy ID from environment or config file."""
    # Try environment first
    policy_id = os.environ.get("AIGUARD_POLICY_ID")
    if policy_id:
        return int(policy_id)

    # Fallback to config file
    file_config = load_config()
    policy_id = file_config.get("policy_id")
    return int(policy_id) if policy_id else None


def get_triggered_detectors(detector_responses: dict) -> list:
    """
    Extract list of triggered detector names from response.

    Args:
        detector_responses: Dictionary of detector name -> DetectorResponse

    Returns:
        List of detector names that were triggered
    """
    triggered = []
    if detector_responses:
        for name, response in detector_responses.items():
            if hasattr(response, "triggered") and response.triggered:
                triggered.append(name)
    return triggered


def format_detectors(detectors: list) -> str:
    """Format detector list as comma-separated string."""
    return ",".join(detectors) if detectors else ""


def scan_content(content: str, direction: str, policy_id: Optional[int] = None) -> dict:
    """
    Scan content through Zscaler AI Guard.

    Args:
        content: The content to scan
        direction: "IN" (prompts) or "OUT" (responses)
        policy_id: Optional specific policy ID (auto-resolved if not provided)

    Returns:
        Dictionary with scan results:
        {
            "action": "ALLOW" | "BLOCK" | "DETECT",
            "severity": str | None,
            "transaction_id": str,
            "policy_name": str | None,
            "triggered_detectors": list[str],
            "error": str | None
        }
    """
    config = get_client_config()

    result = {
        "action": "ALLOW",
        "severity": None,
        "transaction_id": None,
        "policy_name": None,
        "triggered_detectors": [],
        "error": None,
    }

    if not config["api_key"]:
        result["error"] = "AIGUARD_API_KEY environment variable not set"
        return result

    try:
        with LegacyZGuardClient(config) as client:
            if policy_id:
                api_result, response, error = (
                    client.zguard.policy_detection.execute_policy(
                        content=content, direction=direction, policy_id=policy_id
                    )
                )
            else:
                api_result, response, error = (
                    client.zguard.policy_detection.resolve_and_execute_policy(
                        content=content, direction=direction
                    )
                )

            if error:
                result["error"] = str(error)
                return result

            result["action"] = api_result.action or "ALLOW"
            result["severity"] = api_result.severity
            result["transaction_id"] = api_result.transaction_id
            result["policy_name"] = getattr(api_result, "policy_name", None)
            result["triggered_detectors"] = get_triggered_detectors(
                api_result.detector_responses
            )

    except Exception as e:
        result["error"] = str(e)

    return result


def extract_urls(content: str) -> list:
    """
    Extract URLs from content string.

    Args:
        content: Text content to search for URLs

    Returns:
        List of unique URLs found
    """
    url_pattern = r'https?://[^\s<>"\'()\[\]{}]+'
    return list(set(re.findall(url_pattern, content)))


def extract_strings_from_object(
    obj: Any, max_depth: int = 5, max_items: int = 10
) -> list:
    """
    Recursively extract string values from nested objects.

    Args:
        obj: Object to extract strings from (dict, list, str, etc.)
        max_depth: Maximum recursion depth
        max_items: Maximum items to process at each level

    Returns:
        List of extracted strings
    """
    strings = []

    def _extract(item, depth=0):
        if depth > max_depth:
            return
        if isinstance(item, str):
            strings.append(item)
        elif isinstance(item, dict):
            for i, v in enumerate(item.values()):
                if i >= max_items:
                    break
                _extract(v, depth + 1)
        elif isinstance(item, list):
            for i, v in enumerate(item):
                if i >= max_items:
                    break
                _extract(v, depth + 1)

    _extract(obj)
    return strings


def output_block_response(reason: str, message: str) -> None:
    """
    Output JSON response to block content in PostToolUse hooks.

    This outputs the proper JSON format that Claude Code expects
    to stop processing a tool response.

    Args:
        reason: Short reason for blocking
        message: System message to display
    """
    response = {
        "continue": False,
        "stopReason": reason,
        "systemMessage": message,
        "hookSpecificOutput": {"hookEventName": "PostToolUse"},
    }
    print(json.dumps(response))
