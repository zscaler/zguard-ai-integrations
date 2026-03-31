#!/usr/bin/env python3
"""
Zscaler AI Guard - Google Apigee X Deployment Script

Deploys the vertex-aiguard proxy to Apigee X with AI Guard security scanning.
"""

import json
import os
import subprocess
import sys
import time
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
        self._use_kvm = True

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

    def activate_service_account(self):
        """Activate the deployment service account for gcloud/apigeecli."""
        print("== Activating service account ==")
        cmd = [
            "gcloud", "auth", "activate-service-account",
            "--key-file", self.sa_credentials,
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Failed to activate service account: {result.stderr}")
            sys.exit(1)

        with open(self.sa_credentials) as f:
            sa_email = json.load(f)["client_email"]
        print(f"✓ Activated {sa_email}")
        print()

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

    def _check_kvm_support(self) -> bool:
        """Check if the environment supports KVMs (INTERMEDIATE+ tier)."""
        auth_token = self.run_command(["gcloud", "auth", "print-access-token"])
        if not auth_token:
            return False

        url = (
            f"https://apigee.googleapis.com/v1/organizations/{self.org}"
            f"/environments/{self.env}"
        )
        resp = requests.get(url, headers={"Authorization": f"Bearer {auth_token}"})
        if resp.status_code == 200:
            env_type = resp.json().get("type", "BASE")
            if env_type == "BASE":
                return False
        return True

    def setup_kvm(self):
        """Create KVM and set entries (skipped for BASE environments)."""
        print("== Configuring environment ==")

        if not self._check_kvm_support():
            print("  Environment type is BASE (no KVM support)")
            print("  Configuration will be injected directly into the proxy bundle")
            self._use_kvm = False
            print()
            return

        self._use_kvm = True
        auth_token = self.run_command(["gcloud", "auth", "print-access-token"])
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        }
        base_url = (
            f"https://apigee.googleapis.com/v1/organizations/{self.org}"
            f"/environments/{self.env}/keyvaluemaps"
        )

        # Create KVM
        resp = requests.post(
            base_url,
            headers=headers,
            json={"name": "private", "encrypted": True},
        )
        if resp.status_code == 201:
            print("✓ Created encrypted KVM 'private'")
        elif resp.status_code == 409:
            print("✓ KVM 'private' already exists")
        else:
            print(f"⚠ KVM create returned {resp.status_code}: {resp.text}")

        entries = {
            "aiguard.apikey": self.aiguard_api_key,
            "aiguard.cloud": self.aiguard_cloud,
            "aiguard.policyid": self.aiguard_policy_id,
            "vertex.project": self.vertex_project,
            "vertex.model": self.vertex_model,
        }

        entries_url = f"{base_url}/private/entries"
        for key, value in entries.items():
            # Delete existing entry (ignore errors)
            requests.delete(f"{entries_url}/{key}", headers=headers)
            # Create entry
            resp = requests.post(
                entries_url, headers=headers, json={"name": key, "value": value}
            )
            if resp.status_code in (200, 201):
                print(f"  ✓ Set {key}")
            else:
                print(f"  ⚠ Failed to set {key}: {resp.status_code}")

        print("✓ KVM configured")
        print()

    def verify_vertex_permissions(self):
        """Verify Apigee runtime SA has Vertex AI permissions."""
        print("== Verifying Vertex AI access ==")

        auth_token = self.run_command(["gcloud", "auth", "print-access-token"])
        if not auth_token:
            print("⚠ Could not get auth token, skipping Vertex AI check")
            print()
            return

        with open(self.sa_credentials) as f:
            deployer_sa = json.load(f)["client_email"]

        # Grant Vertex AI user role via REST API (avoids gcloud interactive prompts)
        print(f"Service Account: {deployer_sa}")
        print(f"Ensuring roles/aiplatform.user on {self.project_id}...")

        url = f"https://cloudresourcemanager.googleapis.com/v1/projects/{self.project_id}:getIamPolicy"
        headers = {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        }
        resp = requests.post(url, headers=headers, json={})

        if resp.status_code != 200:
            print(f"⚠ Could not check IAM policy: {resp.status_code}")
            print()
            return

        policy = resp.json()
        member = f"serviceAccount:{deployer_sa}"
        role = "roles/aiplatform.user"
        already_has = False

        for binding in policy.get("bindings", []):
            if binding.get("role") == role and member in binding.get("members", []):
                already_has = True
                break

        if already_has:
            print("✓ SA already has Vertex AI access")
        else:
            for binding in policy.get("bindings", []):
                if binding.get("role") == role:
                    binding["members"].append(member)
                    break
            else:
                policy.setdefault("bindings", []).append(
                    {"role": role, "members": [member]}
                )

            set_url = f"https://cloudresourcemanager.googleapis.com/v1/projects/{self.project_id}:setIamPolicy"
            set_resp = requests.post(
                set_url, headers=headers, json={"policy": policy}
            )
            if set_resp.status_code == 200:
                print("✓ Granted roles/aiplatform.user")
            else:
                print(f"⚠ Could not grant role: {set_resp.status_code}")

        print()

    def _generate_config_policy(self) -> str:
        """Generate an AssignMessage policy that injects config as flow variables.

        Used instead of KVM-GetConfig for BASE environments that lack KVM support.
        """
        policy_id = self.aiguard_policy_id if self.aiguard_policy_id else ""
        return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<AssignMessage name="KVM-GetConfig">
  <AssignVariable>
    <Name>private.aiguard.apikey</Name>
    <Value>{self.aiguard_api_key}</Value>
  </AssignVariable>
  <AssignVariable>
    <Name>private.aiguard.cloud</Name>
    <Value>{self.aiguard_cloud}</Value>
  </AssignVariable>
  <AssignVariable>
    <Name>private.aiguard.policyid</Name>
    <Value>{policy_id}</Value>
  </AssignVariable>
  <AssignVariable>
    <Name>private.vertex.project</Name>
    <Value>{self.vertex_project}</Value>
  </AssignVariable>
  <AssignVariable>
    <Name>private.vertex.model</Name>
    <Value>{self.vertex_model}</Value>
  </AssignVariable>
