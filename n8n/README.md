# n8n Integration with Zscaler AI Guard

This package provides a custom n8n community node for integrating Zscaler AI Guard security scanning into your automation workflows.

## 🎯 What This Does

Add AI security scanning directly within n8n workflows:
- **Scan Prompts**: Validate user input before sending to LLMs
- **Scan Responses**: Check AI-generated content for policy violations
- **Dual Scan**: Scan both prompt and response in sequence
- **Block Malicious Content**: Prevent harmful content from proceeding in workflow

---

## 📦 Installation

### Option 1: Install from npm (When Published)

```bash
# In n8n instance
Settings → Community Nodes → Install
Search: @zscaler/n8n-nodes-aiguard
```

### Option 2: Local Development

> **📖 For detailed setup instructions, troubleshooting, and step-by-step guide, see [SETUP_GUIDE.md](./SETUP_GUIDE.md)**

#### Option 2a: Docker (Recommended)

```bash
# Clone repository
git clone https://github.com/zscaler/zguard-ai-integrations
cd zguard-ai-integrations/n8n

# Install dependencies
npm install

# Build the custom node
npm run build

# Start n8n with docker-compose (mounts the built custom node)
docker-compose up -d

# View logs
docker-compose logs -f n8n

# Access n8n at http://localhost:5678
```

The docker-compose setup automatically mounts the custom node into the container. After any code changes, rebuild and restart:

```bash
npm run build
docker-compose restart n8n
```

#### Option 2b: Local n8n Installation

```bash
# Clone repository
git clone https://github.com/zscaler/zguard-ai-integrations
cd zguard-ai-integrations/n8n

# Install dependencies
npm install

# Build
npm run build

# Create n8n custom nodes dir if it doesn't exist
mkdir -p ~/.n8n/custom

# Link to n8n (use full path to this n8n folder — do not use npm package name or registry)
cd ~/.n8n/custom
npm link /path/to/zguard-ai-integrations/n8n

# Restart n8n
n8n restart
```

Use the **full path** to your local `n8n` folder (e.g. `.../zguard-ai-integrations/n8n`). Do not run `npm link @bdzscaler/n8n-nodes-aiguard` or `npm link @zscaler/n8n-nodes-aiguard` here — that would try the npm registry and can 404.

---

## 🔐 Prerequisites

1. **n8n instance** (Cloud or self-hosted)
2. **Zscaler AI Guard account** with:
   - API Key
   - Active policy configured
   - Cloud environment (us1, us2, eu1, eu2)
3. **Instance owner permissions** to install community nodes

---

## 🚀 Quick Start

### Step 1: Create AI Guard Credentials

1. In n8n, go to **Credentials** (left menu)
2. Click **Add Credential**
3. Search for **"Zscaler AI Guard API"**
4. Fill in:
   - **API Key**: Your AI Guard API key
   - **Cloud Environment**: us1 (or your cloud)
   - **Default Policy ID**: 760 (optional)
5. Click **Test** to verify connection
6. Click **Save**

### Step 2: Use AI Guard Node in Workflow

1. Create new workflow
2. Add **"Zscaler AI Guard"** node
3. Select your credential
4. Choose operation:
   - **Scan Prompt** - Before sending to LLM
   - **Scan Response** - After receiving from LLM
   - **Dual Scan** - Both

### Step 3: Handle the Verdict

Use an **IF node** to check the scan result:

```
IF: {{ $json.action }} equals "BLOCK"
  TRUE → Stop or show error message
  FALSE → Continue workflow
```

---

## 📋 Node Operations

### Scan Prompt

**Use Case:** Validate user input before sending to LLM

**Input:**
- Content: User prompt text

**Output:**
```json
{
  "action": "ALLOW",  // or "BLOCK", "DETECT"
  "severity": "NONE",  // or "LOW", "MEDIUM", "HIGH", "CRITICAL"
  "transactionId": "abc-123-def-456",
  "detectors": ["toxicity", "injection"],
  "direction": "IN",
  "scanType": "prompt"
}
```

### Scan Response

**Use Case:** Check AI-generated content before returning to user

**Input:**
- Content: AI response text

**Output:**
```json
{
  "action": "BLOCK",
  "severity": "CRITICAL",
  "transactionId": "ghi-789-jkl-012",
  "detectors": ["pii", "secrets"],
  "direction": "OUT",
  "scanType": "response"
}
```

### Dual Scan

**Use Case:** Scan both prompt and response in one node

**Input:**
- Prompt: User input
- Response: AI output

**Output:**
```json
{
  "action": "ALLOW",
  "severity": "NONE",
  "transactionId": "mno-345-pqr-678",
  "detectors": [],
  "direction": "OUT",
  "scanType": "response",
  "promptScan": {
    "action": "ALLOW",
    "transactionId": "stu-901-vwx-234"
  }
}
```

