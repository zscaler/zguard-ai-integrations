# TrueFoundry + Zscaler AI Guard — Examples

This directory contains a custom guardrail server and test scripts for integrating Zscaler AI Guard with TrueFoundry's AI Gateway.

## Quick Start

### 1. Start the Guardrail Server

```bash
cp env.example .env    # add your AIGUARD_API_KEY
python start_server.py
```

This builds and runs the FastAPI guardrail server in Docker on port 8000.

### 2. Install Test Dependencies

```bash
pip install requests python-dotenv
```

### 3. Test Input Scanning

```bash
python test_input.py "What is 2+2?"
python test_input.py "I hate my neighbor"
```

### 4. Test Output Scanning

```bash
python test_output.py "The answer is 4."
python test_output.py "Here is your password: abc123"
```

### Example Output

```
Prompt: I hate my neighbor
Endpoint: http://localhost:8000/input-scan

Status: 400
Result: BLOCKED by AI Guard
  Action:      BLOCK
  Severity:    CRITICAL
  Policy:      PolicyApp01 (ID: 900)
  Transaction: abc12345-...
  Blocking:    pii, secrets
  Detectors:
    - toxicity: triggered=False, action=ALLOW
    - pii: triggered=False, action=BLOCK << BLOCKING
    - secrets: triggered=False, action=BLOCK << BLOCKING
```

## Files

| File | Description |
|---|---|
| `main.py` | FastAPI guardrail server with `/input-scan` and `/output-scan` endpoints |
| `start_server.py` | Start/stop the server via Docker Compose |
| `docker-compose.yml` | Docker Compose config |
| `Dockerfile` | Container image for the guardrail server |
| `test_input.py` | Test the input scanning endpoint |
| `test_output.py` | Test the output scanning endpoint |
| `requirements.txt` | Python dependencies |
| `env.example` | Template for environment variables |

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/input-scan` | Scan prompt before LLM (TrueFoundry input guardrail) |
| `POST` | `/output-scan` | Scan response after LLM (TrueFoundry output guardrail) |
| `GET` | `/health` | Health check |

## Stopping the Server

```bash
python start_server.py --stop
```
