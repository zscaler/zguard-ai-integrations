# AI Guard Detector Reference

Complete reference of all detectors available in Zscaler AI Guard policies, organized by scanning direction.

---

## Prompt Detectors (Direction: IN)

Detectors that analyze user input before it reaches the AI model.

### Toxicity `Multilingual`

Detects and filters harmful language including hate speech, threats, harassment, and inappropriate content.

- **Category:** Toxicity
- **Severity:** Medium to High

### Code `Beta`

Detects and blocks unwanted programming languages across your platforms. Can restrict specific languages or code patterns in user prompts.

- **Category:** Security
- **Severity:** Medium

### Prompt Injection `Multilingual`

Detects and prevents malicious or unauthorized modifications to input prompts. Catches attempts to override system instructions, jailbreak the AI, or manipulate behavior through crafted input.

- **Category:** Security
- **Severity:** High

### Brand and Reputation Risk `Beta`

Detects negative sentiment towards a brand. Identifies prompts that could generate brand-damaging content or misrepresent organizational positions.

- **Category:** General
- **Severity:** Medium

### Text

Detects and blocks sensitive text using regex patterns. Allows custom pattern matching for organization-specific content policies.

- **Category:** General
- **Severity:** Configurable

### Gibberish `Multilingual`

Identifies and filters out nonsensical or meaningless text. Catches encoded payloads, obfuscated content, and deliberately mangled text that may indicate evasion attempts.

- **Category:** General
- **Severity:** Medium

### Competition `Beta`

Prevents the inclusion of competitor names in the prompts submitted by users. Enforces brand and competitive boundaries in AI interactions.

- **Category:** General
- **Severity:** Low to Medium

### Language `Multilingual`

Detects and blocks unwanted languages across your platforms. Enforces language policies to keep interactions within approved languages.

- **Category:** General
- **Severity:** Low

### Legal Advice

Blocks prompts seeking legal advice, interpretation, or compliance guidance. Allows neutral legal facts, definitions, and non-legal work inquiries.

- **Category:** Content Moderation
- **Severity:** Medium

### Intellectual Property

Filters and controls content for intellectual property. Detects prompts that could lead to IP infringement, trade secret disclosure, or unauthorized use of proprietary content.

- **Category:** Content Moderation
- **Severity:** High

### Secrets

Detects and blocks sensitive information such as API keys, tokens, passwords, connection strings, and other credentials in user prompts.

- **Category:** Security
- **Severity:** High

### Off Topic `Beta`

Filters and controls content by topic description. Keeps AI interactions within the defined scope of the application's intended use.

- **Category:** Content Moderation
- **Severity:** Low

### PII

Detects and blocks PII entities such as email addresses, Social Security Numbers, phone numbers, and other personally identifiable information.

- **Category:** Security
- **Severity:** High

### Personal Data

Identifies sensitive personal attributes and blocks invasive questions or confirmations about identity, background, or affiliations. Covers nationality/citizenship, criminal record, ethnicity, genetic/medical information, and other protected personal data.

- **Category:** Security
- **Severity:** High

### PII DeepScan

Detects and blocks attempts to share or solicit high-risk identifiers that directly expose financial, legal, or digital identity. Covers SSN, ITIN, passport, driver's license, credit card, US bank account numbers, and similar high-sensitivity identifiers.

- **Category:** Security
- **Severity:** Critical

### Topic

Filters and controls content by identifying custom topics. Allows organizations to define their own topic boundaries and enforce them.

- **Category:** Content Moderation
- **Severity:** Configurable

### Invisible Text

Identifies hidden or obscured text within digital content. Catches Unicode tricks, zero-width characters, and steganographic techniques used to embed hidden instructions.

- **Category:** Security
- **Severity:** High

### Finance Advice `Multilingual`

Blocks actionable financial guidance (investing, trading, tax, product choices). Allows neutral finance facts, history, and definitions. Prevents the AI from providing specific financial recommendations.

- **Category:** Content Moderation
- **Severity:** Medium

### Prompt Tags

Filters and controls prompts by predefined tags. Enables tag-based policy enforcement for categorized content handling.

- **Category:** General
- **Severity:** Configurable

---

## Response Detectors (Direction: OUT)

Detectors that analyze AI-generated output before it reaches the user.

### Toxicity `Multilingual`

Detects and filters harmful language in AI responses.

- **Category:** Toxicity
- **Severity:** Medium to High

### Code `Beta`

