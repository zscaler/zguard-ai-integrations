# Kong Konnect - Zscaler AI Guard
# AI Guard API Intercept Request Callout Plugin Integration

Enterprise-grade AI security scanning for Kong Konnect using Zscaler AI Guard Detection as a Service (DAS) API. This integration provides real-time threat detection and blocking for AI API requests and responses through Kong's managed cloud platform.

## Getting Started

### What You Need

1. **Kong Konnect SaaS Account** - Your managed Kong Gateway (cloud.konghq.com)
2. **Zscaler AI Guard API Key** - From your Zscaler tenant
3. **AI API Service** - The upstream AI service you want to protect (e.g., OpenAI, Claude)

### High-Level Setup Process

#### 1. Configure Your AI Guard Credentials
Store your Zscaler AI Guard credentials securely in Kong Konnect's environment variables:
- Navigate to your Control Plane settings
- Add environment variable: `KONG_VAULT_ENV_AIGUARD_API_KEY` (your AI Guard API key)
- AI Guard uses automatic policy resolution — no profile name configuration required
- This enables secure vault-based authentication

#### 2. Create Your Service & Route
Set up the AI service you want to protect:
- **Service**: Points to your AI provider (e.g., `https://api.openai.com`)
- **Route**: Defines the API path (e.g., `/v1/chat/completions`)
- Note your **Service ID** for the plugin configuration

#### 3. Apply the Request-Callout Plugin
Use the provided `request-callout-zscaler-aiguard-config.json`:
- Update the `service.id` field with your Service ID
- Apply via Konnect UI or API
- The plugin automatically intercepts, scans, and protects your AI requests

#### 4. Test & Verify
- Send normal requests → Should pass through with security headers
- Send malicious prompts → Should block with 403 responses
- Monitor via Konnect Analytics for security insights

### What This Integration Does

- **Intercepts** all AI API requests before they reach your AI service
- **Extracts** user prompts intelligently (supports OpenAI format)
- **Scans** content via Zscaler AI Guard for threats (prompt injection, malware, DLP, PII)
- **Blocks** malicious requests with detailed error responses
- **Forwards** clean requests to your AI service unchanged
- **Logs** all scan results for compliance and monitoring

### Key Benefits for Kong Konnect SaaS

- **Zero Infrastructure** - No additional services or proxies required
- **Native Integration** - Uses built-in Kong `request-callout` plugin
- **Fully Managed** - Leverages Kong Konnect's cloud platform
- **Enterprise Ready** - Vault security, auto-scaling, high availability
- **Real-time Protection** - Synchronous scanning with minimal latency
- **Automatic Policy Resolution** - No profile/policy configuration needed at the gateway

### Next Steps

- **Quick Setup**: Follow the 4-step process above to get started in minutes
- **Detailed Deployment**: See `KONNECT-DEPLOYMENT.md` for step-by-step Konnect configuration
- **Configuration Reference**: Review `request-callout-zscaler-aiguard-config.json` for the complete plugin setup
- **Architecture Details**: Continue reading below for deep technical explanation

---

## Architecture

This solution uses **Kong Konnect's** native `request-callout` plugin to provide **comprehensive AI security scanning** with real-time threat detection and blocking capabilities.

### High-Level Workflow

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│           Kong Konnect + Zscaler AI Guard API Intercept Integration             │
└─────────────────────────────────────────────────────────────────────────────────┘

┌──────────────┐    1. POST /v1/chat/completions    ┌──────────────────────────────┐
│              │ ─────────────────────────────────▶ │                              │
│    Client    │                                    │      Kong Konnect            │
│ Application  │                                    │       Gateway                │
│              │ ◀────────── 8. Response ────────── │                              │
└──────────────┘           + Security Headers       └──────────────┬───────────────┘
                                                                   │
                                                    2. Extract     │
                                                       User Prompt │
                                                                   ▼
                                                    ┌──────────────────────────────┐
                                                    │     Request-Callout          │
                                                    │        Plugin                │
                                                    │                              │
                                                    │ • Parse OpenAI JSON          │
                                                    │ • Extract user content       │
                                                    │ • Build AI Guard payload     │
                                                    └──────────────┬───────────────┘
                                                                   │
                                                    3. AI Guard    │
                                                       Scan        │
                                                                   ▼
┌──────────────┐    4. Scan Result               ┌─────────────────────────────────┐
│              │ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ▶ │                                 │
│  Zscaler     │    {"action": "allow|block",    │     Security Decision           │
│  AI Guard    │     "severity": "...",          │        Logic                    │
│  DAS API     │     "detector_responses":{}}    │                                 │
└──────────────┘                                 └──────────────┬──────────────────┘
                                                                │
                                                 5. Decision    │
                                                                ▼
                                                ┌───────────────────────────────┐
                                                │     Malicious Content?        │
                                                │                               │
                                                │    ┌─────────┐ ┌─────────┐    │
                                                │    │  BLOCK  │ │  ALLOW  │    │
                                                │    │   403   │ │Forward  │    │
                                                │    │  Error  │ │   to    │    │
                                                │    └─────────┘ │   AI    │    │
                                                │                │ Service │    │
                                                │                └─────────┘    │
                                                └───────────────┬───────────────┘
                                                                │
                                                 6. Clean       │
                                                    Request     │
                                                                ▼
                                                ┌───────────────────────────────┐
                                                │                               │
                                                │     OpenAI / AI Provider      │
                                                │                               │
                                                │  • GPT-3.5/4                  │
                                                │  • Claude                     │
                                                │  • Custom Models              │
                                                │                               │
                                                └───────────────┬───────────────┘
                                                                │
                                                 7. AI Response │
                                                                ▼
                                                ┌───────────────────────────────┐
                                                │   Direct Response Return      │
                                                │                               │
                                                │ + X-AIGuard-Action            │
                                                │ + X-AIGuard-Transaction-ID    │
                                                │ + X-AIGuard-Blocked: false    │
                                                └───────────────────────────────┘
