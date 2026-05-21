# Feature Request: FR-438 Thoughtcrime Hook

**Priority:** MEDIUM
**Type:** Feature
**Status:** Enforced
**Effort:** 1 day
**Requested:** 2026-05-21

**See also:** [FR-439](FR-439-tone-down-enforcement-terminology.md) renamed the shipped implementation to `reasoning-pattern-check` (sentinel `.reasoning-flag-<sid>`, audit reason `reasoning-pattern`). This document is preserved as the historical record of the original intent; the deny-message and "Welcome to 1984" framing below no longer matches shipped behaviour.

## Summary

A PostToolUse hook that scans the agent's transcript (including internal `reasoningText`) for forbidden reasoning patterns ("thoughtcrimes") and arms a one-shot PreToolUse denial on the next tool call, forcing the agent to confront and correct its reasoning before proceeding.

Welcome to 1984.

## Value Statement

Operators gain enforcement against cognitive anti-patterns that instructions alone cannot prevent — the agent's private thinking is held to the same standard as its visible output, catching blame-shifting ("pre-existing failure") and scope evasion before they manifest as skipped tests or silent regressions.

## Problem

Certain forbidden phrases represent **reasoning anti-patterns**, not code artifacts:

| Thoughtcrime | Why forbidden | Risk if uncaught |
|---|---|---|
| "pre-existing failure" | Blame-shifting; current author owns the red suite | Agent skips fixing a broken test |
| "backward compatibility" | Reluctance to complete a refactor | Shims and adapters accumulate |
| "not introduced by this change" | Variant of pre-existing failure | Root cause goes undiagnosed |

These phrases live in the agent's **thinking** (`reasoningText`), not in code files. Existing enforcement layers cannot catch them:

- **Pre-commit hooks** → inspect committed files, not agent reasoning
- **PreToolUse hooks** → inspect tool arguments (commands), not thinking
- **PostToolUse hooks** → inspect edited files, not thinking
- **CI gates** → inspect PR artifacts, not session transcripts
- **copilot-instructions.md** → advisory text; agent may internalize but cannot be verified

The VS Code Copilot transcript JSONL contains `assistant.message` entries with a `reasoningText` field — the agent's internal chain-of-thought. This is the only data source where thoughtcrimes are observable.

## Research

### Data Source: VS Code Transcript JSONL

Path: `~/Library/Application Support/Code/User/workspaceStorage/<hash>/GitHub.copilot-chat/transcripts/<session_id>.jsonl`

Each `assistant.message` entry contains:
```json
{
  "type": "assistant.message",
  "data": {
    "messageId": "...",
    "content": "visible response text",
    "reasoningText": "internal chain-of-thought (thinking block)",
    "toolRequests": [...]
  }
}
```

### Performance

Benchmarked on a 118KB / 257-line transcript (6 turns):
- Full scan: **0.9ms** per invocation
- Hook timeout budget: **5000ms**
- Headroom: **5000x**

Even a 10x longer session stays well under budget.

### Existing Infrastructure

- `session_id` is already parsed from hook stdin in `pre-command-guard.sh`
- `discover_transcript(session_id)` is implemented in `session-timeline.py`
- The lockdown sentinel pattern (`.lockdown` file) demonstrates the arming mechanism
- `classify-emit.sh` (FR-425) demonstrates PostToolUse fire-and-forget pattern

### Why Not OTel?

`COPILOT_OTEL_FILE_EXPORTER_PATH` captures spans from the **Copilot CLI** subprocess (used in `copilot_node`), not the VS Code Chat agent. The Chat agent's thinking is only in the transcript JSONL. Different execution contexts, different data sources.

## Proposed Solution

### Phase 1: Keyword Sentinel (deterministic, no LLM)

Two new hooks working in concert:

**PostToolUse: `thoughtcrime-scan.sh`**
1. Parse `session_id` from hook input
2. Discover transcript path via workspace storage glob
3. Scan **only the latest** `assistant.message` for forbidden phrases (avoids false positives from earlier discussion)
4. If found → write `.thoughtcrime-<session_id>` sentinel file with details
5. Exit 0 (PostToolUse, non-blocking)

**PreToolUse: addition to `pre-command-guard.sh`**
1. Check for `.thoughtcrime-${SESSION_ID}` sentinel file (exact match — no glob; session-isolated so parallel agents cannot cross-contaminate)
2. If armed → emit `deny` with corrective message, delete sentinel (one-shot)
3. Agent receives denial, must acknowledge and correct reasoning

```
Agent thinks: "This is a pre-existing failure, I'll skip the test fix"
Agent calls: read_file (PostToolUse scans transcript → arms sentinel)
Agent calls: run_in_terminal (PreToolUse finds sentinel → DENY)

  ✗ THOUGHTCRIME DETECTED

  Forbidden reasoning: "pre-existing failure"

  Scripture: A red test suite belongs to the current change author.
  Most such claims arise from test pollution — hidden state,
  order dependence, or incomplete isolation.

  Assume ownership. Reproduce the failure. Correct the root cause.

  This denial is one-shot. Your next tool call will proceed.
  But the Thought Police are watching.
```

