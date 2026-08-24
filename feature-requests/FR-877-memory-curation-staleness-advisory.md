# Feature Request: Memory Curation Staleness Advisory (Session Briefing Line)

**Priority:** LOW
**Type:** Enhancement
**Status:** Proposed
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

1. **Curation-state marker:** `apply.py` (FR-875), after a successful
   apply, writes `.curation-state.json` into the memory root:
   `{applied_at, manifest_sha256, notes: {path: sha256}}` — the frozen
   manifest's note hashes plus the post-apply hashes of redacted notes.
   Hidden file (dotfile) so collect.py's `*.md` glob never sweeps it
   into a future manifest.
2. **Advisory check:** `examples/memory-curation/advisory.py` — pure
   stdlib, no LLM. Inputs: `--memory-root` (explicit in tests; the
   hook passes the discovered workspace root), `--threshold` (default
   5). Compares live `repo/*.md` hashes vs the marker: counts new,
   edited, deleted. Prints ONE line to stdout iff
   `new+edited+deleted >= threshold` or the marker is absent and the
   corpus is non-empty ("never curated"); prints nothing otherwise.
   Exit 0 in all advisory outcomes; nonzero only on real errors.
3. **Briefing integration:** `session-briefing.sh` (FR-743) additionally
   runs the advisory fail-open (timeout-guarded, `|| true`), same as its
   existing pattern; a failure appends one bounded line to the hook log,
   never blocks the session.

```bash
# printed at SessionStart only when drift ≥ threshold
memory: 6 notes new/edited since last curation (2026-08-24) — consider a hygiene pass
```

## Acceptance Criteria

- [ ] AC-01: `apply.py` writes `.curation-state.json` (applied_at,
      manifest_sha256, per-note sha256 reflecting post-apply bytes) into
      the memory root on successful apply; dotfile excluded from collect
      manifests (test).
- [ ] AC-02: advisory prints nothing below threshold, one line at/above
      threshold, and a "never curated" line when the marker is absent
      and notes exist (tests, temp roots only — never the operator's
      real store).
- [ ] AC-03: edited/new/deleted are counted by sha256 comparison, not
      mtime.
- [ ] AC-04: `session-briefing.sh` runs the advisory fail-open with a
      timeout; a broken advisory leaves one bounded log line and exits 0
      (test via env-overridable paths, FR-874-era hook-test pattern).
- [ ] AC-05: zero LLM calls / zero network in the advisory path (pure
      stdlib; test asserts no provider imports).
- [ ] AC-06: tests tagged `REQ-YG-XXX` (extend CAP-247 with a new REQ);
      docs: `examples/memory-curation/README.md` gains a Recurrence
      section stating the advisory model and why scheduling is
      deliberately absent.
- [ ] AC-07: diary reflection.

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

## Judgement (pending)

Not judged in the author's session; route:
`.github/skills/judge-fr/adapters/README.md`.
