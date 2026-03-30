#!/usr/bin/env python3
"""Windsurf pre_mcp_tool_use — AI Guard IN; exit 2 on BLOCK."""

from __future__ import annotations

import json
import sys

from aiguard_utils import (
    EXIT_ALLOW,
    EXIT_BLOCK,
    extract_mcp_request_content,
    get_client_config,
    log_message,
    scan_content,
    trajectory_note,
    windsurf_tool_info,
)


def main() -> int:
    try:
        data = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        return EXIT_ALLOW

    ti = windsurf_tool_info(data)
    content, label = extract_mcp_request_content(ti)

    if not content or content in ("{}", "null"):
        log_message(f"pre_mcp_tool_use: no scannable content for {label}{trajectory_note(data)}")
        return EXIT_ALLOW

    log_message(
        f"pre_mcp_tool_use: scanning {label} ({len(content)} chars){trajectory_note(data)}"
    )

    if not get_client_config().get("api_key"):
        log_message("WARNING: AIGUARD_API_KEY not set — allowing without scan")
        return EXIT_ALLOW

    r = scan_content(content, "IN")
    if r.get("error"):
        log_message(f"pre_mcp_tool_use: API error (fail-closed): {r['error']}")
        print(f"Zscaler AI Guard scan failed: {r['error']}", file=sys.stderr)
        return EXIT_BLOCK

    action = r.get("action") or "ALLOW"
    if action not in ("ALLOW", "BLOCK", "DETECT"):
        log_message("pre_mcp_tool_use: invalid action (fail-closed)")
        print(
            "Zscaler AI Guard returned an unexpected response; blocked for safety.",
            file=sys.stderr,
        )
        return EXIT_BLOCK

    if action == "BLOCK":
        bd = ",".join(r.get("blocking_detectors") or [])
        log_message(
            f"BLOCKED MCP REQUEST {label} detectors=[{bd}] txn={r.get('transaction_id')}"
        )
        sev = r.get("severity") or "NONE"
        txn = r.get("transaction_id") or "unknown"
        pol = r.get("policy_name") or "unknown"
        msg = (
            f"Blocked by Zscaler AI Guard: MCP request to {label} blocked — "
            f"severity={sev}, policy={pol}, transactionId={txn}"
        )
        if bd:
            msg += f", blockingDetectors=[{bd}]"
        print(msg, file=sys.stderr)
        return EXIT_BLOCK

    det = r.get("triggered_detectors") or []
    if det:
        log_message(
            f"ALLOWED MCP REQUEST {label} detected=[{','.join(det)}] "
            f"txn={r.get('transaction_id')}"
        )
    else:
        log_message(f"ALLOWED MCP REQUEST {label} txn={r.get('transaction_id')}")
    return EXIT_ALLOW


if __name__ == "__main__":
    raise SystemExit(main())
