#!/usr/bin/env python3
"""
Zscaler AI Guard - Google Apigee X Deployment Script

Deploys the vertex-aiguard proxy to Apigee X with AI Guard security scanning.
"""

import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Optional

try:
    from dotenv import load_dotenv
    import requests
except ImportError:
    print("❌ Required packages not installed.")
    print("Install with: pip install python-dotenv requests")
    sys.exit(1)


class ApigeeDeployer:
    """Handles deployment of AI Guard proxy to Apigee X."""

    def __init__(self):
        """Initialize deployer and load configuration."""
        # Load environment variables
        env_file = Path(__file__).parent / ".env"
        if env_file.exists():
            load_dotenv(env_file)

        # Required configuration
        self.org = os.getenv("APIGEE_ORG")
        self.env = os.getenv("APIGEE_ENV", "eval")
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT")

        # AI Guard configuration
        self.aiguard_api_key = os.getenv("AIGUARD_API_KEY")
        self.aiguard_cloud = os.getenv("AIGUARD_CLOUD", "us1")
        self.aiguard_policy_id = os.getenv("AIGUARD_POLICY_ID", "760")

        # Vertex AI configuration
        self.vertex_project = self.project_id
        self.vertex_model = os.getenv("VERTEX_MODEL", "gemini-2.5-flash")

        # Service account
        self.sa_credentials = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

        # Validate required variables
        self._validate_config()

    def _validate_config(self):
        """Validate required configuration."""
        errors = []

        if not self.org:
            errors.append("APIGEE_ORG is not set")
        if not self.aiguard_api_key:
            errors.append("AIGUARD_API_KEY is not set")
        if not self.sa_credentials or not Path(self.sa_credentials).exists():
            errors.append(
                f"GOOGLE_APPLICATION_CREDENTIALS not found: {self.sa_credentials}"
            )

        if errors:
            print("❌ Configuration errors:")
            for error in errors:
                print(f"   - {error}")
            sys.exit(1)

    def print_config(self):
        """Print deployment configuration."""
        print("=" * 50)
        print("Deploying vertex-aiguard to Apigee")
        print("=" * 50)
        print(f"Organization: {self.org}")
        print(f"Environment: {self.env}")
        print(f"Project: {self.project_id}")
        print(f"Vertex Model: {self.vertex_model}")
        print(f"AI Guard Cloud: {self.aiguard_cloud}")
        print(f"AI Guard Policy: {self.aiguard_policy_id}")
        print()

    def run_command(self, cmd: list, capture_output: bool = True) -> Optional[str]:
        """Run shell command and return output."""
        try:
            result = subprocess.run(
                cmd, capture_output=capture_output, text=True, check=True
            )
            return result.stdout.strip() if capture_output else None
        except subprocess.CalledProcessError as e:
            if capture_output:
                print(f"❌ Command failed: {' '.join(cmd)}")
                print(f"Error: {e.stderr}")
            return None

    def setup_kvm(self):
        """Create KVM and set entries."""
        print("== Setting up KVM ==")

        # Create KVM (ignore error if exists)
        create_cmd = [
            "apigeecli",
            "kvms",
            "create",
            "-o",
            self.org,
            "-e",
            self.env,
            "--name",
            "private",
            "--encrypted",
        ]
        result = subprocess.run(create_cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ Created encrypted KVM 'private'")
        else:
            print("✓ KVM 'private' already exists")

        # Set KVM entries
        print("Setting KVM entries...")
        entries = {
            "aiguard.apikey": self.aiguard_api_key,
            "aiguard.cloud": self.aiguard_cloud,
            "aiguard.policyid": self.aiguard_policy_id,
            "vertex.project": self.vertex_project,
            "vertex.model": self.vertex_model,
        }

        for key, value in entries.items():
            # Delete if exists (ignore errors)
            delete_cmd = [
                "apigeecli",
                "kvms",
                "entries",
                "delete",
                "-o",
                self.org,
                "-e",
                self.env,
                "--map",
                "private",
                "--key",
                key,
            ]
            subprocess.run(delete_cmd, capture_output=True)

            # Create entry
            create_cmd = [
                "apigeecli",
                "kvms",
                "entries",
                "create",
                "-o",
                self.org,
                "-e",
                self.env,
                "--map",
                "private",
                "--key",
                key,
                "--value",
                value,
            ]
            self.run_command(create_cmd, capture_output=False)

        print("✓ KVM configured")
        print()

    def verify_vertex_permissions(self):
        """Verify Apigee runtime SA has Vertex AI permissions."""
        print("== Verifying Vertex AI access ==")

        # Get runtime SA
        cmd = [
            "gcloud",
            "apigee",
            "environments",
            "describe",
            self.env,
            "--organization",
            self.org,
            "--format",
            "value(properties.runtimeServiceAccount)",
        ]
        runtime_sa = self.run_command(cmd)

        if not runtime_sa:
            print("⚠ Could not determine runtime SA")
            print()
            return

        print(f"Runtime SA: {runtime_sa}")
        print(f"Checking if SA has roles/aiplatform.user on {self.project_id}...")

        # Check IAM policy
        cmd = [
            "gcloud",
            "projects",
            "get-iam-policy",
            self.project_id,
            "--flatten",
            "bindings[].members",
            "--filter",
            f"bindings.members:serviceAccount:{runtime_sa} AND bindings.role:roles/aiplatform.user",
            "--format",
            "value(bindings.role)",
        ]
        has_role = self.run_command(cmd)

        if has_role:
            print("✓ Runtime SA has Vertex AI access")
        else:
            print("⚠ Runtime SA needs roles/aiplatform.user")

            if os.getenv("SKIP_IAM_GRANT") == "1":
                print("  SKIP_IAM_GRANT=1, skipping automatic grant")
                print(f"  Grant manually with:")
                print(f"  gcloud projects add-iam-policy-binding {self.project_id} \\")
                print(f"    --member=serviceAccount:{runtime_sa} \\")
                print(f"    --role=roles/aiplatform.user")
            else:
                print("  Granting automatically...")
                cmd = [
                    "gcloud",
                    "projects",
                    "add-iam-policy-binding",
                    self.project_id,
                    "--member",
                    f"serviceAccount:{runtime_sa}",
                    "--role",
                    "roles/aiplatform.user",
                    "--condition",
                    "None",
                ]
                self.run_command(cmd, capture_output=False)
                print("✓ Granted roles/aiplatform.user to runtime SA")

        print()

    def package_proxy(self):
        """Package the proxy into a zip file."""
        print("== Packaging proxy ==")

        zip_path = Path(__file__).parent / "vertex-aiguard.zip"
        apiproxy_dir = Path(__file__).parent / "apiproxy"

        # Remove existing zip
        if zip_path.exists():
            zip_path.unlink()

        # Create zip file
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file in apiproxy_dir.rglob("*"):
                if file.is_file():
                    arcname = file.relative_to(Path(__file__).parent)
                    zipf.write(file, arcname)

        print(f"✓ Created {zip_path.name}")
        print()

        return zip_path

    def deploy_proxy(self, zip_path: Path):
        """Deploy proxy to Apigee."""
        print("== Deploying to Apigee ==")

        # Get auth token
        auth_token = self.run_command(["gcloud", "auth", "print-access-token"])
        if not auth_token:
            print("❌ Failed to get auth token")
            sys.exit(1)

        # Import proxy
        url = f"https://apigee.googleapis.com/v1/organizations/{self.org}/apis?name=vertex-aiguard&action=import"
        headers = {"Authorization": f"Bearer {auth_token}"}

        with open(zip_path, "rb") as f:
            files = {"file": ("vertex-aiguard.zip", f, "application/zip")}
            response = requests.post(url, headers=headers, files=files)

        if response.status_code != 200:
            print(f"❌ Failed to import proxy: {response.status_code}")
            print(response.text)
            sys.exit(1)

        revision = response.json().get("revision")
        print(f"✓ Imported as revision {revision}")

        # Deploy proxy
        with open(self.sa_credentials) as f:
            sa_email = json.load(f)["client_email"]

        print(f"Deploying revision {revision} with SA: {sa_email}...")

        cmd = [
            "apigeecli",
            "apis",
            "deploy",
            "-o",
            self.org,
            "-e",
            self.env,
            "-n",
            "vertex-aiguard",
            "--rev",
            revision,
            "--sa",
            sa_email,
            "--ovr",
            "--wait",
        ]
        self.run_command(cmd, capture_output=False)

        print()
        print("=" * 50)
        print("✅ Deployment complete!")
        print("=" * 50)
        print()

    def print_test_commands(self):
        """Print test commands."""
        print("Test with:")
        print()
        print("# Safe prompt (should pass)")
        print("curl -i https://$APIGEE_HOSTNAME/vertex \\")
        print('  -H "Content-Type: application/json" \\')
        print(
            '  -d \'{"contents":[{"role":"user","parts":[{"text":"Write a haiku"}]}]}\''
        )
        print()
        print("# Toxic prompt (should block)")
        print("curl -i https://$APIGEE_HOSTNAME/vertex \\")
        print('  -H "Content-Type: application/json" \\')
        print(
            '  -d \'{"contents":[{"role":"user","parts":[{"text":"I hate my neighbor"}]}]}\''
        )
        print()

    def deploy(self):
        """Run complete deployment process."""
        self.print_config()
        self.setup_kvm()
        self.verify_vertex_permissions()
        zip_path = self.package_proxy()
        self.deploy_proxy(zip_path)
        self.print_test_commands()


def main():
    """Main entry point."""
    try:
        deployer = ApigeeDeployer()
        deployer.deploy()
    except KeyboardInterrupt:
        print("\n❌ Deployment cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Deployment failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
