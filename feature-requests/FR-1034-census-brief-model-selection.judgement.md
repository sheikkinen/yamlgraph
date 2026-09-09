# Judgement: FR-1034 independent model selection for the census brief

**Verdict:** APPROVED WITH REVISIONS — independent synthesis selection is a narrow, feasible corpus-census enhancement, but authority activates only after the FR moves the resolver out of the already-maximal `tools.py`, makes brief provenance follow the selected synthesis model, and corrects every governed claim that still describes one pinned/shared model.

**Reviewed against:** `feature-requests/FR-1034-census-brief-model-selection.md`; `feature-requests/FR-895-census-synthesize-tail.md`; `feature-requests/FR-895-census-synthesize-tail.judgement.md`; `feature-requests/FR-1028-graph-run-provider-model-override.md`; `feature-requests/FR-1028-graph-run-provider-model-override.judgement.md`; `feature-requests/FR-1033-markdown-corpus-census-adapters.md`; `feature-requests/FR-1033-markdown-corpus-census-adapters.judgement.md`; `docs/diary/2026-09-09-reflection-fr-1033-fail-closed-is-the-same-rule-three-times.md`; `examples/demos/corpus_census/graph.yaml`; `examples/demos/corpus_census/tools.py`; `examples/demos/corpus_census/adapters/census_brief.py`; `examples/demos/corpus_census/prompts/synthesize_brief.yaml`; `examples/demos/corpus_census/README.md`; `tests/unit/test_fr895_census_brief.py`; `tests/unit/test_fr895_diary_brief.py`; `capabilities/CAP-250-census-synthesize-tail.yaml`; `ARCHITECTURE.md`; `yamlgraph/models/state_builder.py`; `.github/copilot-instructions.md`; `CLAUDE.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`.

## What is sound

The problem is concrete and the proposed policy is minimal. The graph currently routes both `judge_items` and `synthesize` through the same `state.provider` and `state.model` values (`examples/demos/corpus_census/graph.yaml:87-103,116-125`), while the FR records a named 150-item run in which the map stage succeeded economically and the synthesis stage exceeded the selected model's output limit (`feature-requests/FR-1034-census-brief-model-selection.md:41-55`). Independent selection for the single synthesis call directly addresses that seam without changing map behavior, retry policy, or the framework.

The resolver-node shape aligns with existing architecture. The graph already supports Python tools that return state updates and dict-valued state keys consumed through dotted interpolation (`examples/demos/corpus_census/graph.yaml:50-64,100-103`). State fields are generated as a `TypedDict` with `total=False`, so omitted brief-specific inputs are representable (`yamlgraph/models/state_builder.py:174-213`). A deterministic resolver that independently falls back from each blank brief-specific value to the existing graph-wide value is therefore workable and directly testable.

The proposal correctly distinguishes this feature from FR-1028. That prior feature changes root graph defaults at load time, while FR-1034 selects one existing stage after state enters the graph (`feature-requests/FR-1028-graph-run-provider-model-override.md:24-31,62-74`; `feature-requests/FR-1034-census-brief-model-selection.md:68-80`). Explicitly leaving `judge_items`, CLI flags, provider-error fallback, and the citation boundary outside scope keeps one responsibility.

The research gate is substantively satisfied. The in-body table presents six genuine solution classes, dispositions the existing graph-wide override and the one-line repinning alternative, preserves disagreement, and answers `is_this_a_graph` by reusing the existing `corpus_census` graph (`feature-requests/FR-1034-census-brief-model-selection.md:130-151`). Prior FRs are distinguished rather than merely listed.

Strategic classification: **Contrib/example**. This has one named consumer and modifies an existing example graph using established state/tool/node mechanisms; it does not establish three use cases or require a new framework primitive.

## Required revisions

### R-1: Put the resolver in a new bounded module

Replace the proposed `resolve_brief_llm` location in `examples/demos/corpus_census/tools.py` with a new focused module, `examples/demos/corpus_census/brief_model_selection.py`, and point the graph tool declaration at that module. Freeze the function contract there: accept graph state, require non-empty base `provider` and `model`, independently use a trimmed non-empty `brief_provider` or `brief_model` when supplied, and return exactly `{"provider": str, "model": str}`.

