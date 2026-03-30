# Windsurf + Zscaler AI Guard (Cascade hooks)

[Windsurf](https://codeium.com/windsurf) **Cascade** hooks that scan user prompts, terminal commands, MCP tool requests, and (for audit) MCP results and Cascade output via **Zscaler AI Guard** and **`zscaler-sdk-python`** — same API as [Cline](../Cline/) and [Cursor](../Cursor/).

Official hook behavior: [Cascade hooks](https://docs.windsurf.com/windsurf/cascade/hooks).

## What it does

| Hook | Event | Blocking? | AI Guard |
|------|-------|-------------|----------|
| `pre_user_prompt.py` | User message | Yes — **exit 2** | `direction=IN` |
| `pre_run_command.py` | Shell command | Yes — **exit 2** | `IN` |
| `pre_mcp_tool_use.py` | MCP arguments | Yes — **exit 2** | `IN` |
| `post_mcp_tool_use.py` | MCP result | **No** (Windsurf limit) | `OUT` — log + optional stdout alert |
| `post_cascade_response.py` | Cascade reply | **No** | `OUT` — log + optional stdout alert |

**Pre-hooks:** missing `AIGUARD_API_KEY` allows traffic with a warning. API errors and unexpected responses are **fail-closed** (**exit 2**).

**Post-hooks:** cannot block per Windsurf; they log and print user-visible alerts when policy would **BLOCK** or when detectors fire.

## Prerequisites

- Python **3.10+** as `python3` on `PATH`
- `pip install -r requirements.txt` from this **`Windsurf/`** directory

## Setup

```bash
cd Windsurf
pip install -r requirements.txt
```

Credentials: create **`Windsurf/.env`** with `AIGUARD_API_KEY` (and optional `AIGUARD_CLOUD`, `AIGUARD_POLICY_ID`). If you already have that file, you do not need to copy **`.env.example`** — it is only a template for variable names. The hooks also load the parent repository’s **`.env`** when present.

### Workspace root (important)

Windsurf only loads **workspace-level** hooks from **`.windsurf/hooks.json` at the folder you open** ([docs](https://docs.windsurf.com/windsurf/cascade/hooks)).

| How you open the project | What Windsurf uses |
|--------------------------|-------------------|
| **`zguard-ai-integrations`** (repo root) | **`.windsurf/hooks.json`** at repo root — included in this repository; it runs scripts under **`Windsurf/.windsurf/hooks/`**. |
| **`Windsurf/`** subfolder only | **`Windsurf/.windsurf/hooks.json`** (relative commands like `python3 .windsurf/hooks/...`). |

If you opened the repo root before **`/.windsurf/hooks.json`** existed, **reload the window** or restart Windsurf so it picks up the file.

On Windows, if `python3` is not on PATH for the IDE, edit the **`command`** entries to use `python` or a full path to the interpreter, in **both** `hooks.json` files if you use both layouts.

### If nothing runs

1. Confirm **`python3`** works in a terminal whose cwd is your workspace root (same folder you opened in Windsurf).
2. Turn on **`show_output`: true** for `pre_user_prompt` temporarily in `hooks.json` to surface errors in the Cascade UI (copy the stanza pattern from `pre_mcp_tool_use`).
3. Install deps: `pip install -r Windsurf/requirements.txt` (from repo root) or `cd Windsurf && pip install -r requirements.txt`.
4. Ensure **`AIGUARD_API_KEY`** is in **`Windsurf/.env`** or repo root **`.env`**.

## Layout

```
Windsurf/
├── README.md
├── requirements.txt
├── .env.example
└── .windsurf/
    ├── hooks.json
    └── hooks/
        ├── aiguard_utils.py
        ├── pre_user_prompt.py
        ├── pre_run_command.py
        ├── pre_mcp_tool_use.py
        ├── post_mcp_tool_use.py
        ├── post_cascade_response.py
        └── aiguard.log          # runtime (gitignored)
```

## Logging

**`.windsurf/hooks/aiguard.log`** — timestamps, trajectory id notes, BLOCK / ALERT lines. The file is created the first time any hook process starts (empty file until the first log line). If you need the path to exist earlier, run `touch .windsurf/hooks/aiguard.log` from **`Windsurf/`**, then `tail -f .windsurf/hooks/aiguard.log`.

## Limitations

- **Post-hooks cannot block** or redact content — [Windsurf platform constraint](https://docs.windsurf.com/windsurf/cascade/hooks).
- **`show_output: true`** only displays stdout to the user; it does not change Cascade context.
- Post-hook bodies are truncated to **20,000** characters before scanning.

## References

- [Zscaler AI Guard](https://help.zscaler.com/ai-guard)
- [zscaler-sdk-python](https://github.com/zscaler/zscaler-sdk-python)
