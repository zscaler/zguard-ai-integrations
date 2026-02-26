"""
Zscaler AI Guard — Custom Guardrail Server for TrueFoundry AI Gateway.

FastAPI server that integrates with TrueFoundry's custom guardrails system.
Provides input and output scanning endpoints that call the AI Guard DAS API.

Endpoints:
  POST /input-scan   — Scan prompts before they reach the LLM
  POST /output-scan   — Scan LLM responses before returning to the user
  GET  /health        — Health check
"""

import os
import uuid

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

from zscaler.zaiguard.legacy import LegacyZGuardClientHelper

app = FastAPI(title="Zscaler AI Guard Guardrail Server")

CLOUD = os.environ.get("AIGUARD_CLOUD", "us1")
client = LegacyZGuardClientHelper(cloud=CLOUD)


class Subject(BaseModel):
    subjectId: str = ""
    subjectType: str = "user"
    subjectSlug: Optional[str] = None
    subjectDisplayName: Optional[str] = None


class RequestContext(BaseModel):
    user: Optional[Subject] = None
    metadata: Optional[dict] = None


class InputGuardrailRequest(BaseModel):
    requestBody: dict
    context: Optional[RequestContext] = None
    config: Optional[dict] = None


class OutputGuardrailRequest(BaseModel):
    requestBody: dict
    responseBody: dict
    context: Optional[RequestContext] = None
    config: Optional[dict] = None


def _get_attr(obj, name, default=None):
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _extract_last_user_message(request_body: dict) -> str:
    messages = request_body.get("messages", [])
    for msg in reversed(messages):
        if msg.get("role") == "user":
            content = msg.get("content", "")
            if isinstance(content, list):
                return " ".join(
                    p.get("text", "") for p in content
                    if isinstance(p, dict) and p.get("type") == "text"
                )
            return str(content)
    return ""


def _extract_assistant_response(response_body: dict) -> str:
    choices = response_body.get("choices", [])
    if choices:
        return choices[0].get("message", {}).get("content", "")
    return ""


def _scan(content: str, direction: str, transaction_id: str):
    result, response, error = client.policy_detection.resolve_and_execute_policy(
        content=content,
        direction=direction,
        transaction_id=transaction_id,
    )
    if error:
        raise Exception(f"AI Guard API error: {error}")
    return result


def _build_block_detail(result, direction: str, transaction_id: str) -> dict:
    action = _get_attr(result, "action", "BLOCK")
    severity = _get_attr(result, "severity", "unknown")
    policy_name = _get_attr(result, "policy_name") or _get_attr(result, "policyName", "unknown")
    policy_id = _get_attr(result, "policy_id") or _get_attr(result, "policyId", "unknown")

    detector_responses = (
        _get_attr(result, "detector_responses")
        or _get_attr(result, "detectorResponses")
        or {}
    )

    blocking = []
    detectors = {}
    for name, det in (detector_responses.items() if isinstance(detector_responses, dict) else []):
        det_action = _get_attr(det, "action", "unknown")
        det_triggered = _get_attr(det, "triggered", False)
        detectors[name] = {"action": det_action, "triggered": det_triggered}
        if str(det_action).upper() == "BLOCK":
            blocking.append(name)

    return {
        "message": "Request blocked by Zscaler AI Guard",
        "action": action,
        "severity": severity,
        "direction": direction,
        "policy_name": policy_name,
        "policy_id": policy_id,
        "transaction_id": transaction_id,
        "blocking_detectors": blocking,
        "detectors": detectors,
    }


@app.get("/health")
def health():
    return {"status": "ok", "cloud": CLOUD}


@app.post("/input-scan")
def input_scan(request: InputGuardrailRequest):
    """
    TrueFoundry input guardrail endpoint.
    Scans the user's prompt before it reaches the LLM.

    Returns:
      - null (None) if the content is allowed
      - HTTP 400 with detail if the content is blocked
    """
    content = _extract_last_user_message(request.requestBody)
    if not content:
        return None

    txn_id = str(uuid.uuid4())
    result = _scan(content, "IN", txn_id)
    action = _get_attr(result, "action")

    if action and str(action).upper() != "ALLOW":
        detail = _build_block_detail(result, "IN", txn_id)
        raise HTTPException(status_code=400, detail=detail)

    return None


@app.post("/output-scan")
def output_scan(request: OutputGuardrailRequest):
    """
    TrueFoundry output guardrail endpoint.
    Scans the LLM response before it is returned to the user.

    Returns:
      - null (None) if the content is allowed
      - HTTP 400 with detail if the content is blocked
    """
    content = _extract_assistant_response(request.responseBody)
    if not content:
        return None

    txn_id = str(uuid.uuid4())
    result = _scan(content, "OUT", txn_id)
    action = _get_attr(result, "action")

    if action and str(action).upper() != "ALLOW":
        detail = _build_block_detail(result, "OUT", txn_id)
        raise HTTPException(status_code=400, detail=detail)

    return None


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
