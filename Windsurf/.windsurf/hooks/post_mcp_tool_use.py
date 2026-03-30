#!/usr/bin/env python3
"""Windsurf post_mcp_tool_use — AI Guard OUT audit only (cannot block)."""

from __future__ import annotations

import json
import sys

from aiguard_utils import (
    EXIT_ALLOW,
    MAX_POST_CHARS,
    get_client_config,
    log_message,
    normalize_tool_io,
    scan_content,
    trajectory_note,
    truncate_text,
    windsurf_tool_info,
)


def main() -> int:
    try:
        data = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        return EXIT_ALLOW

    ti = windsurf_tool_info(data)
    server = str(ti.get("mcp_server_name") or "unknown")
    mcp_tool = str(ti.get("mcp_tool_name") or "unknown")
    label = f"{server}__{mcp_tool}"
    mcp_result = ti.get("mcp_result")
    result_str = normalize_tool_io(mcp_result)

    if len(result_str) < 5:
        log_message(f"post_mcp_tool_use: no result for {label}{trajectory_note(data)}")
        return EXIT_ALLOW

    if not get_client_config().get("api_key"):
        log_message("post_mcp_tool_use: AIGUARD_API_KEY not set — skipping")
        return EXIT_ALLOW

    args_json = normalize_tool_io(ti.get("mcp_tool_arguments"))
    truncated_in = truncate_text(args_json, MAX_POST_CHARS)
    truncated_out = truncate_text(result_str.replace("\n", " "), MAX_POST_CHARS)
    combined = (
        f"MCP server={server} tool={mcp_tool}\nInput={truncated_in}\nOutput={truncated_out}"
    )

    if len(truncated_out) < 10:
        return EXIT_ALLOW

    log_message(f"post_mcp_tool_use: scanning {label}{trajectory_note(data)}")
    r = scan_content(combined, "OUT")
    if r.get("error"):
        log_message(f"post_mcp_tool_use: API error (audit only): {r['error']}")
        return EXIT_ALLOW

    action = r.get("action") or "ALLOW"
    det = r.get("triggered_detectors") or []
    bd = ",".join(r.get("blocking_detectors") or [])
    txn = r.get("transaction_id") or "unknown"

    if action == "BLOCK":
        log_message(
            f"ALERT post_mcp {label}: would-block policy={r.get('policy_name')} "
            f"detectors=[{bd}] txn={txn} — Windsurf post-hooks cannot block"
        )
        print(
            f"Zscaler AI Guard ALERT: MCP result for {label} would be BLOCKED "
            f"(policy={r.get('policy_name')}, txn={txn}, blocking=[{bd}]). "
            "Post-hooks cannot stop content in Windsurf."
        )
    elif det:
        log_message(
            f"post_mcp_tool_use {label}: detected=[{','.join(det)}] txn={txn}"
        )
        print(
            f"Zscaler AI Guard: detections on {label} tool output: [{','.join(det)}] (txn={txn})"
        )
    else:
        log_message(f"post_mcp_tool_use {label}: clean txn={txn}")

    return EXIT_ALLOW


if __name__ == "__main__":
    raise SystemExit(main())
