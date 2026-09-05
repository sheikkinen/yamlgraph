# Judgement: FR-985 person-profile census coverage floor and population header

**Verdict:** APPROVED WITH REVISIONS — the reducer-boundary gate and deterministic brief header are a sound, single demo-local integrity correction; authority activates only after R-1 through R-4 are folded into the FR.

**Prior art:** [FR-985-census-coverage-floor-and-population-header.md](FR-985-census-coverage-floor-and-population-header.md) — the subject; its `**Prior art:**` line dispositions FR-983, FR-962, FR-943, FR-895, FR-967 and FR-984. [FR-983-map-concurrency-and-census-coverage-gate.judgement.md](FR-983-map-concurrency-and-census-coverage-gate.judgement.md) — the parent SPLIT whose Successor B scope this FR inherits. [FR-984-map-fan-out-max-concurrency.judgement.md](FR-984-map-fan-out-max-concurrency.judgement.md) — the sibling, judged the same day; its R-4 and this R-4 are the same decoupling applied from both sides.

**Reviewed against:** `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/skills/graph-authoring/doctrine.md`; `.github/copilot-instructions.md`; `feature-requests/FR-985-census-coverage-floor-and-population-header.md`; `feature-requests/research-briefs/fr983-map-concurrency-coverage-gate-brief.md`; `feature-requests/FR-983-map-concurrency-and-census-coverage-gate.md`; `feature-requests/FR-983-map-concurrency-and-census-coverage-gate.judgement.md`; `feature-requests/FR-962-person-profile-census-authored-prs.md`; `feature-requests/FR-943-census-row-failure-containment.md`; `feature-requests/FR-895-census-synthesize-tail.md`; `feature-requests/FR-967-unwitnessed-acceptance-criteria.md`; committed `HEAD` version of `feature-requests/FR-984-map-fan-out-max-concurrency.md`; `examples/demos/person_profile_census/tools.py`; `examples/demos/person_profile_census/graph.yaml`. The operator-local corp log and generated brief named at FR-985 lines 62-71 and 190 were not consumed; the committed research brief is the evidence record.

## What is sound

The problem is real and the proposed boundary is the smallest effective correction. FR-985 lines 45-58 identifies the exact integrity failure: the reducer computes coverage, the synthesis path discards failed rows, and the human-facing artifact omits the denominator. The committed research brief records the 259 discovered / 147 judged / 100 failed incident and traces the composition from map containment to a plausible but incomplete brief. This is substantive evidence rather than a shape-only research record.

The gate is placed correctly. `_mechanical_rollup` already owns full-population arithmetic (`examples/demos/person_profile_census/tools.py:302-347`), `_canary_gate` currently runs immediately before the first output path is constructed (`tools.py:458-460`), and the graph orders reduction before prepare, synthesis, and rendering (`examples/demos/person_profile_census/graph.yaml:125-168`). Parsing `min_coverage` once at that reducer boundary and raising before `Path(output_path)` satisfies the repository's normalize-at-entry and fail-loudly rules without changing FR-943's row-containment policy.

The value contract is unusually precise. FR-985 lines 94-107 freezes the default, accepted input classes, inclusive range, non-finite rejection, and diagnostic fields. AC-B01 through AC-B04 (lines 124-138) are directly testable without an LLM and include both reducer-level and compiled-path witnesses. The deterministic header also follows FR-962's division of responsibility: population arithmetic remains code-owned rather than being invented by the synthesis model.

Architecture alignment and strategic classification are correct. This is a **Contrib/example** correction for one census, not a framework primitive: it changes the demo's state, reducer, renderer, documentation, and witnesses while leaving the synthesis prompt and YAMLGraph core untouched. The parent SPLIT judgement expressly assigned these surfaces to Successor B (`feature-requests/FR-983-map-concurrency-and-census-coverage-gate.judgement.md:39-45,63-65,84-99`). The alternatives at FR-985 lines 170-182 preserve meaningful disagreement and reject downstream or model-authored fixes for concrete reasons.

Single responsibility is preserved after the parent split. The coverage floor and population header are two halves of one artifact-integrity policy: fail closed below the operator's floor, and disclose the full-population denominator whenever rendering is allowed. They share the same reducer-owned rollup and one consumer. Feasibility is high because the required seams already exist, and the revised criteria below can all start RED for missing behavior rather than missing imports or unavailable services.

## Required revisions

### R-1: Make the bounded-input sentence true for populations smaller than the cap

Replace the exact header at FR-985 lines 109-114 and AC-B05 at lines 139-142. `prepare_brief_input` returns `rows[:BRIEF_TOP_N]` (`examples/demos/person_profile_census/tools.py:544-573`), so the current sentence, “Brief synthesized from top 30 judged rows,” is false whenever fewer than 30 judged rows exist. That recreates the proposal's own `plausible_wrong_answer` defect on small public or fixture runs.

Freeze this exact truthful shape:

