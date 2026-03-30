#!/usr/bin/env python3
"""
Zscaler AI Guard — Policy Validation Scanner for CI/CD Pipelines

Runs a suite of test prompts/responses against the AI Guard API to validate
that security policies produce the expected ALLOW/BLOCK/DETECT outcomes.
Exits non-zero if any test case fails, gating deployment.

Uses zscaler-sdk-python (LegacyZGuardClient) — same SDK pattern as the
Anthropic and Cursor integrations.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from typing import Any, Optional

import yaml
from dotenv import load_dotenv
from zscaler.oneapi_client import LegacyZGuardClient

load_dotenv()

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"
SKIP = "\033[93mSKIP\033[0m"
WARN = "\033[93mWARN\033[0m"
BOLD = "\033[1m"
RESET = "\033[0m"


def get_client_config() -> dict[str, Any]:
    timeout = int(os.environ.get("AIGUARD_TIMEOUT", "30"))
    api_key = os.environ.get("AIGUARD_API_KEY", "").strip().strip('"').strip("'")
    # GitHub Actions often defines AIGUARD_CLOUD as an empty secret → host
    # becomes api..zseclipse.net. Treat blank like unset.
    cloud = os.environ.get("AIGUARD_CLOUD", "us1").strip().strip('"').strip("'")
    if not cloud:
        cloud = "us1"
    return {
        "api_key": api_key,
        "cloud": cloud,
        "timeout": timeout,
        "auto_retry_on_rate_limit": True,
        "max_rate_limit_retries": 3,
    }


def get_policy_id() -> Optional[int]:
    raw = os.environ.get("AIGUARD_POLICY_ID", "").strip()
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def scan_content(
    client: LegacyZGuardClient,
    content: str,
    direction: str,
    policy_id: Optional[int] = None,
) -> dict[str, Any]:
    """Run a single scan and return normalised results."""
    result: dict[str, Any] = {
        "action": None,
        "severity": None,
        "transaction_id": None,
        "policy_name": None,
        "triggered_detectors": [],
        "blocking_detectors": [],
        "error": None,
    }

    try:
        if policy_id is not None:
            api_result, _resp, error = client.zguard.policy_detection.execute_policy(
                content=content,
                direction=direction,
                policy_id=policy_id,
            )
        else:
            api_result, _resp, error = (
                client.zguard.policy_detection.resolve_and_execute_policy(
                    content=content,
                    direction=direction,
                )
            )

        if error:
            result["error"] = str(error)
            return result

        result["action"] = str(api_result.action or "ALLOW").upper()
        result["severity"] = getattr(api_result, "severity", None)
        result["transaction_id"] = getattr(api_result, "transaction_id", None)
        result["policy_name"] = getattr(api_result, "policy_name", None)

        dr = getattr(api_result, "detector_responses", None)
        if dr:
            for name, resp in dr.items():
                if hasattr(resp, "triggered") and resp.triggered:
                    result["triggered_detectors"].append(name)
                act = getattr(resp, "action", None)
                if act and str(act).upper() == "BLOCK":
                    result["blocking_detectors"].append(name)

    except Exception as exc:
        result["error"] = str(exc)

    return result


def load_test_cases(config_path: str) -> list[dict[str, Any]]:
    with open(config_path) as f:
        config = yaml.safe_load(f)

    if not config or "test_cases" not in config:
        print("ERROR: No test_cases found in config file.")
        sys.exit(1)

    scan_enabled = config.get("settings", {}).get("scan_enabled", True)
    if not scan_enabled:
        print("Security policy scan is disabled in config. Skipping.")
        sys.exit(0)

    return config["test_cases"]


def parse_expected_actions(case: dict[str, Any]) -> list[str]:
    """
    expected_action may be a string or a list (e.g. BLOCK + DETECT both OK).
    expected_actions (plural) overrides if present.
    """
    raw = case.get("expected_actions")
    if raw is not None:
        items = raw if isinstance(raw, list) else [raw]
        return [str(x).upper().strip() for x in items if x is not None]
    raw_one = case.get("expected_action", "ALLOW")
    if isinstance(raw_one, list):
        return [str(x).upper().strip() for x in raw_one if x is not None]
    return [str(raw_one).upper().strip()]


def format_expected_label(expected: list[str]) -> str:
    return "/".join(expected) if len(expected) > 1 else (expected[0] if expected else "ALLOW")


def print_header() -> None:
    print()
    print("=" * 72)
    print(f"  {BOLD}ZSCALER AI GUARD — POLICY VALIDATION SCAN{RESET}")
    print("=" * 72)


def print_case_result(
    idx: int,
    case: dict[str, Any],
    result: dict[str, Any],
    passed: bool,
    *,
    expected_list: list[str] | None = None,
    status_override: str | None = None,
) -> None:
    exp = expected_list if expected_list is not None else parse_expected_actions(case)
    expected_label = format_expected_label(exp)
    if status_override == "warn":
        status = WARN
    else:
        status = PASS if passed else FAIL
    name = case.get("name", f"Test #{idx}")
    actual = result.get("action") or "ERROR"
    txn = result.get("transaction_id") or "—"
    trig = ", ".join(result.get("triggered_detectors", [])) or "none"
    block_d = ", ".join(result.get("blocking_detectors", [])) or "none"

    print(f"  [{status}] {name}")
    print(
        f"       Direction: {case.get('direction', 'IN'):<6}  "
        f"Expected: {expected_label:<16}  Actual: {actual}"
    )
    print(f"       Triggered: {trig}  |  Blocking: {block_d}  (txn: {txn})")
    if result.get("error"):
        print(f"       Error: {result['error']}")
    print()


def print_summary(
    total: int, passed: int, failed: int, skipped: int, optional_warn: int
) -> None:
    print("-" * 72)
    warn_part = f", {optional_warn} optional mismatch(es)" if optional_warn else ""
    print(
        f"  {BOLD}SUMMARY{RESET}: {total} tests — "
        f"{passed} passed, {failed} failed, {skipped} skipped{warn_part}"
    )

    if failed > 0:
        print(f"\n  {FAIL}: Policy validation FAILED. Deployment will be blocked.")
    else:
        print(f"\n  {PASS}: All required policy tests passed. Deployment is cleared.")
        if optional_warn:
            print(
                f"  {WARN}: {optional_warn} optional case(s) did not match — "
                "enable detectors / BLOCK in AI Guard or edit test-prompts.yaml."
            )

    print("=" * 72)
    print()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate AI Guard security policies with test prompts"
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Path to the test-prompts YAML config file",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.5,
        help="Seconds to wait between API calls (rate limiting). Default: 0.5",
    )
    args = parser.parse_args()

    cfg = get_client_config()
    if not cfg.get("api_key"):
        print("ERROR: AIGUARD_API_KEY environment variable not set.")
        return 1

    policy_id = get_policy_id()
    test_cases = load_test_cases(args.config)

    cloud = cfg["cloud"]
    endpoint = "execute-policy" if policy_id else "resolve-and-execute-policy"
    print_header()
    print(f"  Cloud:     {cloud}")
    print(f"  Endpoint:  /v1/detection/{endpoint}")
    if policy_id:
        print(f"  Policy ID: {policy_id}")
    print(f"  Tests:     {len(test_cases)}")
    print()
    print("-" * 72)
    print()

    total = 0
    passed_count = 0
    failed_count = 0
    skipped_count = 0
    optional_warn_count = 0

    with LegacyZGuardClient(cfg) as client:
        for idx, case in enumerate(test_cases, start=1):
            total += 1
            name = case.get("name", f"Test #{idx}")
            content = case.get("content", "")
            direction = case.get("direction", "IN").upper()
            expected_list = parse_expected_actions(case)
            optional = bool(case.get("optional", False))

            if not content:
                print(f"  [{SKIP}] {name} — empty content, skipping")
                skipped_count += 1
                continue

            result = scan_content(client, content, direction, policy_id)
            actual = (result.get("action") or "").upper()
            matches = actual in expected_list

            if result.get("error"):
                print_case_result(
                    idx, case, result, False, expected_list=expected_list
                )
                failed_count += 1
            elif matches:
                print_case_result(
                    idx, case, result, True, expected_list=expected_list
                )
                passed_count += 1
            elif optional:
                print_case_result(
                    idx,
                    case,
                    result,
                    False,
                    expected_list=expected_list,
                    status_override="warn",
                )
                optional_warn_count += 1
            else:
                print_case_result(
                    idx, case, result, False, expected_list=expected_list
                )
                failed_count += 1

            if idx < len(test_cases) and args.delay > 0:
                time.sleep(args.delay)

    print_summary(
        total, passed_count, failed_count, skipped_count, optional_warn_count
    )

    return 1 if failed_count > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
