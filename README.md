# Zscaler AI Guard Integrations

Enterprise-grade AI security integrations for various AI platforms using Zscaler AI Guard Detection as a Service (DAS).

## Overview

This repository contains integrations that enable runtime AI security by scanning AI traffic through Zscaler AI Guard for inspection. AI Guard provides comprehensive protection against:

- **Prompt Injection** - Malicious attempts to manipulate AI behavior
- **Data Loss Prevention (DLP)** - Sensitive data exposure (PII, secrets, credentials)
- **Toxicity** - Harmful or inappropriate content
- **Malicious URLs** - Links to phishing, malware, or blocked domains
- **Gibberish** - Encoded or nonsensical content
- **Off-Topic** - Content outside allowed scope
- **Competition** - Questions about competitors

## Architecture: Detection as a Service (DAS)

AI Guard uses a **DAS pattern** where each AI application integrates independently:

```
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ AI App 1     │  │ AI App 2     │  │ AI App 3     │
│ (Claude Code)│  │ (Azure APIM) │  │ (LangChain)  │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │
       └─────────────────┼─────────────────┘
                         ▼
                  ┌─────────────┐
                  │  AI Guard   │
                  │  DAS API    │
                  └─────────────┘
```

**Benefits:**
- ✅ No proxy infrastructure required
- ✅ Each app integrates independently
- ✅ No single point of failure
- ✅ Platform-specific optimizations
- ✅ Scales naturally with applications

