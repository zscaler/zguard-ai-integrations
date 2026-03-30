#!/usr/bin/env python3
"""Windsurf pre_user_prompt — AI Guard IN; exit 2 on BLOCK."""

from __future__ import annotations

import json
import sys

from aiguard_utils import (
    EXIT_ALLOW,
    EXIT_BLOCK,
    MAX_POST_CHARS,
    get_client_config,
    log_message,
    scan_content,
    trajectory_note,
    truncate_text,
    windsurf_tool_info,
)


def block_stderr(r: dict, prefix: str) -> None:
    sev = r.get("severity") or "NONE"
    pol = r.get("policy_name") or "unknown"
    txn = r.get("transaction_id") or "unknown"
    bd = ",".join(r.get("blocking_detectors") or [])
    msg = (
        f"Blocked by Zscaler AI Guard: {prefix} — severity={sev}, policy={pol}, "
        f"transactionId={txn}"
    )
    if bd:
        msg += f", blockingDetectors=[{bd}]"
    print(msg, file=sys.stderr)


def main() -> int:
    try:
        data = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        return EXIT_ALLOW

    ti = windsurf_tool_info(data)
    prompt = ti.get("user_prompt") or ""
    if not prompt:
        return EXIT_ALLOW

    text = truncate_text(str(prompt), MAX_POST_CHARS)
    log_message(f"pre_user_prompt: scanning ({len(text)} chars){trajectory_note(data)}")

    if not get_client_config().get("api_key"):
        log_message("WARNING: AIGUARD_API_KEY not set — allowing without scan")
        return EXIT_ALLOW

    r = scan_content(text, "IN")
    if r.get("error"):
        log_message(f"pre_user_prompt: API error (fail-closed): {r['error']}")
        print(
            f"Zscaler AI Guard scan failed: {r['error']}",
            file=sys.stderr,
        )
        return EXIT_BLOCK

    action = r.get("action") or "ALLOW"
    if action not in ("ALLOW", "BLOCK", "DETECT"):
        log_message("pre_user_prompt: invalid action (fail-closed)")
        print(
            "Zscaler AI Guard returned an unexpected response; blocked for safety.",
            file=sys.stderr,
        )
        return EXIT_BLOCK

    if action == "BLOCK":
        log_message(
            f"BLOCKED USER INPUT policy={r.get('policy_name')} "
            f"detectors={r.get('blocking_detectors')} txn={r.get('transaction_id')}"
        )
        block_stderr(r, "user prompt")
        return EXIT_BLOCK

    det = r.get("triggered_detectors") or []
    if det:
        log_message(
            f"ALLOWED USER INPUT action={action} detected=[{','.join(det)}] "
            f"txn={r.get('transaction_id')}"
        )
    return EXIT_ALLOW


if __name__ == "__main__":
    raise SystemExit(main())
