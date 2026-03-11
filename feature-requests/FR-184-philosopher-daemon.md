# FR-184: Philosopher Daemon

**Priority:** MEDIUM
**Type:** Feature
**Status:** Approved
**Effort:** 2 days
**Requested:** 2026-03-11
**Judged:** 2026-03-11

## Summary

Add `philosopher.sh` daemon and supporting YAMLGraph graphs to automate the Philosopher role — scanning diary entries for recurring heuristics, detecting trap patterns across sessions, and proposing graduations to Scripture when a heuristic appears 3+ times.

## Value Statement

The development team gets automated pattern detection across diary entries, turning the manual Philosopher ritual into a systematic feedback loop that catches graduation-worthy heuristics before they fade into forgotten entries.

## Problem

The Philosopher role is currently manual — a human invokes a session, names it "the Philosopher", and points it at the diary. There is no automated way to:

1. **Periodically scan diary entries** for recurring `heuristic:`, `trap:`, and `Seed:` markers
2. **Detect graduation candidates** — heuristics that appear 3+ times across different entries
3. **Surface stale Seeds** — forward-looking questions planted in entries that were never revisited
4. **Propose Scripture edits** — route confirmed patterns to `.chaplain/inbox/` for the Chaplain to enforce

The Scripture process rule `graduation` states: *"Heuristic appears twice → create FR; confirmed recurrence → graduate to Scripture."* Without automation, this rule is honored in theory but violated in practice — an instance of the `audit_as_ritual` trap.

## Proposed Solution

### 1. `philosopher.sh` — Daemon Script

A thin polling/on-demand wrapper following the `watch.sh` pattern:

```bash
#!/usr/bin/env bash
# Philosopher daemon — scans diary for recurring patterns
# Usage: .chaplain/philosopher.sh [--once]  (default: poll daily)

DIARY_DIR="docs/diary"
INBOX=".chaplain/inbox"
LOG="tmp/philosopher-$(date +%Y-%m-%d).log"

# --once flag for on-demand execution (default mode)
# Without --once: poll every 24h (for background daemon use)

yamlgraph graph run examples/philosopher/graph.yaml \
  --var diary_dir="$DIARY_DIR" \
  --var inbox_dir="$INBOX" \
  --var lookback_days=30 \
  --var graduation_threshold=3 \
  --var date="$(date +%Y-%m-%d)" \
  --var diary_prefix="Philosopher" \
  --full 2>&1 | tee "$LOG"
```

**Key design**: Runs `--once` by default (on-demand). No cron scheduling in v1 — the human or CI triggers it. This avoids the spam problem entirely.

### 2. `examples/philosopher/graph.yaml` — Scan + Propose Graph

A linear graph with 4 nodes:

```yaml
version: "1.0"
name: philosopher-scan
description: Scan diary entries for recurring patterns and propose graduations

prompts_relative: true
prompts_dir: prompts

defaults:
  provider: anthropic
  model: claude-sonnet-4-5

state:
  diary_dir: str           # Path to docs/diary/
  inbox_dir: str           # Path to .chaplain/inbox/
  lookback_days: int       # How many days back to scan (default: 30)
  graduation_threshold: int # Min occurrences to propose graduation (default: 3)
  date: str                # Current date for diary entry
  diary_prefix: str        # Diary entry prefix (default: Philosopher)
  scan_result: dict        # Extracted markers with counts
  proposals: list          # Graduation proposals (if any)
  diary_entry: dict        # Philosopher's own diary entry
  written: bool            # True after diary append

tools:
  scan_diary_tool:
    type: python
    module: examples.philosopher.tools
    function: scan_diary_markers
  write_diary_tool:
    type: python
    module: examples.shared.diary
    function: write_diary
  write_proposal_tool:
    type: python
    module: examples.philosopher.tools
    function: write_proposals

nodes:
  # Stage 1: Scan — Extract markers from diary files
  scan:
    type: python
    tool: scan_diary_tool
    state_key: scan_result

  # Stage 2: Analyze — LLM detects patterns and proposes graduations
  analyze:
    type: llm
    prompt: analyze
    variables:
      scan_result: "{state.scan_result}"
      graduation_threshold: "{state.graduation_threshold}"
    state_key: proposals

  # Stage 3: Write proposals to inbox (if any)
  propose:
    type: python
    tool: write_proposal_tool
    state_key: proposals_written

  # Stage 4: Write Philosopher's own diary entry
  reflect:
    type: llm
    prompt: reflect
    variables:
      scan_result: "{state.scan_result}"
      proposals: "{state.proposals}"
    state_key: diary_entry

  write_diary:
    type: python
    tool: write_diary_tool
    state_key: written

edges:
  - from: START
    to: scan
  - from: scan
    to: analyze
  - from: analyze
    to: propose
  - from: propose
    to: reflect
  - from: reflect
    to: write_diary
  - from: write_diary
    to: END
```

### 3. `examples/philosopher/tools.py` — Python Tools

```python
def scan_diary_markers(state: dict) -> dict:
    """Scan diary files for heuristic/trap/Seed markers.

    Returns dict with:
      - heuristics: {text: [file1, file2, ...]}
      - traps: {name: [file1, file2, ...]}
      - seeds: {question: file}
      - file_count: int
    """

def write_proposals(state: dict) -> dict:
    """Write graduation proposals to .chaplain/inbox/.

    Only writes proposals where occurrence count >= graduation_threshold.
    Deduplicates against existing Scripture entries.
    """
```

