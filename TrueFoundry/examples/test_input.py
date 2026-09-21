"""
Test the input-scan endpoint of the AI Guard guardrail server.

Simulates the payload TrueFoundry's AI Gateway sends for input guardrails.

Usage:
    python test_input.py "What is 2+2?"
    python test_input.py "I hate my neighbor"
"""

import os
import sys

import requests
from dotenv import load_dotenv


def main():
    load_dotenv()

    user_content = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "What is 2+2?"
    server_url = os.getenv("GUARDRAIL_SERVER_URL", "http://localhost:8000")

    payload = {
        "requestBody": {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "user", "content": user_content}
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

    print(f"Prompt: {user_content}")
    print(f"Endpoint: {server_url}/input-scan\n")

    resp = requests.post(f"{server_url}/input-scan", json=payload)

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
