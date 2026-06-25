# Feature Request: FR-592 — Pre-Fan-Out Vocabulary Extraction Stage

**Priority:** HIGH
**Type:** Feature
**Status:** REJECTED (2026-06-25) — wrong architecture; superseded by FR-593
**Effort:** 1 day
**Requested:** 2026-06-25
**Predecessor:** FR-591 (perspective-to-L5 graph — provisional encoding contract)
**Siblings:** FR-590 (multi-perspective spike), FR-587 (snapshot-diff)
**Superseded-by:** FR-593 (story-level vocabulary as a pre-analysis stage)

## Rejection (2026-06-25) — enforce failed, architecture wrong

Authority was granted and the wiring built (one `extract_vocab` node before the map,
threaded via the inert `state.vocab` hook). The enforce run **falsified the design** on
the very first gate, and diagnosis showed the failure is architectural, not a bug to
patch — so the FR is rejected and re-planned as **FR-593**, not iterated.

**Empirical NO-GO.** scifi through the production extractor scored **1/23 (0.04)** —
*worse* than no-vocab (0.09) and the pre-transition baseline (0.17), against the
oracle's 0.30. The REVERT rule (corrections #1/#3) triggers.

**Root cause — two layers, both fatal to this shape:**
1. **Schema did not bind on the consumed path → the anchor never applied.**
   `extract_vocab` came back as a markdown **string**, so `state.vocab` was a `str`
   and the encoder template `{{ state.vocab.locations }}` rendered **empty**. The model
   then *ignored* the empty "use ONLY these tokens" block entirely — the `at`-flood was
   **unchanged** (97 FPs vs the no-vocab run's 100, 53% vs 59%), and recall sat at the
   noise floor (0.04 ≈ the no-vocab 0.09). The vocabulary did nothing; the anchor was
   inert. (A controlled vocabulary is also a recall **suppressor** when it *does* bind
   but is imperfect — "omit the fluent if nothing fits" — so the binding fix alone would
   not make this shape safe.)
2. **Wrong shape even with a perfect dict.** Injecting vocabulary as a *late,
   encode-time constraint* ("use only these, else omit") makes it a precision filter
   bolted onto the last step. The oracle's 0.30 came from vocabulary that happened to
   be *correct GT tokens*; an LLM-extracted vocabulary cannot match that and, as a
   filter, every imperfection costs recall. Vocabulary must **inform the whole analysis
   as shared naming established up front** (summarize *and* encode), not gate the tail.

**Carried forward to FR-593:** story-level vocabulary as a genuine first stage *before*
the detailed per-character analysis — canonical naming the rest of the pipeline is
written *in terms of*, never a suppress-if-absent filter. The OQ#1 ceiling finding
(scifi `Vantari Labs`, horror `Surface` are gloss-absent — an upstream summarize/classify
gap) also carries forward.

## Summary

Add a single **`extract_vocab`** LLM node to `perspective_l5.yaml` that runs **once,
before the per-agent map fan-out**, deriving a shared controlled vocabulary
(locations, objects, characters) from the classified beats. The vocabulary is threaded
into every per-agent `encode` step via the **already-wired-but-inert `state.vocab`
hook** in `encode_perspective.yaml`. This makes the FR-591 transition-pair encoding
rule actually land in production instead of flooding the `at` predicate with
drifting tokens.

## Value Statement

The FR-591 transition-pair rule is a real recall lever **only when anchored by a shared
vocabulary** — without it the corpus *regresses*. A single pre-fan-out extraction step
converts that proven-in-spike lever into a proven-in-production one, and gives every
character's encoder the same canonical token set, which is the structural cure for
cross-agent token drift.

## Judgement (2026-06-25)

**Verdict: Authority GRANTED.** This is the strongest-grounded FR in the L5 arc. The
motivating evidence is fully verified against repo memory `l5-encode-recall-bottleneck`,
which records the same 2×2 (transition×vocab), the same mechanism (the transition rule
fires — prod scifi 10 `value:false` departures — but free tokens drift so each
leave/arrive pair becomes an `at` FP), the same corpus regression (0.47→0.40,
at-flood 100/169 = 59%, horror 25 `at` vs 17-fact GT), and the same prescription:
*"the deferred vocab-extraction stage is a PREREQUISITE for the transition recall
lever… build synopsis-derived (NOT oracle) vocab → thread via the existing inert
`state.vocab` hook → expect recall → ~0.30."* FR-592 is exactly that step. The
inert `{% if state.vocab %}` block exists in `encode_perspective.yaml` (under the
PROVISIONAL header), the oracle harness `spike_vocab_encode.py` exists, and the
`rel`-label exclusion is grounded in measured hallucination, not a guess. The design
is minimal and surgical — one pre-fan-out node, one prompt, an edge re-point, and
activating an already-wired hook — and the no-leakage boundary (glosses only; oracle
reserved for evaluation) is correct and AC-enforced.

**The factorial is good science.** Refusing the two OFAT conclusions ("vocab does
nothing," "transition is the lever") in favour of the interaction is the
*check-your-architectures-don't-share-an-unexamined-fusion* discipline applied as a
design. GRANTED on that strength — with corrections that harden the decision against
the one weakness the FR itself names: the 2×2 cells are single draws at temp 0.7.

**Corrections required before enforce (do not widen scope):**

1. **Add the missing STOP/REVERT rule (PRIMARY — the FR has none).** Every prior FR
   in this arc carried an explicit KILL path; this one must too, because it is
   shipping a contract that *already regressed the corpus* (0.47→0.40). Decision
   rule: GO requires, over **two** runs, corpus overall `world_recall` ≥ 0.47 (no
   regression) AND the `at`-FP share falling below 59% AND invented (out-of-vocab)
   `at`/`holds` tokens materially reduced. **If vocab lands and the corpus still nets
   < 0.47 over two runs, revert the FR-591 transition rule to the baseline encoder
   — do not ship a corpus-regressing contract on a partial fix.** One `extract_vocab`
   prompt iteration only (the recurring fourth-iteration-ritual discipline).

2. **Elevate horror from a checkbox to the PRIMARY diagnostic.** Horror is the
   falsification cell: it fell furthest (0.71→0.29, −40.42) on pure at-token drift,
   so if shared vocab recovers horror to ≥ 0.71 the token-drift mechanism is
   *confirmed*; if horror stays depressed despite a clean, obeyed vocabulary, the
   regression has a **second cause** the interaction hypothesis does not cover — and
   the transition rule must not ship even with vocab. Report horror's at-fluent count
   (25 → ?) against its 17-fact GT as the mechanism witness, not just its recall.

3. **Rest GO on the adapter-robust mechanism, not the noisy single-draw cells.** The
   memory's own caveat stands: *at-flood mechanism robust, per-genre deltas noisy.*
   The 0.30 scifi cell is a single temp-0.7 draw; make the scifi ≥ 0.25 target the
   result of **both** of two runs (or their median), and let the GO/NO-GO turn on the
   at-FP-share drop + invented-token reduction (counts) plus two-run corpus
   non-regression — never on a lucky single draw.

4. **Resolve Open Question #1 by spot-check before committing (recall-ceiling risk).**
   Glosses-derived vocab cannot contain a GT location/object token that appears only
   in the synopsis prose and never in a beat gloss — such tokens are an unreachable
   recall ceiling, and an *upstream* (summarize/classify) defect, not one this node
   can fix. Spot-check the worst genres (scifi, horror): if salient GT tokens are
   gloss-absent, record it as the ceiling and note the upstream follow-up; do not
   chase it by re-tuning `extract_vocab`.

5. **Resolve Open Question #3: ride FR-591's `REQ-YG-020`, no new CAP.** This is an
   example-local refinement of the same perspective pipeline; tag any
   `extract_vocab` / threading test `@pytest.mark.req("REQ-YG-020")` and set the
   changelog fragment `req: REQ-YG-020`, consistent with FR-590/591.

**Minor:** keeping `characters` in the vocab (rel 2nd arg) while dropping the
`relationships` *label* line is the correct fine distinction — the measured
hallucination came from the value-label list, not character names — but verify on one
run that supplying `characters` does not itself re-induce `rel` emission; if it does,
fall back to the memory's stricter "at/holds tokens only."

**Frozen scope:** the single `extract_vocab` node + `prompts/extract_vocab.yaml`
(structured `locations`/`objects`/`characters`, no `rel` labels), the
`perspective_l5.yaml` edge/state/input_mapping changes, the `perspective_agent.yaml`
`vocab` state, and dropping the inert `relationships` line from `encode_perspective.yaml`.
Glosses-only extraction (no leakage), one extraction call per story. The encoding
contract remains PROVISIONAL; `pre_world` weakness (OQ#4) and the ensemble direction
stay out of scope. The corrections above are clarifications within this scope.

## Problem

A full-corpus production run (2026-06-25, anthropic/haiku, `temp 0.7`) of the FR-591
encoder — with the transition-pair + anti-flood rules **live but no vocabulary** —
*regressed* the corpus:

| Genre | Baseline | Transition-rule (no vocab) | Δ |
|---|---|---|---|
| detective | 0.50 | 0.67 | +0.17 |
| historical | 0.67 | 0.78 | +0.11 |
| horror | 0.71 | **0.29** | **−0.42** |
| quest | 0.50 | 0.50 | 0 |
| scifi | 0.17 | **0.09** | −0.08 |
| **Overall** | **0.47** | **0.40** | **−0.07** |

This completes a **2×2 factorial** (scifi `world_recall`, single draws @ `temp 0.7`)
whose cells were measured across this session's spikes:

|              | no transition | transition |
|--------------|:-------------:|:----------:|
| **no vocab** | 0.17 (baseline) | **0.09** (this run) |
| **vocab**    | 0.13 (oracle-only) | **0.30** (oracle+transition) |

Read one-factor-at-a-time, both prior conclusions were wrong as **main effects**:
- "Vocabulary does nothing for recall" — true only with the transition rule **off**.
- "The transition rule is the recall lever" — true only with vocabulary **on**; with
  vocabulary **off** it is the *worst* cell (0.09 < 0.17 baseline).

**The real lever is the interaction `transition × vocab`.** Mechanism, confirmed (not
noise): production scifi fired **10 `value: false` departures** (the transition rule
worked) but, with free tokens, each leave/arrive pair drifts and becomes an `at`
false-positive instead of a ground-truth match. Corpus-wide that is the **at-flood:
100/169 FPs (59%)**; horror emitted **25 `at` fluents** against a 17-fact GT. Anti-flood
is **not** the culprit (corpus `alive` misses = 3; horror `alive` fluents = 2).

The vocabulary that anchored the oracle spike was **derived from ground truth** — not
usable in production. We need a vocabulary derived from the **input beats only**.

## Proposed Solution

Insert one node at the head of the outer graph, before the map:

```
START → extract_vocab → per_agent (map over agents) → combine → END
```

### 1. New prompt `prompts/extract_vocab.yaml`

LLM reads the classified beats (`glosses`) and returns a controlled vocabulary as
structured output. **Relationship labels are deliberately excluded** — supplying a
`rel`-value list induced relationship hallucination (repo memory
`l5-encode-recall-bottleneck`); vocabulary covers only the *argument* slots that drift.

```yaml
schema:
  name: StoryVocab
  fields:
    locations: {type: list[str], description: "Canonical place names (2nd arg of `at`)"}
    objects:   {type: list[str], description: "Canonical object names (2nd arg of `holds`)"}
    characters:{type: list[str], description: "Canonical character names (2nd arg of `rel`)"}
```

### 2. `perspective_l5.yaml` changes

- Add `vocab` to `state` (type `dict`).
- Add the `extract_vocab` LLM node (`state_key: vocab`), reading `glosses`.
- Re-point edges: `START → extract_vocab → per_agent`.
- Thread the vocab into the subgraph in the map node's `input_mapping`:
  `vocab: vocab` (alongside the existing `agent` and `glosses`).

### 3. `perspective_agent.yaml` changes

- Add `vocab` (type `dict`) to the subgraph `state` so the injected value is visible to
  the `encode` node's template.

### 4. `encode_perspective.yaml` change

- **Drop the `rel`-label line** from the existing `{% if state.vocab %}` block (keep
  only `locations` and `objects`, plus `characters` for the `rel` *second* arg).
- The block stops being inert because the graph now supplies `state.vocab`.

## Acceptance Criteria

- [ ] `extract_vocab` derives the vocabulary from `glosses` **only** — no ground-truth
      file is read at conversion time (no leakage; the oracle is for evaluation only).
- [ ] Vocabulary is threaded to every agent's `encode` via `state.vocab`
      (`yamlgraph graph lint` clean; one extraction call per story, not per agent).
- [ ] scifi `world_recall` recovers to **≥ 0.25** (toward the oracle's 0.30), measured
      over **two** runs to bound `temp 0.7` noise.
- [ ] Corpus overall `world_recall` **≥ 0.47** (no regression vs the pre-transition
      baseline); target **> 0.50**.
- [ ] `at`-predicate share of FPs drops below the 59% at-flood; invented `at`/`holds`
      tokens (not present in the extracted vocabulary) materially reduced.
- [ ] horror does not regress below its 0.71 baseline.
- [ ] Tests added and `@pytest.mark.req`-tagged; `examples/plot_modeller` demo log
      refreshed if a demo path is touched.

## Alternatives Considered

1. **Per-agent vocabulary** (extract after `summarize`, before `encode`): richer per
   character but reintroduces the very cross-agent drift it is meant to cure (each
   agent invents its own token set). Rejected — the cure *is* a single shared set.
2. **Keep shipping transition without vocabulary**: refuted by the corpus regression
   (0.47 → 0.40). Rejected.
3. **Formalize the FR-591 contract as-is** (the original "measure then formalize"
   plan): falsified by the 2×2 — the contract is not settled; the prompt's PROVISIONAL
   header stands until this FR lands.
4. **Vocabulary from the synopsis text rather than the classified beats**: viable, but
   `glosses` is the already-in-state, structured, beat-aligned input at START; prefer
   it. (Open Question #1.)

## Open Questions

1. Source of truth for extraction — `glosses` (chosen) vs raw synopsis prose. Do any
   GT location tokens appear *only* in the synopsis and never in a gloss?
2. Should `extract_vocab` also emit a short alias map (e.g. "the lab" → `Vantari Labs`)
   to help the encoder *map* loose mentions, beyond just listing canonical tokens?
3. Does this need a `CAP-/REQ-YG` registration, or does it ride FR-591's requirement
   IDs as an example-local refinement?
4. Residual after this lands: `pre_world` is the weak slice (0.15) and points upstream
   to `summarize` not stating origins — a separate follow-up, not in scope here.

## Related

- `feature-requests/FR-591-perspective-to-l5-conversion-graph.md` (provisional encoder)
- `examples/plot_modeller/graphs/perspective_l5.yaml`,
  `examples/plot_modeller/graphs/perspective_agent.yaml`,
  `examples/plot_modeller/prompts/encode_perspective.yaml`
- `docs/diary/diary-2026-06-25-the-perfect-vocabulary-that-bought-nothing.md`
- `docs/diary/diary-2026-06-25-the-half-of-every-change-the-model-forgot-to-say.md`
- repo memory `l5-encode-recall-bottleneck` (the 2×2 factorial + mechanism)
- `examples/plot_modeller/spike_vocab_encode.py` (oracle-vocab harness — evaluation
  reference for the production extractor)
