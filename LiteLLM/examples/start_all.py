"""
Start LiteLLM proxy with all providers (Azure + AWS) and Zscaler AI Guard.

Required env vars: AZURE_OPENAI_API_KEY, AZURE_RESOURCE, AWS_ACCESS_KEY_ID,
                   AWS_SECRET_ACCESS_KEY, AWS_REGION, AIGUARD_API_KEY
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

    required = ["AZURE_OPENAI_API_KEY", "AZURE_RESOURCE", "AWS_ACCESS_KEY_ID",
                "AWS_SECRET_ACCESS_KEY", "AWS_REGION", "AIGUARD_API_KEY"]
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        print(f"ERROR: Missing environment variables: {', '.join(missing)}")
        sys.exit(1)

    env = {
        **os.environ,
        "AZURE_API_KEY": os.environ["AZURE_OPENAI_API_KEY"],
        "AZURE_API_BASE": f"https://{os.environ['AZURE_RESOURCE']}.openai.azure.com/",
        "AWS_REGION_NAME": os.environ["AWS_REGION"],
        "LITELLM_ADMIN_KEY": os.environ.get("LITELLM_ADMIN_KEY", "sk-1234"),
    }

    print("Building LiteLLM + AI Guard image...")
    subprocess.run(["docker", "compose", "build"], cwd=COMPOSE_DIR, env=env, check=True)

    print("Starting LiteLLM proxy (all providers + AI Guard)...")
    subprocess.run(
        ["docker", "compose", "-f", "docker-compose.yml", "-f", "/dev/stdin", "up", "-d"],
        cwd=COMPOSE_DIR, env=env, check=True,
        input=b"""
services:
  litellm:
    environment:
      - AZURE_API_KEY=${AZURE_API_KEY}
      - AZURE_API_BASE=${AZURE_API_BASE}
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
      - AWS_REGION_NAME=${AWS_REGION_NAME}
    volumes:
      - ./config-all.yaml:/app/config.yaml
"""
    )

    print()
    print("LiteLLM proxy running on http://localhost:4000")
    print("  Models: gpt-4o (Azure), claude-3-haiku (AWS), titan-text-lite (AWS)")
    print("  AI Guard: enabled (pre_call)")
    print()
    print("Test:")
    print('  python test_azure.py "Hello"')
    print('  python test_aws.py "Hello"')


if __name__ == "__main__":
    main()
