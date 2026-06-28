# L5 Goals — what the encoding layer is actually for

**Date:** 2026-06-25
**Companion:** [vision.md](vision.md) (what and why), [architecture.md](architecture.md)
(how the pieces fit), [README.md](../README.md) (current status)
**Status:** Outsider-view reframing — proposes a target change for L5, not yet enforced.

---

## Why this doc exists

Four feature requests (FR-590 → FR-593) have circled L5 — the layer that assigns
`pre_world`/`eff_world` (and belief) to each beat. Three of four vocabulary-flavored
bets returned nothing measurable; the one clean win (the anti-flood rule) had nothing
to do with vocabulary. The `world_recall` gate could not even resolve its own threshold
(0.46 / 0.49 around 0.47). This doc steps back from the implementation and asks the
naive question the score had buried: **what is L5 trying to accomplish, and are we
measuring it against that?**

## The purpose, stated plainly

The whole Plot Modeller rests on one bet: a prose generator can write chapter 14 from
the **projected state at chapter 14**, without re-reading chapters 1–13. That bet only
pays off if the plan can be *simulated* — pressed "play" and watched evolve beat by beat.

- L3 decomposes prose into beats.
- L4 labels each beat with a structural kind.
- **L5 is the first layer that makes the plan *run*.** Each beat declares what it
  *requires* (preconditions) and what it *changes* (effects). L5 turns a labeled
  beat-list into a **state machine**.

Everything upstream of L5 is description; L5 is execution. It is the load-bearing layer
of the entire compression thesis — without it there is no projected state, and without
projected state there is no coherence beyond the context window.

### L5's job, said as a function

> Produce a world-state trajectory in which **every beat's preconditions are satisfied
> by some earlier beat's effects**, such that the **projected state at any point is a
> sufficient, contradiction-free substitute for having read all the prior prose.**

## The target error

We have been measuring L5 against the wrong thing.

`world_recall` scores the encoder's predicates against **one hand-authored ground-truth
encoding** — which the docs themselves admit is self-derived (an upper bound, one
author's convention). But there are *many* internally-consistent ways to encode the same
story's state. Modeling a move as a single `at` update versus a leave/arrive pair are
both valid state machines; a prose generator is served equally well by either. The GT
scores one correct and the other a miss.

Consequences:

1. **Convention divergence masquerades as failure.** Much of the "low recall" is the
   encoder choosing a *different but valid* encoding, not failing to model state. The
   metric punishes valid alternative state machines. The leave/arrive and `pre_world`
   -direction "bugs" are only bugs *if* we are committed to GT's exact convention.
2. **The real objective is never tested.** No L5 plan has been handed to a prose
   generator with the question "does the projected state keep you consistent?" The whole
   investigation optimizes a proxy with no anchor to the function the proxy is meant to
   predict. That is why every result reads as "maybe" and every fix lands in a vocabulary
   cul-de-sac.

This is deeper than the gate-variance problem recorded in the diary
("the gate that could not resolve its own threshold"). That entry concluded *fix the
ruler*. The stronger correction is *change the target*.

## Two objectives — we have been chasing the weaker one

| | **A — Fidelity (current)** | **B — Function (proposed)** |
|---|---|---|
| Goal | Match a reference encoding | Produce *any* internally-consistent state machine whose projected states keep downstream prose coherent |
| Metric | `world_recall` vs hand-authored GT | (1) simulability + (2) downstream coherence |
| Properties | Convention-sensitive, self-derived ceiling, noisy, can't resolve its own threshold | Convention-free, exact where it matters, tied to the actual purpose |

### Objective B, made concrete

1. **Simulability (the property the thesis actually needs).** Run the plan start to
   finish: is **every** beat's precondition produced by some earlier beat's effect, with
   no contradiction (e.g. a dead character acting, possession without acquisition)? This
   is a **deterministic, zero-variance, no-LLM, no-GT** check. It is free, exact, and it
   is exactly what "the projected state replaces the prose" requires.

2. **Downstream coherence (the real acceptance test).** Project the state at some
   chapter, ask a generator to write that chapter, and check whether the prose
   contradicts the plan. This is the test the entire architecture is built to pass and
   it has never been run.

## What this implies for how L5 should be judged

- **Promote simulability to the primary gate.** It is deterministic and tests the
  load-bearing property directly. An encoder whose state machine is internally consistent
  is *correct for our purpose* even if it diverges from the GT author's convention.
- **Add a downstream-coherence probe** as the true acceptance test (one chapter, one
  generator, contradiction check) before declaring L5 "good."
- **Demote `world_recall`-vs-GT to a diagnostic.** It still catches gross under-encoding
  (a beat that emits nothing), but it must stop being the optimization target — it has
  driven four FRs into vocabulary dead ends and produced a gate that cannot decide.

## The reframed question

The leave/arrive emission gap, the `pre_world` direction, the vocabulary canonicalization
— these stop being recall bugs to chase and collapse into one question:

> **Is the encoder's state machine internally consistent and simulable?**

If yes, a different-from-GT encoding is fine. If no, that is a real defect — and it can be
detected deterministically, today, without an LLM, a corpus, or a two-run gate.

## One-line synthesis

L5 is trying to make the plan **runnable** — a state machine whose projected snapshots
replace having read the prose — so it should be judged on whether it **simulates without
contradiction and keeps downstream prose coherent**, not on whether its predicates match
one person's reference encoding.
