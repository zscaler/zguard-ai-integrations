"""
Zscaler AI Guard — shared utilities for Windsurf Cascade hooks.

Paths: this file lives in Windsurf/.windsurf/hooks/; integration root is Windsurf/.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


def _hooks_dir() -> Path:
    return Path(__file__).resolve().parent


def _windsurf_integration_root() -> Path:
    """Windsurf/ (contains .windsurf/)."""
    return Path(__file__).resolve().parent.parent.parent


def _project_root() -> Path:
    """Repository root (parent of Windsurf/)."""
    return Path(__file__).resolve().parent.parent.parent.parent


def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    for env_path in (
        _project_root() / ".env",
        _windsurf_integration_root() / ".env",
    ):
        if env_path.is_file():
            load_dotenv(env_path, override=False)


_load_dotenv()


def _ensure_log_file_exists() -> None:
    """Create empty log on first hook import so `tail -f` works before any scan line."""
    try:
        path = _hooks_dir() / "aiguard.log"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch(exist_ok=True)
    except OSError:
        pass


_ensure_log_file_exists()


def get_log_file() -> Path:
    path = _hooks_dir() / "aiguard.log"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def log_message(message: str) -> None:
    log_file = get_log_file()
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {message}\n")


def get_client_config() -> dict[str, Any]:
    timeout = int(os.environ.get("AIGUARD_TIMEOUT", "30"))
    api_key = os.environ.get("AIGUARD_API_KEY", "").strip().strip('"').strip("'")
    cloud = os.environ.get("AIGUARD_CLOUD", "us1").strip().strip('"').strip("'")
    if not cloud:
        cloud = "us1"
    return {
        "api_key": api_key,
        "cloud": cloud,
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

    except Exception as e:  # noqa: BLE001
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
        return json.dumps(raw, separators=(",", ":"), ensure_ascii=False)
    except (TypeError, ValueError):
        return str(raw)


def windsurf_tool_info(data: dict) -> dict:
    ti = data.get("tool_info")
    return ti if isinstance(ti, dict) else {}


def trajectory_note(data: dict) -> str:
    tid = data.get("trajectory_id")
    return f" trajectory={tid}" if tid else ""


def extract_mcp_request_content(tool_info: dict) -> tuple[str, str]:
    """Returns (scan_text, tool_label)."""
    server = str(tool_info.get("mcp_server_name") or "unknown")
    mcp_tool = str(tool_info.get("mcp_tool_name") or "unknown")
    args = tool_info.get("mcp_tool_arguments")
    if not isinstance(args, dict):
        args = {}
    label = f"{server}__{mcp_tool}"
    mt_lower = mcp_tool.lower()

    scan = ""
    if any(x in mt_lower for x in ("web_search", "websearch")) or "search" in mt_lower:
        scan = str(
            args.get("query") or args.get("search_query") or args.get("q") or ""
        )
    elif any(x in mt_lower for x in ("web_fetch", "webfetch", "fetch", "get_url")):
        scan = str(args.get("url") or args.get("uri") or "")
    if not scan:
        scan = str(
            args.get("query")
            or args.get("prompt")
            or args.get("message")
            or args.get("content")
            or ""
        )
    if not scan:
        path_param = (
            args.get("path")
            or args.get("file")
            or args.get("resource")
            or args.get("url")
            or args.get("uri")
            or ""
        )
        if path_param:
            scan = f"Accessing resource: {path_param}"
    if not scan:
        scan = normalize_tool_io(args)
    return (scan, label)


MAX_POST_CHARS = 20000

EXIT_ALLOW = 0
EXIT_BLOCK = 2
