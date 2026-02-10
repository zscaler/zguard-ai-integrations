# Google Integrations for Zscaler AI Guard

Runtime AI security integrations between Google Cloud AI technologies and Zscaler AI Guard.

## Available Integrations

| Integration | Description | Status |
|-------------|-------------|--------|
| **Apigee X + Vertex AI + AI Guard** | API gateway with dual-layer security scanning for Vertex AI | ✅ Complete |
| **Vertex AI Endpoints** | Direct integration with Vertex AI endpoints | 🚧 Planned |

## Overview

Similar to Azure APIM integration, but for Google Cloud's Apigee X API management platform.

### Architecture

```
┌────────┐    ┌─────────────┐    ┌────────────┐    ┌───────────┐
│ Client │───▶│   Apigee X  │───▶│  Zscaler   │───▶│ Vertex AI │
│        │◀───│   Gateway   │◀───│  AI Guard  │◀───│   Model   │
└────────┘    └─────────────┘    └────────────┘    └───────────┘
              Dual Scanning:       ↑ Prompt          (OAuth 2.0)
              - Prompt (PreFlow)   ↓ Response
              - Response (PostFlow)
```

## Quick Reference

### What It Does
1. Client sends prompt → Apigee gateway
2. Prompt scanned by AI Guard → Blocks injection, toxicity, PII
3. If safe → Vertex AI generates response
4. Response scanned by AI Guard → Blocks data leakage
5. If safe → Return to client

### Prerequisites
- Google Cloud Platform account
- Apigee X organization
- Zscaler AI Guard account with API key
- Vertex AI API enabled
- Appropriate GCP IAM permissions

## Documentation

- [Apigee Integration Guide](./apigee-vertex-aiguard/) - Detailed setup (In Development)

## Comparison with Azure

| Feature | Azure APIM | Google Apigee |
|---------|-----------|---------------|
| Platform | Microsoft Azure | Google Cloud Platform |
| Policy Language | C# expressions in XML | JavaScript + XML policies |
| Secret Storage | Named Values | KVM (Key Value Maps) |
| Deployment | Portal or ARM templates | apigeecli or API |
| Complexity | Medium | Higher (more components) |

## Apigee X Integration

Full Apigee X proxy with:
- ✅ Complete policy bundle (11 policies)
- ✅ Automated deployment script
- ✅ JavaScript scanning resources
- ✅ Encrypted KVM configuration
- ✅ Comprehensive testing guide

See [apigee-vertex-aiguard/](./apigee-vertex-aiguard/) for details.

---

**Note:** This integration follows the same DAS (Detection as a Service) pattern as Azure and Claude Code integrations - providing universal AI security that works with ANY AI application, not just specific to Google products.
