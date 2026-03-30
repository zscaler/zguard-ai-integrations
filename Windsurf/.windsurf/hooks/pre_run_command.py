#!/usr/bin/env python3
"""Windsurf pre_run_command — AI Guard IN; exit 2 on BLOCK."""

from __future__ import annotations

import json
import sys

from aiguard_utils import (
    EXIT_ALLOW,
    EXIT_BLOCK,
    get_client_config,
    log_message,
    scan_content,
    trajectory_note,
    windsurf_tool_info,
)


def block_stderr(r: dict, cmd: str) -> None:
    sev = r.get("severity") or "NONE"
    pol = r.get("policy_name") or "unknown"
    txn = r.get("transaction_id") or "unknown"
    bd = ",".join(r.get("blocking_detectors") or [])
    msg = (
        f"Blocked by Zscaler AI Guard: command blocked — severity={sev}, policy={pol}, "
        f"transactionId={txn}"
    )
    if bd:
        msg += f", blockingDetectors=[{bd}]"
    print(msg, file=sys.stderr)
    print(f"Command: {cmd}", file=sys.stderr)


def main() -> int:
    try:
        data = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        return EXIT_ALLOW

    ti = windsurf_tool_info(data)
    cmd = ti.get("command_line") or ""
    if not cmd:
        return EXIT_ALLOW

    cmd_s = str(cmd)
    log_message(f"pre_run_command:{trajectory_note(data)} {cmd_s[:200]!r}")

    if not get_client_config().get("api_key"):
        log_message("WARNING: AIGUARD_API_KEY not set — allowing without scan")
        return EXIT_ALLOW

    r = scan_content(cmd_s, "IN")
    if r.get("error"):
        log_message(f"pre_run_command: API error (fail-closed): {r['error']}")
        print(f"Zscaler AI Guard scan failed: {r['error']}", file=sys.stderr)
        return EXIT_BLOCK

    action = r.get("action") or "ALLOW"
    if action not in ("ALLOW", "BLOCK", "DETECT"):
        log_message("pre_run_command: invalid action (fail-closed)")
        print(
            "Zscaler AI Guard returned an unexpected response; blocked for safety.",
            file=sys.stderr,
        )
        return EXIT_BLOCK

    if action == "BLOCK":
        log_message(
            f"BLOCKED COMMAND txn={r.get('transaction_id')} policy={r.get('policy_name')}"
        )
        block_stderr(r, cmd_s)
        return EXIT_BLOCK

    det = r.get("triggered_detectors") or []
    if det:
        log_message(
            f"COMMAND WARNING detected=[{','.join(det)}] txn={r.get('transaction_id')}"
        )
    return EXIT_ALLOW


if __name__ == "__main__":
    raise SystemExit(main())
