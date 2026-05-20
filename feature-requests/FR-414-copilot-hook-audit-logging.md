# Feature Request: Copilot Hook Audit Logging

**Priority:** HIGH
**Type:** Enhancement
**Status:** Enforced
**Effort:** 1 day
**Requested:** 2026-05-20

## Summary

Log **every tool invocation** by the LLM agent — not just enforcement decisions — to an append-only JSONL audit trail. Fix the fail-open parse-error path in the pre-command guard.

## Value Statement

During a major incident, the on-call engineer can reconstruct the complete agent session — every file read, every search, every command, every edit — from a single JSONL file, answering "what did the agent do?" instead of "was the hook running?"

## Problem

Current hooks operate as black boxes:

| Gap | Severity | Impact |
|-----|----------|--------|
| **Zero logging** | Critical | No record of any invocation — block or pass. "Was the hook running?" is unanswerable |
| **Only enforcement logged** | Critical | Hooks fire for EVERY tool call (`read_file`, `grep_search`, `fetch_webpage`, etc.) but early-exit with `exit 0` — throwing away the signal. Only `run_in_terminal`/`send_to_terminal` (pre) and `.py` edits (post) are inspected; all other tool calls leave zero trace |
| **Fail-open on parse error** | Critical | `python3 -c ... \|\| true` → parse failure = empty TOOL_NAME → approve. Malformed JSON bypasses the guard entirely |
| **No invocation forensics** | High | Cannot reconstruct agent session timeline. In data exfiltration scenario (`read_file` on secrets → `fetch_webpage` to external URL), no forensic trail exists |
| **Silent tool failures** | Medium | `ruff ... 2>/dev/null \|\| true` — if ruff binary is missing, the check is silently skipped with no warning |

### Tool coverage gap

| Tool | PreToolUse fires? | Currently logged? | PostToolUse fires? | Currently logged? |
|------|-------------------|-------------------|--------------------|-----------|
| `run_in_terminal` | Yes | Only deny | Yes | No |
| `send_to_terminal` | Yes | Only deny | Yes | No |
| `read_file` | Yes | **No — early exit** | Yes | No |
| `replace_string_in_file` | Yes | No | Yes | Only .py with issues |
| `create_file` | Yes | No | Yes | Only .py with issues |
| `grep_search` | Yes | **No — early exit** | Yes | No |
| `semantic_search` | Yes | **No — early exit** | Yes | No |
| `list_dir` | Yes | **No — early exit** | Yes | No |
| `fetch_webpage` | Yes | **No — early exit** | Yes | No |

Every `exit 0` is a discarded forensic signal.

In a production incident scenario, every move must be traceable. These hooks enforce Scripture-level policy (Co-authored-by ban, --no-verify prohibition) but leave no evidence trail.

## Proposed Solution

### 1. Audit log infrastructure

- Directory: `.github/hooks/logs/`
- File: `audit.jsonl` (append-only, one JSON object per line)
- Gitignored (local-only forensic data, not committed)

### 2. Log format

Every hook invocation emits one JSONL record:

```json
{
  "ts": "2026-05-20T14:32:01.123456+00:00",
  "hook": "pre-command-guard",
  "tool": "run_in_terminal",
  "decision": "deny",
  "reason": "co-authored-by",
  "detail": "git commit -m 'feat: ...' --trailer 'Co-authored..."
}
```

Fields:
- `ts`: UTC ISO-8601 timestamp
- `hook`: hook script name (`pre-command-guard` | `post-edit-checks`)
- `tool`: VS Code tool name that triggered the hook
- `decision`: `pass` (not inspected) | `approve` (inspected, clean) | `deny` (blocked) | `feedback` (advisory issues reported) | `error` (tool/parse failure)
- `reason`: which check fired (e.g., `not-inspected`, `co-authored-by`, `no-verify`, `multiline-m`, `ruff`, `file-size`, `parse-error`)
- `detail`: first 200 chars of the command or file path (truncated for safety)

### 3. Log ALL tool invocations in PreToolUse (one log line per invocation)

The PreToolUse hook logs every tool call. The PostToolUse hook logs **only tools it inspects** (edit tools on .py files). This avoids double-logging — each invocation produces exactly one audit line.

Both hooks currently early-exit for tools they don't inspect. The PreToolUse hook must log before exiting:

```bash
# Current (silent discard):
if [[ "$TOOL_NAME" != "run_in_terminal" && ... ]]; then
  echo '{"decision":"approve"}'
  exit 0
fi

# Fixed (log then approve):
if [[ "$TOOL_NAME" != "run_in_terminal" && ... ]]; then
  audit_log "pre-command-guard" "$TOOL_NAME" "pass" "not-inspected" "$DETAIL"
  echo '{"decision":"approve"}'
  exit 0
fi
```

**Detail extraction strategy**: Generic — `detail` is the first 200 chars of `json.dumps(toolInput)`. No per-tool field mapping (tool names and input shapes change; generic survives).

