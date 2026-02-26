"""
Start the Portkey AI Gateway locally using Docker Compose.

The gateway listens on http://localhost:8787 and proxies requests to any
supported LLM provider (Anthropic, AWS Bedrock, Azure OpenAI, Vertex AI, etc.).
AI Guard guardrails are configured per-request via the x-portkey-config header.

Usage:
    python start_portkey.py          # start gateway
    python start_portkey.py --stop   # stop gateway
"""

import subprocess
import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def run(cmd: list[str]) -> int:
    return subprocess.call(cmd, cwd=SCRIPT_DIR)


def main():
    if "--stop" in sys.argv:
        print("Stopping Portkey gateway...")
        run(["docker", "compose", "down"])
        return

    print("Starting Portkey AI Gateway...")
    rc = run(["docker", "compose", "up", "-d", "--pull", "always"])
    if rc != 0:
        print("Failed to start gateway.")
        sys.exit(rc)

    print()
    print("Portkey gateway is running at http://localhost:8787")
    print()
    print("Test with any of the provider scripts:")
    print("  python test_anthropic.py \"What is 2+2?\"")
    print("  python test_aws.py \"What is 2+2?\"")
    print("  python test_azure.py \"What is 2+2?\"")
    print("  python test_vertex.py \"What is 2+2?\"")
    print()
    print("Stop with:  python start_portkey.py --stop")


if __name__ == "__main__":
    main()
