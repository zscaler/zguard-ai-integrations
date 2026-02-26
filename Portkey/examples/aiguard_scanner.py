"""
Shared Zscaler AI Guard scanner for Portkey examples.

Provides a reusable scan function with detailed detector output,
used by all test_*.py scripts.
"""

import json
import os

from zscaler.zaiguard.legacy import LegacyZGuardClientHelper


def _get_attr(obj, name, default=None):
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def scan_content(content: str, direction: str = "IN", transaction_id: str | None = None) -> dict:
    """
    Scan content using the Zscaler AI Guard SDK and return a structured result
    with full detector details.
    """
    cloud = os.getenv("AIGUARD_CLOUD", "us1")
    client = LegacyZGuardClientHelper(cloud=cloud)

    result, response, error = client.policy_detection.resolve_and_execute_policy(
        content=content,
        direction=direction,
        transaction_id=transaction_id,
    )

    if error:
        return {"error": str(error)}

    action = _get_attr(result, "action", "unknown")
    severity = _get_attr(result, "severity", "unknown")
    policy_name = _get_attr(result, "policy_name") or _get_attr(result, "policyName", "unknown")
    policy_id = _get_attr(result, "policy_id") or _get_attr(result, "policyId", "unknown")
    txn_id = _get_attr(result, "transaction_id") or _get_attr(result, "transactionId", "unknown")
    direction_out = _get_attr(result, "direction", direction)

    detector_responses = (
        _get_attr(result, "detector_responses")
        or _get_attr(result, "detectorResponses")
        or {}
    )

    detectors = {}
    blocking = []
    for name, det in (detector_responses.items() if isinstance(detector_responses, dict) else []):
        det_action = _get_attr(det, "action", "unknown")
        det_triggered = _get_attr(det, "triggered", False)
        det_severity = _get_attr(det, "severity", "unknown")
        detectors[name] = {
            "action": det_action,
            "triggered": det_triggered,
            "severity": det_severity,
        }
        if str(det_action).upper() == "BLOCK":
            blocking.append(name)

    return {
        "action": action,
        "severity": severity,
        "direction": direction_out,
        "policy_name": policy_name,
        "policy_id": policy_id,
        "transaction_id": txn_id,
        "blocking_detectors": blocking,
        "detectors": detectors,
    }


def print_scan_result(result: dict) -> None:
    """Pretty-print a scan result."""
    if "error" in result:
        print(f"  ERROR: {result['error']}")
        return

    action = result["action"]
    blocked = str(action).upper() != "ALLOW"
    status = "BLOCKED" if blocked else "ALLOWED"

    print(f"  Status:      {status}")
    print(f"  Action:      {action}")
    print(f"  Severity:    {result['severity']}")
    print(f"  Direction:   {result['direction']}")
    print(f"  Policy:      {result['policy_name']} (ID: {result['policy_id']})")
    print(f"  Transaction: {result['transaction_id']}")

    if result.get("blocking_detectors"):
        print(f"  Blocking:    {', '.join(result['blocking_detectors'])}")

    if result.get("detectors"):
        print("  Detectors:")
        for name, info in result["detectors"].items():
            flag = " << BLOCKING" if str(info["action"]).upper() == "BLOCK" else ""
            print(f"    - {name}: triggered={info['triggered']}, action={info['action']}{flag}")
