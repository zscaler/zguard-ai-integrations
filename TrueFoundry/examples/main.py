"""
Zscaler AI Guard — Custom Guardrail Server for TrueFoundry AI Gateway.

FastAPI server that integrates with TrueFoundry's custom guardrails system.
Provides input and output scanning endpoints that call the AI Guard DAS API.

Endpoints:
  POST /input-scan   — Scan prompts before they reach the LLM
  POST /output-scan   — Scan LLM responses before returning to the user
  GET  /health        — Health check
"""

import logging
import os
import uuid

from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional

from zscaler.aiguard.legacy import LegacyZGuardClientHelper

app = FastAPI(title="Zscaler AI Guard Guardrail Server")

# uvicorn configures only its own `uvicorn.*` loggers, leaving the root logger
# without a handler — so anything logged here would fall through to Python's
# last-resort handler, which drops everything below WARNING. Attach a handler
# so our own INFO and DEBUG lines are actually emitted, and keep the level on
# our logger alone: raising the root level instead would pull in urllib3's
# per-connection chatter.
logging.basicConfig(format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("aiguard.guardrail")
logger.setLevel(os.environ.get("AIGUARD_LOG_LEVEL", "INFO").upper())

CLOUD = os.environ.get("AIGUARD_CLOUD", "us1")
client = LegacyZGuardClientHelper(cloud=CLOUD)

# The cloud decides which AI Guard the key is presented to, and it defaults to
# production. A stage key against the default cloud authenticates nowhere, so
# make the target explicit at startup rather than leaving it to be inferred.
logger.info("AI Guard target: cloud=%s url=%s", CLOUD, getattr(client, "url", "unknown"))


class Subject(BaseModel):
    """The caller TrueFoundry attributes the request to.

    Two shapes occur in practice. A human subject (``subjectType: "user"``)
    carries ``email``, and its ``subjectSlug`` is that same email. A virtual
    account (``subjectType: "virtualaccount"``) carries neither — only a slug
    naming the service account, so there is no person to attribute unless the
    calling application supplies one in ``RequestContext.metadata``.

    Undeclared fields are dropped by pydantic, so every field we may read has
    to be listed here. ``subjectDisplayName`` is kept for compatibility but
    TrueFoundry does not send it; the display name arrives nested in
    ``metadata.displayName``.
    """

    subjectId: str = ""
    subjectType: str = "user"
    subjectSlug: Optional[str] = None
    subjectDisplayName: Optional[str] = None
    email: Optional[str] = None
    userName: Optional[str] = None
    metadata: Optional[dict] = None


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


def _describe_context(context: Optional[RequestContext]) -> str:
    """Name the identity-bearing fields that arrived, without echoing values.

    TrueFoundry's context includes ``userAuthHeaderValue`` — a bearer token —
    so the object must never be logged wholesale. Listing which keys are
    populated is enough to tell "the payload has no identity" apart from "the
    payload has one under a name we do not read", which are the two shapes
    worth distinguishing when a dashboard row comes out blank.
    """
    if context is None:
        return "<absent>"

    request_metadata_keys = sorted((context.metadata or {}).keys())
    subject = context.user
    if subject is None:
        return f"user=<absent> metadataKeys={request_metadata_keys}"

    present = [
        name
        for name, value in (
            ("email", subject.email),
            ("subjectSlug", subject.subjectSlug),
            ("userName", subject.userName),
            ("subjectDisplayName", subject.subjectDisplayName),
            ("subjectId", subject.subjectId),
        )
        if value
    ]
    return (
        f"subjectType={subject.subjectType} userFieldsPresent={present} "
        f"userMetadataKeys={sorted((subject.metadata or {}).keys())} "
        f"metadataKeys={request_metadata_keys}"
    )


def _extract_user(context: Optional[RequestContext]) -> Optional[str]:
    """Best-effort end-user identity from the TrueFoundry request context.

    Prefer the identity that names a person, because that is what the AI Guard
    dashboard is for. The order matters for service-account traffic: when an
    application calls the gateway under a virtual account, ``context.user``
    describes the *application*, and the only trace of the human is whatever
    the application chose to put in ``context.metadata`` (NetApp's apps use
    ``user_email``). Taking the subject slug first would attribute every one of
    those requests to the same service account.

    Returns None when no identity is present at all, in which case AI Guard
    records no user — indistinguishable on the dashboard from the bug this
    forwarding exists to fix, so the miss is logged.
    """
    if context is None:
        return None

    subject = context.user
    subject_metadata = (subject.metadata if subject is not None else None) or {}
    request_metadata = context.metadata or {}

    candidates = (
        # A human subject carries its email directly.
        ("user.email", subject.email if subject else None),
        # Service-account traffic: the app passes the human through separately.
        ("metadata.user_email", request_metadata.get("user_email")),
        # For a human this is the email again; for a virtual account, its name.
        ("user.subjectSlug", subject.subjectSlug if subject else None),
        ("user.userName", subject.userName if subject else None),
        ("user.metadata.displayName", subject_metadata.get("displayName")),
        ("user.subjectDisplayName", subject.subjectDisplayName if subject else None),
        # Opaque id — last resort, but still better than an anonymous event.
        ("user.subjectId", subject.subjectId if subject else None),
    )

    for source, value in candidates:
        # Log every candidate, not just the winner: seeing which fields came
        # through empty is what distinguishes "TrueFoundry sent no identity"
        # from "it sent one we are reading in the wrong order".
        logger.info(
            "identity candidate: source=%s value=%s",
            source,
            value if value else "<empty>",
        )
        if value:
            logger.info(
                "end-user identity resolved: source=%s value=%s",
                source,
                value,
            )
            return value

    logger.warning(
        "no end-user identity in request context (subjectType=%s); "
        "AI Guard will record this detection with no user",
        subject.subjectType if subject else None,
    )
    return None


def _scan(content: str, direction: str, transaction_id: str, user: Optional[str] = None):
    # Log the content *length*, never the content: prompts are customer data.
    logger.debug(
        "calling AI Guard: direction=%s transactionId=%s contentLength=%d user=%s",
        direction,
        transaction_id,
        len(content),
        user if user is not None else "<none>",
    )

    result, response, error = client.policy_detection.resolve_and_execute_policy(
        content=content,
        direction=direction,
        transaction_id=transaction_id,
        user=user,
    )

    # Logged after the call returns, so it is evidence the SDK accepted the
    # `user` argument rather than just that we intended to send one: an SDK
    # without the parameter raises before reaching this line.
    logger.info(
        "AI Guard call returned: transactionId=%s user=%s hadError=%s",
        transaction_id,
        user if user is not None else "<none>",
        error is not None,
    )

    if error:
        logger.error(
            "AI Guard call failed: direction=%s transactionId=%s error=%s",
            direction, transaction_id, error,
        )
        raise Exception(f"AI Guard API error: {error}")

    # transactionId ties this log line to the row on the AI Guard dashboard,
    # which is how you tell "we never sent a user" apart from "we sent one and
    # it was not recorded".
    logger.debug(
        "AI Guard responded: transactionId=%s action=%s severity=%s "
        "policy=%s detectorErrors=%s",
        _get_attr(result, "transaction_id") or transaction_id,
        _get_attr(result, "action"),
        _get_attr(result, "severity"),
        _get_attr(result, "policy_name") or _get_attr(result, "policyName"),
        _get_attr(result, "detector_error_count"),
    )
    return result


#: Verdicts that let traffic through. DETECT is AI Guard's monitor-only action:
#: reported and logged upstream, deliberately not enforced.
ALLOWED_ACTIONS = ("ALLOW", "DETECT")


def _is_blocked(result) -> bool:
    """Fail-closed: block on anything that is not an explicit ALLOW or DETECT.

    A missing action is not permission. The API reports soft failures — most
    commonly `404 "Policy not found"` — inside an HTTP 200 with no action at
    all, so treating a falsy action as "allowed" silently disables scanning.
    """
    action = _get_attr(result, "action")
    return str(action or "").upper() not in ALLOWED_ACTIONS


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
        # TrueFoundry only surfaces `message` (logs/UI) from this body — the
        # other fields below are ignored by TrueFoundry itself and exist for
        # our own test scripts, so anything worth seeing in TrueFoundry's own
        # UI/traces has to be folded into this string.
        "message": (
            f"Blocked by Zscaler AI Guard: policy={policy_name} severity={severity} "
            f"blocking={', '.join(blocking) if blocking else 'unknown'}"
        ),
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

    Always returns HTTP 200; the policy decision is carried in the body's
    `verdict` field, not the status code. TrueFoundry treats a non-2xx as the
    guardrail itself failing (not a denial) — under "Enforce But Ignore On
    Error" or "Audit" that would silently let a real AI Guard BLOCK through.
    """
    logger.debug("/input-scan received: context=%s", _describe_context(request.context))

    content = _extract_last_user_message(request.requestBody)
    if not content:
        # No user turn to scan, so nothing reaches AI Guard and no event is
        # recorded — worth saying, or it looks like a dropped request.
        logger.debug("/input-scan: no user message found, skipping scan")
        return {"verdict": True}

    txn_id = str(uuid.uuid4())
    result = _scan(content, "IN", txn_id, user=_extract_user(request.context))

    if _is_blocked(result):
        detail = _build_block_detail(result, "IN", txn_id)
        logger.info("/input-scan BLOCKED: %s", detail)
        return {"verdict": False, **detail}

    logger.debug("/input-scan ALLOWED: transactionId=%s", txn_id)
    return {"verdict": True}


@app.post("/output-scan")
def output_scan(request: OutputGuardrailRequest):
    """
    TrueFoundry output guardrail endpoint.
    Scans the LLM response before it is returned to the user.

    Always returns HTTP 200; the policy decision is carried in the body's
    `verdict` field, not the status code. See input_scan for why.
    """
    logger.debug("/output-scan received: context=%s", _describe_context(request.context))

    content = _extract_assistant_response(request.responseBody)
    if not content:
        logger.debug("/output-scan: no assistant content found, skipping scan")
        return {"verdict": True}

    txn_id = str(uuid.uuid4())
    result = _scan(content, "OUT", txn_id, user=_extract_user(request.context))

    if _is_blocked(result):
        detail = _build_block_detail(result, "OUT", txn_id)
        logger.info("/output-scan BLOCKED: %s", detail)
        return {"verdict": False, **detail}

    logger.debug("/output-scan ALLOWED: transactionId=%s", txn_id)
    return {"verdict": True}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