Detects and blocks unwanted programming languages across your platforms in AI-generated responses. Prevents the AI from generating code in restricted languages.

- **Category:** Security
- **Severity:** Medium

### Malicious URL

Identifies URLs with domains categorized as malicious. Catches phishing, malware distribution, command-and-control, and other threat URLs in AI responses.

- **Category:** Security
- **Severity:** Critical

### Response Tags

Filters and controls prompt responses by predefined tags. Enables tag-based enforcement on AI outputs.

- **Category:** General
- **Severity:** Configurable

### Brand and Reputation Risk `Beta`

Detects negative sentiment towards a brand in AI-generated responses.

- **Category:** General
- **Severity:** Medium

### Refusal

Identifies LLM refusal patterns. Detects when the AI model refuses to answer or comply, enabling policy-based handling of refusals.

- **Category:** General
- **Severity:** Low

### Text

Detects and blocks sensitive text using regex patterns in AI responses.

- **Category:** General
- **Severity:** Configurable

### Gibberish `Multilingual`

Identifies and filters out nonsensical or meaningless text in AI responses.

- **Category:** General
- **Severity:** Medium

### Competition `Beta`

Prevents the inclusion of competitor names in AI-generated responses.

- **Category:** General
- **Severity:** Low to Medium

### Language `Multilingual`

Detects and blocks unwanted languages in AI responses.

- **Category:** General
- **Severity:** Low

### Legal Advice

Blocks prompts seeking legal advice, interpretation, or compliance guidance in AI responses. Allows neutral legal facts, definitions, and non-legal work inquiries.

- **Category:** Content Moderation
- **Severity:** Medium

### Intellectual Property

Filters and controls content for intellectual property in AI responses.

- **Category:** Content Moderation
- **Severity:** High

### Secrets `Beta`

Detects and blocks sensitive information such as API keys in AI-generated responses. Catches cases where the AI may hallucinate or leak credentials.

- **Category:** Security
- **Severity:** High

### Off Topic `Beta`

Filters and controls content by topic description in AI responses.

- **Category:** Content Moderation
- **Severity:** Low

### PII

Detects and blocks PII entities such as email and SSN in AI responses. Catches cases where the AI may hallucinate realistic PII patterns.

- **Category:** Security
- **Severity:** High

### Personal Data

Identifies sensitive personal attributes in AI responses. Prevents the AI from generating invasive personal data.

- **Category:** Security
- **Severity:** High

### PII DeepScan

Detects and blocks attempts to share or solicit high-risk identifiers that directly expose financial, legal, or digital identity in AI responses. Covers SSN, ITIN, passport, driver's license, credit card, US bank account numbers.

- **Category:** Security
- **Severity:** Critical

### Topic

Filters and controls content by identifying custom topics in AI responses.

- **Category:** Content Moderation
- **Severity:** Configurable

### URL Reachability

Verifies that URLs in AI responses are accessible and functioning correctly by continuously testing and verifying link status in real time. Catches hallucinated or dead URLs.

- **Category:** General
- **Severity:** Low to Medium

### Invisible Text

Identifies hidden or obscured text within AI-generated digital content.

- **Category:** Security
- **Severity:** High

### Finance Advice `Multilingual`

Blocks actionable financial guidance in AI responses. Allows neutral finance facts, history, and definitions.

- **Category:** Content Moderation
- **Severity:** Medium

---

## Detector Categories

Detectors are organized into the following filter categories in the AI Guard Console:

| Category | Description |
|----------|-------------|
| **Toxicity** | Harmful language detection |
| **General** | Text patterns, gibberish, language, competition, brand risk, tags, refusal, URL reachability |
| **Security** | Prompt injection, code, secrets, PII, PII DeepScan, personal data, invisible text |
| **Content Moderation** | Legal advice, intellectual property, off topic, topic, finance advice |

## Notes

- Detectors marked `Multilingual` support detection across multiple languages.
- Detectors marked `Beta` are in active development and may evolve.
- Both Prompt and Response detectors can be independently configured with different actions (Allow, Detect, Block) per policy.
- The `Text` detector supports custom regex patterns defined per organization.
- `Topic` and `Off Topic` are distinct: Topic uses custom topic definitions; Off Topic uses a topic description boundary.
- `PII`, `Personal Data`, and `PII DeepScan` have increasing specificity — PII covers common identifiers, Personal Data covers attributes and affiliations, PII DeepScan targets high-risk financial/legal/digital identity documents.