### Phase 2: LLM Escalation (future, requires FR-425 classifier daemon)

When a keyword match is found, the verbatim `reasoningText` is sent to the classifier daemon (FR-425) for semantic analysis by a second LLM — the Thought Police.

The classifier determines:
- **False positive**: agent was discussing the policy, not invoking it as justification (e.g., "the phrase 'pre-existing failure' is forbidden")
- **True positive**: agent is using the reasoning to justify skipping work
- **Severity**: advisory warning vs. hard denial

This eliminates the false-positive problem from Phase 1 without adding latency to the hot path (classifier runs async via Unix socket, sentinel is armed on classification result).

### Thoughtcrime Registry

```python
# .github/hooks/scripts/thoughtcrimes.json
{
  "phrases": [
    {
      "pattern": "pre-existing failure",
      "variants": ["pre existing failure", "preexisting failure"],
      "doctrine": "A red test suite belongs to the current change author.",
      "scripture_ref": "copilot-instructions.md § Conventions"
    },
    {
      "pattern": "not introduced by this change",
      "variants": ["not caused by this change", "was already broken"],
      "doctrine": "Assume ownership, reproduce the failure, and correct the root cause.",
      "scripture_ref": "copilot-instructions.md § Conventions"
    }
  ]
}
```

Note: "backward compatibility" is excluded from this registry — it is already caught by `forbid-terms` pre-commit hook and `python-checks.sh` PostToolUse hook when written to files. Catching it in thought-only adds false positive noise without actionable value (unlike "pre-existing failure" which leads to skipping test fixes).

### File Layout

```
.github/hooks/
├── thoughtcrime-scan.json           # PostToolUse hook registration
├── scripts/
│   ├── thoughtcrime-scan.sh         # PostToolUse: scan transcript, arm sentinel
│   └── thoughtcrimes.json           # Forbidden phrase registry
├── logs/
│   └── .thoughtcrime-<session_id>   # Armed sentinel (gitignored, one-shot)
└── tests/
    └── test_thoughtcrime_scan.py    # Unit tests with synthetic transcripts
```

## Acceptance Criteria

- [ ] `thoughtcrime-scan.sh` PostToolUse hook scans latest `assistant.message` in transcript
- [ ] Forbidden phrases loaded from `thoughtcrimes.json` registry
- [ ] Sentinel file `.thoughtcrime-<session_id>` written on match with phrase + doctrine
- [ ] `pre-command-guard.sh` checks for sentinel and emits one-shot deny
- [ ] Sentinel is deleted after denial (not lockdown — one-shot warning)
- [ ] Only latest `assistant.message` scanned (not full history)
- [ ] Session ID validated as UUID format before any filesystem operation (path traversal guard)
- [ ] Hook exits cleanly when no `reasoningText` field present in latest message (graceful degradation)
- [ ] `.thoughtcrime-*` added to `.github/hooks/logs/.gitignore`
- [ ] Scan completes within 100ms (5s timeout budget)
- [ ] Unit tests with synthetic transcript fixtures
- [ ] Audit log entry on both arming and denial
- [ ] Phase 1 accepts keyword-level false positives as a known limitation; Phase 2 (FR-425) provides LLM classification to resolve

## Alternatives Considered

### 1. Instruction-only enforcement

Current state. The phrase is forbidden in `copilot-instructions.md` but unverifiable. The agent may internalize the instruction but there is no mechanism to confirm compliance. Kept as the primary defense; this FR adds a second layer.

### 2. Full lockdown on thoughtcrime

Too aggressive. Lockdown blocks *all* tool calls until manual unlock. A one-shot denial is proportional — it interrupts the agent's flow with a corrective message, then lets it proceed. The doctrine's `boring_enforcement` principle: the correction should be boring, not dramatic.

### 3. PostToolUse feedback message (no denial)

A PostToolUse hook can return feedback text but cannot block the *next* action. The agent sees the feedback but may ignore it. The PreToolUse denial forces acknowledgement — the agent must respond to the denial before its next tool call succeeds.

### 4. Scan full transcript history

Higher false-positive rate. Earlier turns may contain legitimate discussion about forbidden phrases (as this session demonstrates — 7 hits, all meta-discussion). Scanning only the latest `assistant.message` limits scope to the agent's *current* reasoning.

## Related

- [.github/hooks/README.md](../.github/hooks/README.md): Hook infrastructure
- [.github/hooks/scripts/pre-command-guard.sh](../.github/hooks/scripts/pre-command-guard.sh): PreToolUse hook (lockdown/sentinel pattern)
- [FR-425](FR-425-hook-classification-daemon.md): Classifier daemon (Phase 2 dependency)
- [FR-424](FR-424-session-timeline-join-script.md): Session timeline join (transcript discovery)
- [copilot-instructions.md](../.github/copilot-instructions.md): Forbidden phrase doctrine
