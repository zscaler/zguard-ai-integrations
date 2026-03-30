#!/usr/bin/env python3
"""
Deploy a model from Vertex AI Model Garden to a Vertex AI endpoint.

Reads configuration from config/model-config.yaml. This is an example
deployment target — replace with your own infrastructure (AWS SageMaker,
Azure ML, on-prem, etc.).
"""

from __future__ import annotations

import os
import subprocess
import sys

import yaml
from dotenv import load_dotenv

load_dotenv()


def run(cmd: list[str], *, check: bool = True, capture: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=check, capture_output=capture, text=True)


def run_capture(cmd: list[str], *, check: bool = True) -> str:
    result = subprocess.run(cmd, check=check, capture_output=True, text=True)
    return result.stdout.strip()


def main() -> int:
    config_file = os.environ.get("CONFIG_FILE", "config/model-config.yaml")

    with open(config_file) as f:
        config = yaml.safe_load(f)

    model_id = config["model"]["huggingface_id"]
    display_name = config["model"]["display_name"]
    machine_type = config["deployment"]["machine_type"]
    accel_type = config["deployment"]["accelerator_type"]
    accel_count = str(config["deployment"]["accelerator_count"])
    region = os.environ.get("GCP_REGION", config["deployment"].get("region", "us-central1"))
    project = os.environ.get("GCP_PROJECT_ID")

    if not project:
        print("ERROR: GCP_PROJECT_ID environment variable is required.")
        return 1

    endpoint_display_name = f"{display_name}-secure"

    print("=" * 60)
    print("  Deploying Model to Vertex AI")
    print("=" * 60)
    print(f"  Model:         {model_id}")
    print(f"  Display Name:  {endpoint_display_name}")
    print(f"  Machine Type:  {machine_type}")
    print(f"  Accelerator:   {accel_type} x {accel_count}")
    print(f"  Region:        {region}")
    print(f"  Project:       {project}")
    print("=" * 60)

    run(["gcloud", "config", "set", "project", project])

    existing = run_capture([
        "gcloud", "ai", "endpoints", "list",
        f"--region={region}",
        f"--filter=displayName={endpoint_display_name}",
        "--format=value(name)",
    ], check=False)

    if existing:
        endpoint_id = existing.splitlines()[0].split("/")[-1]
        print(f"Found existing endpoint: {endpoint_id}")
        print("Cleaning up before redeploying...")

        deployed_ids = run_capture([
            "gcloud", "ai", "endpoints", "describe", endpoint_id,
            f"--region={region}",
            "--format=value(deployedModels.id)",
        ], check=False)

        for dm_id in deployed_ids.split():
            if dm_id:
                print(f"  Undeploying model: {dm_id}")
                run([
                    "gcloud", "ai", "endpoints", "undeploy-model", endpoint_id,
                    f"--region={region}",
                    f"--deployed-model-id={dm_id}",
                    "--quiet",
                ])

        print(f"  Deleting endpoint: {endpoint_id}")
        run([
            "gcloud", "ai", "endpoints", "delete", endpoint_id,
            f"--region={region}",
            "--quiet",
        ])
        print("Cleanup complete.\n")

    deploy_cmd = [
        "gcloud", "ai", "model-garden", "models", "deploy",
        f"--model={model_id}",
        f"--machine-type={machine_type}",
        f"--accelerator-type={accel_type}",
        f"--accelerator-count={accel_count}",
        f"--region={region}",
        f"--endpoint-display-name={endpoint_display_name}",
        "--accept-eula",
    ]

    hf_token = os.environ.get("HF_TOKEN")
    if hf_token:
        deploy_cmd.append(f"--hugging-face-access-token={hf_token}")

    run(deploy_cmd)

    print()
    print("Model deployed successfully.")
    print(f"Endpoint display name: {endpoint_display_name}")
    print()
    print(f"To test: python scripts/test_model.py --config {config_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
