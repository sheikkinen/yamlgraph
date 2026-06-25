# Feature Request: FR-593 — Story-Level Vocabulary as a Pre-Analysis Stage

**Priority:** HIGH
**Type:** Feature
**Status:** Kept (2026-06-25) — two-run corpus gate marginal (mean world_recall 0.475 ≥ 0.47); author accepted as non-regression keep. See "Corpus Gate Result" below.
**Effort:** 1–2 days
**Requested:** 2026-06-25
**Predecessor:** FR-592 (REJECTED — late encode-time vocab filter)
**Builds-on:** FR-591 (perspective-to-L5 graph — provisional encoding contract)

## Summary

Establish a **story-level vocabulary** at the **gloss-extraction stage** (Mode 4,
`extract-glosses`) — the earliest point that still holds the **synopsis** in state and
the last point before the synopsis is discarded. One pass derives the canonical names
of **places and objects** plus an alias map ("the lab" → `Vantari Labs`); the beat
**glosses are emitted already canonicalized**, so every downstream mode — Mode 8
per-character `summarize` *and* `encode` — inherits one consistent naming layer for
free. Vocabulary **informs the analysis as shared naming**, never gates the tail with
a suppress-if-absent filter — the architecture that sank FR-592.

**Scope note (code-verified):** *characters* are not part of this vocab — at Mode 8
the agent list is already supplied from ground truth (`_load_gt_agents`), so the
novel, non-oracle vocabulary is **locations + objects only**. Replacing the GT-agent
injection with a derived cast is explicitly out of scope here (see Boundary Findings).

## Value Statement

Cross-agent naming drift is the measured cause of the `at`-flood (FR-592 problem
analysis: 100/169 corpus FPs, 59%, are `at`). Fixing naming **once, at the story
level**, before five characters independently re-name the same places, removes the
drift at its source instead of policing it five times at the encoder. The same canon
becomes the natural home for the eventual upstream fix to the gloss-absent ceiling
(`Vantari Labs`, `Surface`).

## Judgement (2026-06-25)

**Verdict: Authority GRANTED.** This is a doctrinally-correct re-architecture, and
its load-bearing claims are code-verified. The reframe — vocabulary as **shared
naming applied at the head**, never a suppress-if-absent filter at the tail — is
literally `the_one_law`: *normalize at the boundary where external data enters, not
downstream where it manifests.* FR-592 policed names five times at the encoder (the
manifestation) and failed twice over (inert markdown-string binding → scifi 0.04, and
tail-filter recall-fragility); FR-593 fixes the name once at the gloss-extraction
boundary where the synopsis still lives. I independently confirmed the three Boundary
Findings: the perspective graph's state carries no synopsis (`run.py` invokes
`{glosses, agents}`); `extract_glosses.yaml` (Mode 4) does hold `synopsis`; and the
encoder reads **both** `state.glosses` *and* `state.viewpoint` (lines 98/103) — so
elevating "drive `summarize` from canonical glosses" from optional to **required** is
correct, not optional polish. FR-592's REJECTED status and its two failure modes are
recorded as cited. The FR learns the right lessons: a validated structured object
+ wiring test (kills the string regression), no encoder filter (kills the recall
fragility), and honest value (precision primarily; the oracle 0.30 was a GT-token
ceiling, not a glosses-reachable target).

**Corrections required before enforce (do not widen scope):**

1. **Contain the blast radius — do NOT rewrite the shared `glosses` output in place
   (PRIMARY).** FR-592 was perspective-local; FR-593 modifies **Mode 4**, the
   gloss-extraction stage whose output every downstream layer consumes (L4 classify,
   L6 causality — the GO layer at recall 0.96 — L7 affects, L8). "Every downstream
   mode inherits the canon for free" is framed as pure benefit, but it is also a
   cross-layer regression surface, and the ACs measure **only** L5 perspective
   recall. Open Question #3's "in-place gloss rewrite" is the dangerous option:
   mutating the shared tokens could perturb a layer that was GO, unmeasured.
   **Resolution: emit canonical glosses on a path only Mode 8 consumes (a separate
   field/artifact, original glosses intact), OR prove non-regression on every
   gloss-consuming layer (at minimum L6 causality) before shipping.** Prefer
   containment — it keeps the change inside the boundary the ACs actually witness.

