# Integration Comparison: Claude Code vs Azure AI Gateway

This document compares the two AI Guard integrations to help you understand the architectural differences and choose the right approach.

## Side-by-Side Comparison

| Aspect | Claude Code | Azure AI Gateway |
|--------|-------------|------------------|
| **Platform** | Anthropic Claude Code CLI | Azure API Management |
| **Integration Type** | Python hooks | APIM Policy XML |
| **Deployment** | User-level (~/.claude/) | Gateway-level (centralized) |
| **Language** | Python 3 | C# (policy expressions) |
| **Trigger Mechanism** | Event hooks | Request/Response pipeline |
| **Scope** | Single user/developer | Organization-wide |
| **Configuration** | .env file or environment variables | Azure Named Values |
| **SDK Usage** | zscaler-sdk-python | Direct HTTP API calls |

## Architecture Patterns

### Claude Code: Client-Side Hooks

```
┌─────────────────────────────────────────────┐
│           Developer's Machine                │
│                                              │
│  User → Claude Code                          │
│            ↓                                 │
│    [Python Hooks] ─────────────┐            │
│            ↓                    │            │
│    Claude LLM                   │            │
│            ↓                    ▼            │
│    MCP Tools          AI Guard DAS API      │
│            ↓                    ↑            │
│    [Python Hooks] ──────────────┘            │
│            ↓                                 │
│    User sees result                          │
└─────────────────────────────────────────────┘
```

**Characteristics:**
- ✅ Installed per developer
- ✅ Full control over configuration
- ✅ Works offline (with fail-open)
- ✅ SDK-based integration
- ❌ Not centrally managed
- ❌ Each user must install

### Azure: Gateway-Level Policy

```
┌─────────────────────────────────────────────┐
│         Azure Cloud (Centralized)            │
│                                              │
│  Client → Azure APIM                         │
│              ↓                               │
│      [Inbound Policy] ─────────┐            │
│              ↓                  │            │
│      LLM Backend                │            │
│              ↓                  ▼            │
│      [Outbound Policy]   AI Guard DAS API   │
│              ↓                  ↑            │
│              └──────────────────┘            │
│              ↓                               │
│      Client sees result                      │
└─────────────────────────────────────────────┘
```

**Characteristics:**
- ✅ Centrally managed
- ✅ Enforced for all users
- ✅ No client installation
- ✅ Organization-wide policies
- ❌ Requires Azure infrastructure
- ❌ Less flexible per-user

## Use Case Scenarios

### When to Use Claude Code Integration

**Best For:**
- Individual developers using Claude Code
- Development/testing environments
- Proof of concept deployments
- Personal productivity tools
- Teams without centralized infrastructure

**Example:**
```
Developer working on Zscaler integrations:
- Uses Claude Code for coding assistance
- Wants AI Guard protection for sensitive Zscaler data
- Installs hooks locally
- Gets immediate protection
```

### When to Use Azure Integration

**Best For:**
- Production AI applications
- Enterprise-wide deployments
- API-based AI services
- Multi-tenant AI platforms
- Centralized security governance

**Example:**
```
Enterprise AI chatbot:
- Public-facing application
- Multiple users/tenants
- Deployed on Azure
- APIM provides rate limiting, auth, monitoring
- AI Guard adds security scanning
- Centrally managed by IT/SecOps
```

## Feature Comparison

### Security Features

| Feature | Claude Code | Azure APIM |
|---------|-------------|------------|
| Prompt scanning | ✅ | ✅ |
| Response scanning | ✅ | ✅ |
| MCP tool scanning | ✅ | ❌ (N/A) |
| URL scanning | ✅ | ❌ (N/A) |
| Fail-open/closed | ✅ | ✅ |
| Custom error messages | ❌ | ✅ |
| Session tracking | ✅ (via logs) | ✅ (via header) |
| Transaction IDs | ✅ | ✅ |

### Operational Features

| Feature | Claude Code | Azure APIM |
|---------|-------------|------------|
| Central management | ❌ | ✅ |
| Per-user config | ✅ | ❌ |
| Auto-updates | ❌ Manual | ✅ Via Azure |
| Monitoring | File logs | Azure Monitor |
| Alerting | ❌ Manual | ✅ Azure Alerts |
| Compliance reporting | ❌ | ✅ |
| Multi-tenancy | ❌ | ✅ |