---

## 🔧 Example Workflows

### Example 1: AI Chatbot with Security

```
1. Webhook (receives user message)
   ↓
2. AI Guard: Scan Prompt
   ↓
3. IF: action == "BLOCK"?
   ├─ YES → Respond: "Message blocked by security policy"
   └─ NO → Continue
       ↓
   4. OpenAI (generate response)
       ↓
   5. AI Guard: Scan Response
       ↓
   6. IF: action == "BLOCK"?
       ├─ YES → Respond: "Response blocked by security policy"
       └─ NO → Return AI response to user
```

### Example 2: Automated Customer Support

```
1. Gmail: New email received
   ↓
2. Extract email body
   ↓
3. AI Guard: Scan Prompt (check for toxic language)
   ↓
4. IF blocked → Send "Please contact support"
   ↓
5. IF allowed → OpenAI: Generate support response
   ↓
6. AI Guard: Scan Response (check for PII leakage)
   ↓
7. IF allowed → Send email reply
```

### Example 3: Form Processing with AI

```
1. Webhook: Form submission
   ↓
2. AI Guard: Scan (validate form content)
   ↓
3. IF blocked → Return error
   ↓
4. IF allowed → Process with LLM
   ↓
5. AI Guard: Scan LLM response
   ↓
6. Store in database (if allowed)
```

---

## 🎨 Workflow Template

Import the pre-built workflow template:

**File:** `workflows/AIGuard_SecureAI_Template.json`

**What it includes:**
- User input handling
- AI Guard prompt scanning
- Conditional blocking
- LLM call (OpenAI example)
- AI Guard response scanning
- Error handling

**To import:**
1. n8n → Workflows → Import from File
2. Select `AIGuard_SecureAI_Template.json`
3. Configure your credentials
4. Activate workflow

---

## 🔒 Security Features

### Detectors Supported

All AI Guard detectors available:
- ✅ Toxicity
- ✅ Prompt Injection
- ✅ PII (SSN, credit cards, phone numbers)
- ✅ Secrets (API keys, passwords)
- ✅ Gibberish
- ✅ Malicious URLs
- ✅ Off-topic content
- ✅ Data leakage

### Fail Modes

**Fail Open (Default):**
- If AI Guard API unavailable → Allow content
- Better for availability

**Fail Closed:**
- If AI Guard API unavailable → Block content
- Better for security

---

## 🛠️ Development

### Build the Node

```bash
# Install dependencies
npm install

# Build TypeScript
npm run build

# Watch mode (development)
npm run dev
```

### Test Locally

```bash
# Create custom nodes dir and link (use your actual path to this repo's n8n folder)
mkdir -p ~/.n8n/custom
cd ~/.n8n/custom
npm link /path/to/zguard-ai-integrations/n8n

# Restart n8n
n8n restart
```

### Publish to npm (Optional)

```bash
# Login to npm
npm login

# Publish
npm publish --access public
```

---

## 📚 Resources

- [n8n Community Nodes](https://docs.n8n.io/integrations/creating-nodes/)
- [Zscaler AI Guard Documentation](https://help.zscaler.com/ai-guard)
- [AI Guard API Reference](https://github.com/zscaler/zscaler-sdk-python)

---

## 💬 Support

For issues or questions:
1. **Read [SETUP_GUIDE.md](./SETUP_GUIDE.md)** - Comprehensive troubleshooting guide
2. **Read [DOCKER_DEV.md](./DOCKER_DEV.md)** - Docker development workflow
3. Check n8n execution logs
4. Verify AI Guard credentials
5. Review AI Guard Console logs
6. File issue in repository

### Common Issues

- **Custom node not appearing?** → Clear browser cache and restart n8n
- **Webhook 404 errors?** → Use exact URL from n8n, activate workflow for production mode
- **"undefined" error in AI Guard node?** → Check Content expression matches webhook payload structure (`{{ $json.body.message }}`)
- **Authentication failures?** → Verify API key, cloud environment, and policy ID in credentials

See [SETUP_GUIDE.md](./SETUP_GUIDE.md) for detailed troubleshooting steps.

---

## 🆚 Comparison with Other Integrations

| Integration | Use Case | Deployment |
|-------------|----------|------------|
| **n8n Node** | Workflow automation | Install community node |
| **Claude Code Hooks** | Developer coding | Python scripts |
| **Azure APIM** | Enterprise API gateway | XML policies |
| **Google Apigee** | GCP API gateway | Proxy bundle |

All use the same **AI Guard DAS API** for consistent security!

---

## License

MIT License - Part of Zscaler AI Guard integrations repository.
