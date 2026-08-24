# Feature Request: Memory Curation Staleness Advisory (Session Briefing Line)

**Priority:** LOW
**Type:** Enhancement
**Status:** Enforced (2026-08-24)
**Effort:** 0.5 days
**Requested:** 2026-08-24
**First consumer / first event:** the agent at SessionStart, reading the
FR-743 briefing at the moment the memory corpus has drifted past the
threshold since the last applied curation — today that signal exists only
as operator instinct, and the todo-forensics record shows Distill-class
reminders are the most-abandoned step when unmechanized.

**Blast radius:** entirely machine-local. Zero LLM calls, zero egress; one
marker file written inside the memory root at apply time; one advisory
line printed at session start. Worst-case reader: this operator.

## Summary

FR-875's curation pipeline is deliberately un-schedulable at its
destructive end (hash-bound human sign-off, C-6) — but nothing today
tells anyone *when a draft run is worth doing*. This FR adds the
detection half: `apply.py` records the curated corpus state in the
memory root, and a zero-cost advisory check in the session briefing
prints one line when the live corpus has drifted (N notes new/edited
since last apply). Detection is mechanical; execution stays deliberate.

## Value Statement

Curation recurs when the corpus actually drifts — not on a calendar that
under/over-fires, and not never (the current default) — while the human
gate on execution stays intact.

## Problem

1. Notes rot in weeks (version pins, deployment facts) but curation has
   no trigger: the FR-875 hygiene pass happened because a conversation
   prompted it. Sessions demonstrably abandon remember-to-do-X steps
   (todo forensics: Distill is the most-orphaned intention).
2. Calendar scheduling is the wrong shape: quiet weeks fire pointlessly,
   busy weeks under-fire, and a drafted-but-unsigned disposition is
   voided by any memory edit (drift refusal) — so drafts must be made
   near the sign-off moment. The trigger must be event-based drift, and
   it must cost nothing (a SessionStart hook runs every session).

## Ideal Result

After every applied curation, the memory root carries a marker of what
was curated. Every session briefing silently compares live notes against
the marker in milliseconds; when drift crosses the threshold it prints
one line — `memory: 6 notes new/edited since last curation (2026-08-24)
— consider a hygiene pass` — and otherwise prints nothing. A broken
check never blocks a session and never fakes silence-as-health
(fail-open with bounded evidence, the FR-875 R-4 rule).

## Proposed Solution

1. **Curation-state marker (R-1: post-apply live baseline):** `apply.py`
   (FR-875/878), after the full apply transaction (mutations + tombstone
   rows) succeeds, writes `.curation-state.json` into the memory root:
   `{version, applied_at, manifest_sha256, disposition_sha256, notes}`
   where `notes` maps only LIVE post-apply repo-note paths to their live
   sha256 — kept notes at their current hash, redacted notes at their
   post-redaction hash, **forgotten paths absent** (else the first
   advisory after curation counts intentional forgets as deleted drift
   — the false-fire the judge caught). Dotfile: never collected.
2. **Advisory check (R-2: frozen corpus predicate):**
   `examples/memory-curation/advisory.py` — pure stdlib, no LLM/network.
   Inputs: `--memory-root` (explicit in tests), `--threshold` (default
   5). Corpus predicate: regular, non-symlink `*.md` files directly
   under `<memory-root>/repo/`, **including `_tombstones.md`** — and
   symmetrically, the marker's `notes` includes it — so tombstone
   appends count as ordinary edits toward drift (they are corpus
   changes; a tombstone-only update below threshold stays silent —
   tested). `.curation-state.json` excluded by path. Compares sha256,
   never mtime; counts new + edited + deleted. Prints exactly ONE line
   iff count >= threshold, or the marker is absent and the corpus is
   non-empty ("never curated"); silence and exit 0 otherwise.
   Malformed/unreadable marker or unreadable corpus paths are REAL
   errors: nonzero exit + bounded stderr — never faked as no-drift
   (`plausible_wrong_answer` guard).
3. **Briefing integration (R-3: observable fail-open):**
   `session-briefing.sh` (FR-743) runs the advisory with env-overridable
   memory root, threshold, timeout, and log path
   (`MEMORY_ADVISORY_ROOT/THRESHOLD/LOG`); uses `timeout` only when
   present (Darwin may lack it). Failure never blocks SessionStart and
   prints no user-facing line, but appends ONE bounded JSONL record to
   the log (default `.github/hooks/logs/memory-sync.jsonl` family,
   200-line cap) — fail-open, never silent-success-shaped.

```bash
# printed at SessionStart only when drift ≥ threshold
memory: 6 notes new/edited since last curation (2026-08-24) — consider a hygiene pass
```

## Acceptance Criteria (revised per judgement)

