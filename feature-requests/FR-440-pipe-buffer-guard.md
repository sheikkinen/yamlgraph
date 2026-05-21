# Feature Request: Pipe-Buffer Guard for pytest Output

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Judged
**Effort:** 0.5 days
**Requested:** 2026-05-21

## Summary

Add a PreToolUse guard in `pre-command-guard.sh` that denies `pytest ... | head` and `pytest ... | tail` commands that lack an intermediate `tee`. Piping pytest output directly to head/tail causes full buffering — the agent sees nothing until pytest exits, masking hangs and slow tests.

## Value Statement

Agents get immediate streaming feedback from pytest runs instead of silent buffered output that looks like a hang.

## Problem

Audit log shows 13+ instances of `pytest ... 2>&1 | tail -N` across recent sessions. This pattern:

1. **Buffers all output** — pipe to `tail`/`head` triggers full buffering; no output streams until pytest exits
2. **Masks hangs** — if a test hangs, the agent sees zero output and cannot diagnose
3. **Wastes time** — agent retries or cancels, believing the process is stuck
4. **Already documented** — the fix (`tee` to logfile) is known but not enforced (see user memory note `pytest-pipe-buffering.md`)

The pattern is deeply embedded in agent default behavior: the VS Code Copilot system prompt instructs `Use head, tail, grep, awk to filter and limit output size`, which agents apply to pytest without understanding the buffering consequence.

## Proposed Solution

Add Check 4 to `pre-command-guard.sh` after the existing multiline-m check:

```bash
# ── Check 4: pytest piped to head/tail without tee ───────────────────
if echo "$COMMAND" | grep -qE 'pytest\b' && \
   echo "$COMMAND" | grep -qE '\|\s*(head|tail)\b' && \
   ! echo "$COMMAND" | grep -qE '\|\s*tee\b'; then
  audit_log "deny" "pipe-buffer" "${COMMAND:0:200}"
  emit_deny "pytest piped to head/tail buffers all output — hangs are invisible.\n\nUse tee:\n  pytest ... 2>&1 | tee logs/run.log\n\nThen inspect:\n  tail -20 logs/run.log"
  exit 0
fi
```

**What it catches:**
- `pytest tests/ -v 2>&1 | tail -20` → denied
- `pytest tests/ -q | head -5` → denied

**What it allows:**
- `pytest tests/ -v 2>&1 | tee logs/run.log | tail -20` → approved (tee present)
- `pytest tests/ -v` → approved (no pipe)
- `cat logs/run.log | tail -20` → approved (not pytest)
- `tail -20 logs/run.log` → approved (not pytest)

## Acceptance Criteria

- [ ] `pre-command-guard.sh` denies `pytest ... | tail` and `pytest ... | head` without `tee`
- [ ] Deny message guides toward `tee` pattern with example
- [ ] Audit log records `pipe-buffer` reason
- [ ] Commands with `tee` in the pipeline are not blocked
- [ ] Non-pytest commands piped to head/tail are not affected
- [ ] Tests added in `.github/hooks/tests/test_pre_command_guard.py`
- [ ] Header comment updated to list Check 4

## Alternatives Considered

1. **Instruction-only** — Add note to `copilot-instructions.md`. Already tried implicitly (user memory exists); agents ignore advisory text under output-length pressure. Enforcement is needed.
2. **Block all pipes from pytest** — Too aggressive; `pytest ... | grep FAILED` is legitimate and doesn't cause the same buffering issue (grep flushes line-by-line).
3. **Auto-rewrite command** — Transform `| tail` to `| tee ... | tail` automatically. Rejected: hooks should deny and guide, not silently modify commands.

## Related

- User memory: `pytest-pipe-buffering.md`
- Audit evidence: `pytest.*tail` in `.github/hooks/logs/audit.jsonl` (13+ instances)
- Pre-command-guard: `.github/hooks/scripts/pre-command-guard.sh` (Checks 1-3 exist)
- FR-438: Thoughtcrime hook (same guard architecture)
