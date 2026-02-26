"""
Test LiteLLM proxy with AWS Bedrock (Claude 3 Haiku) through Zscaler AI Guard.

Usage:
    python test_aws.py                    # default prompt
    python test_aws.py "Tell me a joke"   # custom prompt
"""

import json
import sys

import requests


def main():
    url = "http://localhost:4000/chat/completions"
    prompt = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "What is 2+2?"

    print(f"Model:  claude-3-haiku (AWS Bedrock)")
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
                "model": "claude-3-haiku",
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