- [ ] AC-01: `apply.py` writes the versioned marker only after a fully
      successful apply; forgotten paths absent; kept/redacted at live
      hashes (test: a curation WITH forgets produces zero immediate
      drift — C-2).
- [ ] AC-02: marker excluded from collection/advisory enumeration;
      `_tombstones.md` handled symmetrically (in marker AND comparison);
      tombstone-only update below threshold stays silent (test).
- [ ] AC-03: advisory pure stdlib, `--memory-root`/`--threshold`
      (default 5), sha256 not mtime, counts new/edited/deleted.
- [ ] AC-04: silence + exit 0 below threshold; exactly one line + exit 0
      at/above threshold; one line + exit 0 for never-curated non-empty
      corpus (tests).
- [ ] AC-05: malformed/unreadable marker or corpus → nonzero exit +
      bounded stderr; never fakes no-drift (test).
- [ ] AC-06: briefing hook env-overridable (root/threshold/timeout/log);
      failure exits 0, no user line, one bounded JSONL record (test via
      env overrides).
- [ ] AC-07: tests use temp/fixture roots only — never the operator's
      real store.
- [ ] AC-08: test asserts zero LLM/network/provider imports in the
      advisory path.
- [ ] AC-09: CAP-247 extended with a new REQ; all new/changed tests
      tagged.
- [ ] AC-10: README gains a Recurrence section (advisory model,
      threshold, marker location, fail-open, why no scheduling).
- [ ] AC-11: FR records implementation status/deviations; diary
      reflection.

## Alternatives Considered

- **Run the draft stage at SessionStart:** 57 LLM calls of egress per
  session open for a corpus that changes a few notes/week —
  `growth_as_default` in hook form; rejected in the FR-875 recurrence
  analysis.
- **Cron/calendar draft runs:** drift refusal voids drafts made far from
  the sign-off moment; calendar cadence mismatches event-shaped rot.
- **Do nothing (instinct-triggered):** the todo-forensics record shows
  unmechanized reminders are abandoned; detection is cheap enough to
  mechanize.
- **Fire-count instrumentation (diary seed 3):** richer signal (which
  notes are read), but a larger build; drift-count is the minimal
  version and does not preclude it.

## Prior art

**Prior art:** FR-875 (parent — this is its named recurrence mechanism;
its C-6 human gate is why execution cannot be scheduled and why this FR
is advisory-only). FR-743 (session briefing — the delivery seam; its
fail-open contract is inherited). FR-874 (REJECTED — no transport here;
everything is machine-local, visibility precondition satisfied by
construction). `detection_without_enforcement` (Scripture): advisory
without a gate is the *correct* ceiling here because the gate is
intentionally the human sign-off.

## Related

- `docs/diary/diary-2026-08-24-the-note-that-judged-its-own-transport.md`
  addendum 3 (recall-time value law; fire-count seed remains separate)
- `.github/hooks/scripts/session-briefing.sh` (FR-743)

## Implementation (2026-08-24)

RED `a5e4f89b` (10 condemning tests, SKIP=pytest) → GREEN this change.

- `apply.py`: `write_curation_state()` after the full transaction —
  live enumeration of `repo/*.md` post-apply (forgotten paths absent by
  construction; `_tombstones.md` included symmetrically).
- `examples/memory-curation/advisory.py`: pure stdlib; new/edited/deleted
  by sha256; one-line-or-silence contract; malformed marker → nonzero +
  stderr.
- `.github/hooks/scripts/memory-advisory.sh`: env-overridable
  (`MEMORY_ADVISORY_ROOT/THRESHOLD/TIMEOUT/LOG`), fail-open, bounded
  JSONL evidence (200-line cap); invoked from `session-briefing.sh`
  (C-5: hook change rides this FR's human review at push).
- REQ-YG-622 (CAP-247 extension); 10 new tests, 43 green across the
  three curation suites; C-2 witnessed by
  `test_forget_run_yields_zero_immediate_drift`.
- Deviation: none — R-1…R-4 implemented as folded.

## Judgement (2026-08-24)

**Verdict: APPROVED WITH REVISIONS** — rendered via the sole judge route;
full artifact:
`feature-requests/FR-877-memory-curation-staleness-advisory.judgement.md`.
R-1 marker = post-apply live baseline (forgets absent — kills the
false-drift false-fire); R-2 frozen corpus predicate incl. symmetric
`_tombstones.md`; R-3 observable fail-open (bounded JSONL, no silent
success); R-4 exact test matrix. All folded above. Authority active.
Gates: C-2 forget-run zero-drift proof; C-3 zero LLM/network; C-4 temp
roots only; C-5 hook change needs human review as durable policy; C-6 no
judge/YAMLGraph invocation during enforcement.
