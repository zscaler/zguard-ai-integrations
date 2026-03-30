#!/usr/bin/env python3
"""Cursor postToolUse — scan MCP and Shell tool outputs (direction IN)."""

from __future__ import annotations

import json
import sys

from aiguard_utils import (
    MAX_SCAN_CHARS,
    MAX_TOOL_OUTPUT_BYTES,
    SKIP_BUILTIN_TOOLS,
    extract_urls,
    get_client_config,
    log_message,
    normalize_tool_io,
    scan_content,
    truncate_text,
)


def main() -> int:
    try:
        data = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        log_message("SCAN-RESPONSE: Failed to parse stdin JSON, passing through")
        print("{}")
        return 0

    tool_name = data.get("tool_name") or "unknown"
    if tool_name in SKIP_BUILTIN_TOOLS:
        log_message(f"SCAN-RESPONSE: Skipping built-in tool={tool_name}")
        print("{}")
        return 0

    raw_out = data.get("tool_output")
    tool_output = normalize_tool_io(raw_out)

    log_message(f"SCAN-RESPONSE: tool={tool_name} output_size={len(tool_output)}")

    if not tool_output or not tool_output.strip():
        log_message("SCAN-RESPONSE: tool_output is empty, skipping scan")
        print("{}")
        return 0

    if len(tool_output) > MAX_TOOL_OUTPUT_BYTES:
        log_message(
            f"SCAN-RESPONSE: tool_output too large ({len(tool_output)} bytes), skipping scan"
        )
        print("{}")
        return 0

    if not get_client_config().get("api_key"):
        log_message("SCAN-RESPONSE: WARNING: AIGUARD_API_KEY not set, skipping scan")
        print("{}")
        return 0

    urls = extract_urls(tool_output)
    if urls:
        preview = " ".join(urls[:3])
        log_message(f"SCAN-RESPONSE: Found {len(urls)} URL(s): {preview}")

    truncated = truncate_text(tool_output, MAX_SCAN_CHARS)
    log_message(f"SCAN-RESPONSE: Scanning tool={tool_name} as direction=IN")

    r = scan_content(truncated, "IN")
    if r.get("error"):
        log_message(f"SCAN-RESPONSE: WARNING: API error, allowing by default: {r['error']}")
        print("{}")
        return 0

    action = r.get("action") or "ALLOW"
    if action not in ("ALLOW", "BLOCK", "DETECT"):
        log_message(
            f"SCAN-RESPONSE: WARNING: AI Guard returned invalid/no action, allowing by default"
        )
        print("{}")
        return 0

    txn = r.get("transaction_id") or "unknown"
    sev = r.get("severity") or "NONE"
    blockers = r.get("blocking_detectors") or []
    det = r.get("triggered_detectors") or []

    if action == "BLOCK":
        bd = ",".join(blockers) if blockers else ""
        log_message(
            f"SCAN-RESPONSE: BLOCKED tool={tool_name} severity={sev} detectors=[{bd}] txn={txn}"
        )
        msg = f"BLOCKED by Zscaler AI Guard: severity={sev}"
        if bd:
            msg += f" (detectors: {bd})"
        msg += f" [txn:{txn}]"
        print(json.dumps({"updated_mcp_tool_output": msg}))
        return 0

    if action == "ALLOW" and det:
        log_message(
            f"SCAN-RESPONSE: ALLOWED tool={tool_name} detected=[{','.join(det)}] txn={txn}"
        )
    elif action == "ALLOW":
        log_message(f"SCAN-RESPONSE: ALLOWED tool={tool_name} txn={txn}")
    else:
        log_message(
            f"SCAN-RESPONSE: action={action} tool={tool_name} "
            f"detected=[{','.join(det)}] txn={txn}"
        )

    print("{}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
