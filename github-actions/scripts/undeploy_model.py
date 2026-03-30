#!/usr/bin/env python3
"""
Undeploy and clean up a Vertex AI model endpoint to stop incurring GPU costs.

Usage:
    GCP_PROJECT_ID=your-project GCP_REGION=us-central1 python scripts/undeploy_model.py
"""

from __future__ import annotations

import os
import subprocess
import sys

import yaml
from dotenv import load_dotenv

load_dotenv()


def run_capture(cmd: list[str], *, check: bool = True) -> str:
    result = subprocess.run(cmd, check=check, capture_output=True, text=True)
    return result.stdout.strip()


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def main() -> int:
    config_file = os.environ.get("CONFIG_FILE", "config/model-config.yaml")

    with open(config_file) as f:
        config = yaml.safe_load(f)

    display_name = config["model"]["display_name"]
    endpoint_display_name = f"{display_name}-secure"
    region = os.environ.get("GCP_REGION", config["deployment"].get("region", "us-central1"))
    project = os.environ.get("GCP_PROJECT_ID")

    if not project:
        print("ERROR: GCP_PROJECT_ID environment variable is required.")
        return 1

    print(f"Looking for endpoint: {endpoint_display_name}")
    print(f"  Project: {project}")
    print(f"  Region:  {region}")

    raw = run_capture([
        "gcloud", "ai", "endpoints", "list",
        f"--project={project}",
        f"--region={region}",
        f"--filter=displayName~{endpoint_display_name}",
        "--format=value(name)",
    ], check=False)

    if not raw:
        print("No matching endpoints found. Nothing to clean up.")
        return 0

    endpoint_ids = [line.split("/")[-1] for line in raw.splitlines() if line.strip()]

    for endpoint_id in endpoint_ids:
        print(f"Found endpoint: {endpoint_id}")
        print("Undeploying all models from the endpoint...")

        deployed_ids = run_capture([
            "gcloud", "ai", "endpoints", "describe", endpoint_id,
            f"--project={project}",
            f"--region={region}",
            "--format=value(deployedModels.id)",
        ], check=False)

        for dm_id in deployed_ids.split():
            if dm_id:
                print(f"  Undeploying model: {dm_id}")
                run([
                    "gcloud", "ai", "endpoints", "undeploy-model", endpoint_id,
                    f"--project={project}",
                    f"--region={region}",
                    f"--deployed-model-id={dm_id}",
                    "--quiet",
                ])

        print(f"Deleting endpoint: {endpoint_id}")
        run([
            "gcloud", "ai", "endpoints", "delete", endpoint_id,
            f"--project={project}",
            f"--region={region}",
            "--quiet",
        ])
        print(f"Endpoint {endpoint_id} deleted.")

    print("All matching endpoints cleaned up. GPU costs stopped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
