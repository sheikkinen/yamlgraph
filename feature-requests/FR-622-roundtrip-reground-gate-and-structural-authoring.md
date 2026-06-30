# Feature Request: Round-trip skeleton re-scope — ground the gate, validate the arc, fix the author

**Priority:** HIGH
**Type:** Enhancement / Course-correction
**Effort:** 2-3 days
**Requested:** 2026-06-30
**Status:** Judged — Authority GRANTED for moves 1/2/4 and move 3a (manual grounding read); move 3b (`classify_affect_prose` node) build authority WITHHELD, conditioned on 3a's labels; supersedes FR-614, re-scopes FR-613 (2026-06-30)

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

## Judgement (2026-06-30)

**Verdict: Authority GRANTED for moves 1, 2, 4, and move 3a (the manual grounding read). Move 3b
(the automated `classify_affect_prose` node) is design-approved but build-WITHHELD, conditioned on
3a's labels.** This is the Scripture working as designed: the FR-613 K=6 raw read refuted a metric,
and this FR is the honest course-correction rather than a tune of the refuted lever. The diagnosis
— the gate measured an author's self-report in a symbol layer the prose never has to honour — is
correct, and the "just use a bigger model" rebuttal in the Value Statement is exactly right: a
stronger author makes the self-report *more plausible*, i.e. a more convincing tautology, which is
strictly worse for measurement.

**Every load-bearing claim verified against source:**
- K=6 read evidence exists (`logs/p3-raw/{detective,salt-road,horror,loom-draw1,quest,scifi-loom}.log`,
  2026-06-30); FR-613 status = FILLED + refuted, FR-614 = REFUTED / DO NOT BUILD — internally consistent.
- Graph nodes confirmed: `derive_cast` (structural), `outline_chapter_briefs` (structural),
  `draft_chapter` (`type: map`, prose) at [roundtrip_skeleton.yaml](../examples/plot_modeller/graphs/roundtrip_skeleton.yaml) L72/79/88.