This creates the complete session timeline:
```
14:32:01 read_file      pass     not-inspected  /src/config.py
14:32:02 grep_search     pass     not-inspected  "API_KEY"
14:32:03 run_in_terminal approve  clean          git add .
14:32:04 run_in_terminal deny     co-authored-by git commit --trailer...
14:32:05 replace_string  pass     not-inspected  /src/config.py
14:32:06 fetch_webpage   pass     not-inspected  https://...
```

### 4. Fail-closed in pre-command-guard

If JSON parsing fails (python3 unavailable, malformed input), the hook MUST deny instead of approve:

```bash
# Current (fail-open — DANGEROUS):
TOOL_NAME=$(echo "$INPUT" | python3 -c "..." 2>/dev/null || true)
# Empty → falls through to approve

# Fixed (fail-closed):
PARSE_RESULT=$(echo "$INPUT" | python3 -c "..." 2>/dev/null) || {
  audit_log "pre-command-guard" "unknown" "deny" "parse-error" "JSON parse failed"
  emit_deny "Hook cannot parse input — denying for safety"
  exit 0
}
```

### 5. post-edit-checks: log only inspected tools

PostToolUse logs **only tools it actually inspects** (to avoid double-logging with PreToolUse):
- Non-edit tools: no log (PreToolUse already logged `pass/not-inspected`)
- Non-.py edits: `decision: pass`, `reason: not-python`
- Clean .py files: `decision: approve`, `reason: all-checks-clean`
- .py with issues: `decision: feedback`, `reason: ruff|file-size|...`

### 6. Silent tool failure warning

When ruff is not found, log `decision: error`, `reason: ruff-missing` so the gap is visible in the audit trail.

### 7. Performance budget

Every tool call now pays ~50ms for JSON parse + log write. At 500 tool calls/session, that's 25s total amortized across the session. Acceptable — agent LLM round-trips dwarf this by 100x. If profiling shows otherwise, batch writes or switch to pure-bash append.

### 8. Test isolation

Hooks resolve log directory via `HOOK_LOG_DIR` env var, defaulting to `$(dirname "$0")/../logs`. Tests set `HOOK_LOG_DIR` to a temp directory, then verify JSONL content after invocation.

### 9. Write atomicity

Shell `>>` append is atomic for writes under PIPE_BUF (4096 bytes on macOS/Linux). Each log line is ~200 bytes. The `python3 -c` logger must use a single `print()` call (unbuffered to fd) to ensure atomicity under concurrent hook invocations. If corruption is observed, add `flock` around the append.

## Acceptance Criteria

- [ ] `.github/hooks/logs/` directory exists with `.gitignore` excluding `*.jsonl`
- [ ] `pre-command-guard.sh` logs **every** tool invocation (not just terminal commands) to `audit.jsonl`
- [ ] `post-edit-checks.sh` logs **only inspected tools** (edit tools) — no double-logging with PreToolUse
- [ ] Non-inspected tools logged once in PreToolUse as `decision: pass, reason: not-inspected`
- [ ] `detail` field is generic `json.dumps(toolInput)[:200]`, not per-tool extraction
- [ ] `pre-command-guard.sh` denies on JSON parse failure (fail-closed) with audit log entry
- [ ] `post-edit-checks.sh` logs when ruff binary is missing (`ruff-missing`)
- [ ] New test: malformed JSON input → pre-command-guard denies (not approves)
- [ ] New test: verify JSONL audit line written to log file after any tool invocation
- [ ] New test: `read_file` tool invocation produces `pass/not-inspected` log line
- [ ] Tests use `HOOK_LOG_DIR` env var pointing to temp directory for isolation
- [ ] All existing tests pass (19 + 16 = 35)
- [ ] README updated with audit log section and `jq` query examples

## Alternatives Considered

- **stderr logging**: Simpler but VS Code swallows hook stderr — invisible to the user and unrecoverable.
- **Syslog/os_log**: Cross-platform complexity for no gain — this is a developer-local tool.
- **SQLite**: Structured but overkill for append-only forensics. JSONL can be `jq`-queried trivially.
- **Log rotation**: Deferred — file grows ~200 bytes/invocation; at 1000 invocations/day that's 200KB. Monthly manual truncation is sufficient for now.
- **Log only enforcement decisions**: Original FR-414 scope. Rejected — an agent that reads secrets and calls `fetch_webpage` leaves zero trace. Logging only enforcement is compliance theatre (trap: `gate_checks_shape_not_substance`).

## Related

- `.github/hooks/scripts/pre-command-guard.sh` — PreToolUse hook
- `.github/hooks/scripts/post-edit-checks.sh` — PostToolUse hook
- `.github/hooks/README.md` — hook system documentation
- Scripture: "Thou shalt bear witness of thy errors — Hide nothing"
- Trap: `gate_checks_shape_not_substance` — a hook that runs but leaves no evidence is compliance theatre
