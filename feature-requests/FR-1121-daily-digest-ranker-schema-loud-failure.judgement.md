# Judgement: FR-1121 Daily digest ranker survives constrained decoding and fails loudly

**Verdict:** APPROVED WITH REVISIONS — the incident, causal chain, and consumer-level repair are sound, but authority activates only after the FR names durable authoring inputs, replaces shape-only and ambiguous gates with behavioral witnesses, and binds requirement traceability explicitly.

**Reviewed against:** `feature-requests/FR-1121-daily-digest-ranker-schema-loud-failure.md`; `feature-requests/FR-1121.research.md`; `feature-requests/TEMPLATE.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/skills/graph-authoring/doctrine.md`; `.github/skills/graph-authoring/adapters/README.md`; `.github/copilot-instructions.md`; `docs/development-process.md`; `ARCHITECTURE.md`; `feature-requests/FR-998-anthropic-constrained-structured-output.md`; `feature-requests/FR-905-ranked-story-boundary-validation.md`; `feature-requests/FR-905-ranked-story-boundary-validation.judgement.md`; `feature-requests/FR-903-digest-archive-then-email-ordering.md`; `feature-requests/FR-819-github-native-digest-poc-repo.md`; `feature-requests/FR-1097-graph-run-completed-errors-exit-3.md`; `feature-requests/FR-1073-map-result-contract.md`; `feature-requests/FR-1122-daily-digest-map-contract-migration.md`; `feature-requests/FR-1123-untyped-subschema-constrained-decoding-gate.md`; `feature-requests/FR-1124-llm-node-default-on-error.md`; `examples/daily_digest/graph.yaml`; `examples/daily_digest/prompts/rank_stories.yaml`; `yamlgraph/utils/structured_output.py`; `yamlgraph/node_factory/llm_execution.py`.

## What is sound

