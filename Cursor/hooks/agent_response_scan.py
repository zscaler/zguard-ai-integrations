#!/usr/bin/env python3
"""Cursor afterAgentResponse — scan assistant reply (direction OUT)."""

from __future__ import annotations

import json
import sys

from aiguard_utils import get_client_config, log_message, scan_content, truncate_text


def _response_text(data: dict) -> str:
    for key in ("text", "response", "message", "content", "output"):
        v = data.get(key)
        if isinstance(v, str) and v:
            return v
    return ""


def main() -> int:
    try:
        data = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        return 0

    text = _response_text(data)
    if not text:
        return 0

    truncated = truncate_text(text, 20000)
    log_message(f"AGENT-RESPONSE: Scanning assistant response ({len(truncated)} chars)")

    if not get_client_config().get("api_key"):
        log_message("WARNING: AIGUARD_API_KEY not set — allowing response without scan")
        return 0

    r = scan_content(truncated, "OUT")
    if r.get("error"):
        log_message(f"AGENT-RESPONSE: API error; failing open: {r['error']}")
        return 0

    action = r.get("action") or "ALLOW"
    if action not in ("ALLOW", "BLOCK", "DETECT"):
        log_message("AGENT-RESPONSE: Empty or unparseable AI Guard response; failing open")
        return 0

    if action == "BLOCK":
        sev = r.get("severity") or "NONE"
        pol = r.get("policy_name") or "unknown"
        txn = r.get("transaction_id") or "unknown"
        blockers = r.get("blocking_detectors") or []
        bd = ",".join(blockers) if blockers else ""
        log_message(
            f"BLOCKED AGENT RESPONSE: severity={sev} policy={pol} detectors=[{bd}] (txn:{txn})"
        )
        msg = f"Blocked by Zscaler AI Guard: severity={sev}, policy={pol}"
        if bd:
            msg += f", detectors=[{bd}]"
        msg += f" (txn:{txn})"
        print("", file=sys.stderr)
        print(msg, file=sys.stderr)
        print("", file=sys.stderr)
        return 2

    det = r.get("triggered_detectors") or []
    txn = r.get("transaction_id") or "unknown"
    if det:
        log_message(
            f"ALLOWED AGENT RESPONSE: action={action} severity={r.get('severity')} "
            f"detected=[{','.join(det)}] (txn:{txn})"
        )
    else:
        log_message(f"ALLOWED AGENT RESPONSE: action={action} (txn:{txn})")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
