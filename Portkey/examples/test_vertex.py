"""
Portkey + Zscaler AI Guard — Google Vertex AI test.

Flow:
  1. Pre-scan the prompt with AI Guard SDK (direction=IN).
  2. If allowed, send through Portkey gateway to Vertex AI.
  3. Post-scan the LLM response with AI Guard SDK (direction=OUT).
"""

import json
import os
import sys
import uuid

import requests
from dotenv import load_dotenv

from aiguard_scanner import scan_content, print_scan_result


def send_via_portkey(user_content: str) -> dict:
    """Send a chat completion through the Portkey gateway."""
    env = {
        "project_id": os.getenv("GOOGLE_CLOUD_PROJECT_ID"),
        "region": os.getenv("GOOGLE_CLOUD_REGION"),
        "service_account_file": os.getenv("VERTEX_SERVICE_ACCOUNT_FILE"),
    }

    missing = [k for k, v in env.items() if not v]
    if missing:
        return {"error": f"Missing env vars: {', '.join(missing)}"}

    sa_path = os.path.expanduser(env["service_account_file"])
    if not os.path.isfile(sa_path):
        return {"error": f"Service account file not found: {sa_path}"}

    with open(sa_path) as f:
        sa_json = json.load(f)

    config = {
        "provider": "vertex-ai",
        "vertex_project_id": env["project_id"],
        "vertex_region": env["region"],
        "vertex_service_account_json": sa_json,
    }

    headers = {
        "Content-Type": "application/json",
        "x-portkey-config": json.dumps(config),
    }

    data = {
        "messages": [{"role": "user", "content": user_content}],
        "model": "gemini-2.5-flash",
    }

    portkey_url = os.getenv("PORTKEY_GATEWAY_URL", "http://127.0.0.1:8787")
    resp = requests.post(f"{portkey_url}/v1/chat/completions", headers=headers, json=data)
    return resp.json()


def extract_response_content(result: dict) -> str:
    choices = result.get("choices", [])
    if choices:
        return choices[0].get("message", {}).get("content", "")
    return ""


def main():
    load_dotenv()

    user_content = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "What is 2+2?"
    txn_id = str(uuid.uuid4())

    print(f"Prompt: {user_content}")
    print(f"Transaction: {txn_id}\n")

    print("=== Step 1: AI Guard Pre-Scan (direction=IN) ===")
    pre_result = scan_content(user_content, "IN", txn_id)
    print_scan_result(pre_result)

    if pre_result.get("error"):
        print("\nScan error — aborting.")
        return

    if str(pre_result.get("action", "")).upper() != "ALLOW":
        print(f"\nPrompt BLOCKED by AI Guard — not sending to LLM.")
        return

    print("\n=== Step 2: Portkey Gateway Request (Vertex AI) ===")
    portkey_result = send_via_portkey(user_content)

    if "error" in portkey_result:
        print(f"  Gateway error: {json.dumps(portkey_result, indent=2)}")
        return

    response_text = extract_response_content(portkey_result)
    print(f"  LLM Response: {response_text[:200]}{'...' if len(response_text) > 200 else ''}")

    print("\n=== Step 3: AI Guard Post-Scan (direction=OUT) ===")
    post_result = scan_content(response_text, "OUT", txn_id)
    print_scan_result(post_result)

    if str(post_result.get("action", "")).upper() != "ALLOW":
        print(f"\nResponse BLOCKED by AI Guard — not returning to user.")
        return

    print("\n=== Final Response ===")
    print(response_text)


if __name__ == "__main__":
    main()
