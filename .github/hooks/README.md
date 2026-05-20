# VS Code Copilot Hooks

Deterministic lifecycle hooks for VS Code Copilot agent sessions. These run **before** the agent executes a tool, providing enforcement that instructions alone cannot guarantee.

## How It Works

Hook JSON files in `.github/hooks/` are auto-discovered by VS Code Copilot. Each file declares which lifecycle event to intercept and which script to run.

```
.github/hooks/
├── pre-command-guard.json            # PreToolUse: block dangerous terminal patterns
├── post-edit-checks.json             # PostToolUse: ruff, size, terms, debug, noqa
├── scripts/
│   ├── pre-command-guard.sh          # Co-authored-by, --no-verify, multiline -m
│   ├── post-edit-checks.sh           # Fast lint/style checks on edited .py files
│   └── session-timeline.py           # Join audit + transcript into session narrative
├── logs/
│   ├── .gitignore                    # Excludes *.jsonl from git
│   └── audit.jsonl                   # Append-only audit trail (gitignored)
├── tests/
│   ├── test_pre_command_guard.py     # 31 tests
│   ├── test_post_edit_checks.py      # 20 tests
│   └── test_session_timeline.py      # 8 tests
└── README.md
```

### Lifecycle Events

| Event | When |
|-------|------|
| `PreToolUse` | Before agent invokes any tool (terminal, file edit, etc.) |
| `PostToolUse` | After successful tool invocation |
| `SessionStart` | First prompt of a new session |

### Hook Contract

Scripts receive JSON on **stdin** with tool invocation details:

| Field | Description |
|-------|-------------|
| `tool_name` | Tool being called (e.g. `run_in_terminal`, `read_file`) |
| `tool_input` | Dict of tool arguments |
| `session_id` | UUID identifying the conversation |
| `tool_use_id` | Unique per-invocation ID |
| `timestamp` | ISO 8601 UTC timestamp |
| `transcript_path` | Path to full session transcript JSONL |
| `hook_event_name` | `PreToolUse` or `PostToolUse` |
| `cwd` | Working directory |

They return JSON on **stdout**:

- **Approve**: `{"decision": "approve"}`
- **Deny**: Return `permissionDecision: "deny"` with a reason (see script source for format)

Exit code `0` = success, `2` = blocking error.

## Active Hooks

### `pre-command-guard` (PreToolUse)

Blocks dangerous terminal patterns *before* the command runs:

| Check | What it blocks | What it allows |
|-------|---------------|----------------|
| Co-authored-by | Trailers in commits, merges, file writes | `grep`/`rg` searches referencing the pattern |
| `--no-verify` | Any git/pre-commit command with the flag | `grep`/`echo` mentioning it |
| Multiline `-m` | `git commit -m "...\n..."` (dquote trap) | Single-line `-m`, `git commit -F` |
| Lockdown | When `.lockdown` file is active, **all** tools denied | Only `.github/hooks/cmd unlock` passes through |

### `post-edit-checks` (PostToolUse)

Runs fast checks on Python files immediately after the agent edits them (`replace_string_in_file`, `create_file`, `multi_replace_string_in_file`). Returns issues as a `systemMessage` so the agent can self-correct before writing more code.

| Check | Pre-commit equivalent | What it catches |
|-------|----------------------|-----------------|
| ruff lint | `ruff` | Unused imports, syntax issues, style violations |
| ruff format | `ruff-format` | Files needing reformatting |
| Forbidden terms | `forbid-terms` | `TODO`, `FIXME`, `backward compatibility` |
| File size | `file-size-gate` | Files over 400 lines (warn) / 450 lines (error) |
| Debug statements | `debug-statements` | `breakpoint()`, `import pdb` |
| noqa confession | `noqa-confession` | `# noqa` without matching entry in `docs/confessions.md` |

## Relationship to Other Enforcement

| Layer | When | Scope |
|-------|------|-------|
| **PreToolUse hook** | Before agent runs the command | Agent sessions only |
| **PostToolUse hook** | After agent edits a `.py` file | Agent sessions only |
| `scripts/block_ai_coauthor.py` | `commit-msg` pre-commit hook | All local commits (AI patterns only) |
| `copilot-trailer-gate` CI job | PR merge gate | All `Co-authored-by:` trailers |

## Testing

```bash
python3 .github/hooks/tests/test_pre_command_guard.py
python3 .github/hooks/tests/test_post_edit_checks.py
python3 .github/hooks/tests/test_session_timeline.py
```

## Audit Trail (FR-414)

Both hooks log every invocation to `.github/hooks/logs/audit.jsonl` (gitignored, local-only). This creates a complete forensic timeline of every tool the agent uses during a session.

### What gets logged