2. **Resolve Open Question #1 toward deterministic-first.** Canonicalization must
   start as **deterministic alias substitution** (a pure, testable Python tool, no
   new variance) — an LLM normalize pass adds another generative call that can
   re-seed the very drift this FR removes. Escalate to an LLM normalize pass *only*
   on a measured alias-coverage gap on the worst genres (scifi/horror), and if so it
   is the **one permitted iteration**, not an open tuning loop. Same for Open
   Question #4 (verify viewpoint-uses-canonical-tokens): deterministic token-presence
   check, not an LLM judge.

3. **Sharpen the recall-ceiling honesty: canon recovers gloss-absent *forms*, not
   gloss-absent *events*.** Reading the synopsis lets the canon contain
   `Vantari Labs`, but `canonicalize_glosses` can only insert it where a gloss has a
   mappable loose mention ("the lab" → `Vantari Labs`). A GT-scored location that no
   gloss mentions at all remains unreachable — an upstream (extract/classify) defect,
   not one this stage can cure. State this bound so a recall miss there is recorded
   as the ceiling, not chased by re-tuning the vocab.

4. **Point the FR-592 string-regression guard at the *new* consumption path.** The
   wiring test must assert the structured-object binding where the vocab is now
   consumed — `canonicalize_glosses` (and `extract_vocab`'s output) at Mode 4 — not
   `state.vocab` at the encoder, which OQ#2 removes. If the encoder's controlled-vocab
   block is gone, the test target moves with it.

**Minor:** Boundary Finding #2 (`_load_gt_agents` supplies the cast at Mode 8, so
*characters* are out of vocab and the novel contribution is locations+objects) is
consistent with the established GT-isolation method but is the one finding I did not
read directly — confirm it during enforce. REQ-YG-020 reuse + the `req:` fragment are
correctly pinned.

