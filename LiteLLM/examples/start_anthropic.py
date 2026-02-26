"""
Start LiteLLM proxy with Anthropic and Zscaler AI Guard.

Required env vars: ANTHROPIC_API_KEY, AIGUARD_API_KEY
"""

import os
import subprocess
import sys

COMPOSE_DIR = os.path.dirname(os.path.abspath(__file__))


def load_dotenv():
    env_file = os.path.join(COMPOSE_DIR, ".env")
    if os.path.exists(env_file):
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    os.environ.setdefault(key.strip(), val.strip())


def main():
    load_dotenv()

    required = ["ANTHROPIC_API_KEY", "AIGUARD_API_KEY"]
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        print(f"ERROR: Missing environment variables: {', '.join(missing)}")
        sys.exit(1)

    print("Building LiteLLM + AI Guard image...")
    subprocess.run(["docker", "compose", "build"], cwd=COMPOSE_DIR, check=True)

    print("Starting LiteLLM proxy (Anthropic + AI Guard)...")
    subprocess.run(["docker", "compose", "up", "-d"], cwd=COMPOSE_DIR, check=True)

    print()
    print("LiteLLM proxy running on http://localhost:4000")
    print("  Model: claude-sonnet (Anthropic)")
    print("  AI Guard: enabled (pre_call)")
    print()
    print("Test:")
    print('  python test_anthropic.py "What is 2+2?"')
    print()
    print("Logs:  docker compose logs -f")
    print("Stop:  docker compose down")


if __name__ == "__main__":
    main()
