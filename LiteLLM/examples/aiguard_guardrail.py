"""
Zscaler AI Guard Custom Callback for LiteLLM.

Uses the zscaler-sdk-python to scan prompts (pre_call) and responses (post_call)
via the AI Guard DAS API with automatic policy resolution.

Required environment variables:
    AIGUARD_API_KEY   - Zscaler AI Guard API key
    AIGUARD_CLOUD     - Cloud region (default: us1)

Note: LiteLLM now includes a native Zscaler AI Guard guardrail that requires
no custom code. See: https://docs.litellm.ai/docs/proxy/guardrails/zscaler_ai_guard
This SDK-based callback is an alternative that uses resolve-and-execute-policy
for automatic policy resolution.
"""

import asyncio
import os
import uuid

from fastapi import HTTPException
from litellm.integrations.custom_logger import CustomLogger
from litellm._logging import verbose_proxy_logger

from zscaler.zaiguard.legacy import LegacyZGuardClientHelper


class ZscalerAIGuardCallback(CustomLogger):

    def __init__(self):
        super().__init__()
        cloud = os.environ.get("AIGUARD_CLOUD", "us1")
        self.client = LegacyZGuardClientHelper(cloud=cloud)
        verbose_proxy_logger.info(
            "ZscalerAIGuardCallback initialized (cloud=%s)", cloud
        )

    def _extract_user_content(self, data: dict) -> str:
        """Extract the last user message from the request."""
        messages = data.get("messages", [])
        for msg in reversed(messages):
            if msg.get("role") == "user":
                content = msg.get("content", "")
                if isinstance(content, list):
                    return " ".join(
                        part.get("text", "")
                        for part in content
                        if isinstance(part, dict) and part.get("type") == "text"
                    )
                return str(content)
        return ""

    def _extract_response_content(self, result) -> str:
        """Extract text content from LLM response."""
        try:
            choices = result.get("choices", []) if isinstance(result, dict) else getattr(result, "choices", [])
            for choice in choices:
                message = choice.get("message", {}) if isinstance(choice, dict) else getattr(choice, "message", {})
                content = message.get("content", "") if isinstance(message, dict) else getattr(message, "content", "")
                if content:
                    return str(content)
        except Exception:
            pass
        return ""

    def _scan(self, content: str, direction: str, transaction_id: str | None = None):
        """Call AI Guard resolve-and-execute-policy via SDK."""
        result, response, error = self.client.policy_detection.resolve_and_execute_policy(
            content=content,
            direction=direction,
            transaction_id=transaction_id,
        )
        if error:
            verbose_proxy_logger.error("AI Guard API error: %s", error)
            raise Exception(f"AI Guard API error: {error}")
        return result

    def _get_attr(self, obj, name, default=None):
        """Get attribute from object or dict."""
        if isinstance(obj, dict):
            return obj.get(name, default)
        return getattr(obj, name, default)

    def _build_block_message(self, result) -> str:
        """Build a detailed block message from the AI Guard response."""
        action = self._get_attr(result, "action", "BLOCK")
        severity = self._get_attr(result, "severity", "unknown")
        policy_name = self._get_attr(result, "policy_name") or self._get_attr(result, "policyName", "unknown")
        policy_id = self._get_attr(result, "policy_id") or self._get_attr(result, "policyId", "unknown")
        transaction_id = self._get_attr(result, "transaction_id") or self._get_attr(result, "transactionId", "unknown")
        direction = self._get_attr(result, "direction", "unknown")

        detector_responses = (
            self._get_attr(result, "detector_responses")
            or self._get_attr(result, "detectorResponses")
            or {}
        )

        blocking_detectors = []
        all_detectors = []
        for name, det in (detector_responses.items() if isinstance(detector_responses, dict) else []):
            det_action = self._get_attr(det, "action", "unknown")
            det_triggered = self._get_attr(det, "triggered", False)
            all_detectors.append(f"{name}(triggered={det_triggered}, action={det_action})")
            if str(det_action).upper() == "BLOCK":
                blocking_detectors.append(name)

        parts = [
            f"Request blocked by Zscaler AI Guard.",
            f"Action: {action} | Severity: {severity} | Direction: {direction}",
            f"Policy: {policy_name} (ID: {policy_id})",
            f"Transaction: {transaction_id}",
        ]

        if blocking_detectors:
            parts.append(f"Blocking detectors: {', '.join(blocking_detectors)}")

        if all_detectors:
            parts.append(f"All detectors: {', '.join(all_detectors)}")

        return " | ".join(parts)

    async def async_pre_call_hook(self, user_api_key_dict, cache, data, call_type):
        """Scan user prompt before sending to LLM (direction=IN)."""
        content = self._extract_user_content(data)
        if not content:
            return data

        transaction_id = str(uuid.uuid4())
        verbose_proxy_logger.info(
            "AI Guard pre_call scan (direction=IN, txn=%s)", transaction_id
        )

        result = await asyncio.to_thread(self._scan, content, "IN", transaction_id)
        action = self._get_attr(result, "action")

        verbose_proxy_logger.info(
            "AI Guard verdict: action=%s, txn=%s", action, transaction_id
        )

        if action and str(action).upper() != "ALLOW":
            msg = self._build_block_message(result)
            verbose_proxy_logger.warning("AI Guard BLOCKED (input): %s", msg)
            raise HTTPException(status_code=403, detail=msg)

        return data

    async def async_post_call_success_hook(self, data, user_api_key_dict, response):
        """Scan LLM response before returning to client (direction=OUT)."""
        content = self._extract_response_content(response)
        if not content:
            return response

        transaction_id = str(uuid.uuid4())
        verbose_proxy_logger.info(
            "AI Guard post_call scan (direction=OUT, txn=%s)", transaction_id
        )

        result = await asyncio.to_thread(self._scan, content, "OUT", transaction_id)
        action = self._get_attr(result, "action")

        verbose_proxy_logger.info(
            "AI Guard verdict: action=%s, txn=%s", action, transaction_id
        )

        if action and str(action).upper() != "ALLOW":
            msg = self._build_block_message(result)
            verbose_proxy_logger.warning("AI Guard BLOCKED (output): %s", msg)
            raise HTTPException(status_code=403, detail=msg)

        return response


proxy_handler_instance = ZscalerAIGuardCallback()
