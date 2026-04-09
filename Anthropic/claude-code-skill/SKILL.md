---
name: aiguard
description: |
  Scan prompts, AI responses, and code for security threats using Zscaler AI Guard.
  Supports 19 prompt detectors and 21 response detectors including: prompt injection, toxicity, DLP,
  PII, PII DeepScan, personal data, secrets, malicious URLs, code, gibberish, invisible text,
  brand risk, competition, language, legal advice, intellectual property, finance advice,
  off topic, topic, refusal, URL reachability, and tag-based filtering.
  Auto-invoke when: checking content for prompt injection, detecting sensitive data (PII, credentials, secrets),
  identifying malicious URLs, filtering toxic or harmful content, or validating AI-generated responses.
  Auto-invoke when: user asks to "scan this", "check for sensitive data", "is this safe",
  "check for injection", "review for security", or mentions DLP, PII, or credentials.
  Auto-invoke when: generating code that handles user input, authentication, or financial/legal content.
  Auto-invoke when: checking for brand safety, competitor mentions, intellectual property,
  hidden/invisible text, or compliance with language and topic policies.
allowed-tools:
  - Bash
  - Read
  - Write
---

# Zscaler AI Guard Security Scanner

Detect security threats in prompts, AI responses, and code using Zscaler AI Guard.

## What It Detects

All detectors enabled in your AI Guard policy are applied automatically. Available detectors include:

**Security:** Prompt Injection, Code, Secrets, PII, Personal Data, PII DeepScan, Invisible Text, Malicious URL
**Toxicity:** Toxicity (multilingual)
**General:** Text (regex), Gibberish, Competition, Language, Brand and Reputation Risk, Refusal, URL Reachability, Prompt/Response Tags
**Content Moderation:** Legal Advice, Intellectual Property, Off Topic, Topic, Finance Advice

## Prerequisites

Environment variables required:
- `AIGUARD_API_KEY` — API key from AI Guard Console (Private AI Apps → App API Keys)
- `AIGUARD_CLOUD` — Cloud region (us1, us2, eu1, eu2)
- `AIGUARD_POLICY_ID` — (Optional) Specific policy ID; auto-resolved if not provided

## How to Pass Content

### Method 1: Heredoc (recommended — handles quotes and newlines)

```bash
python3 scripts/scan.py --type prompt <<'EOF'
Content with "quotes" and
multiple lines works fine.
EOF
```

### Method 2: File (recommended for code)

```bash
python3 scripts/scan.py --type code --file path/to/file.py
```

### Method 3: Direct argument (simple content only)

```bash
python3 scripts/scan.py --type prompt --content "simple text"
```

### Conversation (prompt + response together)

```bash
python3 scripts/scan.py --type conversation --prompt "user prompt" --response "ai response"
```

## Scan Types

| Type | Use Case |
|------|----------|
| `prompt` | Scan user input before processing (direction: IN) |
| `response` | Scan AI-generated content before delivery (direction: OUT) |
| `code` | Scan generated code for vulnerabilities (direction: OUT) |
| `conversation` | Scan both prompt and response together |

## Interpreting Results

- **action: ALLOW** — Content is safe, proceed normally
- **action: DETECT** — Threat detected but not blocked (alert); review and decide
- **action: BLOCK** — Threat detected and blocked; do NOT proceed with this content

## Workflow

1. Extract content to scan from the conversation
2. Choose appropriate scan type and input method
3. Run the scanner
4. Check the `action` field in the result
5. If `BLOCK` or `DETECT`: address the issue before proceeding

For threat category details, see [references/threat-categories.md](references/threat-categories.md).
