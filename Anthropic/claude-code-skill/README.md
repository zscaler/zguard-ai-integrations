# Claude Code Skill Integration with Zscaler AI Guard

A Claude Code skill that integrates Zscaler AI Guard for scanning prompts, code, and AI responses for security threats.

## Coverage

| Scanning Phase | Supported | Description |
|----------------|:---------:|-------------|
| Prompt | ✅ | User-invoked via `/aiguard` command with `--type prompt` |
| Response | ✅ | User-invoked scanning of AI-generated content |
| Code | ✅ | Scan generated code for security vulnerabilities |
| Conversation | ✅ | Scan both prompt and response together |
| Streaming | ❌ | Synchronous blocking scan only |
| Pre-tool call | ❌ | Not designed for pre-tool validation |
| Post-tool call | ❌ | Not designed for post-tool validation |

> **Note:** For automatic pre/post tool scanning, see the [Claude Code Hooks integration](../claude-code-aiguard/).

## Detectors

AI Guard provides 19 prompt detectors and 21 response detectors. All detectors enabled in your AI Guard policy are automatically applied when scanning.

### Prompt Detectors (Direction: IN)

| Detector | Description |
|----------|-------------|
| Toxicity | Detects and filters harmful language `Multilingual` |
| Code | Detects and blocks unwanted programming languages `Beta` |
| Prompt Injection | Detects malicious or unauthorized modifications to input prompts `Multilingual` |
| Brand and Reputation Risk | Detects negative sentiment towards a brand `Beta` |
| Text | Detects and blocks sensitive text using regex patterns |
| Gibberish | Identifies nonsensical or meaningless text `Multilingual` |
| Competition | Prevents inclusion of competitor names `Beta` |
| Language | Detects and blocks unwanted languages `Multilingual` |
| Legal Advice | Blocks prompts seeking legal advice or compliance guidance |
| Intellectual Property | Filters and controls content for intellectual property |
| Secrets | Detects sensitive information such as API keys |
| Off Topic | Filters content by topic description `Beta` |
| PII | Detects PII entities such as email, SSN |
| Personal Data | Identifies sensitive personal attributes and blocks invasive questions |
| PII DeepScan | Detects high-risk identifiers (SSN, ITIN, passport, credit card, etc.) |
| Topic | Filters content by identifying custom topics |
| Invisible Text | Identifies hidden or obscured text within digital content |
| Finance Advice | Blocks actionable financial guidance `Multilingual` |
| Prompt Tags | Filters and controls prompts by predefined tags |

### Response Detectors (Direction: OUT)

| Detector | Description |
|----------|-------------|
| Toxicity | Detects harmful language in AI responses `Multilingual` |
| Code | Detects unwanted programming languages in responses `Beta` |
| Malicious URL | Identifies URLs with domains categorized as malicious |
| Response Tags | Filters responses by predefined tags |
| Brand and Reputation Risk | Detects negative brand sentiment in responses `Beta` |
| Refusal | Identifies LLM refusal patterns |
| Text | Detects sensitive text using regex patterns |
| Gibberish | Identifies nonsensical text in responses `Multilingual` |
| Competition | Prevents competitor names in responses `Beta` |
| Language | Detects unwanted languages in responses `Multilingual` |
| Legal Advice | Blocks legal advice in AI responses |
| Intellectual Property | Filters IP content in responses |
| Secrets | Detects sensitive information in responses `Beta` |
| Off Topic | Filters off-topic content in responses `Beta` |
| PII | Detects PII entities in responses |
| Personal Data | Identifies sensitive personal attributes in responses |
| PII DeepScan | Detects high-risk identifiers in responses |
| Topic | Filters content by custom topics |
| URL Reachability | Verifies URLs are accessible and functioning in real time |
| Invisible Text | Identifies hidden text in AI-generated content |
| Finance Advice | Blocks actionable financial guidance in responses `Multilingual` |

