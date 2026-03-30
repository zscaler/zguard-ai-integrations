# n8n Integration with Zscaler AI Guard

This document provides instructions for using the Zscaler AI Guard community node within n8n to add a layer of security to your automation workflows. This node allows you to scan prompts and responses for threats directly within a workflow.

## Coverage

> For detection categories and use cases, see the [Zscaler AI Guard documentation](https://help.zscaler.com/ai-guard).

| Scanning Phase | Supported | Description |
|----------------|:---------:|-------------|
| Prompt | ✅ | "Prompt Scan" operation scans user input for threats (direction: `IN`) |
| Response | ✅ | "Response Scan" operation scans AI-generated responses (direction: `OUT`) |
| Dual Scan | ✅ | "Dual Scan" operation scans both prompt and response in sequence |
| Streaming | ❌ | Node processes complete responses after generation |
| Pre-tool call | ❌ | Workflow-based — not automatic tool interception |
| Post-tool call | ❌ | Tool result scanning not implemented |

---

## Prerequisites

* An active n8n instance (Cloud or self-hosted) — [Setup Docs](https://docs.n8n.io/hosting/installation/docker/).
* Instance owner permissions to install community nodes.
* An active Zscaler AI Guard license.
* A Zscaler AI Guard **API Key** (Bearer token).

---

## Configuration Steps

### Step 1: Install the Community Node

1.  Open your n8n instance.
2.  Navigate to **Settings → Community Nodes**.
3.  Search for `@bdzscaler/n8n-nodes-aiguard` or visit the [npm package page](https://www.npmjs.com/package/@bdzscaler/n8n-nodes-aiguard).
4.  Click **Install**.
5.  Restart your n8n instance if prompted for the installation to take effect.

### Step 2: Create Zscaler AI Guard Credentials

1.  In your n8n instance, go to the **Credentials** section from the left-hand menu.
2.  Click **Add Credential**.
3.  Search for and select **"Zscaler AI Guard API"**.
4.  Fill in the credential details:
    * **API Key:** Your Zscaler AI Guard API key (Bearer token).
    * **Cloud:** The Zscaler cloud for your tenancy (default: `us1`). Used to build the API URL: `https://api.{cloud}.zseclipse.net`.
    * **Override URL:** (Optional) Override the API base URL entirely. When set, the Cloud field is ignored. Equivalent to `AIGUARD_OVERRIDE_URL` in the [zscaler-sdk-python](https://github.com/zscaler/zscaler-sdk-python).
    * **Policy ID:** (Optional) A specific AI Guard policy ID. When omitted, the API automatically resolves the policy linked to your API key via `resolve-and-execute-policy`.
5.  Click **Test** to validate the connection before saving.

### Step 3: Use the AI Guard Node in a Workflow

1.  Create a new workflow or open an existing one.
2.  Click the `+` icon to add a new node.
3.  Search for **"AI Guard"** or **"Zscaler"** and add it to your canvas.
4.  In the node's properties panel, select the credential you created in Step 2.
5.  Choose an **Operation** from the dropdown menu:
    * **Prompt Scan:** Scans user input/prompts for security threats (direction: `IN`).
    * **Response Scan:** Scans AI-generated responses for policy violations (direction: `OUT`).
    * **Dual Scan:** Scans both a prompt and a response sequentially. If the prompt is blocked, the response scan is skipped.
6.  Enter content to scan in the **Content** field (plain text or an n8n expression referencing data from a previous node).

### Additional Options

The node exposes several optional settings under **Additional Options** → **Add Option**:

| Option | Default | Description |
|--------|---------|-------------|
| Policy ID Override | *(empty)* | Override the credential-level policy ID for this node |
| Transaction ID | *(empty)* | Custom transaction ID for tracking; omitted if empty |
| Timeout (ms) | `30000` | Request timeout in milliseconds |
| Environment | *(empty)* | Environment tag (e.g. `production`) included in output metadata |

---

## API Endpoints

The node automatically selects the correct AI Guard DAS API endpoint based on configuration:

| Scenario | Endpoint |
|----------|----------|
| Policy ID provided | `POST /v1/detection/execute-policy` |
| No Policy ID (default) | `POST /v1/detection/resolve-and-execute-policy` |

When no Policy ID is configured, the API automatically resolves the policy linked to your API key.

---

## Implementation Details

The node makes direct HTTPS calls to the Zscaler AI Guard API using Node.js's native `https` module, matching the authentication and request format of the [zscaler-sdk-python](https://github.com/zscaler/zscaler-sdk-python):

* **Authentication:** `Authorization: Bearer <API_KEY>` header
* **Headers:** `Content-Type: application/json`, `Accept: application/json`
* **Request body:** `{ "content": "...", "direction": "IN"|"OUT" }` with optional `policyId` and `transactionId` fields
* **Fail-closed behavior:** On internal errors, the node returns `action: BLOCK` when "Continue On Fail" is enabled, ensuring security is never silently bypassed

The node source code is maintained in a standalone repository and published as an npm package independently from this integrations repository.

---

## Verification

Run your workflow. The AI Guard node will send the specified content to the Zscaler AI Guard API for scanning. The output includes the full API response:

* `action` — The verdict: `ALLOW`, `BLOCK`, or `DETECT`
* `severity` — Severity level (e.g. `CRITICAL`)
* `detectorResponses` — Per-detector results (toxicity, PII, secrets, etc.)
* `policyId` / `policyName` — The policy that was applied
* `maskedContent` — Content with sensitive data masked (when applicable)
* `transactionId` — Unique ID for the scan transaction

Use the `action` field in subsequent nodes (e.g., an IF node) to control the workflow's logic.

You can monitor detailed logs of all scans and security events in your Zscaler dashboard.

## Example Workflows

Find workflow templates in the `workflows/` directory. Have a useful template to share? We welcome contributions via pull request!

## Links

* npm package: <https://www.npmjs.com/package/@bdzscaler/n8n-nodes-aiguard>
* Source code: <https://github.com/zscaler/n8n-nodes-aiguard>
* Zscaler AI Guard docs: <https://help.zscaler.com/ai-guard>
* Zscaler SDK (Python): <https://github.com/zscaler/zscaler-sdk-python>
