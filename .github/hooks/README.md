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
│   └── post-edit-checks.sh           # Fast lint/style checks on edited .py files
├── logs/
│   ├── .gitignore                    # Excludes *.jsonl from git
│   └── audit.jsonl                   # Append-only audit trail (gitignored)
├── tests/
│   ├── test_pre_command_guard.py     # 23 tests
│   └── test_post_edit_checks.py      # 20 tests
└── README.md
```

### Lifecycle Events

| Event | When |
|-------|------|
| `PreToolUse` | Before agent invokes any tool (terminal, file edit, etc.) |
| `PostToolUse` | After successful tool invocation |
| `SessionStart` | First prompt of a new session |

### Hook Contract

Scripts receive JSON on **stdin** with tool invocation details (`toolName`, `toolInput`). They return JSON on **stdout**:

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
{"ts": "2026-05-20T14:32:01.123456+00:00", "hook": "pre-command-guard", "tool": "run_in_terminal", "decision": "deny", "reason": "co-authored-by", "detail": "git commit --trailer 'Co-authored..."}
```

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
```

### Log directory override

Set `HOOK_LOG_DIR` env var to redirect logs (used by tests for isolation):

```bash
HOOK_LOG_DIR=/tmp/audit-test .github/hooks/scripts/pre-command-guard.sh
```