> For full descriptions and severity levels, see [references/threat-categories.md](references/threat-categories.md).

## Installation

### 1. Install the SDK

```bash
pip install zscaler-sdk-python
```

### 2. Copy to Claude Skills Directory

```bash
mkdir -p ~/.claude/skills
cp -r claude-code-skill ~/.claude/skills/aiguard
```

### 3. Configure Environment Variables

Add the following to your shell profile (`~/.bashrc`, `~/.zshrc`, etc.):

```bash
export AIGUARD_API_KEY="your-api-key-here"
export AIGUARD_CLOUD="us1"
# Optional:
# export AIGUARD_POLICY_ID="12345"
```

Or copy the environment template:

```bash
cp .env.example .env
# Edit .env with your credentials
source .env
```

### 4. Obtain API Credentials

1. Log in to the AI Guard Console
2. Navigate to **Private AI Apps** → **App API Keys**
3. Generate an API key
4. Note your cloud region (us1, us2, eu1, eu2)

---

## Usage

### As a Slash Command

```
/aiguard
```

Claude will also automatically invoke this skill when appropriate based on context (e.g., when generating security-sensitive code or handling user input).

### Input Methods

The scanner accepts content via three methods:

```bash
# Method 1: Heredoc (recommended — handles quotes and newlines)
python3 scripts/scan.py --type prompt <<'EOF'
Content with "quotes" and
multiple lines works fine.
EOF

# Method 2: File (recommended for code)
python3 scripts/scan.py --type code --file path/to/file.py

# Method 3: Direct argument (simple content only)
python3 scripts/scan.py --type prompt --content "simple text"

# Conversation (prompt + response together)
python3 scripts/scan.py --type conversation --prompt "user prompt" --response "ai response"
```

## Scan Types

| Type | Direction | Use Case |
|------|-----------|----------|
| `prompt` | IN | Scan user input before processing |
| `response` | OUT | Scan AI-generated content before delivery |
| `code` | OUT | Scan generated code for vulnerabilities |
| `conversation` | IN + OUT | Scan both prompt and response together |

## Output Format

```json
{
  "status": "safe|threat_detected|blocked",
  "action": "ALLOW|DETECT|BLOCK",
  "severity": "INFO|LOW|MEDIUM|HIGH|CRITICAL",
  "transaction_id": "unique-identifier",
  "policy_name": "policy-name",
  "triggered_detectors": ["prompt_injection", "dlp"]
}
```

Use `--verbose` for additional detail in the output.

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Safe — no threats detected |
| 1 | Error — scan failed |
| 2 | Block — threat detected, action blocked |

## Directory Structure

```
claude-code-skill/
├── SKILL.md           # Skill definition and instructions
├── README.md          # This file
├── .env.example       # Environment variable template
├── requirements.txt   # Python dependencies
├── scripts/
│   └── scan.py        # Main scanning script
└── references/
    └── threat-categories.md  # Detection category documentation
```

## Requirements

- Python 3.10+
- `zscaler-sdk-python` package
- Network access to Zscaler AI Guard API
- Valid AI Guard API key

---

## Comparison: Skill vs Hooks

| Feature | Skill (this) | Hooks |
|---------|:------------:|:-----:|
| Automatic scanning | Semi (auto-invoke rules) | ✅ |
| On-demand scanning | ✅ | ❌ |
| Pre/Post tool scanning | ❌ | ✅ |
| Slash command | ✅ (`/aiguard`) | ❌ |
| Uses zscaler-sdk-python | ✅ | ✅ |

---

## Resources

- [Zscaler AI Guard Documentation](https://help.zscaler.com/ai-guard)
- [zscaler-sdk-python](https://github.com/zscaler/zscaler-sdk-python)
- [Claude Code Skills Documentation](https://code.claude.com/docs/en/skills)
- [Threat Categories Reference](references/threat-categories.md)

---

## License

Part of the Zscaler AI Guard integrations repository.
