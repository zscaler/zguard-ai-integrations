# Azure Integration Troubleshooting

## Error: Cannot find a property 'AIGUARD-CLOUD'

### Symptoms
When creating the policy fragment, you get:
```
Error in element 'set-url' on line 188, column 26: Cannot find a property 'AIGUARD-CLOUD'
```

### Cause
The Named Value `AIGUARD-CLOUD` is not found by Azure APIM.

### Solution

#### Step 1: Verify Named Values Exist

1. Go to **Named values** in the left menu
2. Check that you have EXACTLY these names (case-sensitive):
   - `AIGUARD-API-KEY`
   - `AIGUARD-CLOUD`
   - `AIGUARD-POLICY-ID`

#### Step 2: Check Exact Names

Named Values in Azure are **case-sensitive**. They must be EXACTLY:

```
✅ AIGUARD-CLOUD (correct)
❌ aiguard-cloud (wrong - lowercase)
❌ AIGuard-Cloud (wrong - mixed case)
❌ AIGUARD_CLOUD (wrong - underscore instead of hyphen)
```

#### Step 3: Verify Scope

Named Values must be at the **APIM service level**, not scoped to specific APIs.

#### Step 4: Create Missing Named Values

If any are missing, create them:

**AIGUARD-API-KEY** (Secret):
```
Name: AIGUARD-API-KEY
Display name: AI Guard API Key
Type: Secret ✅
Value: <your-ai-guard-api-key>
```

**AIGUARD-CLOUD** (Plain):
```
Name: AIGUARD-CLOUD
Display name: AI Guard Cloud Environment
Type: Plain
Value: us1
```

**AIGUARD-POLICY-ID** (Plain):
```
Name: AIGUARD-POLICY-ID
Display name: AI Guard Policy ID
Type: Plain
Value: 760
```

## Alternative: Use Hardcoded Values for Testing

If you want to test quickly without Named Values, you can temporarily hardcode values in the policy fragment.

### Find and Replace in Policy Fragment

**Line ~188** - Replace:
```xml
<!-- BEFORE (using Named Value) -->
<set-url>@{
    string cloud = "{{AIGUARD-CLOUD}}";
    return $"https://api.{cloud}.zseclipse.net/v1/detection/execute-policy";
}</set-url>

<!-- AFTER (hardcoded for testing) -->
<set-url>https://api.us1.zseclipse.net/v1/detection/execute-policy</set-url>
```

**Line ~196** - Replace:
```xml
<!-- BEFORE -->
<set-header name="Authorization" exists-action="override">
    <value>Bearer {{AIGUARD-API-KEY}}</value>
</set-header>

<!-- AFTER (hardcoded for testing) -->
<set-header name="Authorization" exists-action="override">
    <value>Bearer {{aiguard-api-key}}</value>
</set-header>
```

**Line ~210** - Replace:
```xml
<!-- BEFORE -->
var policyId = context.Variables.GetValueOrDefault("currentPolicy", "{{AIGUARD-POLICY-ID}}");

<!-- AFTER -->
var policyId = context.Variables.GetValueOrDefault("currentPolicy", "760");
```

⚠️ **WARNING**: This is only for testing! Use Named Values in production for security.

## Error: Timeout or 503 Service Unavailable

### Symptoms
Requests fail with 503 or timeout after adding the policy.

### Possible Causes
1. AI Guard API unreachable from Azure
2. Invalid API key
3. Network/firewall blocking zseclipse.net
4. Policy syntax error causing infinite loop

### Solution

#### Test AI Guard API Connectivity

From Azure Cloud Shell or local machine:
```bash
curl -X POST "https://api.us1.zseclipse.net/v1/detection/execute-policy" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "test",
    "direction": "IN",
    "policyId": 760
  }'
```

Expected response:
```json
{
  "action": "ALLOW",
  "transactionId": "...",
  "severity": null
}
```

#### Check APIM Outbound Connectivity

Ensure your APIM instance can reach `*.zseclipse.net`:
- Check virtual network settings if using VNet integration
- Verify no NSG rules blocking outbound HTTPS
- Check if firewall rules allow zseclipse.net

#### Verify API Key

Test your API key is valid in AI Guard Console.

## Error: All Requests Return 403

### Symptoms
Even safe prompts are blocked with 403.

### Possible Causes
1. Policy too restrictive
2. Wrong policy ID
3. All detectors set to BLOCK

### Solution

1. **Check AI Guard Policy**
   - Log in to AI Guard Console
   - Verify policy 760 exists and is active
   - Check detector configurations
   - Test with curl to AI Guard API directly

2. **Enable Fail-Open Temporarily**
   ```xml
   <set-variable name="FailOpen" value="true" />
   ```

3. **Check Azure APIM Traces**
   - Enable tracing in Test tab
   - Look for AI Guard API response
   - Check what detectors are triggering

## Error: Policy Syntax Invalid

### Symptoms
XML validation errors when saving policy.

### Solution

1. **Check XML is Well-Formed**
   - All tags properly closed
   - Quotes escaped correctly (`&quot;` instead of `"` in XML attributes)
   - No unclosed C# code blocks

2. **Common Syntax Issues**
   ```xml
   ❌ WRONG:
   <when condition="@(condition == "value")">
   
   ✅ CORRECT:
   <when condition="@(condition == &quot;value&quot;)">
   ```

3. **Validate Fragment Independently**
   - Copy policy to a text editor
   - Check XML syntax
   - Ensure all `<choose>` blocks have matching `</choose>`

## Get Help

If issues persist:

1. **Check Azure APIM Logs**
   - Application Insights
   - APIM Activity Log
   
2. **Enable Verbose Tracing**
   - Add `<trace>` statements to see execution flow

3. **Test AI Guard API Directly**
   - Bypass APIM temporarily
   - Verify AI Guard is working

4. **Contact Support**
   - Zscaler Support for AI Guard issues
   - Microsoft Support for Azure APIM issues
