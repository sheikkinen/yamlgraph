# FR-741: Orphan Intention Triage — DIED OPEN todos in the session-start briefing

**Status:** Judged — APPROVED with corrections (see Judgement)
**Type:** Enhancement (agent-facing tooling, `scripts/vscode/`)
**Effort:** 0.5 day
**Requested:** 2026-07-16
**Judged:** 2026-07-16 — the 30-day briefing cap would hide 4 of 6 dead
sessions including both exhibit cases; backlog-triage-first ordering bound
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

## Judgement (2026-07-16)

**Verdict: APPROVED — with the FR's own defaults measured against the
evidence they were written from.**

| # | Finding | Resolution (binding) |
|---|---------|----------------------|
| F1 | **The 30-day cap hides the FR's own exhibits.** DIED OPEN ages measured: 0.2 / 3.3 / 93 / 106 / 120 / 133 days — the cap excludes 4 of 6 dead sessions including the Vertex case AND the NC-365 case. A briefing filtered to recency is right; shipping it against an untriaged backlog silently buries the archaeology forever | **Backlog-zero precondition**: AC-04's full 18-orphan triage executes FIRST (every ancient orphan explicitly dropped or resumed via the sidecar); only then does the 30-day cap arm. Enforce order: AC-01 → AC-04 → AC-02/03 |
| F2 | **The artifact cross-check covers 3 of 29 open orphans** (10%) — and 2 of those 3 belong to LIVE sessions. The DELIVERED-ELSEWHERE detector applies to exactly one dead orphan today (NC-365). Correct, cheap, but the FR's framing oversells it | Keep (it is one regex + one glob); reframed as a triage *aid*, not the mechanism. The FR's primary value is visibility + disposition — F1's backlog-zero is the real deliverable |
| F3 | `--drop <session8> <n>` is **positionally keyed** — fragile against any list mutation and ambiguous in review | Content key: `(session_id, sha1(title)[:8])`. A disposition names what it dropped |
| F4 | Dispositions sidecar location unpinned | Beside compactions.jsonl (`scripts/vscode/orphan-dispositions.jsonl`), same append-only JSONL discipline, git-tracked — dispositions are decisions, decisions get history |

**Purge additions:** none beyond the FR's own list.

**Scope frozen:** AC-01 (cross-check witnesses) → AC-04 (backlog-zero
triage, recorded here) → AC-02 (capped briefing section, receipt
witnessed) → AC-03 (content-keyed drops persist).

### Questions for the human (as options, or 'none')

None — F1's reordering resolves the only real hazard found.

## Judgement Addendum (2026-07-16): A1 — live intent rows, in git we trust

Human reflection after judgement: "now should include the next steps
agents are/were planning ... and in git we trust." Correct on both
halves, and the second constrains the first:

**A1 (binding):** AC-02's briefing section gains LIVE-session rows —
each live session's in-progress/next todos — completing the board's
tense triad: git = past (fact), tap = present (fact), todos = future
(**claim**). Constraints, from measured staleness (the authoring
session's own todos read not-started for work pushed hours earlier;
NC-365's orphan likewise — claims lag reality asymmetrically because
updating is optional effort):
- Intent rows are rendered as testimony, visually distinct from fact
  rows (a `claims:` prefix), never merged with git-derived state.
- The artifact cross-check runs on live claims too: a "next step"
  naming an FR/NC id that already has a git artifact is flagged
  `STALE CLAIM` — git overrules the todo, mechanically, every time.
- No collision inference in this FR (two sessions' next-steps naming
  the same file = future work; recorded as a seed, not scope).