The problem is real, bounded, and supported by a complete causal chain. The FR identifies a concrete first consumer and event (`feature-requests/FR-1121-daily-digest-ranker-schema-loud-failure.md:8-13), then traces the production silence through schema rejection, default error handling, status misclassification, runner behavior, and persisted dedup state (`feature-requests/FR-1121-daily-digest-ranker-schema-loud-failure.md:38-68`). The repository mirror corroborates the relevant configuration: its prompt still declares `stories: list[Any]` (`examples/daily_digest/prompts/rank_stories.yaml:27-30`), while its `rank_stories` node has no `on_error` declaration (`examples/daily_digest/graph.yaml:90-96`). The execution code confirms that `fail` re-raises while an unmatched policy falls through to `handle_default` (`yamlgraph/node_factory/llm_execution.py:135-167`).

The proposed repair is minimal relative to the ideal. `list[dict]` removes the empty item subschema without inventing nested schema grammar; `on_error: fail` stops downstream laundering; and the runner guard closes the separate recorded-error path (`feature-requests/FR-1121-daily-digest-ranker-schema-loud-failure.md:88-137`). The element-level semantic boundary from FR-905 remains intact rather than being confused with provider schema compatibility. Framework-wide schema refusal, map migration, default-policy changes, historical recovery, and version pinning are explicitly excluded (`feature-requests/FR-1121-daily-digest-ranker-schema-loud-failure.md:169-176`).

The research record satisfies the prospective research gate in substance. Four executed perspectives converge on boundary enforcement while preserving disagreement about whether loudness belongs in the framework or consumer, and the record explains why this FR takes the graph-plus-runner path (`feature-requests/FR-1121.research.md:34-57`). The failed fifth perspective is disclosed rather than laundered into success (`feature-requests/FR-1121.research.md:10-18`). Prior art is dispositioned, including FR-905's deliberate schema deferral and the separate FR-1122/1123/1124 territories.

Single responsibility is satisfied. Schema compatibility, node propagation, and runner refusal are not orthogonal features; they are defenses at successive boundaries of the one witnessed "ranker failure becomes quiet day" chain. Implementing them separately would leave a known silent path between releases.

Strategic classification: **contrib/example bug fix**. There are two concrete consumers, the standalone digest and its repository example, and existing schema, graph error-policy, and runner mechanisms suffice. No new framework primitive is authorized.

## Required revisions

### R-1: Name the committed briefs and treat adapter reports as transient evidence

Replace the generic brief/report language in S-1 and AC-5 with two exact committed brief paths, one for the YAMLGraph example authoring run and one for the standalone digest authoring run. Each brief must name its repository boundary, target directory, graph, prompt, tests, and expected validation. The governing FR must cite those paths before enforcement. The graph-authoring contract requires the governing FR to cite a committed brief that survives `tmp/` cleanup (`.github/skills/graph-authoring/doctrine.md:21-30`).

Do not require an adapter report to be committed. Each authoring run must produce and verify the transient `tmp/draft-authoring-report.md`, and the FR implementation record must persist, separately for each repository, the report's authored paths, precedent, exact validation commands and outcomes, repairs, and blocked validation. The report contract places that artifact under `tmp/` (`.github/skills/graph-authoring/doctrine.md:53-75`); FR-1121 currently conflates the committed brief with the transient report (`feature-requests/FR-1121-daily-digest-ranker-schema-loud-failure.md:83-86`, `feature-requests/FR-1121-daily-digest-ranker-schema-loud-failure.md:190-192`).

### R-2: Replace the shape-only `on_error` assertion with an execution-path witness

Retain the YAML declaration assertion, but add a behavioral witness in each repository using that repository's actual graph configuration: force the `rank_stories` LLM execution to raise, assert the original exception propagates from graph invocation, and assert the downstream formatting node is not invoked. A test that only reads `on_error: fail` from YAML (`feature-requests/FR-1121-daily-digest-ranker-schema-loud-failure.md:146`, `feature-requests/FR-1121-daily-digest-ranker-schema-loud-failure.md:183-184`) checks shape, not the required behavior. FR-1073 is direct precedent that a correctly spelled `on_error` key can sit where a compiler does not read it. The FR's claim is that node, graph, runner, and job fail in order, so at least the graph propagation seam must be exercised.

### R-3: Make lint comparison reproducible

Replace "`yamlgraph graph lint` reports no new diagnostic" with a reproducible before/after contract. Before authoring, capture the complete lint diagnostics for each target graph in that repository's authoring report. After authoring, run the same command and assert that the diagnostic identity set is unchanged or reduced and that no diagnostic points to the modified `rank_stories` node or prompt schema. Record both commands and result sets in the FR implementation record. "No new diagnostic" has no mechanical baseline as currently written (`feature-requests/FR-1121-daily-digest-ranker-schema-loud-failure.md:190-192`), while authoring doctrine requires command-backed, honest validation (`.github/skills/graph-authoring/doctrine.md:77-90`).

### R-4: Replace the tautological scheduled-run gate with an error/no-error invariant

Rewrite AC-6 so a legitimate no-article day remains green. The current binary requires the first scheduled run either to publish or fail (`feature-requests/FR-1121-daily-digest-ranker-schema-loud-failure.md:193-195`), but a run with no fresh articles is an intentional third outcome established by FR-903 and FR-905. Require the run ID and logs to prove one of these mutually exclusive outcomes:

1. `rank_stories` succeeds and the run archives and sends a bulletin;
2. no articles reach the ranker, `result["errors"]` is empty, and the legitimate no-op exits zero; or
3. an error is recorded or raised, the runner exits non-zero, no no-op line is printed, and the workflow commit step does not execute.

This tests the promised invariant — no recorded error reaches a green quiet-day result — rather than depending on whether the news feed happens to contain articles that morning.

### R-5: Bind tests to the exact governing requirement

Name `REQ-YG-664` in the proposed witnesses and revised acceptance criteria for every new test function added in this repository, and require `python scripts/req_coverage.py --strict` to pass. FR-1121 currently says only "the REQ ID FR-998 owns" (`feature-requests/FR-1121-daily-digest-ranker-schema-loud-failure.md:151-155`); FR-998 names that requirement as `REQ-YG-664` (`feature-requests/FR-998-anthropic-constrained-structured-output.md:144-146`), and repository doctrine requires every test function to carry an exact requirement marker (`.github/copilot-instructions.md:169-171`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `feature-requests/FR-1121-daily-digest-ranker-schema-loud-failure.md`: fold R-1 through R-5 and later record implementation evidence and deviations |
| D-2 | Two exact committed briefs under `feature-requests/authoring-briefs/`, one closing the YAMLGraph example authoring run and one closing the standalone digest authoring run |
| D-3 | This repository: `examples/daily_digest/prompts/rank_stories.yaml`, `examples/daily_digest/graph.yaml`, focused `tests/unit/` witnesses, and one `changelog/unreleased/` fragment |
| D-4 | External `sheikkinen/yamlgraph-daily-digest`: `prompts/rank_stories.yaml`, `graph.yaml`, `run_digest.py`, and focused FR-1121 tests |
| D-5 | One verified transient authoring report per repository, with its durable validation summary copied into the FR implementation record |
| D-6 | One post-merge production witness recording the scheduled run ID and evidence for exactly one R-4 outcome |
| D-7 | One Distill entry under `docs/diary/` containing `**Seed:**` |

Not authorized: any change to YAMLGraph framework code, schema-loader grammar, structured-output binding policy, provider fallback behavior, default `llm` error policy, map contract or map migration, formatting-node validation semantics, article collection/filtering, dedup persistence, workflow scheduling or permissions, dependency pinning, recovery of historical articles, CI/hooks, judge/review doctrine, or any graph/prompt artifact beyond the four paths named in D-3 and D-4.

## Revised acceptance criteria

- [ ] AC-01: FR-1121 folds R-1 through R-5 before enforcement begins and cites two exact committed authoring briefs under `feature-requests/authoring-briefs/`, each naming its repository boundary and complete artifact/validation surface.
- [ ] AC-02: In each repository, a separate RED commit adds a transform witness that builds the actual committed ranker prompt model and fails because `stories.items` is untyped; the corresponding GREEN commit changes `stories` to `list[dict]` and the same Anthropic SDK transform completes without raising.
- [ ] AC-03: In both prompt files, `model_json_schema()` contains `stories.items.type == "object"` after the change; FR-905's Python `RankedStory` boundary and all of its remaining tests are unchanged and pass.
- [ ] AC-04: `rank_stories` declares `on_error: fail` in both graphs, and a configuration assertion proves the declaration in each repository.
- [ ] AC-05: A behavioral test in each repository loads that repository's graph configuration, forces `rank_stories` execution to raise, proves the original exception propagates from graph invocation, and proves the downstream formatting node is not invoked.
- [ ] AC-06: In the standalone digest, a stubbed completed invocation carrying at least two real `PipelineError` instances and `digest_status == "no_articles"` makes `run_digest.py` print every error to stderr, print no no-op line, and exit 2 before any later success/no-op handling.
- [ ] AC-07: Before and after each authoring run, the same `yamlgraph graph lint <graph>` command is recorded with its complete diagnostic identity set; the after set is unchanged or reduced, and no after diagnostic points to the modified ranker node or prompt schema.
- [ ] AC-08: Each repository's graph and prompt edits are produced through `scripts/author.sh` from its named committed brief. Each run produces a non-empty `tmp/draft-authoring-report.md` satisfying the required headings and artifact checks; the report remains transient, while its paths, precedent, commands, outcomes, repairs, and blocked validation are copied into FR-1121's implementation record.
- [ ] AC-09: Every new YAMLGraph-repository test function carries `@pytest.mark.req("REQ-YG-664")`; the focused tests and `python scripts/req_coverage.py --strict` pass.
- [ ] AC-10: Every FR-905 test other than the replaced schema-pin test passes without weakened assertions; the schema-pin test is replaced by, not merely deleted in favor of, the transform witness.
- [ ] AC-11: The first scheduled run after merge records its run ID and logs proving exactly one outcome: successful ranker plus archived/sent bulletin; legitimate no-input no-op with zero recorded errors and no ranker invocation; or non-zero failure with the error on stderr, no no-op line, and no workflow commit step.
- [ ] AC-12: No framework, map, formatting-boundary, collection, dedup, dependency-floor, workflow-policy, CI, hook, or doctrine surface listed as not authorized is changed.
- [ ] AC-13: This repository receives one scoped changelog fragment and one Distill diary entry containing `**Seed:**`; FR-1121 records RED/GREEN commits for both repositories, exact validation results, the production witness, implementation status, decisions, and deviations.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Authority is inactive until R-1 through R-5 are folded into FR-1121. | GATE |
| C-2 | Every graph or prompt edit must be made by the governed authoring route from the exact committed brief for that repository; direct edits are forbidden. | GATE |
| C-3 | The two repository boundaries remain separate: do not vendor, nest, submodule, or commit the standalone digest working tree into this repository. | GATE |
| C-4 | The schema RED must fail for the missing item type, and the graph-path RED must fail for absent loud propagation; import, fixture, credential, or unrelated setup failures do not satisfy TDD. | GATE |
| C-5 | A declared `on_error: fail` without a behavioral propagation witness grants no completion credit. | GATE |
| C-6 | A green no-op is permitted only when no articles reach the ranker and no errors are recorded; any recorded or raised error must produce a non-zero process and prevent the workflow commit step. | GATE |
| C-7 | `list[dict]` is the full schema change authorized here; do not add nested schema grammar or weaken FR-905's typed deterministic boundary. | GATE |
| C-8 | No framework, map, dependency, workflow-policy, CI, hook, or doctrine change may be absorbed into this FR; any such need stops enforcement and re-enters the judged process separately. | GATE |

Authority granted: after R-1 through R-5 are folded, the enforcer may retype the two ranker schemas, add `on_error: fail` to the two ranker nodes, add the standalone runner error guard, and implement only the frozen witnesses and records above.