| Hook | Tool scope | Decision values |
|------|-----------|-----------------|
| `pre-command-guard` | **All tools** (every PreToolUse invocation) | `pass` (not inspected), `approve` (clean), `deny` (blocked), `error` (parse failure) |
| `post-edit-checks` | **Only edit tools** on `.py` files | `approve` (all-checks-clean), `feedback` (issues found), `error` (ruff-missing) |

Non-edit tools are logged once by PreToolUse as `pass/not-inspected` (no double-logging).

### Log format

```json
{"ts": "2026-05-20T14:32:01+00:00", "hook": "pre-command-guard", "tool": "run_in_terminal", "decision": "deny", "reason": "co-authored-by", "detail": "git commit --trailer...", "session_id": "6f3f3dbf-...", "tool_use_id": "toolu_vrtx_01ABC"}
```

`session_id` and `tool_use_id` are included when the hook payload provides them (VS Code Copilot always sends both). This enables correlation with the session transcript.

### Fail-closed

If `pre-command-guard` cannot parse the hook input (malformed JSON, python3 unavailable), it **denies** the command and logs `decision: deny, reason: parse-error`. It never fails open.

### Querying the audit log

```bash
# All denials
jq 'select(.decision == "deny")' .github/hooks/logs/audit.jsonl

# Session timeline
jq -r '[.ts[11:19], .tool, .decision, .reason] | @tsv' .github/hooks/logs/audit.jsonl

# Tool frequency
jq -r '.tool' .github/hooks/logs/audit.jsonl | sort | uniq -c | sort -rn

# All file reads
jq 'select(.tool == "read_file")' .github/hooks/logs/audit.jsonl

# Filter by session
jq 'select(.session_id == "6f3f3dbf-...")' .github/hooks/logs/audit.jsonl
```

## Order 66 — User Command Channel

Since VS Code has no user-prompt hook, the command channel uses a sentinel pattern that the agent relays through `run_in_terminal`. The PreToolUse hook intercepts it before execution.

**Usage**: Tell the agent to run `.github/hooks/cmd <command>`

| Command | Effect |
|---------|--------|
| `lockdown` | Deny **all** tool calls until unlocked. Creates `.lockdown` state file. |
| `unlock` | Lift lockdown. Resume normal operations. |
| `status` | Return audit summary (total entries, decisions, top tools, lockdown state). |

### How it works

1. User says: *"lock it down"* or *"run `.github/hooks/cmd lockdown`"*
2. Agent calls `run_in_terminal` with the command
3. PreToolUse hook intercepts the sentinel pattern **before execution**
4. Hook processes the command and returns a `deny` with the response in the reason text
5. The agent sees the response and relays it to the user

The deny response is the communication channel — the command never actually runs in the terminal.

### Lockdown behavior

- When active, **every tool call** (not just terminal) is denied with `"LOCKDOWN ACTIVE"`
- Only `.github/hooks/cmd unlock` passes through the lockdown
- Lockdown state persists in `.github/hooks/logs/.lockdown` (survives session restarts)
- All lockdown events are logged to `audit.jsonl` with `reason: order66-*`

## Session Timeline (FR-424)

Joins `audit.jsonl` with VS Code transcript JSONL to produce a unified session narrative: "user asked X → agent used tool Y → hook decided Z".

```bash
# Current session (auto-detects transcript from VS Code workspace storage)
python3 .github/hooks/scripts/session-timeline.py --audit .github/hooks/logs/audit.jsonl

# Explicit transcript path
python3 .github/hooks/scripts/session-timeline.py --audit .github/hooks/logs/audit.jsonl --transcript /path/to/transcript.jsonl

# Specific session
python3 .github/hooks/scripts/session-timeline.py --audit .github/hooks/logs/audit.jsonl --session <uuid>

# JSON output
python3 .github/hooks/scripts/session-timeline.py --audit .github/hooks/logs/audit.jsonl --json

# Show only denials
python3 .github/hooks/scripts/session-timeline.py --audit .github/hooks/logs/audit.jsonl --filter deny
```

Sample output:

```
Session: 6f3f3dbf-3ced-461c-bbf4-eed24526c0f2

[09:26:55] USER: "test the check-coauthor hook"
  [09:26:56] read_file          pass    not-inspected
  [09:27:01] run_in_terminal    DENY    co-authored-by  git commit -m "fix...Co-authored-by..."

Summary: 42 tool calls, 16 approve, 24 pass, 2 error
```

Works without a transcript (audit-only timeline). Handles Python `+00:00` and JS `Z` timestamp formats.

### Log directory override

Set `HOOK_LOG_DIR` env var to redirect logs (used by tests for isolation):

```bash
HOOK_LOG_DIR=/tmp/audit-test .github/hooks/scripts/pre-command-guard.sh
```