</AssignMessage>"""

    def package_proxy(self):
        """Package the proxy into a zip file."""
        print("== Packaging proxy ==")

        zip_path = Path(__file__).parent / "vertex-aiguard.zip"
        apiproxy_dir = Path(__file__).parent / "apiproxy"

        if zip_path.exists():
            zip_path.unlink()

        use_kvm = getattr(self, "_use_kvm", True)

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file in apiproxy_dir.rglob("*"):
                if file.is_file():
                    arcname = file.relative_to(Path(__file__).parent)

                    if not use_kvm and file.name == "KVM-GetConfig.xml":
                        zipf.writestr(
                            str(arcname), self._generate_config_policy()
                        )
                        print("  Replaced KVM-GetConfig with inline configuration")
                    else:
                        zipf.write(file, arcname)

        print(f"✓ Created {zip_path.name}")
        print()

        return zip_path

    def deploy_proxy(self, zip_path: Path):
        """Deploy proxy to Apigee."""
        print("== Deploying to Apigee ==")

        auth_token = self.run_command(["gcloud", "auth", "print-access-token"])
        if not auth_token:
            print("❌ Failed to get auth token")
            sys.exit(1)

        headers = {"Authorization": f"Bearer {auth_token}"}

        # Import proxy
        url = f"https://apigee.googleapis.com/v1/organizations/{self.org}/apis?name=vertex-aiguard&action=import"
        with open(zip_path, "rb") as f:
            files = {"file": ("vertex-aiguard.zip", f, "application/zip")}
            response = requests.post(url, headers=headers, files=files)

        if response.status_code != 200:
            print(f"❌ Failed to import proxy: {response.status_code}")
            print(response.text)
            sys.exit(1)

        revision = response.json().get("revision")
        print(f"✓ Imported as revision {revision}")

        with open(self.sa_credentials) as f:
            sa_email = json.load(f)["client_email"]

        print(f"Deploying revision {revision} to {self.env}...")

        # Deploy via Apigee API — try with SA first, fall back without
        deploy_url = (
            f"https://apigee.googleapis.com/v1/organizations/{self.org}"
            f"/environments/{self.env}/apis/vertex-aiguard/revisions/{revision}"
            f"/deployments?override=true&serviceAccount={sa_email}"
        )
        resp = requests.post(deploy_url, headers=headers)

        if resp.status_code == 403:
            print("  SA actAs permission missing, deploying without SA binding...")
            deploy_url = (
                f"https://apigee.googleapis.com/v1/organizations/{self.org}"
                f"/environments/{self.env}/apis/vertex-aiguard/revisions/{revision}"
                f"/deployments?override=true"
            )
            resp = requests.post(deploy_url, headers=headers)

        if resp.status_code not in (200, 202):
            print(f"❌ Deployment failed: {resp.status_code}")
            print(resp.text)
            sys.exit(1)

        print("✓ Deployment initiated")

        # Wait for deployment to complete
        for i in range(30):
            time.sleep(5)
            check_url = (
                f"https://apigee.googleapis.com/v1/organizations/{self.org}"
                f"/environments/{self.env}/apis/vertex-aiguard/revisions/{revision}"
                f"/deployments"
            )
            check_resp = requests.get(check_url, headers=headers)
            if check_resp.status_code == 200:
                state = check_resp.json().get("state", "")
                if state == "READY":
                    print("✓ Proxy is READY")
                    break
                print(f"  Status: {state}...")
            if i == 29:
                print("⚠ Timed out waiting for deployment, check Apigee console")

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
        self.activate_service_account()
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
