"""
Zscaler AI Guard — shared utilities for Cursor IDE hooks.

Uses the same client pattern as Anthropic Claude Code hooks: `LegacyZGuardClient`
from `zscaler.oneapi_client` with `execute_policy` / `resolve_and_execute_policy`.

`LegacyZGuardClientHelper` reads `AIGUARD_OVERRIDE_URL` from the environment when set
(after `load_dotenv`).
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


def _hooks_dir() -> Path:
    return Path(__file__).resolve().parent


def _project_root() -> Path:
    # Cursor/hooks/aiguard_utils.py -> project root is parent of Cursor/
    return Path(__file__).resolve().parent.parent.parent


def _cursor_integration_dir() -> Path:
    """Directory containing this integration (parent of hooks/)."""
    return Path(__file__).resolve().parent.parent


def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    # Try both locations so credentials work whether .env lives at the
    # workspace root or next to the Cursor integration (common when
    # editing Cursor/.env). Real process env always wins (override=False).
    for env_path in (
        _project_root() / ".env",
        _cursor_integration_dir() / ".env",
    ):
        if env_path.is_file():
            load_dotenv(env_path, override=False)


_load_dotenv()


def get_log_file() -> Path:
    """Log next to this package (Cursor/hooks/aiguard.log)."""
    path = _hooks_dir() / "aiguard.log"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def log_message(message: str) -> None:
    log_file = get_log_file()
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {message}\n")


def get_client_config() -> dict[str, Any]:
    """Build LegacyZGuardClient config (matches Anthropic `aiguard_utils`)."""
    timeout = int(os.environ.get("AIGUARD_TIMEOUT", "3"))
    return {
        "api_key": os.environ.get("AIGUARD_API_KEY", "").strip().strip('"').strip("'"),
        "cloud": os.environ.get("AIGUARD_CLOUD", "us1").strip().strip('"').strip("'"),
        "timeout": timeout,
        "auto_retry_on_rate_limit": True,
        "max_rate_limit_retries": 3,
    }


def get_policy_id() -> Optional[int]:
    raw = os.environ.get("AIGUARD_POLICY_ID", "").strip()
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def get_triggered_detectors(detector_responses: Any) -> list[str]:
    triggered: list[str] = []
    if not detector_responses:
        return triggered
    for name, response in detector_responses.items():
        if hasattr(response, "triggered") and response.triggered:
            triggered.append(name)
    return triggered


def get_blocking_detectors(detector_responses: Any) -> list[str]:
    blocking: list[str] = []
    if not detector_responses:
        return blocking
    for name, response in detector_responses.items():
        action = getattr(response, "action", None)
        if action and str(action).upper() == "BLOCK":
            blocking.append(name)
    return blocking


def scan_content(content: str, direction: str) -> dict[str, Any]:
    """
    Scan via AI Guard. On error, returns ALLOW + error (fail-open).
    """
    from zscaler.oneapi_client import LegacyZGuardClient

    result: dict[str, Any] = {
        "action": "ALLOW",
        "severity": None,
        "transaction_id": None,
        "policy_name": None,
        "triggered_detectors": [],
        "blocking_detectors": [],
        "error": None,
    }

    cfg = get_client_config()
    if not cfg.get("api_key"):
        result["error"] = "AIGUARD_API_KEY not set"
        return result

    policy_id = get_policy_id()

    try:
        with LegacyZGuardClient(cfg) as client:
            if policy_id is not None:
                api_result, _r, error = client.zguard.policy_detection.execute_policy(
                    content=content,
                    direction=direction,
                    policy_id=policy_id,
                )
            else:
                api_result, _r, error = (
                    client.zguard.policy_detection.resolve_and_execute_policy(
                        content=content,
                        direction=direction,
                    )
                )

            if error:
                result["error"] = str(error)
                return result

            act = api_result.action or "ALLOW"
            result["action"] = str(act).upper()
            result["severity"] = getattr(api_result, "severity", None)
            result["transaction_id"] = getattr(api_result, "transaction_id", None)
            result["policy_name"] = getattr(api_result, "policy_name", None)
            dr = getattr(api_result, "detector_responses", None)
            result["triggered_detectors"] = get_triggered_detectors(dr)
            result["blocking_detectors"] = get_blocking_detectors(dr)

    except Exception as e:  # noqa: BLE001 — hooks must not crash Cursor
        result["error"] = str(e)

    return result


def truncate_text(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars]


def normalize_tool_io(raw: Any) -> str:
    if raw is None:
        return ""
    if isinstance(raw, str):
        return raw
    try:
        return json.dumps(raw, separators=(",", ":"))
    except (TypeError, ValueError):
        return str(raw)


def extract_urls(content: str) -> list[str]:
    pattern = r'https?://[^\s<>"\'()\[\]{}]+'
    return list(dict.fromkeys(re.findall(pattern, content)))


SKIP_BUILTIN_TOOLS = frozenset(
    {"Grep", "Read", "Write", "Delete", "Task", "Glob", "Edit", "NotebookEdit"},
)

MAX_SCAN_CHARS = 20000
MAX_TOOL_OUTPUT_BYTES = 51200