`> Population: {judged}/{total} PRs classified ({coverage:.1%}); {failed} row_failed. Brief synthesized from {selected} of {judged} judged rows, selected by descending delta (cap {BRIEF_TOP_N}).`

`judged`, `total`, `coverage`, and `failed` must come from `state["ledger"]["rollup"]`. `selected` must equal `len(state["brief_input"])` and is the only header field derived from the bounded synthesis input. Add fixtures both below and above the cap so the sentence proves `7 of 7 ... (cap 30)` and `30 of 40 ... (cap 30)` rather than merely matching one large-run example. This changes disclosure only; it does not authorize changing `BRIEF_TOP_N` or its selection rule.

### R-2: Commit and cite the graph-authoring task brief

FR-985 lines 88-89 materially add `min_coverage` to `graph.yaml`, but AC-B09 at lines 152-153 requires only the transient report, lint, and smoke. The graph-authoring input contract requires an FR-bound task brief committed under `feature-requests/authoring-briefs/` and cited by the governing FR (`.github/skills/graph-authoring/doctrine.md`, “Input closure” and “Artifact boundary and report”).

Add and cite `feature-requests/authoring-briefs/fr-985-census-coverage-floor-brief.md`. It must name the only authorized graph change: add `min_coverage` to the person-profile census state so `--var min_coverage=...` reaches the reducer. It must also name the directly related README/demo-output artifacts and require the standard authoring report, graph lint, and smoke attempt. No prompt or node/edge change is authorized.

### R-3: Replace the unrelated FR-943 regression claim with a local person-profile witness

FR-985 lines 29-31 correctly treats FR-943 as precedent, but FR-962 explicitly reimplemented containment in the specialized person-profile reducer rather than inheriting FR-943's corpus-census implementation. The current repository has no person-profile reducer/render tests; the only matching test surface is the later FR-966 adapter test. Therefore AC-B07 at lines 145-147 cannot be satisfied by saying “existing FR-943 witnesses remain green”: those witnesses exercise a different reducer.

Require a person-profile fixture that feeds one valid `_error` finding with an attributable map index plus judged peers into `reduce_pr_ledger`, proves one local `classification_status="row_failed"` row is produced and peers survive when the configured floor permits it, and separately proves invalid/missing/duplicate indices and mechanical bundle failures remain fatal. Existing FR-943 tests may remain a broad regression check, but they cannot substitute for this local witness.

### R-4: Move the combined private-corpus run out of acceptance

Remove AC-B12 at FR-985 lines 162-168 from the acceptance checklist and preserve it as an explicitly authorized, non-gating operational observation. The FR says Successor A is independent and may land in either order (lines 39-41), while AC-B12 cannot run until FR-984 is also enforced. Calling deterministic tests “the enforcement gate” inside a mandatory acceptance criterion is internally contradictory.

Record that the operator authorized one combined run after both successors are enforced. When run, append the sanitized configured concurrency, 429 count, discovered/classified/failed counts, coverage, and terminal result to the implementation record. FR-985 completion must neither wait for FR-984 nor claim provider-quota improvement. No private/corp identifier may enter committed evidence.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 — coverage policy | `examples/demos/person_profile_census/tools.py`: parse `min_coverage`; gate after canary and before the first artifact path/write |
| D-2 — deterministic disclosure | `examples/demos/person_profile_census/tools.py`: prefix accepted briefs with the revised truthful population/input-selection header |
| D-3 — invocation state | `examples/demos/person_profile_census/graph.yaml`: add only the `min_coverage` state variable through the governed authoring route |
| D-4 — witnesses | Focused person-profile reducer, compiled-path, parser, rendering, and local containment tests |
| D-5 — user evidence | Person-profile census README and regenerated public-safe smoke output; committed FR-985 authoring brief and generated authoring report |
| D-6 — traceability | `CAP-263-census-coverage-gate`, `REQ-YG-646`, regenerated `ARCHITECTURE.md`, one fix changelog fragment, FR implementation record, and FR-985 diary reflection |
| D-7 — non-gating observation | One operator-authorized combined private-corpus run only after FR-984 and FR-985 are enforced; sanitized result appended when available |

Not authorized: changes to YAMLGraph core; map concurrency plumbing; provider retry or timeout policy; `max_items`; FR-943 containment semantics; `BRIEF_TOP_N` value or selection order; synthesis prompts, models, schemas, or node/edge topology; fabricated-URL scan behavior; coverage gates in other demos; broad person-profile refactoring; or any committed private/corp identifier.

## Revised acceptance criteria

