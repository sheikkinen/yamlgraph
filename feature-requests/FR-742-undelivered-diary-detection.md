# FR-742: Undelivered Diary Detection — the Distill step's measured abandonment

**Status:** Judged — APPROVED with corrections (see Judgement)
**Type:** Enhancement (process enforcement, `scripts/vscode/` + doctrine)
**Effort:** 0.5 day
**Requested:** 2026-07-16
**Judged:** 2026-07-16 — transcripts do NOT survive for 2 of the 3 real
debts; the posthumous-diary material clause corrected to chatSessions
fallback before a line of code exists
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

## Judgement (2026-07-16)

**Verdict: APPROVED — with the material clause corrected by
measurement** (`read_raw_output_first` applied to the stores the FR
plans to read).

| # | Finding | Resolution (binding) |
|---|---------|----------------------|
| F1 | **Transcripts do not survive for 2 of the 3 real debts.** Measured: 31027c36 (†93d) and 32c7dcee (†120d) have NO transcripts/ file; both have chatSessions files (1.5 MB, 13.6 MB — which contain the full session, both sides). Only the freshest debt (1c395e06, †0.2d) has a transcript. The FR's "transcript path" material clause fails exactly where the debt is oldest | Material = transcript **if present, else chatSessions file** — path + size in the debt row. AC-03 reworded accordingly. Transcripts are a recent store; age of debt anti-correlates with material richness — recorded as a fact for the successor |
| F2 | The mtime window "last active week" is direction-ambiguous (a successor's later posthumous entry must not count as the dead session's own delivery) | Window = [last_active − 7d, last_active + 1d]. Later entries are FR-742's own products, not evidence of delivery |
| F3 | 1c395e06's debt status is undecidable by inspection (its NC-393 work produced commits; whether a diary landed needs the mechanical check, not eyeballing) | Correct behavior: the tool decides. Recorded as the acceptance fixture's first real input — AC-02's verdict on 1c395e06 is part of AC-03's triage record |
| F4 | The `diary\|reflect\|distill` class regex will hit LIVE sessions' pending diary todos (measured: c0f1927c carries one now) | Class applies to DIED OPEN only; LIVE sessions own their futures |

**Purge additions:** none; the FR's own purge list (no LLM
auto-writing, no blocking gate) stands confirmed.

**Scope frozen:** AC-01 (classification + cap exemption) → AC-02
(window check, F2 bounds) → AC-03 (three debts triaged; ≥1 posthumous
diary from best-available material per F1) → AC-04 (Scripture
sentence).

### Questions for the human (as options, or 'none')

None — all findings resolved mechanically; the posthumous diary's
subject choice (which of the three debts) falls to enforce, guided by
F1's material table.
