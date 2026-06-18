# The signal that ran after the run it should have informed

**Date:** 2026-06-18
**FR:** FR-530 (Stage 1) — DM v2 reviewer continuity as an in-loop signal

## What happened

The cross-seam critic — the only component that reads *across* chapter seams and grades
continuity — already ran in `generate_and_review.sh`. But it ran as a separate example,
*after* generation, writing prose into `review.md`. Its verdict never travelled with the
run that produced the book. To answer "did this run regress continuity?" you had to open a
markdown file and read it with your eyes.

Stage 1 was small: after the review, emit the continuity axis as a tiny JSON next to the
book — `{book, continuity_score, break_count, posture}`. Three tests, one shell line, one
reused parser. The hard part was not the code; it was *not building Stage 2*.

## The trap: the corrective-loop gravity well

The FR's own body sketches Stage 2 — a per-seam re-roll that *corrects* low-continuity
seams in-loop. That is the exciting part. The witness is boring plumbing. Every instinct
pulled toward "while I'm here, let me wire the re-roll." The Judgement had already named
this exact pull (J2: "keeping it as a 'sketch' inside this FR invites scope creep at
enforce") and removed Stage 2 from scope entirely — not deferred, *removed*. Honoring that
meant shipping the boring half and stopping, even though the interesting half was one
function away.

The discipline that held: a corrective loop driven by an *un-calibrated* critic optimizes
whatever the critic over-weights. FR-532 (committed an hour earlier) had just *proven* the
critic over-weighted physical micro-state — 61% of its breaks were things a reader
forgives. Building a re-roll on top of that pre-calibration critic would have spent
generation budget fixing rope-grip "breaks." The sequencing — calibrate (FR-532), then
witness (FR-530 Stage 1), then *maybe* correct (future FR) — is not bureaucracy; each
stage de-risks the next.

## The reuse instinct that paid off

The witness needs to parse `review.md`'s continuity section. FR-532's calibration harness
already had `parse_continuity_breaks`. The FR-531 lesson ("don't duplicate the
measurement") was fresh, so I imported it rather than re-writing the parser. This creates
a cross-FR import (FR-530 code → FR-532 code) that feels slightly odd, but the alternative
— two parsers that can drift — is the real defect. One parser, one definition of what a
"break" is.

## Heuristic

**A diagnostic that runs after the thing it diagnoses is documentation; a diagnostic that
emits a machine-readable artifact on the same run is telemetry.** The difference is not
*when* it runs but *whether its output can be joined without a human*. Stage 1 changed
nothing about *when* the critic runs — it changed whether the score leaves a structured
trace. That single JSON is the precondition for trending, for joining, and (eventually)
for correcting. Prose is a dead end; structure is a join key.

**Corollary:** when a Judgement removes the exciting half of an FR, the enforce step's job
is to ship the boring half *well* and resist re-litigating the cut. The removed scope is
not lost — it is a future FR with better-calibrated inputs.

## Seed

The witness now emits `continuity_witness.json` per run, but nothing yet *reads* the
accumulating fleet of them. FR-531's report joins them in principle but isn't wired to.
When does a directory full of per-run witnesses stop being telemetry and become a
training signal — and who decides the critic that scores them is still calibrated by then?
*Who watches the witnesses accumulate?*
