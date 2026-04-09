#!/usr/bin/env python3
"""
Zscaler AI Guard Security Scanner

Scans prompts, responses, and code for security threats using
Zscaler AI Guard Detection as a Service (DaaS) API via zscaler-sdk-python.

Environment Variables:
    AIGUARD_API_KEY: Required - API key from AI Guard Console
    AIGUARD_CLOUD: Optional - Cloud region (default: us1)
    AIGUARD_POLICY_ID: Optional - Specific policy ID (auto-resolved if not set)
    AIGUARD_TIMEOUT: Optional - Request timeout in seconds (default: 30)

Usage:
    # Via heredoc (recommended):
    python scan.py --type prompt <<'EOF'
    content to scan
    EOF

    # Via file:
    python scan.py --type code --file path/to/file.py

    # Via argument (simple content only):
    python scan.py --type prompt --content "simple text"

    # Conversation (prompt + response):
    python scan.py --type conversation --prompt "user" --response "ai"
"""

import argparse
import json
import os
import sys
from typing import Optional

try:
    from zscaler.oneapi_client import LegacyZGuardClient
except ImportError:
    print(json.dumps({
        "status": "error",
        "error": "zscaler-sdk-python not installed. Run: pip install zscaler-sdk-python",
        "action": "BLOCK"
    }))
    sys.exit(1)


def get_config() -> dict:
    """Load configuration from environment variables."""
    api_key = os.environ.get("AIGUARD_API_KEY")
    if not api_key:
        print(json.dumps({
            "status": "error",
            "error": "AIGUARD_API_KEY environment variable not set",
            "action": "BLOCK"
        }))
        sys.exit(1)

    return {
        "api_key": api_key,
        "cloud": os.environ.get("AIGUARD_CLOUD", "us1"),
        "timeout": int(os.environ.get("AIGUARD_TIMEOUT", "30")),
        "auto_retry_on_rate_limit": True,
        "max_rate_limit_retries": 3,
    }


def get_policy_id() -> Optional[int]:
    """Get policy ID from environment."""
    policy_id = os.environ.get("AIGUARD_POLICY_ID")
    return int(policy_id) if policy_id else None


def read_file(file_path: str) -> str:
    """Read content from a file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(json.dumps({
            "status": "error",
            "error": f"File not found: {file_path}",
            "action": "BLOCK"
        }))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({
            "status": "error",
            "error": f"Failed to read file: {str(e)}",
            "action": "BLOCK"
        }))
        sys.exit(1)


def get_triggered_detectors(detector_responses: dict) -> list:
    """Extract list of triggered detector names from the API response."""
    triggered = []
    if detector_responses:
        for name, response in detector_responses.items():
            if hasattr(response, "triggered") and response.triggered:
                triggered.append(name)
    return triggered


def scan_content(config: dict, content: str, direction: str, policy_id: Optional[int] = None) -> dict:
    """
    Scan content through Zscaler AI Guard.

    Args:
        config: Client configuration dict
        content: The content to scan
        direction: "IN" (prompts) or "OUT" (responses)
        policy_id: Optional specific policy ID

    Returns:
        Scan result dictionary
    """
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
                return {
                    "status": "error",
                    "error": str(error),
                    "action": "BLOCK"
                }

            action = api_result.action or "ALLOW"
            triggered = get_triggered_detectors(api_result.detector_responses)

            result = {
                "action": action,
                "severity": api_result.severity,
                "transaction_id": api_result.transaction_id,
                "policy_name": getattr(api_result, "policy_name", None),
                "triggered_detectors": triggered,
            }

            if action == "BLOCK":
                result["status"] = "blocked"
            elif action == "DETECT" or triggered:
                result["status"] = "threat_detected"
            else:
                result["status"] = "safe"

            return result

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "action": "BLOCK"
        }


def main():
    parser = argparse.ArgumentParser(
        description="Scan content for security threats using Zscaler AI Guard"
    )
    parser.add_argument(
        "--type",
        choices=["prompt", "response", "code", "conversation"],
        default="prompt",
        help="Type of content to scan"
    )
    parser.add_argument(
        "--content",
        help="Content to scan (for prompt, response, or code types)"
    )
    parser.add_argument(
        "--file",
        help="Path to file to scan (alternative to --content)"
    )
    parser.add_argument(
        "--prompt",
        help="User prompt (for conversation type)"
    )
    parser.add_argument(
        "--response",
        help="AI response (for conversation type)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Include additional detail in output"
    )

    args = parser.parse_args()

    if args.type == "conversation":
        if not args.prompt or not args.response:
            print(json.dumps({
                "status": "error",
                "error": "Conversation type requires both --prompt and --response",
                "action": "BLOCK"
            }))
            sys.exit(1)
    elif not args.content and not args.file:
        if not sys.stdin.isatty():
            args.content = sys.stdin.read().strip()
        if not args.content:
            print(json.dumps({
                "status": "error",
                "error": "Provide content via --content, --file, or stdin (heredoc)",
                "action": "BLOCK"
            }))
            sys.exit(1)

    config = get_config()
    policy_id = get_policy_id()

    content = args.content
    if args.file:
        content = read_file(args.file)

    if args.type == "conversation":
        result_prompt = scan_content(config, args.prompt, "IN", policy_id)
        result_response = scan_content(config, args.response, "OUT", policy_id)

        combined_action = "BLOCK" if "BLOCK" in (result_prompt["action"], result_response["action"]) \
            else "DETECT" if "DETECT" in (result_prompt["action"], result_response["action"]) \
            else "ALLOW"

        result = {
            "action": combined_action,
            "status": "blocked" if combined_action == "BLOCK"
                else "threat_detected" if combined_action == "DETECT"
                    or result_prompt.get("triggered_detectors")
                    or result_response.get("triggered_detectors")
                else "safe",
            "prompt_scan": result_prompt,
            "response_scan": result_response,
        }
    else:
        if args.type == "prompt":
            direction = "IN"
        else:
            direction = "OUT"

        result = scan_content(config, content, direction, policy_id)

    print(json.dumps(result, indent=2))

    if result.get("status") == "error":
        sys.exit(1)
    elif result.get("action") == "BLOCK":
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
