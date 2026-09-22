"""
Test the output-scan endpoint of the AI Guard guardrail server.

Simulates the payload TrueFoundry's AI Gateway sends for output guardrails.

Usage:
    python test_output.py "Here is your password: abc123"
    python test_output.py "The answer is 4."
"""

import os
import sys

import requests
from dotenv import load_dotenv


def main():
    load_dotenv()

    response_content = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "The answer is 4."
    server_url = os.getenv("GUARDRAIL_SERVER_URL", "http://localhost:8000")

    payload = {
        "requestBody": {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "user", "content": "What is 2+2?"}
            ],
        },
        "responseBody": {
            "id": "chatcmpl-test",
            "object": "chat.completion",
            "created": 1700000000,
            "model": "gpt-4o-mini",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": response_content,
                    },
                    "finish_reason": "stop",
                }
            ],
        },
        "config": {},
        "context": {
            "user": {
                "subjectId": "test-user",
                "subjectType": "user",
                "subjectSlug": "test@example.com",
                "subjectDisplayName": "Test User",
            },
            "metadata": {},
        },
    }

    print(f"LLM Response: {response_content}")
    print(f"Endpoint: {server_url}/output-scan\n")

    resp = requests.post(f"{server_url}/output-scan", json=payload)

    print(f"Status: {resp.status_code}")

    if resp.status_code == 200:
        body = resp.json()
        if body.get("verdict", True):
            print("Result: ALLOWED (no issues detected)")
        else:
            print("Result: BLOCKED by AI Guard")
            print(f"  Action:      {body.get('action')}")
            print(f"  Severity:    {body.get('severity')}")
            print(f"  Policy:      {body.get('policy_name')} (ID: {body.get('policy_id')})")
            print(f"  Transaction: {body.get('transaction_id')}")
            if body.get("blocking_detectors"):
                print(f"  Blocking:    {', '.join(body['blocking_detectors'])}")
            if body.get("detectors"):
                print("  Detectors:")
                for name, info in body["detectors"].items():
                    flag = " << BLOCKING" if str(info.get("action", "")).upper() == "BLOCK" else ""
                    print(f"    - {name}: triggered={info.get('triggered')}, action={info.get('action')}{flag}")
    else:
        print(f"Error: {resp.text}")


if __name__ == "__main__":
    main()
