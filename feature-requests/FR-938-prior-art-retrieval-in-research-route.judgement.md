# Judgement: FR-938 Prior-art retrieval inside the research route

**Verdict:** APPROVED WITH REVISIONS — the problem is real, evidenced, and scoped to an existing retrieval seam, but authority activates only after the FR clarifies `rare_floor=False` candidate semantics, `none-retrieved` validation/counting, and graph-state wiring for the verbatim report block.

**Reviewed against:** `feature-requests/FR-938-prior-art-retrieval-in-research-route.md`; `feature-requests/FR-938.research.md`; `feature-requests/FR-737-graveyard-hook-prior-art-on-fr-creation.md`; `feature-requests/FR-738-prior-art-disposition-gate.md`; `feature-requests/FR-814-fr-knowledge-graph-extraction.md`; `feature-requests/FR-890-research-sole-route-closed-input-alternatives.md`; `feature-requests/FR-896-research-route-precedent-traceability.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `.github/hooks/scripts/checks/prior_art.py`; `.github/hooks/scripts/checks/prior_art_gate.py`; `.github/hooks/tests/test_fr738_disposition_gate.py`; `examples/demos/research-route/graph.yaml`; `examples/demos/research-route/nodes/research_tools.py`; `scripts/research_preflight.py`; `tests/unit/test_fr890_research_route.py`; `tests/unit/test_fr896_precedent_traceability.py`; `feature-requests/TEMPLATE.md`.

## What is sound

The FR satisfies the research-evidence gate: it cites a committed research artifact (`FR-938` lines 13, 279-290), and that artifact preserves five alternatives with disagreement rather than a single persona assertion (`FR-938.research.md` lines 9-13). Four rows converge on deterministic FR-corpus grounding, while the subtractionist preserves the real counterargument: deleting the hollow precedent check instead of strengthening it (`FR-938.research.md` line 12).

The problem statement is concrete and borne out by the cited implementation surfaces. The current research context is deterministic but does not include the feature-request corpus: `collect_committed_context` currently assembles CAP one-liners, `ARCHITECTURE.md` headings, and Scripture keys only (`research_tools.py` lines 223-257), and `graph.yaml` passes that same `committed_context` to every persona (`graph.yaml` lines 79-182). The FR's diagnosis that personas are asked for precedent while running without the precedent corpus is therefore sound (`FR-938` lines 54-66).

The prior-art disposition is credible. FR-737 established that rejected FRs are precedent and that filename-only extraction was deliberately chosen until a real miss appeared (`FR-737` lines 88-90, 163-166). FR-738 moved the same retrieval into a pre-commit disposition gate while keeping substance with the Judge (`FR-738` lines 67-73). FR-938 distinguishes those completed mechanisms rather than replacing them (`FR-938` lines 14-23), and it correctly classifies the witnessed failure as retrieval-floor calibration, not title/body extraction (`FR-938` lines 87-112).

The architecture choice aligns with existing patterns. Reusing `build_prior_art` keeps ranking, status annotation, self-exclusion, graph-cluster boost, and the `TOP_N = 5` cap at the existing boundary (`prior_art.py` lines 175-257), while injecting results through `collect_committed_context` preserves FR-890's author-independent research route (`FR-890` lines 88-108; `FR-938` lines 184-186). Strategic classification: **Contrib/example process-route enhancement**, not a new framework primitive; an existing abstraction fits with a consumer-specific floor.

## Required revisions

### R-1: Define `rare_floor=False` candidate eligibility mechanically

Amend FR-938 R-1/R-1a and AC-03a to state the exact behavior of `build_prior_art(new_file, rare_floor=False)`: with the default `rare_floor=True`, the current `rare` early return and candidate filter remain unchanged for hook callers; with `rare_floor=False`, eligible nouns are all nouns whose corpus frequency is greater than zero, the no-hit return fires only when no query noun matches any corpus file, and candidate filtering uses that eligible set while preserving scoring, `_weighted_zone`, status tags, graph-cluster boost, self-exclusion, and `TOP_N = 5`.

This revision is required because the current implementation has two rare-floor gates, not one: it returns on `not rare` and later filters candidates to files matching `rare` (`prior_art.py` lines 219-226). The FR currently says only "gating the existing `rare` early return" (`FR-938` lines 172-176), which is ambiguous enough to implement a no-op for the research consumer.

### R-2: Replace `brief-echo` with bounded `none-retrieved` semantics

Amend R-4/R-6 and AC-05 to define the post-FR row-validation states in both `research_tools.py` and `scripts/research_preflight.py`: non-librarian precedent cells pass only with a committed identifier, a URL, or `none-retrieved`; `brief-echo` is rejected in newly generated artifacts; `none-retrieved` is accepted only when the artifact header's prior-art block is exactly `none-retrieved`; and `none-retrieved` counts toward the existing minimum-grounding threshold as a grounded-empty row, not as an echo.

This revision is required because FR-896's current reducer accepts `brief-echo` as a non-traceable demotion (`FR-896` lines 108-149; `research_tools.py` lines 345-401), while FR-938 proposes prose-only precedent failure and a new `none-retrieved` token (`FR-938` lines 163-166, 188-191, 231-233). Without an explicit replacement rule, the enforcer can either preserve the hollow echo path or make honest no-hit runs fail the existing "fewer than 3 non-echo traceable findings" gate.

### R-3: Specify the single source of truth for the verbatim report block

Amend R-2/R-5, AC-01, and AC-07 to name the graph and reducer wiring: `examples/demos/research-route/graph.yaml` passes `brief_path: "{state.brief_path}"` to `collect_committed_context`; `collect_committed_context(repo_root, brief_path)` computes the prior-art subsection once; and `write_alternatives` writes that already-computed subsection from `state["committed_context"]` into the artifact header byte-for-byte, without recomputing retrieval during reduction.

This revision is required because the current graph node passes only `repo_root` (`graph.yaml` lines 79-84), while the current writer receives `brief_path` but not an explicit prior-art block argument in `reduce_findings` (`research_tools.py` lines 411-482). The FR requires the Judge to read "the same block verbatim" (`FR-938` lines 192-193); the state edge that guarantees sameness must be frozen.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `.github/hooks/scripts/checks/prior_art.py`: add exactly one defaulted keyword to `build_prior_art` and adjust only the rare-floor eligibility path needed by R-1. |
| D-2 | `.github/hooks/tests/test_fr738_disposition_gate.py`: add regression coverage for default floor preservation and `rare_floor=False` retrieval under a high-frequency fixture corpus. |
| D-3 | `examples/demos/research-route/nodes/research_tools.py`: collect the prior-art subsection, include it in committed context, propagate it to artifact writing, and mirror row-validation semantics from R-2. |
| D-4 | `examples/demos/research-route/graph.yaml`: wire `brief_path` into `collect_committed_context`; no other graph behavior change is authorized. |
| D-5 | `scripts/research_preflight.py`: mirror the artifact/header validation semantics from R-2 without changing the frozen table columns. |
| D-6 | `tests/unit/test_fr890_research_route.py` and/or `tests/unit/test_fr896_precedent_traceability.py`: deterministic unit tests for context injection, header identity, prospective verifier behavior, bounds, and schema mirrors. |
| D-7 | `feature-requests/TEMPLATE.md`: document that `**Prior art:**` dispositions the retrieval block printed in the research record. |
| D-8 | `feature-requests/FR-938-prior-art-retrieval-in-research-route.md`: fold this judgement's revisions before enforcement and record implementation decisions/status afterward. |
| D-9 | `feature-requests/FR-938.research.md` and `feature-requests/research-runs.jsonl`: live demo evidence only if AC-10 replaces or appends the run record. |

Not authorized: semantic or embedding retrieval; title/body noun extraction; relocating `prior_art.py`; changing `prior_art_gate.py` or the pre-commit marker rule; passing prior-art or research paths to the judge graph; changing judge doctrine; adding a new research schema column; changing `TABLE_COLUMNS`/`COLUMNS`; retro-gating the twelve committed research artifacts; broad path configurability; prompt/persona rewrites beyond consuming the existing `committed_context`.

## Revised acceptance criteria

- [ ] AC-01: `build_prior_art(path)` preserves current hook behavior with `rare_floor=True`: a high-frequency-only fixture returns `""`, existing FR-737/FR-738 ranking/status/self-exclusion tests still pass, and `prior_art_gate.py` continues to call the default form.
- [ ] AC-02: `build_prior_art(path, rare_floor=False)` returns ranked `TOP_N` hits for a fixture corpus where every matching noun exceeds `RARE_MAX_FILES`; the returned rows preserve status tags, `_weighted_zone` ranking, graph-cluster boost behavior when present, self-exclusion, and filename-only noun extraction.
- [ ] AC-03: `collect_committed_context(repo_root, brief_path)` emits `### Prior art retrieved for this brief (filename-noun, IDF-ranked)` and searches a synthetic `feature-requests/<brief-stem>.md` path, proven by a fixture where the brief's own directory has tempting hits but the emitted hits come from `feature-requests/`.
- [ ] AC-04: A fixture corpus with a rejected FR asserts the emitted prior-art block includes the candidate filename and `[REJECTED]` status, preserving the FR-737 rule that rejected proposals are precedent.
- [ ] AC-05: Empty retrieval is explicit: when `rare_floor=False` finds no matching noun in the FR corpus, `collect_committed_context` emits `none-retrieved`, `write_alternatives` writes the same token in the artifact header, and non-librarian row precedent may use `none-retrieved` only under that empty-retrieval header.
- [ ] AC-06: The committed-context block remains bounded under `_MAX_CONTEXT_LINES` with a full five-hit prior-art block, and the existing overflow `ValueError` still fires when the bound is exceeded.
- [ ] AC-07: `write_alternatives` copies the prior-art subsection from `state["committed_context"]` into the artifact header byte-for-byte; a unit test compares the two slices exactly.
- [ ] AC-08: `verify_artifact` and the reducer reject a non-librarian precedent cell with no committed identifier, no URL, and no valid `none-retrieved`; accept committed identifiers, URLs, and header-backed `none-retrieved`; reject `brief-echo` in newly generated artifacts; and leave librarian URL/error-string checks unchanged.
- [ ] AC-09: The frozen `TABLE_COLUMNS`/`COLUMNS` tuples and class/verdict enums are byte-identical after the change; the existing schema-mirror tests between `research_preflight.py` and `research_tools.py` pass.
- [ ] AC-10: A live `scripts/research.sh` run on this FR's own brief produces an artifact whose header carries the prior-art retrieval block, whose non-librarian precedent cells satisfy AC-08, and whose run is logged to `feature-requests/research-runs.jsonl`.
- [ ] AC-11: `feature-requests/TEMPLATE.md` states that the `**Prior art:**` disposition line dispositions the hits printed in the linked research record, naming that record as retrieval evidence.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold R-1 through R-3 into `feature-requests/FR-938-prior-art-retrieval-in-research-route.md` before implementation authority activates. | GATE |
| C-2 | Because `examples/demos/research-route/graph.yaml` is a graph artifact, any graph edit must satisfy the repo graph-authoring route contract and produce its `tmp/draft-authoring-report.md` evidence; unsentineled manual graph writes are not authorized by this judgement. | GATE |
| C-3 | Keep `prior_art_gate.py` and the pre-commit marker semantics unchanged; only default-call preservation tests may touch that surface. | GATE |
| C-4 | Do not modify `.github/skills/judge-fr/doctrine.md`, the judge adapter, or any judge graph as part of this FR. | GATE |
| C-5 | Apply tightened research-artifact validation prospectively only; do not rewrite or retro-gate the twelve committed research artifacts used as the measurement baseline. | GATE |

Authority granted: after R-1 through R-3 are folded, the enforcer may implement deterministic prior-art retrieval inside the research route by reusing `build_prior_art` with a research-only lifted floor, injecting the bounded result into committed context, printing the same block in the research artifact header, and prospectively tightening precedent validation as specified above.
