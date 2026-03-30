#!/usr/bin/env python3
"""Windsurf post_cascade_response — AI Guard OUT audit only (cannot block)."""

from __future__ import annotations

import json
import sys

from aiguard_utils import (
    EXIT_ALLOW,
    MAX_POST_CHARS,
    get_client_config,
    log_message,
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
    response = ti.get("response") or ""
    response_str = str(response) if response is not None else ""

    if len(response_str) < 10:
        return EXIT_ALLOW

    if not get_client_config().get("api_key"):
        log_message("post_cascade_response: AIGUARD_API_KEY not set — skipping")
        return EXIT_ALLOW

    truncated = truncate_text(response_str.replace("\n", " "), MAX_POST_CHARS)
    log_message(
        f"post_cascade_response: scanning ({len(truncated)} chars){trajectory_note(data)}"
    )

    r = scan_content(truncated, "OUT")
    if r.get("error"):
        log_message(f"post_cascade_response: API error (audit only): {r['error']}")
        return EXIT_ALLOW

    action = r.get("action") or "ALLOW"
    det = r.get("triggered_detectors") or []
    bd = ",".join(r.get("blocking_detectors") or [])
    txn = r.get("transaction_id") or "unknown"

    if action == "BLOCK":
        log_message(
            f"ALERT Cascade response: would-block policy={r.get('policy_name')} "
            f"detectors=[{bd}] txn={txn}"
        )
        print(
            f"Zscaler AI Guard ALERT: Cascade response would be BLOCKED "
            f"(policy={r.get('policy_name')}, txn={txn}, blocking=[{bd}]). "
            "Post-hooks cannot block in Windsurf."
        )
    elif det:
        log_message(
            f"ALERT Cascade response: detected=[{','.join(det)}] txn={txn}"
        )
        print(
            f"Zscaler AI Guard: detections on Cascade output: [{','.join(det)}] (txn={txn})"
        )

    return EXIT_ALLOW


if __name__ == "__main__":
    raise SystemExit(main())
