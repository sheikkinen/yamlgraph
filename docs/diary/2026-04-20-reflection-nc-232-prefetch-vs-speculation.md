# Diary: Prefetch vs Speculation — NC-232 Design Discussion

**Date:** 2026-04-20
**FR:** NC-232 (draft)
**Related:** NC-220 (rolled back, NC-227), NC-226 (checkpoint isolation, unfixed), NC-229 (concurrent ack+LLM)
**Boundary touched:** `streaming` + `state` — a new actor proposed to share mutable state with the primary turn handler.

## The proposal on the table

> "Run the LLM extraction on each interim STT result, accumulate extracted fields, process the decision after the silence fires."

Reframing: "Move the LLM off the critical path by prefetching extraction during user speech."

## The trap the idea is shaped like

This is **NC-220 wearing a new costume**. NC-220 failed with a 4-bug cascade (NC-227 rollback) because the speculative task shared the LangGraph checkpoint with the real task. Each fix addressed a symptom; the root cause — concurrent actors on shared mutable state — was never resolved.

If the user's proposal is treated as "fire LLM on partials, merge results", it would reintroduce the same failure class. The Scripture prescribes the cure: **normalize at the boundary**. The boundary here is not the LLM call; it's the ownership of `extracted` state.

## The distinction I drew

**Speculation (NC-220 shape):** fork → commit/rollback. Speculative task writes the same state the real task writes. Correctness requires consensus; concurrency requires locks or checkpoint isolation. NC-226 documented the isolation problem and never solved it.

**Prefetch (NC-232 shape):** launch → cache → invalidate. Speculative task writes a scratch dict that nobody else reads during the launch window. Real task, on its normal schedule, reads scratch **if** it's valid, else recomputes. Cancellation is free (drop scratch). Worst case is "today's latency plus a wasted LLM call".

Syntactically the two look similar: both fire an LLM on partials. Semantically they are different universes. The trap is **false_duplicate**: syntactic similarity ≠ semantic equivalence.

## What shifted my thinking

Initially I was going to say "too risky, don't do it." Then I noticed the proposal itself was already in the safer shape — the user said *identify the answer fields populated, accumulate*. That's overwrite semantics, not merge semantics. The dangerous version is one the user didn't propose. I was about to argue against a strawman.

The Judge move: before rejecting, translate the proposal into its strongest form. The strongest form is prefetch-with-invalidation, and that form is safe if the boundary is drawn correctly.

## The cheap-first discipline

Before writing any FR involving concurrency, the Scripture says: kill the cheapest bug first. The cheapest bug here is the silence threshold itself — 3.0s is pure wall-clock dead air, zero code change to lower, zero new failure modes. If lowering it from 3.0 → 1.2s delivers 1.5s/turn on its own, a large chunk of the user's complaint is resolved without touching concurrency at all.

Hence the FR is staged: **Phase A is config + prompt split**, both zero-risk and measurable. **Phase B (prefetch) is judged against Phase A's new baseline**. If Phase A is enough, Phase B doesn't get written.

This is the same discipline as FR-219's dependency audit: don't optimize the hot path until you've measured it. The whole point of Phase A's Prometheus histograms is to make Phase B's go/no-go a numerical decision, not an enthusiasm decision.

## What I learned about framing

Every time someone proposes "do X during Y to save latency", the first question should be: **what state does the X-task write, and who else writes the same state?** If the answer is "nobody else writes it", it's prefetch — proceed. If the answer is "the main pipeline also writes it", you're in NC-220 territory — redesign or don't ship.

This is the same pattern as graph checkpoint isolation (FR-255 extract shared invoke_graph), auditor gates (FR-247), and boundary normalization across the Scripture. Every performance optimization that introduces a new writer is a state-ownership question in disguise.

## The four invariants that make prefetch legal

Writing them down because they will matter again:

1. **No shared durable state.** Scratch dict, not checkpoint.
2. **Overwrite, never merge.** Last write wins; final input is authoritative.
3. **Debounce + cancel.** Upper bound on in-flight work.
4. **Validate before use.** Input-equality check at consumption; stale → fallback.

Violate any one and the feature becomes NC-220.

## Trap catalogue hits

- **framework_costume**: would have been if we'd reached for threading or asyncio concurrency primitives. The cure is to use the FSM's existing action-tick loop as the scheduler (debounce via `context["_spec_last_launched"]`). No new concurrency framework, no new lifecycle.
- **symptom_patch**: almost slipped into "just tune the silence threshold" without measuring. Phase A's histograms are the verify-root-cause-before-fix discipline.
- **quick_confidence**: my first instinct was to reject. Judging turned rejection into staging. "When I feel certain → Judge instead."

## Seed

If prefetch-with-invalidation is the shape that makes concurrent LLM work safe, should YAMLGraph expose a first-class **`prefetch` node decorator** that enforces the four invariants by construction — no shared checkpoint, overwrite semantics, debounce parameter, input-equality validation? A graph author could annotate any LLM node as `prefetch: true` and get the safety properties for free, rather than re-implementing them per feature. The alternative is every speed-optimization FR will quietly re-derive NC-227's lessons.

**Companion question:** Can the LangGraph checkpoint itself grow a `fork/scratch` primitive such that sub-graph invocations default to isolated state unless explicitly `shared: true`? That would turn NC-220's 4-bug cascade into a compile-time error.
