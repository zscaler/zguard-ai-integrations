"""
Zscaler AI Guard Action for NeMo Guardrails

Uses the zscaler-sdk-python to scan prompts and responses via the
AI Guard DAS API.

By default uses resolve-and-execute-policy (automatic policy selection).
Set AIGUARD_POLICY_ID to use execute-policy with a specific policy.
"""

import asyncio
import logging
import os
from enum import Enum
from typing import Any, Optional

from dotenv import load_dotenv
from nemoguardrails.actions import action

from zscaler.zaiguard.legacy import LegacyZGuardClientHelper

load_dotenv(override=False)

log = logging.getLogger(__name__)


class Direction(str, Enum):
    INBOUND = "IN"
    OUTBOUND = "OUT"


class PolicyAction(str, Enum):
    BLOCK = "BLOCK"
    ALLOW = "ALLOW"
    DETECT = "DETECT"


CLOUD = os.environ.get("AIGUARD_CLOUD", "us1")

_client: Optional[LegacyZGuardClientHelper] = None
_policy_id: Optional[int] = None

_env_policy_id = os.environ.get("AIGUARD_POLICY_ID")
if _env_policy_id:
    try:
        _policy_id = int(_env_policy_id)
    except ValueError:
        log.warning("AIGUARD_POLICY_ID=%r is not a valid integer, ignoring", _env_policy_id)


def _get_client() -> LegacyZGuardClientHelper:
    global _client
    if _client is None:
        _client = LegacyZGuardClientHelper(cloud=CLOUD)
    return _client


def _get_attr(obj, name, default=None):
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _scan_sync(content: str, direction: str, transaction_id: str | None = None):
    """Synchronous SDK call — will be run via asyncio.to_thread."""
    client = _get_client()

    if _policy_id is not None:
        result, response, error = client.policy_detection.execute_policy(
            content=content,
            direction=direction,
            policy_id=_policy_id,
            transaction_id=transaction_id,
        )
    else:
        result, response, error = client.policy_detection.resolve_and_execute_policy(
            content=content,
            direction=direction,
            transaction_id=transaction_id,
        )

    if error:
        raise Exception(f"AI Guard API error: {error}")
    return result


def _is_blocked(result) -> bool:
    action_value = str(_get_attr(result, "action", "")).upper()
    return action_value != PolicyAction.ALLOW


def _get_triggered_detectors(result) -> list[dict[str, Any]]:
    triggered = []
    detector_responses = (
        _get_attr(result, "detector_responses")
        or _get_attr(result, "detectorResponses")
        or {}
    )

    for name, det in (detector_responses.items() if isinstance(detector_responses, dict) else []):
        det_action = _get_attr(det, "action", "unknown")
        det_triggered = _get_attr(det, "triggered", False)
        if det_triggered or str(det_action).upper() == "BLOCK":
            triggered.append({
                "detector": name,
                "action": det_action,
                "severity": _get_attr(det, "severity"),
                "triggered": det_triggered,
            })

    return triggered


@action(name="CallZsAiGuardAction")
async def call_zs_ai_guard(
    prompt: Optional[str] = None,
    response: Optional[str] = None,
) -> dict[str, Any]:
    """
    Call Zscaler AI Guard to scan content for policy violations.

    Uses zscaler-sdk-python with fail-closed logic — content is blocked
    if the API call fails or returns anything other than ALLOW.
    """
    if response is not None:
        direction = Direction.OUTBOUND
        text = str(response)
    elif prompt is not None:
        direction = Direction.INBOUND
        text = str(prompt)
    else:
        raise ValueError("Either prompt or response must be provided")

    log.debug("Scanning %s content (%d chars)", direction.value, len(text))

    verdict: dict[str, Any] = {
        "blocked": True,
        "triggered_by": [],
        "transaction_id": None,
        "policy_name": None,
    }

    try:
        result = await asyncio.to_thread(
            _scan_sync, text, direction.value, None
        )

        if result is None:
            log.warning("AI Guard returned None")
            return verdict

        blocked = _is_blocked(result)
        transaction_id = (
            _get_attr(result, "transaction_id")
            or _get_attr(result, "transactionId")
        )
        policy_name = (
            _get_attr(result, "policy_name")
            or _get_attr(result, "policyName")
        )

        verdict = {
            "blocked": blocked,
            "triggered_by": _get_triggered_detectors(result) if blocked else [],
            "transaction_id": transaction_id,
            "policy_name": policy_name,
        }

        if blocked:
            detector_names = [d["detector"] for d in verdict["triggered_by"]]
            log.info(
                "Content blocked by AI Guard [txn=%s, policy=%s, detectors=%s]",
                transaction_id, policy_name, detector_names,
            )
        else:
            log.debug(
                "Content allowed by AI Guard [txn=%s, policy=%s]",
                transaction_id, policy_name,
            )

    except Exception as e:
        log.error("AI Guard scan failed: %s - %s", type(e).__name__, str(e))

    return verdict
