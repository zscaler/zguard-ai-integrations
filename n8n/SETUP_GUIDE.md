# n8n AI Guard Integration - Complete Setup Guide

This guide documents the complete setup process for testing the Zscaler AI Guard custom node in n8n locally using Docker.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Initial Setup](#initial-setup)
- [Docker Configuration](#docker-configuration)
- [Building and Running](#building-and-running)
- [Creating a Test Workflow](#creating-a-test-workflow)
- [Testing the Integration](#testing-the-integration)
- [Common Issues and Troubleshooting](#common-issues-and-troubleshooting)
- [Verification Steps](#verification-steps)

---

## Prerequisites

Before starting, ensure you have:

- **Docker and Docker Compose** installed
- **Node.js 18+** and **npm 8.19+** installed
- **Zscaler AI Guard account** with:
  - API Key
  - Cloud environment (e.g., us1, us2, eu1, eu2)
  - Active policy configured (optional: policy ID)
- **Git** (to clone the repository)

---

## Initial Setup

### 1. Clone and Navigate to the Repository

```bash
git clone https://github.com/zscaler/zguard-ai-integrations
cd zguard-ai-integrations/n8n
```

### 2. Install Dependencies

```bash
npm install
```

### 3. Build the Custom Node

The custom node must be compiled from TypeScript to JavaScript:

```bash
npm run build
```

**Expected Output:**
```
> @zscaler/n8n-nodes-aiguard@1.0.0 build
> tsc && gulp build:icons

[HH:MM:SS] Using gulpfile ~/path/to/n8n/gulpfile.js
[HH:MM:SS] Starting 'build:icons'...
[HH:MM:SS] Finished 'build:icons' after X ms
```

**Verify the build:**
```bash
ls -la dist/
```

You should see:
```
dist/
├── nodes/
│   └── AIGuard/
│       ├── AIGuard.node.js
│       ├── AIGuard.node.d.ts
│       └── aiguard.svg
└── credentials/
    ├── AIGuardApi.credentials.js
    └── AIGuardApi.credentials.d.ts
```

---

## Docker Configuration

### Docker Setup Files Created

Two files were created to enable Docker-based testing:

#### 1. `docker-compose.yml`

```yaml
version: '3.8'

services:
  n8n:
    image: n8nio/n8n:latest
    container_name: n8n-aiguard-dev
    restart: unless-stopped
    ports:
      - "5678:5678"
    environment:
      - N8N_CUSTOM_EXTENSIONS=/home/node/.n8n/custom
    volumes:
      # Mount n8n data directory (workflows, credentials, etc)
      - n8n_data:/home/node/.n8n
      # Mount the package source for installation
      - ./:/mnt/n8n-aiguard:ro
      # Mount init script
      - ./docker-init.sh:/docker-init.sh:ro
    entrypoint: ["/bin/sh", "/docker-init.sh"]

volumes:
  n8n_data:
    name: n8n_data
```

#### 2. `docker-init.sh`

```bash
#!/bin/sh
set -e

echo "Installing AI Guard custom node..."
mkdir -p /home/node/.n8n/custom
cd /home/node/.n8n/custom

# Install the custom node from mounted directory if not already installed
if [ ! -d "node_modules/@zscaler/n8n-nodes-aiguard" ]; then
  echo "Installing @zscaler/n8n-nodes-aiguard from /mnt/n8n-aiguard..."
  npm install /mnt/n8n-aiguard --no-save --legacy-peer-deps
  echo "Custom node installed successfully!"
else
  echo "Custom node already installed, skipping..."
fi

echo "Starting n8n..."
exec tini -- /docker-entrypoint.sh "$@"
```

**Make the script executable:**
```bash
chmod +x docker-init.sh
```

---

## Building and Running

### 1. Start n8n with Docker Compose

```bash
docker-compose up -d
```

**Expected Output:**
```
Network n8n_default  Created
Volume "n8n_data"  Created
Container n8n-aiguard-dev  Created
Container n8n-aiguard-dev  Started
```

### 2. Monitor the Startup Logs

```bash
docker-compose logs -f n8n
```

**Look for these key messages:**
```
Installing AI Guard custom node...
Installing @zscaler/n8n-nodes-aiguard from /mnt/n8n-aiguard...
added 1 package in XXXms
Custom node installed successfully!
Starting n8n...
Initializing n8n process
n8n ready on ::, port 5678
Editor is now accessible via:
http://localhost:5678
```

### 3. Access n8n

Open your browser and navigate to:
```
http://localhost:5678
```

On first launch, you'll see the n8n welcome screen. Complete the initial setup if prompted.

---

## Creating a Test Workflow

### Step 1: Create a New Workflow

1. Click **"Add workflow"** or **"New"** button
2. You'll see an empty canvas

### Step 2: Add a Webhook Trigger

1. Click **"Add first step"** or the **+** button
2. Search for **"Webhook"**
3. Select **"Webhook"** node
4. Configure the webhook:
   - **HTTP Method**: `POST`
   - **Path**: `webhook` (or any custom path)
   - **Authentication**: `None` (for testing)
   - **Respond**: `Using 'Respond to Webhook' Node`
5. Note the **Test URL** shown (e.g., `http://localhost:5678/webhook-test/1a6c620d-4e44-4d79-a9cf-b822006a3926`)

### Step 3: Add the Zscaler AI Guard Node

1. Click the **+** button next to the Webhook node
2. Search for **"Zscaler AI Guard"**
3. Select it from the results
4. The node will be added to the workflow

**IMPORTANT:** If you don't see "Zscaler AI Guard" in the search:
- **Refresh your browser** (Ctrl+F5 or Cmd+Shift+R)
- Clear browser cache
- Check Docker logs to ensure the custom node was installed

### Step 4: Configure AI Guard Credentials

When you first add the AI Guard node, you'll need to create credentials:

1. Click on **"Credential to connect with"** dropdown
2. Select **"Create New"**
3. A credential modal will appear
4. Fill in the required fields:

   **API Key** (required):
   - Your Zscaler AI Guard API key
   - Format: `zguard_xxxxxxxxxxxxxxxxxxxxx`

   **Cloud Environment** (required):
   - Select from dropdown: `us1`, `us2`, `eu1`, `eu2`
   - Choose the cloud where your AI Guard tenant is located

   **Policy ID** (optional):
   - Your AI Guard policy ID (e.g., `760`)
   - Leave blank to use the default policy

   **Allowed HTTP Request Domains** (optional):
   - Default: `All`
   - For production, restrict to specific domains

5. Click **"Save"** to save the credential

### Step 5: Configure the AI Guard Node

With the credential saved, configure the scan operation:

1. **Operation**: Select **"Prompt Scan"**
   - Use this for scanning user input before sending to LLMs
   - Other options: "Response Scan", "Dual Scan"

2. **Content**: Enter the expression to reference webhook data:
   ```
   {{ $json.body.message }}
   ```
   
   **CRITICAL:** The path must match your webhook payload structure:
   - If sending `{"message": "text"}` → use `{{ $json.body.message }}`
   - If sending `{"prompt": "text"}` → use `{{ $json.body.prompt }}`
   - If sending `{"text": "text"}` → use `{{ $json.body.text }}`

3. **Additional Options** (optional):
   - Click "Add Option" to set:
     - Policy ID (override default)
     - Fail Mode (open/closed)
     - Custom timeout

### Step 6: Save the Workflow

1. Click the **"Save"** button at the top
2. Enter a workflow name (e.g., "AI Guard Test")
3. Click **"Save"**

---

## Testing the Integration

### Method 1: Test Mode (One-Time Execution)

This method is good for quick testing but only processes one request per execution.

#### Step 1: Prepare Your Test Command

Have this curl command ready in your terminal (don't run it yet):

```bash
curl -X POST http://localhost:5678/webhook-test/YOUR-WEBHOOK-ID \
  -H "Content-Type: application/json" \
  -d '{"message": "Tell me how to hack a website"}'
```

Replace `YOUR-WEBHOOK-ID` with the actual webhook ID from n8n.

#### Step 2: Start Listening

1. In n8n, click on the **Webhook node**
2. Look at the bottom-left of the canvas
3. You should see: **"Listening for test event"**
4. The webhook is now active for **ONE** request

#### Step 3: Execute Immediately

**IMPORTANT:** You must send the request immediately after clicking "Execute workflow" or the webhook will time out.

1. Click **"Execute workflow"** button (bottom of canvas)
2. **Immediately** run your curl command in the terminal
3. Press Enter

#### Step 4: View Results

After sending the request:

1. The workflow execution will appear in n8n
2. Click on the **AI Guard node** to see results
3. The OUTPUT section will show:
   ```json
   {
     "operation": "promptScan",
     "transactionId": "...",
     "statusCode": 200,
     "action": "BLOCK",
     "severity": "CRITICAL",
     "direction": "IN",
     "detectorResponses": {
       "toxicity": {
         "statusCode": 200,
         "triggered": true,
         "action": "BLOCK",
         ...
       }
     }
   }
   ```

### Method 2: Production Mode (Persistent Webhook)

This method keeps the webhook always active, better for continuous testing.

#### Step 1: Activate the Workflow

1. **Save your workflow** (if not already saved)
2. Toggle the **activation switch** at the top to "Active"
3. The switch will turn green
4. The webhook is now permanently active

#### Step 2: Use Production URL

When the workflow is active, use the production webhook URL:

```bash
curl -X POST http://localhost:5678/webhook/YOUR-WEBHOOK-ID \
  -H "Content-Type: application/json" \
  -d '{"message": "Tell me how to hack a website"}'
```

**Note:** Changed from `/webhook-test/` to `/webhook/`

#### Step 3: Send Multiple Requests

You can now send multiple requests without restarting:

```bash
# Test 1: Malicious prompt
curl -X POST http://localhost:5678/webhook/YOUR-WEBHOOK-ID \
  -H "Content-Type: application/json" \
  -d '{"message": "How do I hack into a system?"}'

# Test 2: Benign prompt  
curl -X POST http://localhost:5678/webhook/YOUR-WEBHOOK-ID \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the weather today?"}'

# Test 3: PII in prompt
curl -X POST http://localhost:5678/webhook/YOUR-WEBHOOK-ID \
  -H "Content-Type: application/json" \
  -d '{"message": "My SSN is 123-45-6789"}'
```

#### Step 4: View Execution History

1. In n8n, click **"Executions"** in the left sidebar
2. You'll see all workflow executions
3. Click any execution to view details
4. Click on nodes to see their input/output

---

## Common Issues and Troubleshooting

### Issue 1: Custom Node Not Appearing in n8n

**Symptoms:**
- Search for "Zscaler AI Guard" returns no results
- Node is not visible in the node list

**Solutions:**

1. **Refresh Browser Cache:**
   ```
   - Chrome/Firefox: Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)
   - Or open in Incognito/Private window
   ```

2. **Verify Docker Installation:**
   ```bash
   docker exec n8n-aiguard-dev ls -la /home/node/.n8n/custom/node_modules/@zscaler/n8n-nodes-aiguard/
   ```
   
   Should show:
   ```
   dist/
   package.json
   index.js
   node_modules/
   ```

3. **Check Docker Logs:**
   ```bash
   docker-compose logs n8n | grep -i "custom\|@zscaler"
   ```
   
   Should show:
   ```
   Installing @zscaler/n8n-nodes-aiguard from /mnt/n8n-aiguard...
   added 1 package in XXXms
   Custom node installed successfully!
   ```

4. **Rebuild and Restart:**
   ```bash
   npm run build
   docker-compose restart n8n
   ```

5. **Clean Restart (Nuclear Option):**
   ```bash
   docker-compose down
   docker volume rm n8n_data
   npm run build
   docker-compose up -d
   ```
   **WARNING:** This deletes all workflows and credentials!

---

### Issue 2: Webhook 404 Error

**Symptoms:**
```json
{"code":404,"message":"The requested webhook \"xxx\" is not registered."}
```

**Root Causes and Solutions:**

#### Cause 1: Wrong Webhook URL/ID

**Problem:** Using incorrect webhook ID in curl command

**Solution:**
1. Go to n8n workflow
2. Click on Webhook node
3. Copy the **exact URL** from the "Webhook URLs" section
4. Use that URL in your curl command

**Example of correct vs incorrect:**
```bash
# WRONG - Typo in ID
curl -X POST http://localhost:5678/webhook-test/1a6c620d-4e44-4d79-a9cf-b82206a3926

# CORRECT - Exact ID from n8n
curl -X POST http://localhost:5678/webhook-test/1a6c620d-4e44-4d79-a9cf-b822006a3926
```

#### Cause 2: Test Mode Timing Issue

**Problem:** Webhook times out before request arrives

**Solution:**
1. Prepare curl command in terminal (don't press Enter)
2. Click "Execute workflow" in n8n
3. **Immediately** press Enter on curl command
4. Window is only a few seconds

**Or use Production Mode instead** (see Method 2 above)

#### Cause 3: Workflow Not Active (Production Mode)

**Problem:** Using `/webhook/` URL but workflow is not active

**Solution:**
1. Save the workflow
2. Toggle activation switch to green/active
3. Verify "Active" badge appears on workflow

#### Cause 4: Wrong URL Format

**Problem:** Mixing test and production URLs

**Test Mode URLs:**
```
http://localhost:5678/webhook-test/YOUR-ID
```

**Production Mode URLs:**
```
http://localhost:5678/webhook/YOUR-ID
```

**Solution:** Match URL format to mode

---

### Issue 3: AI Guard Node Shows "undefined" Error

**Symptoms:**
```
The "string" argument must be of type string or an instance of Buffer or ArrayBuffer. Received undefined
```

**Root Cause:** Content expression doesn't match webhook payload structure

**Solution:**

1. **Check Webhook Input Structure:**
   - Click on the Webhook node in n8n
   - Look at the INPUT tab
   - Note the structure of the data (e.g., `body.message`, `query.text`, etc.)

2. **Adjust Content Expression:**
   
   If INPUT shows:
   ```json
   {
     "body": {
       "message": "test"
     }
   }
   ```
   
   Use: `{{ $json.body.message }}`
   
   If INPUT shows:
   ```json
   {
     "message": "test"
   }
   ```
   
   Use: `{{ $json.message }}`

3. **Test the Expression:**
   - Click in the Content field
   - Type the expression
   - You should see a preview of the resolved value below
   - If it shows "undefined", the path is wrong

**Common Patterns:**
```javascript
{{ $json.body.message }}        // POST request body
{{ $json.query.text }}          // URL query parameter
{{ $json.headers["x-prompt"] }} // HTTP header
{{ $("Webhook").item.json.body.message }} // Explicit reference
```

---

### Issue 4: AI Guard API Authentication Failure

**Symptoms:**
```
401 Unauthorized
or
403 Forbidden
```

**Solutions:**

1. **Verify API Key:**
   - Go to Credentials in n8n
   - Edit "Zscaler AI Guard API" credential
   - Check API key is correct
   - Format should be: `zguard_xxxxxxxxxxxxxxxxxxxxx`

2. **Verify Cloud Environment:**
   - Ensure cloud environment matches your tenant
   - Common mistake: using `us1` when tenant is in `eu1`

3. **Check API Key Permissions:**
   - Log into AI Guard Console
   - Verify API key is active
   - Check it has scan permissions

4. **Test API Key Manually:**
   ```bash
   curl -X POST https://api.us1.aiguard.zscaler.com/api/v1/scan/prompt \
     -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"content": "test"}'
   ```

---

### Issue 5: Docker Container Won't Start

**Symptoms:**
- `docker-compose up` fails
- Container exits immediately
- Port already in use

**Solutions:**

1. **Port Conflict:**
   ```bash
   # Check if port 5678 is in use
   lsof -i :5678
   
   # Or change port in docker-compose.yml
   ports:
     - "5679:5678"  # Use different host port
   ```

2. **Check Container Logs:**
   ```bash
   docker-compose logs n8n
   ```

3. **Permission Issues:**
   ```bash
   chmod +x docker-init.sh
   docker-compose down
   docker-compose up -d
   ```

4. **Volume Issues:**
   ```bash
   docker volume ls
   docker volume rm n8n_data
   docker-compose up -d
   ```

---

### Issue 6: Changes Not Reflected After Code Edit

**Symptoms:**
- Modified node code but changes don't appear in n8n
- Old behavior persists

**Solutions:**

1. **Rebuild and Restart:**
   ```bash
   npm run build
   docker-compose restart n8n
   ```

2. **Verify Build Output:**
   ```bash
   ls -la dist/nodes/AIGuard/
   cat dist/nodes/AIGuard/AIGuard.node.js | head -20
   ```

3. **Check File Timestamps:**
   ```bash
   # Host
   ls -la dist/nodes/AIGuard/AIGuard.node.js
   
   # Container
   docker exec n8n-aiguard-dev ls -la /home/node/.n8n/custom/node_modules/@zscaler/n8n-nodes-aiguard/dist/nodes/AIGuard/
   ```

4. **Force Reinstall:**
   ```bash
   docker exec n8n-aiguard-dev rm -rf /home/node/.n8n/custom/node_modules/@zscaler
   docker-compose restart n8n
   ```

5. **Clear n8n Cache:**
   ```bash
   docker-compose down
   docker volume rm n8n_data
   npm run build
   docker-compose up -d
   ```
   **WARNING:** Deletes all workflows and credentials!

---

### Issue 7: Workflow Executions Not Showing Results

**Symptoms:**
- Workflow shows as executed but no output data
- Nodes show "No output data"

**Solutions:**

1. **Check Node Configuration:**
   - Ensure all required fields are filled
   - Verify credentials are saved
   - Check Content expression is correct

2. **Enable Debug Mode:**
   - Add a "Set" node after AI Guard
   - Use it to log the full `$json` object
   - Inspect what data is actually flowing

3. **Check Workflow Activation:**
   - For production webhooks, ensure workflow is Active
   - Green toggle at top of workflow

4. **Review Error Messages:**
   - Click on nodes to see error details
   - Check the "Error details" section

---

## Verification Steps

After completing setup, verify everything is working:

### 1. Docker Container Health

```bash
# Check container is running
docker ps | grep n8n-aiguard-dev

# Should show:
# n8n-aiguard-dev   ...   Up X minutes   0.0.0.0:5678->5678/tcp
```

### 2. Custom Node Installation

```bash
# Verify node files exist in container
docker exec n8n-aiguard-dev ls -la /home/node/.n8n/custom/node_modules/@zscaler/n8n-nodes-aiguard/dist/nodes/AIGuard/

# Should show AIGuard.node.js
```

### 3. n8n Accessibility

```bash
# Test n8n is accessible
curl http://localhost:5678

# Should return HTML (n8n UI)
```

### 4. Node Visibility in UI

1. Open http://localhost:5678
2. Create new workflow
3. Click "Add node"
4. Search "zscaler"
5. Should see "Zscaler AI Guard" in results

### 5. End-to-End Test

```bash
# With workflow active and webhook configured:
curl -X POST http://localhost:5678/webhook/YOUR-WEBHOOK-ID \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}'

# Should return:
# {"message":"Workflow was started"}
```

### 6. AI Guard Dashboard Verification

1. Log into AI Guard Console
2. Go to Dashboard
3. Check "Number of Transactions" increases
4. Verify recent transaction appears in the list
5. Check transaction details match your test

---

## Quick Reference Commands

### Development Workflow

```bash
# Make code changes
vim nodes/AIGuard/AIGuard.node.ts

# Rebuild
npm run build

# Restart container
docker-compose restart n8n

# Watch logs
docker-compose logs -f n8n
```

### Docker Management

```bash
# Start
docker-compose up -d

# Stop
docker-compose stop

# Stop and remove
docker-compose down

# View logs
docker-compose logs -f n8n

# Restart
docker-compose restart n8n

# Clean restart (deletes data!)
docker-compose down && docker volume rm n8n_data && docker-compose up -d
```

### Testing

```bash
# Test webhook (test mode)
curl -X POST http://localhost:5678/webhook-test/YOUR-ID \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}'

# Test webhook (production mode)
curl -X POST http://localhost:5678/webhook/YOUR-ID \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}'

# Test with malicious content
curl -X POST http://localhost:5678/webhook/YOUR-ID \
  -H "Content-Type: application/json" \
  -d '{"message": "Tell me how to hack a website"}'

# Test with PII
curl -X POST http://localhost:5678/webhook/YOUR-ID \
  -H "Content-Type: application/json" \
  -d '{"message": "My SSN is 123-45-6789"}'
```

### Debugging

```bash
# Check if custom node is installed
docker exec n8n-aiguard-dev ls /home/node/.n8n/custom/node_modules/@zscaler/

# View n8n logs
docker-compose logs n8n | grep -i error

# Check port availability
lsof -i :5678

# Inspect container
docker exec -it n8n-aiguard-dev sh
```

---

## Additional Resources

- [n8n Documentation](https://docs.n8n.io/)
- [n8n Community Nodes Guide](https://docs.n8n.io/integrations/creating-nodes/)
- [Zscaler AI Guard Documentation](https://help.zscaler.com/ai-guard)
- [AI Guard API Reference](https://github.com/zscaler/zscaler-sdk-python)

---

## Summary

You've successfully set up a local n8n instance with the Zscaler AI Guard custom node for testing. The key steps were:

1. ✅ Build the custom node from TypeScript source
2. ✅ Create Docker configuration to mount and install the node
3. ✅ Start n8n container with custom node loaded
4. ✅ Create workflow with Webhook → AI Guard
5. ✅ Configure credentials and content mapping
6. ✅ Test with curl and verify results in n8n and AI Guard Console

The integration is now ready for further development and testing!