### Configuration

| Aspect | Claude Code | Azure APIM |
|--------|-------------|------------|
| Credentials | .env file | Named Values (encrypted) |
| Policy ID | Environment variable | Named Value or variable |
| Error messages | Hardcoded in Python | Configurable in policy |
| Fail mode | Environment variable | Policy variable |
| Updates | Copy new scripts | Update fragment |

## Integration Complexity

### Claude Code: Simple Setup

**Installation Time**: ~10 minutes  
**Steps**: 4 (install SDK, copy files, configure .env, copy settings)  
**Prerequisites**: Python, pip  
**Maintenance**: Manual updates

**Complexity**: ⭐⭐☆☆☆ (Simple)

### Azure: More Setup, Better Operations

**Installation Time**: ~30 minutes  
**Steps**: 6 (create named values, create fragment, configure policies, test)  
**Prerequisites**: Azure APIM, Contributor role  
**Maintenance**: Managed via Azure Portal

**Complexity**: ⭐⭐⭐☆☆ (Moderate)

## Performance Comparison

### Claude Code Hooks

**Latency per scan**: ~100-300ms (SDK overhead + API call)  
**Total added latency**: 300-900ms (3 scans: input, mcp, response)  
**Client impact**: Noticeable in interactive use  
**Scalability**: Per-developer (no shared resources)

### Azure APIM Policy

**Latency per scan**: ~50-150ms (direct HTTP call)  
**Total added latency**: 100-300ms (2 scans: prompt, response)  
**Client impact**: Minimal (gateway-level)  
**Scalability**: Shared APIM instance (thousands of requests/sec)

## Cost Considerations

### Claude Code

**Infrastructure**: None (client-side)  
**AI Guard API Calls**: Pay per scan  
**Scaling Cost**: Linear with number of developers  
**Hidden Costs**: Developer time for maintenance

### Azure APIM

**Infrastructure**: Azure APIM costs (~$2000-4000/month for Standard tier)  
**AI Guard API Calls**: Pay per scan  
**Scaling Cost**: Fixed (APIM tier-based)  
**Hidden Costs**: Azure operational overhead

## When to Use Both

You can (and should) use both integrations for comprehensive coverage:

```
Development:
└─ Claude Code with hooks
   └─ Developers protected while coding
   └─ Catches issues early

Production:
└─ Azure APIM with policy
   └─ All production traffic protected
   └─ Centralized governance
   └─ Compliance reporting

Result: Defense in depth across entire SDLC
```

## Migration Path

### From Claude Code to Azure

1. **Develop with Claude Code**
   - Use hooks during development
   - Test AI Guard policies
   - Iterate on detector configuration

2. **Deploy to Azure**
   - Set up APIM with AI Guard policy
   - Use same policy ID as dev
   - Consistent security posture

3. **Maintain Both**
   - Developers keep using hooks locally
   - Production uses APIM enforcement
   - Same AI Guard backend

### From Azure to Claude Code

1. **Already have Azure APIM**
   - Developers want local protection
   - Install Claude Code hooks
   - Point to same AI Guard policy

2. **Consistent Policies**
   - Use same policy ID in both
   - Developers see same blocks as production
   - Better testing before deployment

## Summary

### Choose Claude Code If:
- ✅ You're a developer using Claude Code
- ✅ You want quick personal setup
- ✅ You don't have centralized infrastructure
- ✅ You need MCP tool scanning
- ✅ You're doing POC or testing

### Choose Azure If:
- ✅ You're deploying production AI services
- ✅ You have Azure APIM infrastructure
- ✅ You need centralized management
- ✅ You want compliance reporting
- ✅ You serve multiple users/tenants

### Use Both If:
- ✅ You want comprehensive coverage
- ✅ Different needs for dev vs production
- ✅ You want defense in depth
- ✅ Your team uses multiple tools

## Next Steps

- **For Developers**: Start with [Claude Code integration](../Anthropic/claude-code-aiguard/)
- **For Platform Teams**: Start with [Azure integration](./INSTALLATION_GUIDE.md)
- **For Architects**: Read [Architecture documentation](../ARCHITECTURE.md)
