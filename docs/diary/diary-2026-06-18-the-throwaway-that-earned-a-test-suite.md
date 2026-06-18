# The Throwaway That Earned a Test Suite

**Date:** 2026-06-18
**FR:** FR-522 (scripted single-chapter replay witness)
**Arc:** DM v2 continuity hardening — the instrument, not the fix

## What happened

To falsify FR-521's S1 I had hand-built a one-off script: deep-copy the story, wipe
one chapter, re-play it, count the director's Arnulf flags. It did its job — 8/16 →
13/16, S1 dead. The reflex was to delete it. Instead the user asked the right
question: *"fr for scripted replay of a chapter."* The disposable script was a
reusable primitive wearing throwaway clothes.

Promoting it surfaced three things the throwaway had gotten away with because it was
never tested:

1. **The script lied about its own coupling.** Its docstring would have said "drives
   the real `invoke_turn`, no doc-shape coupling" — but wiping a chapter
   (`card["turns"] = []`, popping `world_state`) is *pure* doc-shape surgery. The
   judgement (J1) forced me to name it: one tested `reset_chapter_for_replay`, not
   scattered statements pretending to be coupling-free.
2. **The isolation claim was untestable where it lived.** AC-1 wants "a prior
   chapter is byte-identical after a *mocked-LLM* replay." Impossible if the replay
   loop lives in `__main__`. J2 moved the driver into the API layer so a test can
   monkeypatch the LLM — and only then could I *prove* the deep-copy actually
   isolates, rather than assert it in prose.
3. **The metric measured through its own contaminant.** This is the deep one. In the
   live smoke run the new instrument reported BASELINE `8/16 flagged` but
   `16/16 acting` — the director under-detects by half. The throwaway only counted
   flags; it would have shown "8" and hidden that Arnulf acted every single turn.
   J4's confound-separation (report director-flag *and* intent-map-acting side by
   side) turned a single number into a diagnosis.

## The trap

**`instrument_as_byproduct`.** The thing built to *measure* a fix is treated as
scaffolding — written fast, untested, deleted after. But the measurement device
outlives any single fix: FR-519, FR-521-S1, FR-521-S2, and the next continuity FR
all need the same controlled single-chapter A/B. An untested instrument is worse
than no instrument, because its number carries false authority. The throwaway's "8"
was *true* and *misleading* — exactly the `plausible_wrong_answer` shape, one level
up from the code into the tooling that judges the code.

## The cure

A witness instrument earns the same discipline as production: pure measurement in a
tested module (`witness_metrics.chapter_actor_flag_metrics`), impure driver isolated
and mockable (`chapter_replay.replay_chapter`), one extractor reused for baseline and
replay so they cannot drift, and — the load-bearing amendment — **never measure a
generator's output with a signal you injected into its input** (J4/J6). The
director-flag count alone is corruptible by any change that writes into `scene`
(which `running_scene` feeds to all three turn nodes); the independent acting count
is the control. And it stays an instrument, not a gate (J6): efficacy is
non-deterministic, so wiring it into CI would manufacture the flaky gate the whole
arc was written to avoid.

## Heuristic

When a script exists only to produce a number that decides a design, that script is
infrastructure, not scaffolding — give it the boundary it deserves: a tested pure
metric, a mockable impure driver, and a second independent signal so the number
cannot quietly lie. The cost of testing the witness is repaid the first time it
tells you something the headline metric hid (here: the director sees half the breaks
it should).

**Seed:** The BASELINE line revealed the director under-detects (16/16 acting,
8/16 flagged) — the *detector* is lossy, upstream of every enforcement that consumes
its flags. FR-521-S2 dropped the actor on `cast_exits`, but `cast_exits` rides the
same lossy director. Should the next continuity FR measure and harden the
director's *recall* (does it flag every turn an exited actor acts?) before trusting
any downstream gate that keys off its judgement — i.e. is the cheapest remaining
continuity bug in the detector, not the enforcer?