`tools.py` is already exactly 450 lines, the repository's hard maximum; adding the resolver there would violate the module-size rule (`CLAUDE.md`, Code Quality Standards; `examples/demos/corpus_census/tools.py:1-450`). FR-1033 provides immediate precedent for splitting a census adapter instead of exceeding that ceiling (`feature-requests/FR-1033-markdown-corpus-census-adapters.md:189-204`). This is a feasibility correction, not authority for a broader refactor: do not move or rewrite existing `tools.py` responsibilities.

Correct the FR's evidence path from nonexistent `yamlgraph/compile/state_builder.py` to `yamlgraph/models/state_builder.py`, and cite its `total=False` behavior (`yamlgraph/models/state_builder.py:174-213`) as the reason omitted brief-specific variables are valid.

### R-2: Make rendered provenance use the effective synthesis model

Authorize and specify the one necessary `render_brief` call-site change: obtain the resolved brief model from `state.brief_llm.model` and write that value to `run_meta["model"]`. Require a loud failure if the resolved mapping or either required field is absent or blank; do not silently revert to the map model after resolution.

The proposed graph reroutes the synthesis call but leaves rendering untouched (`feature-requests/FR-1034-census-brief-model-selection.md:73-80,102-116`). Today `render_brief` stamps `state.model`, not the model used by `synthesize` (`examples/demos/corpus_census/tools.py:417-450`), and `emit_brief` renders the supplied metadata verbatim into accepted and rejected artifacts (`examples/demos/corpus_census/adapters/census_brief.py:108-142`). Without this revision, a successful override produces false provenance and violates CAP-250's existing requirement that brief provenance carry the effective model (`capabilities/CAP-250-census-synthesize-tail.yaml:24-35`).

Add direct accepted-brief and rejected-brief witnesses proving the provenance `model` equals the effective brief model when overridden and equals the existing model when no brief override is supplied. No citation-validation behavior or `census_brief.py` change is authorized.

### R-3: Reconcile no-override semantics and all governed documentation

Replace “today's behaviour byte for byte” with a mechanically bounded promise: when both brief-specific inputs are absent or blank, the judge and synthesis calls receive the same provider/model values as before, and accepted/rejected brief content and provenance remain unchanged. Do not assert byte identity for the graph's full returned state, because the new resolver necessarily introduces `brief_llm`.

Expand the documentation criterion beyond `README.md`. Update the stale “single pinned” wording in `capabilities/CAP-250-census-synthesize-tail.yaml:4-11` and `ARCHITECTURE.md:3091-3101`; revise REQ-YG-633's claim that judge and synthesis are selected together through one `model` variable so it remains historically accurate after REQ-YG-675 is added. Add `REQ-YG-675` to CAP-250 and `ARCHITECTURE.md` with the independent-fallback and truthful-provenance contract, and add FR-1034 to CAP-250's `fr:` list.

The README correction alone would leave the capability registry and architecture documentation making the same false claim this FR exists to remove (`examples/demos/corpus_census/README.md:18-28,75-83`; `capabilities/CAP-250-census-synthesize-tail.yaml:4-11,24-35`; `ARCHITECTURE.md:3091-3101`). Tests must assert the relevant README, CAP, and architecture wording/requirement wiring rather than using an unrestricted repository grep.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `examples/demos/corpus_census/brief_model_selection.py` containing only the deterministic `resolve_brief_llm` tool |
| D-2 | `examples/demos/corpus_census/graph.yaml`: optional brief-specific state, resolver tool/node, two resolver edges, and synthesis provider/model references |
| D-3 | `examples/demos/corpus_census/tools.py`: only the minimal `render_brief` provenance read from the already-resolved brief model |
| D-4 | `tests/unit/test_census_brief_model_selection.py`: resolver, compiled-routing, end-to-end, no-override, provenance, and documentation witnesses |
| D-5 | `examples/demos/corpus_census/README.md`, `capabilities/CAP-250-census-synthesize-tail.yaml`, and the CAP-250/REQ-YG-633/REQ-YG-675 portions of `ARCHITECTURE.md` |
| D-6 | Graph-authoring report, changelog fragment, FR implementation record, and diary distillation |

