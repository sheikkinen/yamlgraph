# FR-741: Orphan Intention Triage — DIED OPEN todos in the session-start briefing

**Status:** Proposed
**Type:** Enhancement (agent-facing tooling, `scripts/vscode/`)
**Effort:** 0.5 day
**Requested:** 2026-07-16
**Spawned by:** todos.py forensics (CSI arc, 2026-07-16): 191 todo
slots, 21 non-empty, **18 orphaned open intentions** in
`memento/chat-todo-list`. Case evidence: the Vertex migration
(dee997c4 died mid-research; e06433d5 shipped the work; the record
never reconciled) and NC-365 (orphan reads "Create NC-365
[not-started]" while NC-365-supervisor-boot-resilience.md and its
judgement exist). The authoring session's own row listed three
not-started items for work completed and pushed hours earlier.

**Prior art:** `scripts/vscode/todos.py` (the observation spike this
FR integrates — lane rule: integration moment = FR moment);
FR-739/FR-740 (the delivery discipline: name the rung, the reader,
the moment — `a_view_without_a_reader_is_a_write_only_database`);
FR-738 (disposition-required precedent: an orphan, like prior art,
must be resumed or explicitly dropped, never silently ignored);
`one_session_one_repo` Scripture + session-introspection skill (the
rung-2 surface this extends). Disposition: no rejected FR touches
todo-store territory; the store itself was dark until today.

## Problem

Sessions die holding open intentions. The todo store is honest about
plans and silent about outcomes: work migrates to successor sessions
(Vertex, NC-365) or evaporates, and nothing ever reconciles the
record. 18 orphans have accumulated invisibly. A successor session
starting work has no view of what its predecessors left open — the
`unasked_question_is_an_unowned_gate` trap, for intentions.

## Proposed Solution

1. **Artifact cross-check in todos.py**: an orphan whose title names
   an `FR-\d+`/`NC-\d+` id is auto-resolved against the filesystem —
   verdict `DELIVERED ELSEWHERE` (artifact exists) vs `DROPPED`
   (nothing found). Mechanical, no LLM.
2. **Rung-2 delivery**: `now.py` gains a `== orphaned intentions ==`
   section for the current workspace — DIED OPEN items ≤30 days old,
   with verdicts, capped at 10 rows (FR-737 F2: silence over noise;
   ancient orphans are archaeology, not triage).
3. **Explicit drop**: `todos.py --drop <session8> <n>` records a
   disposition (local JSONL beside compactions.jsonl) so a triaged
   orphan stops appearing. Resume-or-drop, never silent.

## Acceptance Criteria

- [ ] AC-01 RED: fixture todo store → cross-check verdicts exact
      (DELIVERED ELSEWHERE requires the named artifact on disk).
- [ ] AC-02: now.py section capped and age-filtered; witnessed in a
      real tool result (the FR-738 receipt standard).
- [ ] AC-03: dropped orphans persist across runs and are excluded.
- [ ] AC-04: raw read of the first full triage recorded in this FR
      (which of the 18 orphans are DELIVERED / DROPPED / real debt).

## Out of scope (purge list)

- Writing back to state.vscdb (read-only forever; dispositions live
  in our own sidecar).
- LLM classification of orphan similarity to commits.
- Cross-machine reconciliation.
- Diary-class orphans (FR-742's territory).

## Questions for the human (as options, or 'none')

None — mechanism and rung are pinned by measured evidence; scope
questions (age cap 30d, row cap 10) are judgement-adjustable defaults.
