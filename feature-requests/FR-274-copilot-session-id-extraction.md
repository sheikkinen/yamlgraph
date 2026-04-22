# Feature Request: Copilot CLI Session ID Extraction

**Priority:** MEDIUM
**Type:** Fix
**Status:** Proposed
**Effort:** 0.5 days
**Requested:** 2026-04-22
**Related:** FR-105 (session continuations), FR-273 (watcher2 pipeline)

## Summary

Fix copilot node session ID extraction so `--resume` actually works. The current regex was speculative and never empirically verified — copilot CLI does not emit `Session: <id>` in stderr.

## Problem

FR-105 introduced session continuations with a regex `Session:\s*([a-zA-Z0-9-]+)` to extract session IDs from copilot CLI stderr. This format was a guess — the test comment says `"format TBD - empirical verification needed"`. In practice:

- `--silent` mode: stderr is empty
- Normal mode: stderr contains only ANSI stats (`Changes`, `Requests`, `Tokens`)
- No session ID is ever emitted in either mode

Every copilot node in the codebase (copilot graph, enforce graph, watcher2 graphs) silently starts a fresh session because `session_id` is always `None`.

## Empirical Findings (2026-04-22)

| Flag combo | Stderr content | Session ID? |
|---|---|---|
| `--silent` | empty | No |
| (no --silent) | ANSI stats only | No |
| `--share` (no --silent) | Stats + `Session exported to: .../copilot-session-<uuid>.md` | Yes (stderr) |
| `--silent --share=<path>` | empty | Yes (in share file line 4) |

The share file format:
```markdown
# 🤖 Copilot CLI Session

> [!NOTE]
> - **Session ID:** `d0137402-936d-4e5c-a3fe-27e924ef5dd2`
```

Session resume verified working: `copilot --resume=<uuid>` correctly recalls previous conversation.

## Proposed Solution

Add `--share=<tmpfile>` to copilot CLI invocations and extract session ID from the share file.

### Changes

1. **`yamlgraph/node_factory/copilot_node.py`**:
   - Add `--share=<tmpdir>/copilot-session.md` to the subprocess command
   - Replace `_extract_session_id(stderr)` with `_extract_session_id_from_share_file(path)`
   - New regex: `\*\*Session ID:\*\*\s*` `` ` `` `([a-f0-9-]+)` `` ` ``
   - Clean up share file after extraction

2. **Tests**:
   - Update `test_session_id_populated_from_stderr` to use share file mock
   - Remove "format TBD" comment — format is now empirically verified

### Acceptance Criteria

- AC-1: After a copilot node runs, `CopilotResult.session_id` is a valid UUID (not `None`)
- AC-2: A second copilot node with `resume: "{state.prev.session_id}"` passes `--resume=<uuid>` to CLI
- AC-3: Share file is cleaned up after session ID extraction
- AC-4: Graceful fallback to `None` if share file is missing or unparseable
