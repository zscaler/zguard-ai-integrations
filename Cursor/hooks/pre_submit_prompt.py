#!/usr/bin/env python3
"""Cursor beforeSubmitPrompt — scan user prompt (direction IN)."""

from __future__ import annotations

import json
import sys

from aiguard_utils import get_client_config, log_message, scan_content, truncate_text


def main() -> int:
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        print(json.dumps({"continue": True}))
        return 0

    prompt = data.get("prompt") or ""
    if not prompt:
        print(json.dumps({"continue": True}))
        return 0

    text = truncate_text(prompt, 20000)
    log_message(f"PRE-PROMPT: Scanning user prompt ({len(text)} chars)")

    if not get_client_config().get("api_key"):
        log_message("WARNING: AIGUARD_API_KEY not set — allowing prompt without scan")
        print(json.dumps({"continue": True}))
        return 0

    r = scan_content(text, "IN")
    if r.get("error"):
        log_message(f"PRE-PROMPT: API error; failing open: {r['error']}")
        print(json.dumps({"continue": True}))
        return 0

    action = r.get("action") or "ALLOW"
    if action not in ("ALLOW", "BLOCK", "DETECT"):
        log_message("PRE-PROMPT: Empty or unparseable AI Guard response; failing open")
        print(json.dumps({"continue": True}))
        return 0

    if action == "BLOCK":
        sev = r.get("severity") or "NONE"
        pol = r.get("policy_name") or "unknown"
        txn = r.get("transaction_id") or "unknown"
        blockers = r.get("blocking_detectors") or []
        bd = ",".join(blockers) if blockers else ""
        log_message(
            f"BLOCKED USER PROMPT: severity={sev} policy={pol} detectors=[{bd}] (txn:{txn})"
        )
        msg = f"Blocked by Zscaler AI Guard: severity={sev}, policy={pol}"
        if bd:
            msg += f", detectors=[{bd}]"
        msg += f" (txn:{txn})"
        print("", file=sys.stderr)
        print(msg, file=sys.stderr)
        print("", file=sys.stderr)
        print(json.dumps({"continue": False, "user_message": msg}))
        return 2

    det = r.get("triggered_detectors") or []
    txn = r.get("transaction_id") or "unknown"
    if det:
        log_message(
            f"ALLOWED USER PROMPT: action={action} severity={r.get('severity')} "
            f"detected=[{','.join(det)}] (txn:{txn})"
        )
    else:
        log_message(f"ALLOWED USER PROMPT: action={action} (txn:{txn})")

    print(json.dumps({"continue": True}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
