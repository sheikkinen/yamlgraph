# Feature Request: Session Timeline Join Script

**Priority:** MEDIUM
**Type:** Feature
**Status:** Enforced
**Effort:** 0.5 days
**Requested:** 2026-05-20

## Summary

A script that joins two data sources — audit.jsonl and VS Code transcripts — into a unified, human-readable session timeline. Each tool invocation is annotated with the user prompt that triggered it and the enforcement decision that resulted.

## Value Statement

Developers and auditors get a complete session narrative ("user asked X → agent tried Y → hook decided Z") from a single command, eliminating manual timestamp correlation across three separate JSONL files.

## Problem

Three complementary data sources exist but live in isolation:

| Source | Contains | Missing |
|---|---|---|
| `audit.jsonl` | Enforcement decisions (approve/deny/feedback) | User prompts, agent reasoning |
| Transcript JSONL | User prompts, agent thinking, tool args+results | Enforcement decisions |
| OTel spans (future) | Duration, hierarchy | Everything else |

Today, correlating "what did the user ask?" with "what did the hook block?" requires manually cross-referencing timestamps across files. The audit.jsonl now includes `session_id` (FR-414), making programmatic joins possible.

## Proposed Solution

A Python script at `.github/hooks/scripts/session-timeline.py` that:

1. Reads `audit.jsonl` filtered by `session_id`
2. Reads the matching transcript JSONL (path derived from `session_id` or passed as arg)
3. Joins by timestamp: each tool invocation gets the nearest preceding `user.message` as its trigger
4. Outputs a structured timeline

### Usage

```bash
# Current session (auto-detect from latest audit entries)
python3 .github/hooks/scripts/session-timeline.py

# Specific session
python3 .github/hooks/scripts/session-timeline.py --session 6f3f3dbf-3ced-461c-bbf4-eed24526c0f2

# Explicit transcript path (when auto-discovery fails)
python3 .github/hooks/scripts/session-timeline.py --transcript /path/to/transcripts/abc.jsonl

# JSON output for downstream tooling
python3 .github/hooks/scripts/session-timeline.py --json

# Filter to denials only
python3 .github/hooks/scripts/session-timeline.py --filter deny
```

### Output format (human-readable)

```
Session: 6f3f3dbf-3ced-461c-bbf4-eed24526c0f2
Model: claude-opus-4.6  |  Duration: 09:14–09:52 UTC  |  Turns: 24

[09:26:55] USER: "test the check-coauthor hook"
  [09:26:56] read_file          pass    not-inspected
  [09:26:57] run_in_terminal    approve clean         git status
  [09:27:01] run_in_terminal    DENY    co-authored-by  git commit -m "fix...Co-authored-by..."

[09:31:23] USER: "create the config. save the tests..."
  [09:31:24] create_file        pass    not-inspected
  [09:31:25] create_file        pass    not-inspected
  ...

Summary: 185 tool calls, 87 approve, 56 pass, 24 feedback, 18 deny
```

### Data flow

```
audit.jsonl ──────────┐
                      ├──→ join by session_id + timestamp ──→ timeline
transcript.jsonl ─────┘
                          ↑
                    user.message timestamps
                    become group headers
```

### Join algorithm

1. Load all `user.message` events from transcript, sorted by timestamp
2. Load all audit entries for the session, sorted by timestamp
3. For each audit entry, find the most recent `user.message` with `ts < audit.ts`
4. Group audit entries under their triggering user message
5. Render grouped output

## Acceptance Criteria

- [ ] Script reads audit.jsonl and transcript JSONL
- [ ] Joins tool invocations to triggering user prompts by timestamp
- [ ] Human-readable output with user prompts as group headers
- [ ] `--json` flag for machine-readable output
- [ ] `--filter` flag to show only specific decisions (deny, feedback)
- [ ] `--session` flag to select session (default: most recent in audit.jsonl)
- [ ] `--transcript` flag to provide explicit transcript path
- [ ] Auto-discovers transcript path from VS Code workspace storage (fallback)
- [ ] Handles timezone-aware and Z-suffix timestamps correctly (Python isoformat vs JS toISOString)
- [ ] Works with zero transcript (graceful degradation: audit-only timeline)
- [ ] Tests added (standalone, not pytest)

## Alternatives Considered

1. **Embed user prompts in audit.jsonl** — Rejected. No user-prompt hook exists; agent-relayed logging is unreliable. Transcript is the source of truth.
2. **Replace audit.jsonl with OTel** — Rejected. Different purposes: audit = enforcement log (security), OTel = performance traces (operations). They complement, not replace.
3. **Build a dashboard** — Over-engineered for current scale. A script that outputs text is sufficient until session volume justifies a UI.
4. **Order 66 `cmd timeline`** — Deferred. Timeline output exceeds deny-reason channel length. `cmd status` already provides a summary. The script is a standalone CLI tool.
5. **OTel span join** — Deferred. No OTel spans are emitted by hooks today. Add when spans exist.

## Judgement Notes

- Scope frozen: audit.jsonl + transcript join only. No OTel, no Order 66 integration.
- Transcript path: `--transcript` explicit flag is primary; auto-discovery is convenience fallback.
- Timestamp normalization is a required acceptance criterion (Python vs JS ISO format mismatch).
- `--filter` limited to decision values (deny, feedback, approve, pass). Expand later if needed.

## Related

- FR-414: Copilot hook audit logging (created audit.jsonl, session_id)
- `.github/hooks/README.md`: Order 66 command channel documentation
- VS Code transcript path: `~/Library/Application Support/Code/User/workspaceStorage/<hash>/GitHub.copilot-chat/transcripts/<session>.jsonl`
- `YAMLGRAPH_OTEL_DIR`: Existing OTel integration for copilot nodes (future join target)