- **The Marren continuity defect is real and severe.** Pronoun counts within ±60 chars of "Marren"
  in the detective sample: `her 72 / his 64 / he 51 / she 47 / him 20`. Male-only windows are
  unambiguous ("Marren was three blocks away… **He was walking** the perimeter"; "Marren forced
  **himself** toward the open door… the heat drove **him** back"). The same character is both he and
  she across chapters — a ~50/50 split, not a stray typo. AC #4's framing as "a larger coherence hole
  than affect closure" is justified.

**Correction 1 (PRIMARY — move 3 gates the benefit of move 1; make ordering explicit).** Promoting
structural-authoring to the strong model (move 1) must NOT be measured by an improved self-report
number — that is the FR's own warning made real (a frontier author manufactures a more convincing
tautology). Bind the ordering: the grounded number (move 3a's manual read) and the reproducibility
check must land **before** any quality claim is attributed to move 1, and the variance-over-≥3-draws
check (AC #5) must run on the **grounded** number, never the self-report. Otherwise move 1 silently
buys a prettier tautology.

**Correction 2 (PRIMARY — the validator's first proof is the K=6 defects as fixtures).** The
deterministic arc validator (move 2) is the cheapest, strongest part of this FR. Require that its
first RED tests are the *specific* invalid arcs the read already found: loom draw2 phantom `close
hope`, salt-road `relief` ch8 / horror `loss` ch4 last-chapter opens, horror 4/4 proactive over
grief content. The investigation→fix pattern: the K=6 read's findings become the validator's
regression suite. A validator that does not red-flag the exact arcs the read condemned has not
earned trust.

**Correction 3 (PRIMARY — split move 3: read first by hand, automate only if it earns it).** Do NOT
build `classify_affect_prose` as the *first* grounding step — that constructs a suspect automated
classifier before establishing what the prose-vs-plan divergence even looks like, swapping an unread
author self-report for an unread classifier self-report one layer down (the exact failure that
produced this FR). Invert the order:

- **3a — grounding read (GRANTED now; manual, by the strong reasoning agent).** The agent reads K ≥ 5
  `(authored arc, generated prose)` pairs and records, per pair, the concrete divergence **with cited
  prose spans** (e.g. "authored `close hope` ch7; prose never re-raises hope after ch4 — span: …").
  This is not a node; it *is* the Raw Output Read the gate precondition already demands, and it
  produces the **labelled ground-truth fixture set**. It is the cheapest, highest-bandwidth probe
  (`read_raw_output_first`). Trustworthiness comes from the citation + the recording, not the model
  tier — an un-recorded "the agent looked and it seemed grounded" is the same unread-output /
  audit-as-ritual trap one tier up, and is forbidden.
- **3b — automated classifier (build-WITHHELD; conditioned on 3a).** `classify_affect_prose` becomes
  worth building **only if** a cheaper model reproduces 3a's manual labels on held-out pairs.
  Validated → ship it as the production gate. Not validated → the gate stays manual/advisory, or the
  affect gate is deleted. The `investigation_before_fix` pattern: 3a's cited reads are the regression
  suite 3b must pass. "An un-reproducible automated number is worse than none."

**Correction 4 (secondary — grade continuity deterministically, not with another caprice-prone
model).** AC #4's stability assertion should be a deterministic check (pinned cast sheet carries a
fixed `gender`/attribute; assert the prose's pronouns for each named character do not contradict the
sheet), not an LLM judge. The Marren sample is the regression fixture. Pin the cast sheet (name +
fixed attributes) into every map branch so each `draft_chapter` context is bound, then verify
mechanically.

**Correction 5 (secondary — scope honesty on the pull-forward and effort).** This FR pulls
`classify_affect_prose` forward from FR-615; update FR-615's scope so two FRs do not both claim it.
On effort: with move 3 split, 3a (the manual grounding read) is cheap and lands now; 3b (the
automated node) is FR-613-scale and should be its own phase/FR once 3a's labels exist — do not let
the 2-3 day bundle imply the automated classifier ships in this FR. Moves 1, 2, 4, 3a fit the
estimate; 3b does not and is explicitly deferred behind 3a.

**Frozen scope.** Moves 1, 2, 4, and 3a are GRANTED to do now (config + two deterministic gates that
turn the K=6 read into fixtures + the manual cited grounding read that produces the labelled
fixture set). Move 3b (the automated `classify_affect_prose` node) is design-approved but build
authority is conditioned on 3b reproducing 3a's manual labels on held-out pairs; it is its own
phase, not part of this FR's 2-3 day estimate. The headline coherence number must be the grounded
one (manual in 3a, automated only once 3b is validated) or the affect gate is deleted — no third
option.

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

- [x] Structural-authoring nodes (`derive_cast`, `outline_chapter_briefs`) run on the strong model;
      `draft_chapter` map stays on haiku. Model is config, not hard-coded.
- [x] A deterministic arc validator rejects phantom closes, final-chapter opens, and
      scene_type/ops contradictions; an invalid arc fails the gate (does not score 0.0).
- [ ] `classify_affect_prose` reports prose-vs-plan fidelity; the headline coherence number is the
      grounded one, not the self-report.
- [ ] Character identity (name + fixed attributes) is pinned into every map branch and asserted
      stable across chapters; the Marren-style gender flip is caught by a test.
- [ ] Reproducibility check: report variance of the grounded number across \u2265 3 draws of one premise;
      document it (a coherence metric must be stable or its instability must be measured).
- [ ] Raw Output Read filled with K \u2265 5 (arc, prose) divergence pairs before the metric is trusted.

## Enforcement (2026-06-30)

Enforced under the Judgement, scope-gated. Status by move:

- **Move 2 (C2) — DONE.** `validate_authored_arc(briefs)` added to
  `examples/plot_modeller/nodes/roundtrip_tools.py`: a deterministic, no-LLM walk that rejects
  `phantom_close` (close of a never-opened `(char, kind)`), `final_chapter_open` (an open in the last
  chapter, which cannot close by position), and `scene_type_dose` (a `proactive` chapter accumulating
  >= 2 opens with 0 closes — lingering interior where the MRU prescribes feeling spent through
  action). `coherence_gate` now surfaces `arc_valid`, `arc_violations`, and `verdict` (`fail` on any
  violation OR `dangling > 0`); it does NOT raise, so the failing verdict is persisted as an artifact.
  First RED tests are the K=6 defects the FR-613 read condemned (loom draw2 phantom `close hope`;
  salt-road `relief` last-chapter open; horror 4/4 proactive over grief). `tests/unit/test_roundtrip_arc_validator.py`
  (8 tests) + the 9 persist tests are GREEN; ruff clean.
- **Move 1 (C1) — DONE.** `derive_cast` and `outline_chapter_briefs` pinned to `claude-sonnet-4-6`
  via per-node `model:` config (not hard-coded in Python); `draft_chapter` stays on the writer model.
  Skeleton lints clean. Provenance note: `persist_run` still records the env `ANTHROPIC_MODEL`
  (writer) in `manifest.json`; the structural nodes' strong-model use is config-visible but not yet
  reflected in the manifest — tracked for a follow-up provenance pass.
- **Move 4 (C4) — TODO.** Deterministic character-continuity check (pinned cast attributes incl.
  gender vs prose pronouns); Marren detective sample is the regression fixture. Requires extending
  the `derive_cast` schema to emit fixed attributes, then a pronoun-vs-sheet checker.
- **Move 3a — TODO.** Manual cited grounding read of K >= 5 (authored arc, prose) pairs to fill
  `## Raw Output Read`; produces the labelled fixtures.
- **Move 3b — WITHHELD.** `classify_affect_prose` node build authority withheld pending 3a labels.

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
