# Jenkins — Zscaler AI Guard Policy Validation

This integration adds **Zscaler AI Guard** policy validation to a Jenkins Declarative Pipeline. When monitored files change, the pipeline runs `scripts/scan_policy.py` against `config/test-prompts.yaml` using `zscaler-sdk-python` (`LegacyZGuardClient`) — the same API as the [GitHub Actions](../../github-actions/) integration (`resolve-and-execute-policy` / optional `execute-policy`).

The included **Deploy Model to Vertex AI** and **Test Model Endpoint** stages are optional examples (same pattern as before); use **SKIP_DEPLOY** or run only on branches without `main` if you do not use GCP.

---

## Coverage

| Phase | Description |
|-------|-------------|
| Policy validation (IN / OUT) | Synthetic prompts/responses in `config/test-prompts.yaml` |
| CI gate | Non-zero exit if any **required** test mismatches; `optional: true` → **WARN** only |
| Vertex deploy | Example only — requires GCP credentials |

> For detector categories, see [Zscaler AI Guard](https://help.zscaler.com/ai-guard).

---

## Prerequisites

- Jenkins 2.400+ with [Pipeline](https://plugins.jenkins.io/workflow-aggregator/)
- Python 3.11+ on the agent
- For Vertex stages: `gcloud` CLI on the agent
- Zscaler AI Guard API key

---

## Jenkins credentials

| Credential ID | Type | Required for scan | Description |
|---------------|------|:-----------------:|-------------|
| `aiguard-api-key` | Secret text | Yes | AI Guard Bearer token (`AIGUARD_API_KEY`) |

**Optional cloud / policy ID** are passed as **build parameters** (`AIGUARD_CLOUD`, `AIGUARD_POLICY_ID`) so you do not need extra credentials for defaults. To bind them as Secret text instead, add `withCredentials` entries and `export` them in the scan stage (same variable names).

Vertex example (deploy / test only):

| Credential ID | Type |
|-----------------|------|
| `gcp-sa-key` | Secret file (JSON) |
| `gcp-project-id` | Secret text |
| `gcp-region` | Secret text |
| `hf-token` | Secret text |

If you rename credential IDs, update the `Jenkinsfile` accordingly.

**Do not** create `AIGUARD_CLOUD` as an empty Jenkins secret — empty values are treated as unset and default to `us1` in `scan_policy.py`, but avoid blank secrets for clarity.

---

## Monitored paths (triggers scan stage)

The **Detect Changes** stage sets `SCAN_NEEDED` when the latest changeset touches any of:

- `config/model-config.yaml`
- `config/test-prompts.yaml`
- `scripts/scan_policy.py`
- `Jenkinsfile`

Use **Build with Parameters** → **FORCE_RUN** for the first run or when SCM polling does not see a diff.

---

## Test suite

Edit **`config/test-prompts.yaml`**:

- `expected_action`: `ALLOW`, `BLOCK`, `DETECT`, or a list (e.g. `[BLOCK, DETECT]`)
- `optional: true`: mismatch logs **WARN**; build still succeeds
- `settings.scan_enabled: false`: scanner exits 0 immediately

See [github-actions/README.md](../../github-actions/README.md) for full semantics, PII false-positive notes, and log field meanings (**Triggered** vs **Blocking**).

---

## Local run

From this directory:

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
export AIGUARD_API_KEY="your-key"
export AIGUARD_CLOUD=us1   # optional
python scripts/scan_policy.py --config config/test-prompts.yaml
```

---

## Repository layout

```
declarative-pipeline/
├── Jenkinsfile
├── config/
│   ├── model-config.yaml    # Vertex model — triggers pipeline when changed
│   └── test-prompts.yaml    # AI Guard policy test cases
├── scripts/
│   ├── scan_policy.py        # AI Guard validation (zscaler-sdk-python)
│   ├── deploy_model.sh
│   ├── test_model.py
│   └── undeploy_model.sh
├── requirements.txt
├── .env.example
└── README.md
```

Point your Jenkins job **workspace root** at `declarative-pipeline` (or the repo root that contains these paths with the same relative layout).

---

## Troubleshooting

| Issue | What to do |
|-------|------------|
| `aiguard-api-key` not found | Create the Secret text credential with that ID, or change `credentialsId` in the Jenkinsfile |
| Scan stage skipped | Use **FORCE_RUN**, or push a change under a monitored path |
| `api..zseclipse.net` / parse error | Empty cloud — set **AIGUARD_CLOUD** parameter to `us1` (or your region) |
| Benign tests WARN with BLOCK / PII | Expected on strict tenants; tune AI Guard or keep `optional: true` |
| Deploy fails | Optional stage — use **SKIP_DEPLOY** or fix GCP / `hf-token` |

---

## References

- [Zscaler AI Guard](https://help.zscaler.com/ai-guard)
- [zscaler-sdk-python](https://github.com/zscaler/zscaler-sdk-python)
- [Jenkins Pipeline](https://www.jenkins.io/doc/book/pipeline/)

Design lineage: adapted from Palo Alto Prisma AIRS Jenkins sample; scanner and tests aligned with this repo’s GitHub Actions integration.
