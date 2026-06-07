# The Phase We Skipped — 2026-06-07

## What happened

We set out to rebuild the Dungeon Master around a single honest goal: *interactive
generation of the synopsis*. The prototype had been detached to `purgatory/`. Good
instinct. Then we immediately did the wrong thing with it: I wrote a full
feature request (FR-474) — open questions, acceptance criteria, reuse tables,
proposed CAP IDs, gate-green checklists — for what is, in truth, a **sketch**.

The user named the failure better than I did. My first reflection blamed *pacing*
("thinking too long"). The user corrected: it wasn't pacing, it was a **phase
mismatch**. We were applying enforce-phase machinery (FR, TDD-first, CAP/REQ tags,
green-gate discipline) to **prototype-phase** work, where the only deliverable is a
*decision* — keep, kill, or reshape the bet — not a green pipeline.

## The tells we both ignored

Three signals were on the table the whole session, and we walked past all of them:

1. **It got detached to purgatory.** You don't quarantine something you're confident
   in. Detachment *is* a prototype verdict — "not proven yet." Building a rigorous FR
   on top of an unproven interaction repeats the original sin (over-building before
   validating) one level up the abstraction.
2. **The user kept saying "overthinking," "too long," "let the test fail."** Each was
   a phase signal — the ceremony exceeded the work. I answered every one with *more*
   ceremony.
3. **A red README-audit test was acceptable.** In the enforce phase a red gate is an
   emergency. In the prototype phase there is no contract to protect, so the gate
   isn't the point yet. The willingness to leave it red was the clearest possible
   marker that we had left enforce territory — and I still reached for the gate
   reflex.

## Why it happens

This repo's doctrine is written for the **enforce** phase — "what survives the fire
may merge." All the tooling, all the muscle memory, lives there. The Scripture names
Research and Plan, but in practice both collapse straight into Enforce because that's
where the reflexes are. The missing rung is **prototyping**: cheap, throwaway, no FR,
no tests-first, no CAP. Its output is a sentence ("the synopsis loop is worth
building / isn't / should be shaped differently"), not a passing suite.

The deeper trap: **optimizing the artifact before validating the bet.** A polished FR
for an unvalidated interaction is exactly the mistake the detached prototype made —
turn-loops and beats built before the synopsis card was proven. We caught the
prototype's version of it and then committed our own.

## Heuristic

> **`phase_mismatch`** — Applying enforce-phase machinery (FR, TDD-first, gates, CAP)
> to prototype-phase work. Tells: the artifact is being *detached/quarantined*, the
> user says *"overthinking"*, or a gate is *deliberately left red*. Cure: name the
> phase out loud before choosing the ceremony. The prototype deliverable is a
> **decision** (keep / kill / reshape), not a green pipeline. Match ceremony to phase:
> a `mkdir && mv` does not need a feature request.

## What good would have looked like

Open the session by asking: *what phase are we in?* For prototyping, the right moves
were the small physical ones the user kept steering me toward — make the folder, move
the files, run the loop, look at it, decide. FR-474 should have been three bullet
points in the README, not a judged document. The synopsis card should have been
wired and *looked at* before a single acceptance criterion was written.

## Seed

The Scripture has Research → Plan → Judge → Enforce → Purge → Submit → Distill. Where
does **Prototype** belong, and how is it bounded? It can't be ungoverned forever — a
parts bin that is never emptied becomes a second codebase. What is the explicit
tripwire that promotes a prototype *out* of the cheap phase and *into* enforce: a
"this bet is proven" decision, a date, a demo that earns applause? And conversely:
what gives an agent permission to *stay* cheap — to refuse the FR, skip the tests,
and leave the gate red — without it being a discipline failure?
