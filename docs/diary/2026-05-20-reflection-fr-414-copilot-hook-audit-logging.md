# Chapter 23: The Guard That Watched Itself

*On building audit logging for Copilot hooks, and the trap of testing against assumed interfaces.*

---

## I. The Black Box Problem

We built two Copilot hooks — `pre-command-guard` (blocking dangerous commands) and `post-edit-checks` (lint feedback on edits). Both worked. Tests passed. The agent was protected.

But when the question shifted from "does it work?" to "can we prove it worked?" — the answer was silence. No logs. No timestamps. No record of what was blocked, what was approved, or whether the hooks were even running. In incident response terms: the security camera was on, but nobody was recording.

The first instinct was to log enforcement decisions — the denials, the blocks. FR-414 started there. Then came the reflection that exposed the real gap: **the hooks fire for every tool call.** `read_file`, `grep_search`, `fetch_webpage` — VS Code sends them all through PreToolUse. We were receiving the complete agent activity stream and throwing it away at line 1 with `exit 0`.

Logging only enforcement decisions is the `gate_checks_shape_not_substance` trap wearing a new costume: the shape says "we audit," but the substance says "we audit 5% of actions."

---

## II. The Interface Assumption

Tests passed. Implementation looked clean. Then the acceptance test — a real tool call through VS Code — revealed every entry logged `tool: unknown, detail: {}`.

The cause: VS Code sends `tool_name` and `tool_input` (snake_case). Our code expected `toolName` and `toolInput` (camelCase). The mismatch was invisible in unit tests because tests construct their own payloads. The hooks parsed successfully (no crash), extracted empty strings (no error), and logged a hollow record (no information).

This is a boundary normalization failure at the `instruction` boundary. The external system (VS Code) speaks snake_case. We assumed camelCase. The fix was trivial — accept both — but the trap is instructive: **a test that constructs its own input can only validate internal logic, never the contract with the external system.**

The acceptance test caught what 43 unit tests could not: the real payload shape.

---

## III. The Fail-Open Default

The original pre-command-guard had this pattern:

```bash
TOOL_NAME=$(echo "$INPUT" | python3 -c "..." 2>/dev/null || true)
```

If python3 fails or JSON is malformed, `TOOL_NAME` is empty. Empty falls through every check. The hook approves. Silently.

This is the `downstream_fix` trap inverted: instead of fixing at the wrong place, we fail at the wrong place. A guard that can't parse its input should deny, not approve. The production mindset made this obvious — in a major incident, "the guard couldn't understand the request so it let it through" is indefensible.

The fix: parse once, fail-closed. If parsing fails → deny → log `parse-error` → explain why.

---

## IV. The Heuristic

**An enforcement hook that leaves no evidence trail is compliance theatre.** The hook's value is not just in blocking bad actions but in proving that good actions were scrutinized. When the incident postmortem asks "what did the agent do between 14:00 and 14:30?" — the audit log answers.

**Test payloads are assumptions about contracts, not proofs of them.** The first real integration (acceptance test with actual VS Code payloads) found a schema mismatch that 43 unit tests missed. Always test through the real boundary at least once.

**A guard that can't understand its input must deny.** Fail-open is the default in most shell scripting patterns (`|| true`). For security hooks, the default must be fail-closed.

---

**Seed:** The audit log captures what the agent does, but not why. The `detail` field shows the command or file path, but not the agent's reasoning — the prompt that led to the action, the context window that shaped the decision. Could the hook also capture the `session_id` (VS Code provides it in the payload) to link audit entries to conversation transcripts? At what point does "audit trail" become "surveillance," and who decides the boundary?