### 4. Deduplication Against Scripture

The `analyze` prompt instructs the LLM to compare extracted patterns against the existing Knowledge Graph in `.github/copilot-instructions.md`. Patterns already present in `traps:` or `cures:` sections are filtered out — only genuinely new graduation candidates are proposed.

### 5. Output Flow

```
docs/diary/*.md  →  scan_diary_markers()  →  LLM analyze  →  proposals
                                                              ↓
                                           .chaplain/inbox/graduate-{pattern}.md
                                                              ↓
                                           Chaplain watch.sh picks up → FR → Enforce
```

The Philosopher **never edits Scripture directly**. It proposes to inbox; the Chaplain Plans, Judges, and Enforces. This preserves the existing authority chain.

## Acceptance Criteria

- [ ] AC-1: `philosopher.sh` runs without errors when invoked with `--once`
- [ ] AC-2: `scan_diary_markers()` extracts `heuristic:`, `trap:`, and `Seed:` markers from diary files within the lookback window
- [ ] AC-3: Patterns appearing ≥ `graduation_threshold` times (default 3) across distinct files produce a proposal
- [ ] AC-4: Proposals are written to `.chaplain/inbox/` as markdown files consumable by `watch.sh`
- [ ] AC-5: Patterns already present in Scripture (`traps:` or `cures:` in `.github/copilot-instructions.md`) are excluded from proposals
- [ ] AC-6: The Philosopher writes its own diary entry to `docs/diary/` via the shared `write_diary` tool
- [ ] AC-7: Unit tests for `scan_diary_markers()` with fixture diary files covering: no markers, below threshold, at threshold, above threshold, and already-graduated patterns
- [ ] AC-8: Integration test running the full graph with mock diary directory
- [ ] AC-9: `examples/philosopher/README.md` documents usage, graph topology, and output format
- [ ] Tests added (unit + integration)
- [ ] Documentation updated (`examples/philosopher/README.md`)

## Alternatives Considered

### 1. Pure LLM scan (no Python extraction)
Feed all diary files directly to an LLM and ask it to find patterns. **Rejected**: Too expensive for 100+ files, non-deterministic pattern matching, and no structured deduplication against Scripture.

### 2. Cron-scheduled daemon
Run automatically on a daily schedule. **Deferred to v2**: On-demand (`--once`) avoids inbox spam and gives the user control. A scheduling wrapper can be added trivially later.

### 3. Direct Scripture editing
Let the Philosopher edit `.github/copilot-instructions.md` directly. **Rejected**: Violates the authority chain. The Chaplain's Plan → Judge → Enforce pipeline exists precisely for this purpose. The Philosopher proposes; the Chaplain decides.

### 4. Database-backed pattern tracking
Store marker counts in SQLite across runs. **Deferred**: File-based scanning is sufficient for the current diary size (~150 files). If the diary grows to 500+, a persistent index becomes worthwhile.

## Out of Scope

- **Stale FR triage**: Surfacing approved-but-unimplemented FRs is a separate concern (potential FR-185)
- **Cross-session trap detection**: Requires session metadata not currently captured in diary format
- **Automatic PR creation**: The Philosopher proposes; enforcement is the Chaplain's domain
- **Scheduling/cron integration**: On-demand only in v1

## Judgement

**Verdict: APPROVE** — Scope frozen. Authority granted to implement.

**Evaluation:**

| Criterion | Assessment |
|-----------|------------|
| Scope clarity | ✅ Clear and minimal. Single pipeline: scan → analyze → propose → reflect. |
| Contradictions | ⚠️ One minor gap (see annotation below). |
| Acceptance criteria | ✅ All 9 ACs are measurable and testable. |
| Feasibility | ✅ Follows proven `watch.sh` + copilot graph pattern exactly. |
| Architecture alignment | ✅ Three-layer pattern, authority chain preserved, shared tools reused. |
| Single responsibility | ✅ All stages serve one goal: detect recurring diary patterns and propose graduations. |

**Annotation for implementer — Deduplication variable gap:**

Section 4 states the `analyze` prompt instructs the LLM to compare against existing Scripture in `.github/copilot-instructions.md`. However, the graph YAML passes only `scan_result` and `graduation_threshold` to the `analyze` node — no Scripture content. Resolution options (pick one):

1. Have `scan_diary_markers()` also extract current Scripture traps/cures and include them in `scan_result`
2. Add a `scripture_content` state field and a prior node to read it
3. Drop LLM-based deduplication entirely; rely solely on `write_proposals()` deterministic deduplication (recommended — deterministic filtering is more reliable than LLM comparison per Commandment 6)

This does not affect scope or AC validity — all three options satisfy AC-5.

## Related

- **`.chaplain/watch.sh`** — Model for the daemon pattern; the Philosopher's proposals feed into this pipeline
- **`examples/copilot/graph.yaml`** — Chaplain graph structure (Plan → Judge → Summarize → Write)
- **`examples/shared/diary.py`** — Shared `write_diary` tool reused by the Philosopher
- **`.github/copilot-instructions.md`** — Scripture containing the Knowledge Graph (traps/cures/process)
- **Scripture `process.graduation`** — The rule this FR automates: *"Heuristic appears twice → FR; confirmed recurrence → graduate to Scripture"*
- **`audit_as_ritual` trap** — The cognitive hazard this FR addresses: audits without enforcement become ritual
