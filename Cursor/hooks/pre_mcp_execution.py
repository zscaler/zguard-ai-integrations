#!/usr/bin/env python3
"""Cursor beforeMCPExecution — scan MCP tool input (direction IN)."""

from __future__ import annotations

import json
import sys

from aiguard_utils import get_client_config, log_message, normalize_tool_io, scan_content


def main() -> int:
    try:
        data = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        print(json.dumps({"permission": "allow"}))
        return 0

    tool_name = data.get("tool_name") or ""
    if not tool_name:
        log_message("PRE-MCP: No tool_name in input; allowing through")
        print(json.dumps({"permission": "allow"}))
        return 0

    raw_in = data.get("tool_input")
    if raw_in is None:
        log_message(f"PRE-MCP: tool_name={tool_name} — empty tool_input; allowing through")
        print(json.dumps({"permission": "allow"}))
        return 0

    tool_input_str = normalize_tool_io(raw_in)
    if not tool_input_str:
        log_message(
            f"PRE-MCP: tool_name={tool_name} — could not normalize tool_input; allowing through"
        )
        print(json.dumps({"permission": "allow"}))
        return 0

    if not get_client_config().get("api_key"):
        log_message(
            f"PRE-MCP: WARNING — AIGUARD_API_KEY not set; skipping scan for tool={tool_name} (fail-open)"
        )
        print(json.dumps({"permission": "allow"}))
        return 0

    log_message(f"PRE-MCP: Scanning tool={tool_name}")

    r = scan_content(tool_input_str, "IN")
    if r.get("error"):
        log_message(f"PRE-MCP: API error scanning tool={tool_name}; failing open: {r['error']}")
        print(json.dumps({"permission": "allow"}))
        return 0

    action = r.get("action") or "ALLOW"
    if action not in ("ALLOW", "BLOCK", "DETECT"):
        log_message(
            f"PRE-MCP: Empty or unparseable AI Guard response for tool={tool_name}; failing open"
        )
        print(json.dumps({"permission": "allow"}))
        return 0

    if action == "BLOCK":
        sev = r.get("severity") or "NONE"
        txn = r.get("transaction_id") or "unknown"
        pol = r.get("policy_name") or "unknown"
        blockers = r.get("blocking_detectors") or []
        bd = ",".join(blockers) if blockers else ""
        log_message(
            f"PRE-MCP: BLOCKED tool={tool_name} severity={sev} detectors=[{bd}] txn={txn}"
        )
        user_msg = f"""Zscaler AI Guard blocked this MCP tool call.

Tool: {tool_name}
Severity: {sev}
Policy: {pol}"""
        if bd:
            user_msg += f"\nDetectors: {bd}"
        user_msg += f"\nTransaction: {txn}\n\nThe tool input was flagged for potential security issues."

        agent_msg = (
            f"AI Guard security scan blocked the {tool_name} tool call (txn: {txn}, severity: {sev}). "
            "Do not retry this tool call. Inform the user that the tool input was flagged by security scanning."
        )

        print(
            json.dumps(
                {
                    "permission": "deny",
                    "user_message": user_msg,
                    "agent_message": agent_msg,
                }
            )
        )
        return 2

    det = r.get("triggered_detectors") or []
    txn = r.get("transaction_id") or "unknown"
    if det:
        log_message(
            f"PRE-MCP: ALLOWED tool={tool_name} action={action} "
            f"detected=[{','.join(det)}] txn={txn}"
        )
    else:
        log_message(f"PRE-MCP: ALLOWED tool={tool_name} action={action} txn={txn}")

    print(json.dumps({"permission": "allow"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