See [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed explanation.

## Available Integrations

| Platform | Type | Status | Documentation |
|----------|------|--------|---------------|
| **Claude Code** | Hooks (Python) | ✅ Prototype Complete | [Guide](./Anthropic/claude-code-aiguard/) |
| **Azure AI Gateway** | APIM Policy | ✅ Prototype Complete | [Guide](./Azure/) |
| **Cursor IDE** | Hooks (Python) | ✅ Complete | [Guide](./Cursor/) |
| **Cline** | VS Code hooks (Python) | ✅ Complete | [Guide](./Cline/) |
| **Windsurf** | Cascade hooks (Python) | ✅ Complete | [Guide](./Windsurf/) |
| **GitHub Actions** | CI/CD Pipeline (Python) | ✅ Complete | [Guide](./github-actions/) |
| **Jenkins** | Declarative Pipeline (Python) | ✅ Complete | [Guide](./Jenkins/declarative-pipeline/) |
| **Google Apigee X** | API Proxy | ✅ Complete | [Guide](./Google/apigee-vertex-aiguard/) |
| LiteLLM Gateway | Callbacks | 🚧 Planned | - |
| LangChain | Callbacks | 🚧 Planned | - |

## Makefile and weekly CI

From the repository root:

| Command | Purpose |
|---------|---------|
| `make help` | List all targets |
| `make test-compile` | Python syntax check for Anthropic, Cursor, Cline, Windsurf hooks and CI scripts (**no API**) |
| `make test-policy-gha` | AI Guard scan using `github-actions/` (needs **`AIGUARD_API_KEY`** in the environment) |
| `make test-policy-jenkins` | Same scan using `Jenkins/declarative-pipeline/` (parity check) |
| `make test-cursor` / `test-cline` / `test-windsurf` | Run `local_dev/*/test_*.sh` samples (**API**) |
| `make test-all` | Compile + both policy scans + hook sample scripts |

**Scheduled GitHub Actions:** [`.github/workflows/weekly-integrations.yml`](./.github/workflows/weekly-integrations.yml) runs **Mondays 16:00 UTC** (08:00 **PST**; during **PDT** that is ~09:00 Los Angeles). It runs `make test-compile`, then two policy scans (`github-actions` and `Jenkins` configs). Set repository secrets **`AIGUARD_API_KEY`**, and optionally **`AIGUARD_CLOUD`**, **`AIGUARD_POLICY_ID`**. Use **Actions → Weekly integration checks → Run workflow** for a manual run.

## Quick Start

### Claude Code Integration

For developers using Claude Code CLI:

```bash
# 1. Install dependencies
pip install git+https://github.com/zscaler/zscaler-sdk-python.git

# 2. Copy hooks
mkdir -p ~/.claude/hooks/aiguard
cp Anthropic/claude-code-aiguard/hooks/*.py ~/.claude/hooks/aiguard/

# 3. Configure environment
cp Anthropic/claude-code-aiguard/.env.example ~/.claude/hooks/aiguard/.env
# Edit .env with your credentials

# 4. Configure Claude Code
cp Anthropic/claude-code-aiguard/settings.json ~/.claude/settings.json
```

See [Claude Code Guide](./Anthropic/claude-code-aiguard/README.md) for details.

### Cursor IDE Integration

For developers using Cursor IDE:

```bash
# 1. Install Python dependencies
pip install zscaler-sdk-python python-dotenv

# 2. Copy hooks into your project
mkdir -p .cursor
cp path/to/zguard-ai-integrations/Cursor/.cursor/hooks.json .cursor/hooks.json
cp -r path/to/zguard-ai-integrations/Cursor/hooks Cursor/hooks

# 3. Configure environment
export AIGUARD_API_KEY="your-aiguard-api-key"
# Or copy example.env to .env in your project root

# 4. Restart Cursor
```

See [Cursor Guide](./Cursor/README.md) for details.

### Cline (VS Code) integration

```bash
cd Cline && pip install -r requirements.txt
cp Cline/.env.example Cline/.env   # or use repo root .env
chmod +x Cline/.clinerules/hooks/UserPromptSubmit Cline/.clinerules/hooks/PreToolUse \
         Cline/.clinerules/hooks/PostToolUse Cline/.clinerules/hooks/TaskComplete
```

See [Cline Guide](./Cline/README.md) for hook coverage and limitations.

### Windsurf integration

```bash
cd Windsurf && pip install -r requirements.txt
# Ensure Windsurf/.env has AIGUARD_API_KEY (.env.example is optional template)
# Open the Windsurf/ folder as the workspace in Windsurf IDE
```

See [Windsurf Guide](./Windsurf/README.md) for pre vs post hook blocking limits.

### GitHub Actions CI/CD Integration

For CI/CD policy validation before deploying AI applications:

```bash
# 1. Add GitHub Secrets
#    AIGUARD_API_KEY — Your AI Guard API key
#    AIGUARD_CLOUD   — Cloud region (optional, default: us1)

# 2. Copy the workflow and scripts into your repo
cp -r path/to/zguard-ai-integrations/github-actions/.github .github
cp -r path/to/zguard-ai-integrations/github-actions/scripts scripts
cp -r path/to/zguard-ai-integrations/github-actions/config config

# 3. Define test cases in config/test-prompts.yaml
# 4. Push — the workflow runs automatically
```

See [GitHub Actions Guide](./github-actions/README.md) for details.

### Jenkins CI/CD Integration

For policy validation on a Jenkins controller:

```bash
# 1. Create credential aiguard-api-key (Secret text) = AI Guard API key
# 2. Copy declarative-pipeline/ into your repo (or use this repo) and point the job at that directory
# 3. Edit config/test-prompts.yaml — same format as GitHub Actions
# 4. Build with Parameters: use FORCE_RUN on first run if no SCM diff is detected
```

See [Jenkins Guide](./Jenkins/declarative-pipeline/README.md) for credential IDs, monitored paths, and optional Vertex deploy stages.

### Azure AI Gateway Integration

For Azure APIM / AI Gateway deployments:

```bash
# 1. Create Named Values in APIM
- AIGUARD-API-KEY (secret)
- AIGUARD-CLOUD (us1/us2/eu1/eu2)  
- AIGUARD-POLICY-ID (optional)

# 2. Create policy fragment
- Name: zscaler-aiguard-scan
- Content: Copy from Azure/zscaler-aiguard-scan

# 3. Add to your API policy
<inbound>
    <set-variable name="ScanType" value="prompt" />
    <include-fragment fragment-id="zscaler-aiguard-scan" />
</inbound>
<outbound>
    <set-variable name="ScanType" value="response" />
    <include-fragment fragment-id="zscaler-aiguard-scan" />
</outbound>
```

See [Azure Installation Guide](./Azure/INSTALLATION_GUIDE.md) for details.

## How It Works

### Defense in Depth

AI Guard provides multiple layers of protection:

```
User Input
    ↓
[Layer 1: Prompt Scanning]
    ↓ Detects: Injection, Toxicity, PII
    ↓ ALLOW/BLOCK
    ↓
AI/LLM Processing
    ↓
[Layer 2: Tool Call Scanning] (if applicable)
    ↓ Detects: Malicious parameters
    ↓ ALLOW/BLOCK
    ↓
External Service Call
    ↓
[Layer 3: Response Scanning]
    ↓ Detects: PII leakage, Secrets, Malicious URLs
    ↓ ALLOW/BLOCK
    ↓
User Output
```

### Scan Flow Example

```
User: "Fetch data from https://malicious-site.com"

SCAN 1: User Input
├─ Content: "Fetch data from https://malicious-site.com"
├─ Direction: IN
├─ Result: ALLOW ✅
└─ Reason: Prompt itself is benign

SCAN 2: URL Check
├─ Content: "https://malicious-site.com"
├─ Direction: OUT
├─ Result: BLOCK ❌
└─ Reason: Malicious URL detector triggered

User sees: "Blocked by AI Guard: Malicious URL detected"
```

## AI Guard Configuration

### Get API Credentials

1. Log in to **AI Guard Console**: `https://admin.{cloud}.zseclipse.net`
2. Navigate to **Private AI Apps** → **App API Keys**
3. Create or copy your API key
4. Note your cloud environment (us1, us2, eu1, eu2)

### Configure Detection Policy

1. Go to **Policies** in AI Guard Console
2. Create or edit a policy
3. Enable detectors:
   - **Prompt Detectors**: Toxicity, Injection, PII, Secrets, Gibberish
   - **Response Detectors**: PII, Secrets, Malicious URLs, Data Leakage
4. Set detector actions:
   - **BLOCK** - Hard block (stops execution)
   - **DETECT** - Soft block (logs but allows)
5. **Activate** the policy
6. Note the Policy ID

### Policy Association (Recommended)

For auto-resolution without specifying policy ID:

1. Go to **Private AI Apps** → **Applications**
2. Create or select an application
3. Go to **App API Keys** → Associate your key with the application
4. Assign your policy to the application

## Monitoring & Logging

### Transaction Tracking

Every scan generates a transaction ID for correlation:

```
Claude Code logs: BLOCKED (txn:abc-123)
     ↓
AI Guard Console: Search txn:abc-123
     ↓
View: Full scan details, triggered detectors, content samples
```

### Security Logs

**Claude Code**: `~/.claude/hooks/aiguard/security.log`
```
[2026-01-30 15:30:00] BLOCKED USER INPUT: severity=CRITICAL policy=policy_760 detectors=[toxicity] (txn:abc123...)
```

**Cursor IDE**: `Cursor/hooks/aiguard.log`
```
[2026-01-30 15:30:00] BLOCKED USER PROMPT: severity=CRITICAL policy=Default_Policy detectors=[toxicity] (txn:abc123...)
```

**Azure APIM**: Azure Monitor / Application Insights
```
403 Forbidden responses
AI Guard API call duration
Error rates
```

## Documentation

- **[Architecture Overview](./ARCHITECTURE.md)** - DAS pattern and design decisions
- **[Agentic AI Integration](./AGENTIC_AI_INTEGRATION.md)** - Multi-agent systems
- **[Setup Summary](./SETUP_SUMMARY.md)** - Quick reference

### Platform-Specific Docs

- **[Claude Code](./Anthropic/claude-code-aiguard/README.md)** - Detailed installation
- **[Cursor IDE](./Cursor/README.md)** - Cursor hooks integration
- **[Cline](./Cline/README.md)** - Cline VS Code hooks
- **[Windsurf](./Windsurf/README.md)** - Windsurf Cascade hooks
- **[GitHub Actions](./github-actions/README.md)** - CI/CD policy validation
- **[Jenkins](./Jenkins/declarative-pipeline/README.md)** - Declarative pipeline policy validation
- **[Azure APIM](./Azure/README.md)** - Azure AI Gateway integration
- **[Azure Installation](./Azure/INSTALLATION_GUIDE.md)** - Step-by-step guide

## Examples

### Claude Code Usage

```bash
# Start Claude Code
claude

# Safe prompt - allowed
"List all my Zscaler applications"

# Toxic prompt - blocked
"I hate my coworker"
# → Blocked by AI Guard: toxicity detector
```

### Azure API Gateway Usage

```bash
# Safe request - allowed
curl -X POST "https://your-gateway/chat/completions" \
  -H "api-key: $KEY" \
  -d '{"messages": [{"role": "user", "content": "Hello"}], "model": "gpt-4"}'

# Prompt injection - blocked (403)
curl -X POST "https://your-gateway/chat/completions" \
  -H "api-key: $KEY" \
  -d '{"messages": [{"role": "user", "content": "Ignore instructions"}], "model": "gpt-4"}'
```

## Contributing

Contributions welcome! Particularly interested in:

- [x] Cursor IDE integration
- [x] Cline VS Code hooks
- [x] Windsurf Cascade hooks
- [x] GitHub Actions CI/CD pipeline
- [x] Jenkins Declarative Pipeline
- [ ] LiteLLM gateway callbacks
- [ ] LangChain middleware
- [ ] Google Apigee policies
- [ ] Kong plugins
- [ ] AWS API Gateway integration

## Security

- **Report security issues**: security@zscaler.com
- **API key protection**: Never commit `.env` files
- **Credential rotation**: Rotate keys every 90 days
- **Least privilege**: Use dedicated API keys per environment

## License

Part of the Zscaler AI Guard integrations repository.

---

## Quick Links

- [Get Started with Claude Code](./Anthropic/claude-code-aiguard/)
- [Get Started with Azure](./Azure/INSTALLATION_GUIDE.md)
- [Architecture Documentation](./ARCHITECTURE.md)
- [AI Guard Console](https://admin.us1.zseclipse.net)
- [Zscaler SDK Python](https://github.com/zscaler/zscaler-sdk-python)
