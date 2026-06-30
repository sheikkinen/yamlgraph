# Feature Request: Round-trip skeleton re-scope — ground the gate, validate the arc, fix the author

**Priority:** HIGH
**Type:** Enhancement / Course-correction
**Effort:** 2-3 days
**Requested:** 2026-06-30
**Status:** Proposed — supersedes FR-614 (P4) and re-scopes FR-613 (P3)

## Summary

The FR-613 K=6 Raw Output Read (2026-06-30) proved the affect-closure gate, as built,
measures the **author's self-report in an abstract symbol layer decoupled from the prose**, and is
**non-reproducible** across draws. This FR replaces the refuted P4 (FR-614, "widen the reactive
close-op") with the three moves the read actually pointed to:

1. **Re-assign by task type, not blanket model.** `outline_chapter_briefs` and `derive_cast` author
   *structure* (scene_type classification, affect-op planning) — a judgement task mislabelled as a
   "writer." Promote the **structural-authoring** nodes to the strong model
   (`claude-sonnet-4-6`); keep **prose drafting** (the `draft_chapter` map) on haiku. This preserves
   the cost thesis (cheap prose at scale) while removing the capability-driven defects.
2. **Validate the authored arc deterministically** before any rate is reported. Reject:
   - a `close` op for a `(char, kind)` thread never opened (phantom close);
   - an `open` op in the final chapter (cannot close by position);
   - a `scene_type` label that contradicts its ops (e.g. all-`open` internal grief/guilt tagged
     `proactive`).
   An invalid arc fails the gate; it does not silently score 0.0.
3. **Ground the gate in the prose, or remove it.** Add `classify_affect_prose` (the rejected option
   (b), now mandatory): extract affect opens/closes from the generated prose and diff against the
   **authored** arc. The reported coherence number is **prose-vs-plan fidelity**, not plan
   self-report. If grounding is declined, delete the affect gate — an ungrounded number is worse
   than none.

Plus the lateral defect the read surfaced and the gate is blind to:

4. **Enforce character continuity across map branches.** The detective sample flips Marren's gender
   between chapters (he\u2192she) because each map branch is a fresh context with no bound cast identity.
   Pin the cast sheet (name + fixed attributes) into every `draft_chapter` branch and assert
   identity stability. This is a larger coherence hole than affect closure and must not ship hidden.

## Value Statement

Turns the skeleton from an instrument that grades a model's self-description into one that grades the
**artifact** — reproducibly, deterministically where possible, and grounded in the prose where not.
Resolves the "just use a bigger model" critique correctly: model size is a quality knob, not a
substitute for a grounded gate (a stronger author makes the self-report *more plausible*, i.e. a more
convincing tautology — strictly worse for measurement).

## Problem

Under decision (a) the gate walks the authored `eff_affect` arc. The K=6 read (FR-613) found:

- **Non-reproducible:** Loom draw1 = 0.40, draw2 = 0.00 (same premise, same model).
- **No hypothesis support:** reactive dangling 1.0 (salt-road) / 0.0 (detective, loom); proactive
  0.75 (horror) / 0.0 (quest, loom). No reactive\u226bproactive direction.
- **Invalid ops scored as success:** phantom closes (loom draw2 `close hope`, never opened) and
  last-chapter opens (salt-road `relief` ch8, horror `loss` ch4) dangle/close by position.
- **scene_type unreliable:** horror 4/4 proactive over grief/guilt/loss content.
- **Prose defect invisible to the gate:** character gender flip (Marren he\u2192she across chapters).

`authored_dangling_rate` therefore measures haiku's caprice in a symbol layer the prose never has to
honour. A bigger author model does not fix non-reproducibility, continuity binding, or the
self-report tautology.

## Raw Output Read (measurement / metric-tooling FR)

> **Gate precondition (read_raw_output_first):** the grounded `classify_affect_prose` metric must be
> validated against K \u2265 5 (authored-arc, prose) pairs, recording per pair one concrete
> prose-vs-plan divergence the diff must capture, before the metric is trusted.

- **Samples read:** inherits the FR-613 K=6 read (`logs/p3-raw/*.log`).
- **What I saw:** the authored arc and the prose diverge by construction — affect "kinds"
  (`hope`, `betrayal`) are abstract tags that need not surface in the text; the only honest check is a
  semantic prose classifier, not a symbol walk. (Detailed per-sample notes in FR-613.)

## Acceptance Criteria

- [ ] Structural-authoring nodes (`derive_cast`, `outline_chapter_briefs`) run on the strong model;
      `draft_chapter` map stays on haiku. Model is config, not hard-coded.
- [ ] A deterministic arc validator rejects phantom closes, final-chapter opens, and
      scene_type/ops contradictions; an invalid arc fails the gate (does not score 0.0).
- [ ] `classify_affect_prose` reports prose-vs-plan fidelity; the headline coherence number is the
      grounded one, not the self-report.
- [ ] Character identity (name + fixed attributes) is pinned into every map branch and asserted
      stable across chapters; the Marren-style gender flip is caught by a test.
- [ ] Reproducibility check: report variance of the grounded number across \u2265 3 draws of one premise;
      document it (a coherence metric must be stable or its instability must be measured).
- [ ] Raw Output Read filled with K \u2265 5 (arc, prose) divergence pairs before the metric is trusted.

## Alternatives Considered

- **"Use the largest model for everything and ditch the gate."** Correct only for one-pass short
  content. Rejected as a general conclusion: it does not fix non-reproducibility (temp>0) or
  cross-branch continuity, abandons the cost/scale thesis, and makes the self-report tautology *more*
  convincing. Model size is orthogonal to the need for a grounded gate.
- **Keep the self-report gate, just on a bigger author.** Rejected: strictly worse — pays frontier
  price to manufacture a more plausible (harder-to-falsify) tautological number.

## Related

- Supersedes: [FR-614](FR-614-roundtrip-skeleton-p4-scene-type-close-op.md) (refuted).
- Re-scopes: [FR-613](FR-613-roundtrip-skeleton-p3-coherence-gate.md) (gate implemented, read refutes
  it as a coherence signal); pulls forward [FR-615](FR-615-roundtrip-skeleton-p5-roundtrip-closure.md)
  `classify_affect_prose`.
- Reflection: `docs/diary/diary-2026-06-30-grading-the-self-report.md`.
- Evidence: `logs/p3-raw/*.log`, [plan-roundtrip-phased.md](../examples/plot_modeller/docs/plan-roundtrip-phased.md).