**Frozen scope:** the Mode-4 extension (`extract_vocab` over synopsis+glosses →
`{locations, objects, aliases}`, validated object; `canonicalize_glosses`,
deterministic-first) emitting canonical glosses on a **contained** path; driving
`summarize` from canonical glosses (Boundary Finding #3); removing the encoder's
suppress-if-absent vocab block. No GT read for vocab, one extraction per story, one
prompt iteration. Value is **precision without recall regression** — the PRIMARY/REVERT
AC stands: corpus < 0.47 over two runs → revert to the FR-591 baseline. The GT-agent
derivation (OQ#5) and `pre_world` weakness stay out of scope.

## Problem

FR-592 injected an LLM-extracted vocabulary as a **late encode-time constraint**
("use ONLY these tokens, omit the fluent if nothing fits") threaded into the inert
`state.vocab` hook. Enforce falsified it: scifi scored **1/23 (0.04)** — worse than
no-vocab (0.09) and baseline (0.17). Two failures, both architectural:

1. The vocab never reliably became a usable dict on the consumed path (it arrived as a
   markdown string), so the anchor was **inert** — the `at`-flood was unchanged (97 vs
   100 FPs) and recall sat at the noise floor.
2. Even with a perfect dict, a *tail filter* makes every imperfection in an
   LLM-extracted vocabulary cost recall (omit-if-absent). The oracle's 0.30 ceiling
   used **GT-exact tokens** no glosses-derived extractor can reproduce.

The correct shape — the user's reframe — is **vocabulary as a pre-analysis naming
stage**: derive the canon first, rewrite the beats into it, and let the existing
"use names exactly as they appear in the beats" rule carry consistent tokens through
the whole pipeline with **no filter** at the encoder.

## Boundary Findings (code-verified 2026-06-25)

Three facts read from the running code reshape where this stage must live:

1. **The synopsis is not in the perspective graph's state.** `run_perspective`
   invokes `{"glosses": glosses, "agents": agents}` — no synopsis
   (`examples/plot_modeller/run.py`). The synopsis exists only upstream at the
   gloss-extraction stage (Mode 4) and is then discarded. A vocab node placed *inside*
   `perspective_l5.yaml` could read **only glosses** — it could never recover the
   gloss-absent tokens (`Vantari Labs`, `Surface`) that motivate this FR. **The L5
   eval harness loads GT glosses (`load_glosses_with_kinds`), bypassing Mode 4
   entirely — so the contained, actually-measured place to canonicalize is the Mode-8
   harness path, additively (new `canonical_gloss` field, original `gloss` intact),
   with the synopsis loaded alongside.**

2. **Agents are oracle-supplied at Mode 8.** `_load_gt_agents(gt_path)` reads the cast
   from ground truth. So "identifying the agents" is not a pipeline step at conversion
   time, and the *characters* slice of any vocab is already free. The genuinely new
   contribution is **locations + objects**.

3. **The encoder reads the viewpoint PROSE, not just the glosses.**
   `encode_perspective.yaml` consumes both `state.glosses` (name tokens) **and**
   `state.viewpoint` — the `summarize` retelling, a free LLM prose pass that can
   re-introduce loose names and is the larger text the encoder attends to. Canonical
   glosses fix only the name-token channel; **`summarize` must also be driven from the
   canonical glosses** or the prose channel re-seeds the at-flood. This makes the
   former "optional" §3 **required**.

## Proposed Solution

The L5 evaluation harness loads **ground-truth glosses** (`load_glosses_with_kinds`)
for isolation, so the contained, actually-measured place to apply canonicalization is
the **Mode-8 harness path** — over the glosses Mode 8 itself consumes, using the
synopsis loaded alongside. Canonicalization is **additive**: it writes a new
`canonical_gloss` field and **leaves the original `gloss` untouched**, so no other
gloss-consuming layer (L4/L6/L7/L8) is perturbed (Judge correction #1, containment).

```
Mode 8 harness (has synopsis + GT glosses):
  synopsis + glosses
      → extract_vocab (LLM, structured)  → StoryVocab{locations, objects, aliases}
      → canonicalize_glosses (deterministic) → glosses + canonical_gloss   (gloss intact)
      → per_agent(summarize→encode reads canonical_gloss) → combine → l5
```

### 1. `extract_vocab` — structured, *verified* binding, over synopsis + glosses

LLM over the **synopsis + glosses** → `StoryVocab { locations, objects, aliases }`
(no `characters` — agents are GT-supplied at Mode 8). `aliases` maps loose mentions to
canonical tokens. **The schema must bind as a real object** — the wiring test asserts
the binding at the **new consumption path** (`extract_vocab` output / the
`canonicalize_glosses` input), not at the removed encoder `state.vocab` hook (Judge
correction #4). Reading the synopsis here lets the canon include gloss-absent *forms*
like `Vantari Labs`.

### 2. `canonicalize_glosses` — deterministic, additive (Judge corrections #1, #2)

A **pure Python tool** (no LLM, no new variance) that, for each gloss, substitutes
loose mentions with canonical tokens via the alias map (case-insensitive, longest-alias
first, word-boundary aware) and writes the result to a **new `canonical_gloss`** field,
leaving `gloss` intact. Deterministic-first is mandatory; an LLM normalize pass is
permitted **only** on a measured alias-coverage gap on the worst genres (scifi/horror)
and is the **one permitted iteration**, not an open tuning loop.

### 3. Drive `summarize` from `canonical_gloss` (REQUIRED, not optional)

The encoder reads `state.viewpoint` (the `summarize` prose) **as well as** the
glosses. If `summarize` retells from loose names, the prose channel re-seeds the
at-flood regardless of canonical glosses. `summarize`/`encode` read `canonical_gloss`
when present (falling back to `gloss`); a **deterministic token-presence check** (not
an LLM judge — Judge correction #2) confirms the `viewpoint` prose carries canonical
names. The encoder keeps its "use names exactly as in the beats" rule and needs **no
controlled-vocabulary block** — that block stays removed (no omit-if-absent).

## Acceptance Criteria

- [ ] Vocabulary (`locations`, `objects`, `aliases`) is derived once at the Mode-8
      harness from **synopsis + glosses** — no ground-truth read for vocab.
- [ ] **Containment (PRIMARY):** canonicalization is **additive** — it writes
      `canonical_gloss` and leaves the original `gloss` byte-identical; a test asserts
      the original gloss is untouched so no other gloss-consuming layer (L4/L6/L7/L8)
      is perturbed.
- [ ] `extract_vocab` output is a **validated structured object** (`StoryVocab` with
      list/dict fields); a unit test asserts the binding at the **new consumption
      path** and **fails on a bare string** (FR-592 regression guard).
- [ ] `canonicalize_glosses` is **deterministic** (pure Python alias substitution); a
      unit test pins case-insensitive, longest-alias-first, word-boundary substitution
      and idempotence when no alias matches.
- [ ] **Summarize uses canonical tokens (REQUIRED):** a **deterministic** token-presence
      check confirms the `viewpoint` prose carries canonical names — the encoder's
      prose channel must not re-seed drift (Boundary Finding #3).
- [ ] **Precision proxy:** the count of **distinct `at` tokens per location** drops
      toward 1 (divergence removed at source), and corpus `at`-FP share drops below
      FR-592's 59% — both measured over **two** runs to bound `temp 0.7` noise.
- [ ] **Recall non-regression (PRIMARY/REVERT):** corpus overall `world_recall` ≥ 0.47
      over two runs. If canonicalization nets < 0.47 or fails to reduce the `at`-flood,
      **revert to the FR-591 baseline** — do not ship. One prompt iteration only.
- [ ] **Recall-ceiling honesty:** canon recovers gloss-absent *forms* (`Vantari Labs`),
      not gloss-absent *events* — a GT location no gloss mentions stays unreachable
      (upstream defect). A miss there is **recorded as the ceiling**, not chased by
      re-tuning vocab.
- [ ] horror does not regress below its 0.71 baseline (the FR-592 falsification cell).
- [ ] Tests `@pytest.mark.req("REQ-YG-020")`; changelog fragment `req: REQ-YG-020`.

## Value Honesty (carried from the 2×2)

The attainable benefit is primarily **precision** — killing the at-flood by removing
cross-agent naming drift. A recall lift is *possible* where the tolerant scorer matches
a consistent canonical token, but the oracle's 0.30 was a **GT-token ceiling**, not a
glosses-reachable target. This FR ships if it improves precision **without** regressing
recall; it does not promise the oracle number.

## Alternatives Considered

1. **FR-592 late encode-time filter** — rejected (empirical NO-GO + recall-fragile by
   design).
2. **LLM canonicalize vs deterministic substitution** — Open Question #1; prefer
   deterministic if alias coverage suffices (no new variance, fully testable).
3. **Do nothing / keep per-agent naming** — leaves the at-flood (59% of FPs) in place.

## Open Questions (resolved by Judgement 2026-06-25)

1. **Canonicalization — RESOLVED: deterministic-first.** Pure Python alias substitution;
   LLM normalize only on a measured coverage gap (scifi/horror), one permitted iteration.
2. **Encoder controlled-vocab block — RESOLVED: removed** (no inert no-op left behind).
3. **Shared-gloss mutation — RESOLVED: contained.** Additive `canonical_gloss` field;
   original `gloss` byte-identical; no in-place rewrite of the shared token.
4. **Viewpoint-uses-canonical check — RESOLVED: deterministic** token-presence, not an
   LLM judge.
5. **Out of scope:** replacing the GT-agent injection (`_load_gt_agents`) with a derived
   cast, unifying agent-identification and vocab into one entity-resolution stage
   (the diary Seed).

## Implementation Status (2026-06-25)

**Deterministic witness core: DONE (RED→GREEN).**

- `examples/plot_modeller/schema/vocab.py` — `StoryVocab {locations, objects, aliases}`
  (`extra="forbid"`, list/dict defaults). Rejects a bare string → FR-592 markdown-string
  regression guard at the new consumption path (Judge correction #4).
- `examples/plot_modeller/nodes/tools.py` — `canonicalize_glosses(glosses, vocab)`: pure,
  deterministic, **additive** (writes `canonical_gloss`, leaves `gloss` byte-identical;
  case-insensitive, longest-alias-first, word-boundary aware; accepts `StoryVocab` or
  dict). Containment proof = original-gloss-untouched assertion (Judge correction #1).
- `tests/unit/test_perspective_vocab_canonicalize.py` — 8 tests, all `REQ-YG-020`:
  structured binding, empty defaults, bare-string rejection, additive+containment,
  case/longest-first, word-boundary, idempotence, `StoryVocab` acceptance. RED confirmed
  (collection error pre-impl) → GREEN 8/8. `ruff` clean; `req_coverage --strict` exit 0;
  related plot_modeller suites (combine_perspectives, diff_snapshots) still green (28/28).

**Deviation from the FR diagram (recorded):** the L5 eval harness loads **GT glosses**
(`load_glosses_with_kinds`), bypassing Mode 4. The change therefore lives on the
**Mode-8 harness path** as an additive field, not as a Mode-4 prologue — which *is* the
maximal containment the PRIMARY correction demanded. See
`docs/diary/diary-2026-06-25-the-stage-the-gate-would-never-have-run.md`.

**Pending (acceptance gate, requires live LLM + two runs):**

1. Wire the harness: load synopsis in `_main_perspective`, call `extract_vocab`
   (LLM→`StoryVocab`) then `canonicalize_glosses`, invoke perspective with canonicalized
   glosses; `summarize`/`encode` read `canonical_gloss` (fallback `gloss`).
2. `extract_vocab.yaml` prompt with inline schema bound via the LLM node path (must pass
   `output_model`/node binding — not a raw `execute_prompt` string).
3. Deterministic viewpoint-uses-canonical token-presence check.
4. Corpus PRIMARY/REVERT gate: `world_recall` ≥ 0.47 over two runs; distinct-`at`-tokens
   per location → 1; horror ≥ 0.71. **Risk surfaced (diary Seed):** GT glosses are
   already clean, so canonicalization may be a near no-op under isolation — consider a
   drift-injection eval mode so the gate measures repair, not a no-op.

## Live Wiring + Smoke (2026-06-25, addendum)

**Acceptance path wired (items 1–2 above DONE).**

- `examples/plot_modeller/graphs/perspective_l5.yaml` — added state (`synopsis`,
  `vocab_raw`, `vocab`, `vocab_validation`), tools (`validate_vocab`,
  `canonicalize_glosses_node`), nodes (`extract_vocab` LLM → `validate_vocab` →
  `canonicalize`), rewired `START → extract_vocab → validate_vocab → canonicalize →
  per_agent → combine → END`. **No retry loop** — `validate_vocab` degrades gracefully
  (J1: `ok:False` → empty vocab → `canonicalize` is a safe no-op).
- `examples/plot_modeller/prompts/extract_vocab.yaml` — emits YAML `{locations, objects,
  aliases}` over `state.synopsis` + `state.glosses`; excludes characters (GT-supplied).
- `summarize_perspective.yaml` / `encode_perspective.yaml` — gloss loops now render
  `{{ g.canonical_gloss or g.gloss }}`; the FR-592 `{% if state.vocab %}` CONTROLLED
  VOCABULARY suppress block was **removed** from `encode` (Judge correction #2).
- `run.py` — `run_perspective` loads the synopsis and threads it into
  `app.invoke({glosses, agents, synopsis})`.

**Verification:** `graph lint` clean on both graphs; `ruff` clean; vocab+canonicalize
suites 20/20 green. Full scifi Mode-8 pipeline ran end-to-end (no crash): vocab stage →
5 perspectives → 13 L5 beats → eval.

**The no-op Seed risk is FALSIFIED (for scifi).** A direct `extract_vocab` +
`canonicalize` probe (`logs/fr593-vocab-probe.log`) changed **9/13 glosses**: GT glosses
do carry loose mentions (`the lab`, `the building`, `home`, `the shutdown key`) that
normalize to canonical tokens (`Vantari Labs`, `Vantari root server facility`,
`Mara's apartment`, `Firmware Drive`). Canonicalization is *active*, not a no-op.

**New risk surfaced — alias over-mapping (false-positive aliases).** The LLM proposed
semantically loose aliases that the deterministic substituter applied verbatim:
- `the nightstand` → `Mara's apartment` (furniture coerced to a location)
- `the maze` → `Vantari Labs` (a test apparatus *inside* the lab, not the lab)
- `the shutdown key` → `Firmware Drive` (defensible, but a referential leap)

These can *depress* recall where GT expects the literal token, and plausibly explain the
scifi smoke cell (`world_recall 3/23 = 0.13`; corpus 0.41 includes stale non-scifi L5 from
prior FR-591 runs and is **not** a valid gate reading). The deterministic substituter is
faithful — the risk lives at the LLM aliasing boundary. Candidate mitigations for the gate
decision: constrain aliases to whole-noun-phrase place/object mentions, drop single-common-
noun aliases (`nightstand`, `maze`), or require the alias key to already co-occur with the
canonical token in the synopsis.

**Still pending (PRIMARY/REVERT decision — not yet run):** the two-run corpus gate
(`world_recall` ≥ 0.47, horror ≥ 0.71, distinct-`at`-tokens/location → 1, at-FP share <
59%). This is the explicit kill/keep measurement and should be authorized as its own step;
the alias over-mapping risk above is the first thing the gate run must be read against.

## Corpus Gate Result (2026-06-25) — INCONCLUSIVE, leaning KILL

Two full-corpus runs (`logs/fr593-gate-run1.log`, `logs/fr593-gate-run2.log`),
`claude-haiku-4-5`, all five genres:

| Cell | Run 1 | Run 2 | Gate |
|------|-------|-------|------|
| Overall `world_recall` | 39/85 = **0.46** | 42/85 = **0.49** | ≥ 0.47 |
| horror (falsification) | 8/17 = **0.47** | 12/17 = **0.71** | ≥ 0.71 |
| scifi (target worst cell) | 4/23 = 0.17 | 5/23 = 0.22 | — |
| detective | 0.67 | 0.58 | — |
| historical | 0.78 | 0.78 | — |
| quest | 0.50 | 0.46 | — |
| Predicate precision | 39/278 = 0.14 | 42/266 = 0.16 | → improve |
| Evaluator verdict | **KILL** | **KILL** | — |

**The two runs straddle every threshold.** Run 1 fails *both* primary criteria
(0.46 recall, 0.47 horror); run 2 passes *both* (0.49, 0.71). The mean recall (0.475)
clears 0.47 by 0.005 — inside the noise band. Horror swings ±0.24 between runs, far wider
than the margin the gate is trying to resolve, so n=2 cannot separate signal from the
FR-591 baseline. The evaluator's own verdict is **KILL on both runs**.

**Mechanism read (why canonicalization bought nothing measurable):** scifi held at
0.17–0.22 *despite* the probe confirming 9/13 of its glosses were canonicalized. Recall
only improves when a canonical token tolerant-matches the GT token; the over-mapping
false-positives (`the nightstand → Mara's apartment`, `the maze → Vantari Labs`) replace a
GT-matching literal with a non-matching canonical, cancelling gains. Precision never moved
(0.14 → 0.16), consistent with no net change in `at`-token discipline.

**Decision (author, 2026-06-25): KEEP as-is.** The mean two-run `world_recall` (0.475)
clears the PRIMARY gate (≥ 0.47), so the REVERT trigger does not fire on the criterion as
specified. The author accepts the marginal result and the agent's REVERT recommendation is
overridden. The change is retained at commit `fe413479`.

**Known limitations carried forward (do not re-litigate without new evidence):**
- The lift over the FR-591 baseline is within run-to-run noise; this is a *non-regression*
  keep, not a demonstrated win. Treat any future "vocabulary helps recall" claim as
  unproven until a lower-variance gate (more runs, or a drift-injection eval mode) shows
  separation.
- Alias over-mapping (`nightstand → apartment`, `maze → Labs`) remains live. If a later FR
  revisits recall, constraining `extract_vocab` aliases (drop single-common-noun keys;
  require the alias key to co-occur with its canonical token in the synopsis) is the first
  cheap lever to try.
- The deterministic `canonicalize_glosses` + `StoryVocab` witness core is fully tested
  (20/20) and stays regardless of recall outcome — it is the audited, reusable boundary
  primitive.

- `feature-requests/FR-592-perspective-vocab-extraction-stage.md` (REJECTED predecessor)
- `feature-requests/FR-591-perspective-to-l5-conversion-graph.md`
- `examples/plot_modeller/graphs/perspective_l5.yaml`,
  `examples/plot_modeller/graphs/perspective_agent.yaml`,
  `examples/plot_modeller/prompts/encode_perspective.yaml`
- repo memory `l5-encode-recall-bottleneck` (the 2×2 factorial, at-flood mechanism,
  gloss-absent ceiling)
