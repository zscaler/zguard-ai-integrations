"""
Start the Zscaler AI Guard guardrail server for TrueFoundry.

The server exposes /input-scan and /output-scan endpoints that
TrueFoundry's AI Gateway calls to scan prompts and responses.

Usage:
    python start_server.py           # start server
    python start_server.py --stop    # stop server
"""

import subprocess
import sys
import os

from dotenv import load_dotenv

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def run(cmd: list[str]) -> int:
    return subprocess.call(cmd, cwd=SCRIPT_DIR)


def check_env():
    load_dotenv(os.path.join(SCRIPT_DIR, ".env"))
    key = os.environ.get("AIGUARD_API_KEY", "")
    if not key or key.startswith("<"):
        print("WARNING: AIGUARD_API_KEY is not set.")
        print("Copy env.example to .env and fill in your credentials.")
        print()


def main():
    if "--stop" in sys.argv:
        print("Stopping guardrail server...")
        run(["docker", "compose", "down"])
        return

    check_env()

    print("Building and starting AI Guard guardrail server...")
    rc = run(["docker", "compose", "up", "-d", "--build"])
    if rc != 0:
        print("Failed to start server.")
        sys.exit(rc)

    print()
    print("AI Guard guardrail server running at http://localhost:8000")
    print()
    print("Endpoints:")
    print("  POST /input-scan    — Scan prompts (direction=IN)")
    print("  POST /output-scan   — Scan LLM responses (direction=OUT)")
    print("  GET  /health        — Health check")
    print()
    print("Test with:   python test_input.py \"What is 2+2?\"")
    print("Stop with:   python start_server.py --stop")


if __name__ == "__main__":
    main()