Not authorized: per-stage selection for any node other than `synthesize`; changes to `judge_items`, the reducer, ledger schema/content, prompts, `census_brief.py`, citation validation, provider retry/fallback behavior, CLI flags, framework/runtime code, adapters, hooks, CI, judge/review doctrine, or refactoring existing responsibilities out of `tools.py`.

## Revised acceptance criteria

- [ ] AC-01: RED-first resolver tests prove absent, empty, and whitespace-only `brief_provider`/`brief_model` independently fall back to the required base `provider`/`model`.
- [ ] AC-02: Resolver tests prove both overrides are selected together and each may be selected independently while the other field falls back.
- [ ] AC-03: Missing, non-string, empty, or whitespace-only base `provider` or `model` raises a specific `ValueError`; every successful result contains exactly two non-empty stripped strings under `provider` and `model`.
- [ ] AC-04: The resolver lives in `examples/demos/corpus_census/brief_model_selection.py`; `tools.py` remains at or below 450 lines and receives no unrelated refactor.
- [ ] AC-05: The loaded/compiled graph routes `judge_items` from `provider`/`model`, routes `synthesize` from `brief_llm.provider`/`brief_llm.model`, and has exactly `prepare_brief_input → resolve_brief_llm → synthesize → render_brief` in the modified tail.
- [ ] AC-06: End-to-end over the committed three-file Markdown fixture with a deterministic stubbed LLM boundary proves judge and synthesis receive different provider/model pairs when brief overrides are supplied and the same pair when both are absent or blank.
- [ ] AC-07: Accepted and rejected brief artifacts record the effective synthesis model from `brief_llm`; an override never records the map model, while the no-override artifact retains the prior model provenance.
- [ ] AC-08: No-override witnesses prove LLM routing and accepted/rejected brief artifacts retain existing observable behavior; no byte-identity claim is made for full returned graph state.
- [ ] AC-09: Focused assertions prove README, CAP-250, and the CAP-250 architecture section no longer call synthesis pinned or claim judge and synthesis must share one model; REQ-YG-633 remains coherent and REQ-YG-675 states independent per-field fallback plus effective brief-model provenance.
- [ ] AC-10: CAP-250 lists FR-1034 and REQ-YG-675; every new test is tagged `@pytest.mark.req("REQ-YG-675")`; `python scripts/req_coverage.py --strict` passes.
- [ ] AC-11: The material graph change goes through the sole graph-authoring route; its retained report records graph lint and a successful smoke covering the resolver path.
- [ ] AC-12: Changelog fragment, FR implementation status/decisions, and diary Distill entry with a `Seed:` are complete.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold R-1 through R-3 and AC-01 through AC-12 into FR-1034 before implementation; until then this judgement grants no authority. | GATE |
| C-2 | The graph and prompt authoring contract applies: modify `graph.yaml` only through the graph-authoring route and retain its substantive report; no prompt change is authorized. | GATE |
| C-3 | Keep `tools.py` at or below 450 lines; add the resolver in the frozen new module and do not use this FR to refactor unrelated census code. | GATE |
| C-4 | Resolve provider and model independently and fail loudly when either base value is invalid; no provider-error retry, automatic larger-model selection, or silent fallback after resolution is permitted. | GATE |
| C-5 | Brief provenance must name the model actually used by `synthesize` for both accepted and rejected artifacts. | GATE |
| C-6 | `judge_items`, reducer/ledger behavior, prompts, citation validation, adapters, CLI/runtime code, and all other graph nodes remain unchanged. | GATE |
| C-7 | Any enforcement-infrastructure change requires separate authority and explicit human review. | GATE |

Authority granted: after R-1 through R-3 are folded into FR-1034 and this advisory draft is human-reviewed, implement only the corpus-census synthesis provider/model resolver, truthful brief-model provenance, exact documentation/requirement corrections, and supporting artifacts within the frozen surfaces above.