```

### Detailed Request Flow

#### Phase 1: Request Scanning
1. **Request Interception**: Kong captures incoming AI API requests
2. **Prompt Extraction**: Lua script extracts user prompts from request body (supports OpenAI format)
3. **AI Guard Scan**: Content sent to AI Guard DAS API with `direction: IN`
4. **Security Decision**: AI Guard returns `allow` or `block` action with detector results
5. **Enforcement**: Malicious requests blocked with detailed error response

#### Phase 2: AI Service Call
6. **Upstream Forwarding**: Clean requests forwarded to AI provider (OpenAI, etc.)
7. **Response Delivery**: AI service response returned directly to client with security headers

> **Note**: The current implementation focuses on **request-side scanning** to block malicious prompts before they reach AI services. Response scanning capabilities are available using the custom plugin approach (see `../custom-plugin/`).

### Key Components

- **Request-Callout Plugin**: Single-phase request scanning with intelligent prompt extraction
- **Zscaler AI Guard DAS API**: Real-time AI security scanning with automatic policy resolution
- **Kong Vault Integration**: Secure API key management
- **Graceful Fallback**: Continue operation during AI Guard API outages

---

## Plugin Configuration

### Required Plugin: `request-callout`

**Plugin Execution Order**: Single plugin with three phases:
1. **Request Phase**: Extract and scan user prompts via AI Guard API
2. **Response Phase**: Process AI Guard scan results and block if malicious
3. **Upstream Phase**: Restore original request body and forward to AI service

**Key Configuration**:
- **API Endpoint**: `https://api.us1.zseclipse.net/v1/detection/resolve-and-execute-policy`
- **Authentication**: `{vault://env/aiguard-api-key}` (Bearer token)
- **Cache Strategy**: Disabled for real-time scanning
- **Error Handling**: Fail fast with 403 blocks

#### Core Request Processing Lua Script

The main request scanning logic extracts user prompts from OpenAI-formatted requests:

```lua
local original_body, err = kong.request.get_raw_body()
if not original_body then
    kong.log.err("Failed to get request body: ", err)
    return
end

kong.ctx.shared.original_request_body = original_body

local user_prompt = ""
local messages_start = string.find(original_body, '"messages"%s*:%s*%[')
if messages_start then
    local content_pattern = '"role"%s*:%s*"user".-"content"%s*:%s*"([^"]*)"'
    for content in string.gmatch(original_body, content_pattern) do
        user_prompt = content
    end
end

local function escape_json_string(str)
    if not str then return '""' end
    str = string.gsub(str, '\\', '\\\\')
    str = string.gsub(str, '"', '\\"')
    str = string.gsub(str, '\n', '\\n')
    str = string.gsub(str, '\r', '\\r')
    str = string.gsub(str, '\t', '\\t')
    return '"' .. str .. '"'
end

-- Build AI Guard DAS payload
local tr_id = ngx.var.request_id or "kong-unknown"
local full_json = string.format([[{
  "content": %s,
  "direction": "IN",
  "transaction_id": %s
}]], escape_json_string(user_prompt), escape_json_string(tr_id))

kong.ctx.shared.callouts.aiguard_request_scan.request.params.body = full_json
```

#### Security Decision Logic

Response processing determines whether to block or allow the request:

```lua
local co = kong.ctx.shared.callouts
if not (co and co.aiguard_request_scan and co.aiguard_request_scan.response) then
  kong.log.warn("No AI Guard callout response found")
  return
end

local response_body = co.aiguard_request_scan.response.body
kong.log.info("Raw AI Guard response: ", response_body)

if response_body:match('"action"%s*:%s*"block"') then
  kong.ctx.shared.aiguard_blocked = true
  kong.log.warn("AI Guard blocking request")
  return kong.response.exit(403, {
    error = "Request blocked by Zscaler AI Guard security scan",
    details = "Malicious content detected in prompt"
  })
end
```

#### Upstream Forwarding Logic

Clean requests are forwarded to the AI service with proper headers:

```lua
if kong.ctx.shared.aiguard_blocked then
  return
end

local body = kong.ctx.shared.original_request_body
kong.service.request.set_raw_body(body)
kong.service.request.set_header("content-type", "application/json")
kong.service.request.set_header("accept", "application/json")
kong.service.request.set_header("host", "api.openai.com")
kong.service.request.clear_header("transfer-encoding")
kong.service.request.set_header("content-length", tostring(#body))
```

### AI Guard API Response Handling

**Scan Result Processing**:
```json
{
  "transaction_id": "kong-request-id",
  "action": "allow",
  "severity": "informational",
  "direction": "IN",
  "detector_responses": {
    "prompt_injection": { "triggered": false, "action": "allow" },
    "malware": { "triggered": false, "action": "allow" },
    "dlp": { "triggered": false, "action": "allow" }
  },
  "policy_id": 12345,
  "policy_name": "Default-Policy"
}
```

### Performance Optimization

**Configuration Settings**:
- **Cache Strategy**: Disabled (`"off"`) for real-time scanning accuracy
- **Timeout Management**:
  - Connect: 2000ms
  - Read: 10000ms (10s)
  - Write: 10000ms (10s)
- **Error Handling**: 2 retries with fail-fast behavior
- **Regional Endpoint**: US1 region (`api.us1.zseclipse.net`)

---

**This integration provides enterprise-grade AI security scanning for Kong Konnect, protecting AI applications against malicious content using Zscaler AI Guard real-time threat detection.**
