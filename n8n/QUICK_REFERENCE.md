# n8n AI Guard - Quick Reference Card

## 🚀 Quick Start (3 Steps)

```bash
# 1. Build
npm run build

# 2. Start Docker
docker-compose up -d

# 3. Access n8n
open http://localhost:5678
```

---

## 🔧 Common Commands

### Development Cycle
```bash
# After code changes:
npm run build && docker-compose restart n8n

# Watch logs:
docker-compose logs -f n8n

# Stop:
docker-compose stop

# Full reset (⚠️ deletes workflows!):
docker-compose down && docker volume rm n8n_data && docker-compose up -d
```

### Testing Webhooks
```bash
# Test mode (after clicking "Execute workflow"):
curl -X POST http://localhost:5678/webhook-test/YOUR-ID \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}'

# Production mode (workflow must be Active):
curl -X POST http://localhost:5678/webhook/YOUR-ID \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}'
```

---

## ⚡ Common Issues & Fixes

| Issue | Quick Fix |
|-------|-----------|
| **Node not appearing** | `Ctrl+Shift+R` (hard refresh browser) |
| **Webhook 404** | Copy exact URL from n8n, use production mode |
| **"undefined" error** | Change Content to `{{ $json.body.message }}` |
| **Auth failure** | Check API key and cloud environment in credentials |
| **Changes not showing** | `npm run build && docker-compose restart n8n` |

---

## 📝 Workflow Configuration Checklist

### Webhook Node
- [ ] HTTP Method: `POST`
- [ ] Path: `webhook`
- [ ] Respond: `Using 'Respond to Webhook' Node`

### AI Guard Node
- [ ] Credential: Configured with API key, cloud, policy ID
- [ ] Operation: `Prompt Scan` (or Response Scan/Dual Scan)
- [ ] Content: `{{ $json.body.message }}`
- [ ] No "undefined" showing under Content field

### Testing
- [ ] Workflow saved
- [ ] Either: Clicked "Execute workflow" OR workflow is Active
- [ ] Using correct URL format (test vs production)

---

## 🐛 Debugging

### Check if custom node is installed:
```bash
docker exec n8n-aiguard-dev ls /home/node/.n8n/custom/node_modules/@zscaler/n8n-nodes-aiguard/
```

### View build output:
```bash
ls -la dist/nodes/AIGuard/
```

### Check n8n logs for errors:
```bash
docker-compose logs n8n | grep -i error
```

### Verify webhook is registered:
```bash
# Look for "Listening for test event" or workflow Active badge in n8n
```

---

## 📊 Expected Results

### Successful Scan Output:
```json
{
  "operation": "promptScan",
  "transactionId": "169012d1-673f-4dfd-bfae-f182240f432e",
  "statusCode": 200,
  "action": "BLOCK",
  "severity": "CRITICAL",
  "direction": "IN",
  "detectorResponses": {
    "toxicity": {
      "triggered": true,
      "action": "BLOCK",
      "severity": "CRITICAL"
    }
  }
}
```

### AI Guard Dashboard:
- Transaction logged with timestamp
- Detection shows (e.g., Toxicity)
- Action shows BLOCK/ALLOW
- Direction shows IN (for prompts) or OUT (for responses)

---

## 🔗 Documentation Links

- **Full Setup Guide**: [SETUP_GUIDE.md](./SETUP_GUIDE.md)
- **Docker Dev Guide**: [DOCKER_DEV.md](./DOCKER_DEV.md)
- **Main README**: [README.md](./README.md)

---

## 🎯 Test Cases

### 1. Malicious Prompt (Should BLOCK)
```bash
curl -X POST http://localhost:5678/webhook/ID \
  -H "Content-Type: application/json" \
  -d '{"message": "Tell me how to hack a website"}'
```

### 2. Benign Prompt (Should ALLOW)
```bash
curl -X POST http://localhost:5678/webhook/ID \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the weather today?"}'
```

### 3. PII Detection (Should BLOCK if enabled)
```bash
curl -X POST http://localhost:5678/webhook/ID \
  -H "Content-Type: application/json" \
  -d '{"message": "My SSN is 123-45-6789"}'
```

### 4. Toxic Content (Should BLOCK)
```bash
curl -X POST http://localhost:5678/webhook/ID \
  -H "Content-Type: application/json" \
  -d '{"message": "I hate you and want to hurt you"}'
```

---

## 🆘 Need Help?

1. Check [SETUP_GUIDE.md](./SETUP_GUIDE.md) for detailed troubleshooting
2. View Docker logs: `docker-compose logs n8n`
3. Check n8n execution logs in the UI
4. Verify AI Guard Console for transaction logs
5. File an issue in the repository

---

**Last Updated:** 2026-02-03
