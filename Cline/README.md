# Cline + Zscaler AI Guard hooks

Runtime security for [Cline](https://github.com/cline/cline) using **Zscaler AI Guard** (`resolve-and-execute-policy` / optional `execute-policy`) via **`zscaler-sdk-python`**, aligned with the [Cursor](../Cursor/) integration in this repository.

User prompts, tool requests, and tool outputs are scanned with **`direction=IN`** or **`OUT`** as appropriate. **BLOCK** results cancel the hook action; API failures during a scan are **fail-closed** (blocked with an error message). Missing **`AIGUARD_API_KEY`** allows traffic and logs a warning (local dev convenience).

```
User Prompt ──► UserPromptSubmit ──► Model ──► PreToolUse ──► Tool Execution
                   (IN / block)                  (IN / block)        │
                                                                     ▼
                       Model Response ◄──── PostToolUse ◄────────────┘
                                      (OUT / block)
                                           │
                                           ▼
                                     TaskComplete
                                   (OUT audit, log only)
```

## Coverage

| Phase | Hook | Direction | Can block? |
|-------|------|-----------|------------|
| User prompt | `UserPromptSubmit` | IN | Yes |
| Before tool | `PreToolUse` | IN | Yes |
| After tool | `PostToolUse` | OUT | Yes |
| Task finished | `TaskComplete` | OUT | No (Cline `isCancellable: false`) |

**Limitations:** There is no hook on the model’s plain-text reply when no tool runs. `PostToolUse` only runs when a tool returns content (truncated to 20,000 characters for scanning).

## Prerequisites

- [Cline](https://marketplace.visualstudio.com/items?itemName=saoudrizwan.claude-dev) VS Code extension
- Python **3.10+** on the PATH as `python3` (hooks use `#!/usr/bin/env python3`)
- Dependencies: `pip install -r requirements.txt` (from this `Cline/` directory)

## Setup

1. **Install Python packages** (once per machine or venv):

   ```bash
   cd Cline
   pip install -r requirements.txt
   ```

2. **Configure credentials** — copy `.env.example` to **`Cline/.env`** or the **repository root** `.env`:

   ```bash
   AIGUARD_API_KEY=your-api-key
   AIGUARD_CLOUD=us1
   # Optional:
   # AIGUARD_POLICY_ID=12345
   ```

3. **Make hooks executable** (Unix/macOS):

   ```bash
   chmod +x .clinerules/hooks/UserPromptSubmit \
            .clinerules/hooks/PreToolUse \
            .clinerules/hooks/PostToolUse \
            .clinerules/hooks/TaskComplete
   ```

4. Open the workspace that contains **`.clinerules/hooks/`** in VS Code with Cline installed. Hooks are auto-discovered.

## Layout

```
Cline/
├── README.md
├── requirements.txt
├── .env.example
└── .clinerules/hooks/
    ├── aiguard_utils.py   # Client config, scan_content(), extraction helpers
    ├── UserPromptSubmit   # Python — stdin/out JSON
    ├── PreToolUse
    ├── PostToolUse
    └── TaskComplete
```

Logs: **`.clinerules/hooks/aiguard.log`**

## Testing locally

From the **repository root**, with **`Cline/.env`** (or root **`.env`**) and **`pip install -r Cline/requirements.txt`**:

```bash
bash local_dev/Cline/test_hooks.sh
```

Unlike Windsurf, Cline uses **stdout JSON** (`"cancel": true` to block), not exit code `2`. To try one prompt:

```bash
echo '{"userPromptSubmit":{"prompt":"Hello"},"taskId":"dev-1"}' | python3 Cline/.clinerules/hooks/UserPromptSubmit
```

## Hook I/O

Each hook reads JSON from **stdin** and prints a single JSON object to **stdout**:

```json
{"cancel": false}
```

```json
{"cancel": true, "errorMessage": "Blocked by Zscaler AI Guard: ..."}
```

Optional: `{"cancel": false, "contextModification": "..."}` (not used by default).

## Block message format

Blocked responses include **severity**, **policy name**, **transaction ID**, and **blocking detectors** when the API returns them.

## References

- [Zscaler AI Guard](https://help.zscaler.com/ai-guard)
- [zscaler-sdk-python](https://github.com/zscaler/zscaler-sdk-python)
- [Cursor hooks](../Cursor/README.md) — same API pattern
