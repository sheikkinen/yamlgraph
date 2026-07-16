# FR-742: Undelivered Diary Detection — the Distill step's measured abandonment

**Status:** Proposed
**Type:** Enhancement (process enforcement, `scripts/vscode/` + doctrine)
**Effort:** 0.5 day
**Requested:** 2026-07-16
**Spawned by:** todos.py forensics (2026-07-16): **three separate dead
sessions orphan the same final item — the diary reflection** (1c395e06
†0.2d "Document findings and diary entry" in-progress; 31027c36 †93d
"Write diary reflection"; 32c7dcee †120d "Diary reflection"
not-started). The Scripture's Distill step is the most-abandoned step
in the process — no longer suspicion, measurement. Three occurrences
clears the two-strike bar with a strike to spare.

**Prior art:** Scripture Sermon **Distill** + `diary-gate` CI check
(the existing enforcement — which only fires on feat/fix PRs with
FR refs; sessions that die BEFORE committing escape it entirely: the
gap this FR closes); FR-741 (sibling: generic orphan triage — this FR
is the elevated-severity diary class, split because its consumer and
its debt semantics differ); `scripts/vscode/todos.py` (the observation
spike); reception hierarchy (delivery on rung 2). Disposition: extends
diary-gate's intent to the pre-commit-less death path; no rejected FR
occupies this territory.

## Problem

The diary is written last, and sessions die at exactly the moment
reflection is due — the guillotine and the deadline coincide. The
existing diary-gate catches missing reflections only when a PR/commit
happens; a session that ends (closed, compacted into oblivion,
abandoned) with its insights unwritten leaves no trace except the
orphaned todo. Three documented losses. The insight inventory of a
dead session is exactly the knowledge `document_for_the_successor`
says must not be re-paid for.

## Proposed Solution

1. **Diary-class orphan detection** in todos.py: orphan titles
   matching `diary|reflect|distill` (case-insensitive) are class
   `DIARY DEBT`, exempt from FR-741's 30-day age cap (doctrine debt
   does not expire).
2. **Debt check against the record**: for each DIARY DEBT orphan,
   check `docs/diary/` for entries dated within the session's last
   active week (mtime window). Entry found → `LIKELY DELIVERED`
   (verdict, not proof); none → `UNWRITTEN`.
3. **Rung-2 delivery**: surfaced in the same now.py section as FR-741
   with distinct marking; an UNWRITTEN debt row includes the session
   title and transcript path — everything a successor needs to write
   the reflection posthumously (the transcript store holds the
   verbatim material).
4. **Doctrine line**: one sentence in the Scripture's Distill
   paragraph: a session's diary debt survives the session; successors
   inherit it via the briefing.

## Acceptance Criteria

- [ ] AC-01 RED: fixture with diary-class orphans → classification and
      age-cap exemption exact.
- [ ] AC-02: docs/diary mtime-window check yields LIKELY DELIVERED /
      UNWRITTEN verdicts; fixture-pinned.
- [ ] AC-03: the three real debts triaged and recorded in this FR —
      each either matched to an existing diary entry or written
      posthumously from its transcript (at least one posthumous diary
      produced as the witness).
- [ ] AC-04: Scripture sentence landed.

## Out of scope (purge list)

- Auto-writing diaries by LLM (the successor writes; the tool only
  delivers the debt + material).
- Blocking gates (this is a briefing signal; diary-gate remains the
  merge-boundary enforcement).
- Generic orphan triage (FR-741).

## Questions for the human (as options, or 'none')

None — the three-strike evidence pins the pain; AC-03's posthumous
diary is the only judgement call and it is the natural witness.
