"""
Test LiteLLM proxy with Azure OpenAI through Zscaler AI Guard.

Usage:
    python test_azure.py                    # default prompt
    python test_azure.py "Tell me a joke"   # custom prompt
"""

import json
import sys

import requests


def main():
    url = "http://localhost:4000/chat/completions"
    prompt = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "What is 2+2?"

    print(f"Model:  gpt-4o (Azure OpenAI)")
    print(f"Prompt: {prompt}")
    print("---")

    try:
        resp = requests.post(
            url,
            headers={
                "Content-Type": "application/json",
                "Authorization": "Bearer sk-1234",
            },
            json={
                "model": "gpt-4o",
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=30,
        )
        print(json.dumps(resp.json(), indent=2))
    except requests.exceptions.ConnectionError:
        print("ERROR: Cannot connect. Start the proxy first: python start_all.py")
        sys.exit(1)


if __name__ == "__main__":
    main()