- [ ] AC-01: RED first: a 10-row person-profile reducer fixture with 3 `row_failed` rows fails at the default floor `1.0`, passes at `min_coverage="0.7"`, and its failure names coverage, floor, failed count, and total count.
- [ ] AC-02: `min_coverage` defaults to `1.0`; booleans, non-numeric strings, NaN, infinities, negatives, and values above `1.0` fail with `min_coverage` in the diagnostic; numeric values and numeric strings are accepted within inclusive `[0.0, 1.0]`, with both boundaries tested.
- [ ] AC-03: the coverage gate runs after the existing canary and before constructing, opening, or writing ledger, JSONL, run-metadata, claims, rejected-brief, or accepted-brief paths; a canary failure still takes precedence over a coverage failure.
- [ ] AC-04: a compiled-path fixture with 100 of 259 rows failed proves `reduce_pr_ledger` raises, `prepare_brief_input`, `synthesize`, and `render_brief` do not run, and no output artifact is created.
- [ ] AC-05: when coverage meets the floor, `render_brief` obtains `judged`, `total`, `coverage`, and `failed` from reducer-owned full-population rollup data, obtains only `selected` from `len(brief_input)`, and writes this exact first line: `> Population: {judged}/{total} PRs classified ({coverage:.1%}); {failed} row_failed. Brief synthesized from {selected} of {judged} judged rows, selected by descending delta (cap {BRIEF_TOP_N}).`
- [ ] AC-06: known-count rendering fixtures below and above the cap assert exact first lines for `selected/judged` values `7/7` and `30/40`, respectively, and prove the header precedes model-authored content.
- [ ] AC-07: a local person-profile containment fixture proves one attributable `_error` finding becomes one `row_failed` ledger row while judged peers survive when the floor permits partial coverage; separate local fixtures prove invalid, missing, duplicate, and out-of-range indices plus invalid mechanical bundles remain fatal. Relevant FR-943 suites remain green but do not substitute for these witnesses.
- [ ] AC-08: person-profile census documentation states the default fail-closed behavior, shows explicit `--var min_coverage=...` acceptance of a partial population, explains the population and bounded-input header fields, and regenerates smoke output without private/corp identifiers.
- [ ] AC-09: FR-985 cites a committed `feature-requests/authoring-briefs/fr-985-census-coverage-floor-brief.md`; the graph edit is produced through the governed authoring route; `tmp/draft-authoring-report.md` names the graph and documentation artifacts; graph lint passes; the narrow smoke is attempted and its exact outcome or blocker is recorded.
- [ ] AC-10: `CAP-263-census-coverage-gate` and `REQ-YG-646`, re-verified against `origin/main` at push, cover every changed production branch; every new test carries that REQ marker; regenerated `ARCHITECTURE.md` and `python scripts/req_coverage.py --strict` pass.
- [ ] AC-11: the FR status and implementation decisions, one `fix` changelog fragment, and `docs/diary/diary-<date>-reflection-fr-985-<slug>.md` containing a `Seed:` are committed.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | R-1 through R-4 are folded into FR-985 before implementation authority activates. | GATE |
| C-2 | RED witnesses are committed before GREEN production changes; import errors, missing fixtures, or unavailable services do not count as RED. | GATE |
| C-3 | The coverage check remains after `_canary_gate` and before every artifact path construction/write; downstream stages cannot run after a threshold failure. | GATE |
| C-4 | Population counts come only from reducer-owned full-population rollup data; bounded `brief_input` supplies only its actual selected-row count. | GATE |
| C-5 | The only graph change is the declared `min_coverage` state variable, made through the committed FR-985 authoring brief and governed authoring route; no prompt or topology change is permitted. | GATE |
| C-6 | Person-profile containment is proved locally; FR-943's separate corpus-census witnesses are not accepted as a proxy. | GATE |
| C-7 | The private-corpus run is non-gating, occurs only after both successors are enforced, and commits no private/corp identifier. | GATE |
| C-8 | Human review must accept this advisory draft and the revised exact header contract before enforcement begins. | GATE |

Authority granted: after R-1 through R-4 are folded and human review accepts the draft, implement only the frozen person-profile coverage gate, truthful deterministic header, minimal graph state exposure, and their direct witnesses and documentation.

## Human review — 2026-09-04

Draft rendered by the sole route (`scripts/judge.sh`, backend `copilot`,
`gpt-5.6-sol`) in the FR worktree; folded verbatim above. Each revision
was verified before folding:

- **R-1 verified and accepted.** `prepare_brief_input` returns
  `rows[:BRIEF_TOP_N]` (`tools.py:573`), so "top 30" is false below 30
  judged rows — the FR would have shipped its own `plausible_wrong_answer`
  on every public smoke. Header contract frozen as written in R-1; the
  revised exact line is accepted (C-8).
- **R-2 done.** Brief committed at
  `feature-requests/authoring-briefs/fr-985-census-coverage-floor-brief.md`,
  cited from the FR; AC-09 revised.
- **R-3 verified.** `tools.py:177 _row_failed` is this demo's own
  containment; `tests/unit/test_fr943_census_row_failure_containment.py`
  imports the corpus-census reducer. AC-07 now demands the local witness.
- **R-4 done.** AC-B12 removed from criteria; retained as a non-gating
  observation with the operator's 2026-09-04 authorization intact.
- No finding falsified. Authority is active for the frozen scope.
