# Judgement: FR-1122 Daily digest map node on the FR-1073 contract

**Verdict:** APPROVED WITH REVISIONS — the consumer migration is necessary, narrow, and aligned with the shipped map contract, but authority activates only after R-1 through R-5 are folded into the FR.

**Reviewed against:** `feature-requests/FR-1122-daily-digest-map-contract-migration.md`; `feature-requests/FR-1122.research.md`; `feature-requests/FR-1073-map-result-contract.md`; `feature-requests/FR-939-map-overflow-policy.md`; `feature-requests/FR-984-map-fan-out-max-concurrency.md`; `feature-requests/FR-1113-meta-map-demo.md`; `feature-requests/FR-1119-lint-map-owned-state-fields.md`; `feature-requests/FR-1121-daily-digest-ranker-schema-loud-failure.md`; `feature-requests/069-map-node-timeout.md`; `feature-requests/052-map-output-flattening.md`; `feature-requests/FR-903-digest-archive-then-email-ordering.md`; `feature-requests/FR-904-slot-bound-digest-collection.md`; `feature-requests/FR-905-ranked-story-boundary-validation.md`; `feature-requests/FR-903-digest-archive-then-email-ordering.judgement.md`; `feature-requests/FR-904-slot-bound-digest-collection.judgement.md`; `feature-requests/FR-905-ranked-story-boundary-validation.judgement.md`; `reference/graph-yaml.md`; `yamlgraph/compile/map_compiler.py`; `yamlgraph/compile/map_contract.py`; `yamlgraph/models/map_results.py`; `.github/skills/graph-authoring/doctrine.md`; `.github/skills/graph-authoring/adapters/README.md`; `scripts/author.sh`; `.github/copilot-instructions.md`; `CLAUDE.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`.

## What is sound

The problem is real and the proposed core change is the smallest contract migration. FR-1073 explicitly names `daily_digest/graph.yaml` row 10 and approves moving its unread map-level `on_error: skip` into the LLM sub-node (`feature-requests/FR-1073-map-result-contract.md:253-261`, `:344-351`). FR-1122 follows that decision, uses `state_key` to remove the generated wrapper at collection rather than flattening afterward, and keeps framework changes, source changes, ranker-schema work, and an unevidenced `min_success` threshold outside scope (`feature-requests/FR-1122-daily-digest-map-contract-migration.md:108-156`, `:201-208`). That is consistent with the documented contract: map-level `on_error` is unread, nested skip is tolerated, timeout is not tolerated, failures are separate, and strict completeness counts tolerated outcomes as accepted (`reference/graph-yaml.md:669-732`).

The research record is substantive: it compares five solution classes, preserves the strict-failure dissent and accounting-location disagreement, corrects the dual-version claim, dispositions precedent, and answers `is_this_a_graph` (`feature-requests/FR-1122.research.md:30-59`, `:77-83`). The proposal also respects layer ownership: policy and collection shape stay in YAML, while rendering the already-produced verdict stays in the runner (`feature-requests/FR-1122-daily-digest-map-contract-migration.md:145-185`). The gate `output` repair is acceptable validation collateral because the graph cannot satisfy the requested clean lint witness while E601 remains (`feature-requests/FR-1122-daily-digest-map-contract-migration.md:83-88`, `:158-168`).

Against the eight criteria: scope is narrow apart from the explicit lint collateral; objectives and map semantics are consistent; most criteria are mechanical; the graph changes use existing primitives; architecture alignment is strong; graph, prompt, and runner changes form one consumer migration rather than independent capabilities; strategic classification is **Contrib/example** because one external application consumes existing abstractions; and direct failing tests are derivable once the gaps below are repaired. No framework primitive is authorized.

## Required revisions

### R-1: Consume the typed map result contract as typed data

Replace S-4's dictionary access with Pydantic boundary validation and attribute access. The runtime stores a `MapVerdict` at `_map_verdict.<name>` and `MapFailure` instances in the failures channel (`yamlgraph/compile/map_contract.py:48-70`, `:190-217`; `yamlgraph/models/map_results.py:13-43`); existing consumers normalize with `MapFailure.model_validate`, and framework tests read verdict attributes. As written, `verdict.get(...)` and `f["index"]` will raise on a successful invocation.

Fold an implementation equivalent to:

```python
verdict_raw = (result.get("_map_verdict") or {}).get("analyze_all")
if verdict_raw is None:
    raise RuntimeError("analyze_all map verdict is missing")
verdict = MapVerdict.model_validate(verdict_raw)
failures = [
    MapFailure.model_validate(item)
    for item in (result.get("analysis_failures") or [])
]
print(
    f"Analysed {verdict.succeeded} of {verdict.dispatched}"
    f" - {len(failures)} skipped"
)
for failure in failures:
    print(
        f"  skipped #{failure.index}: {failure.error_type}:"
        f" {failure.message[:120]}"
    )
```

The exact typography may follow the application's established output, but missing verdict state must fail loudly rather than become `?`, and the test must exercise actual `MapVerdict` and `MapFailure` instances as returned by the runtime.

### R-2: Test the policies this FR newly chooses

Expand the acceptance criteria beyond key-presence checks. `on_overflow: truncate`, `timeout: 120`, and `config.max_concurrency: 8` are behavioral policy choices, not documentation. Add deterministic witnesses that:

1. dispatch 101 items through the migrated map and prove exactly the first 100 run and exactly one overflow warning names the map, observed count, and cap;
2. time out one branch while nested `on_error: skip` is present and prove the failure has `tolerated == false` and the join raises `MapCompletenessError`;
3. load the real graph and assert its parsed run configuration carries `max_concurrency == 8`.

Keep AC-3's nested-skip positive and missing-skip negative controls. These tests may stub the LLM, but they must compile and invoke the consumer graph contract rather than merely inspect YAML.

### R-3: Freeze the external-repository and authoring boundaries

Add a `Files` or `Surface` section stating that `graph.yaml`, `prompts/rank_stories.yaml`, `run_digest.py`, `.github/workflows/digest.yml`, and focused tests are paths in the external `sheikkinen/yamlgraph-daily-digest` repository. No digest checkout, nested repository, generated bulletin, or database may be committed into this YAMLGraph repository; this is the same boundary previously imposed for digest work (`feature-requests/FR-903-digest-archive-then-email-ordering.judgement.md:62-82`; `feature-requests/FR-905-ranked-story-boundary-validation.judgement.md:23-23`, `:78-85`).

Create and cite `feature-requests/authoring-briefs/fr-1122-daily-digest-map-contract-migration-brief.md` before enforcement. It must name the external checkout as the target and enumerate the graph and prompt artifacts. Run the canonical authoring route from the YAMLGraph checkout with the external checkout as `AUTHOR_WORKDIR`, and require the verified report at that target's `tmp/draft-authoring-report.md`; the authoring contract requires an explicit target and repo-relative authored paths (`.github/skills/graph-authoring/doctrine.md:21-29`, `:53-75`, `:92-108`; `scripts/author.sh:18-21`, `:95-114`). AC-8 must say which repository owns each implementation record, changelog artifact if the target policy requires one, and Distill entry; it must not leave “changelog fragment” repository-ambiguous.

### R-4: Make FR-1121 and release sequencing explicit

State that the FR-1122 digest PR is based on the merged FR-1121 runner/prompt changes, or is stacked with an explicit shared-file resolution. The current text assigns the ranker defect to FR-1121 but relies on its runner guard without declaring a dependency (`feature-requests/FR-1122-daily-digest-map-contract-migration.md:35-39`, `:181-199`; `feature-requests/FR-1121-daily-digest-ranker-schema-loud-failure.md:110-151`). Correct the causal claim: an untolerated map failure raises `MapCompletenessError` at the join and never returns a result to FR-1121's post-invoke `errors` guard; that guard covers error-bearing successful returns, not raised join exceptions.

Split release readiness from deployment observation. Before merge, the workflow floor must name the exact published minimum version carrying FR-1073 and FR-939, and an isolated install of that version must pass lint, compile, and focused tests. The first scheduled run and its log are a post-merge operational witness recorded afterward; they must not make a PR logically unmergeable until after it has merged.

### R-5: Record the human decision for the paid smoke

Add an explicit operator question and record its answer before enforcement:

**Q-1:** Authorize one manual `workflow_dispatch` against the exact target release, including provider spend and the digest's normal archive/email side effects, or decline it and record the exact blocked smoke while retaining deterministic acceptance.

The proposal currently schedules this paid, side-effecting run without a recorded human authorization (`feature-requests/FR-1122-daily-digest-map-contract-migration.md:187-199`). The ordinary next 06:00 UTC scheduled run needs no new spend decision; the additional manual run does.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | External `sheikkinen/yamlgraph-daily-digest/graph.yaml`: migrate `analyze_all`, declare `config.max_concurrency: 8`, and add the `gate.output` lint repair |
| D-2 | External `sheikkinen/yamlgraph-daily-digest/prompts/rank_stories.yaml`: consume flat successful analysis items |
| D-3 | External `sheikkinen/yamlgraph-daily-digest/run_digest.py`: typed map-verdict and failure reporting, composed after FR-1121 |
| D-4 | External focused tests for YAML shape, flat prompt rendering, skip/strict behavior, timeout, overflow, typed reporting, lint, and parsed concurrency |
| D-5 | External `.github/workflows/digest.yml`: minimum yamlgraph release floor only |
| D-6 | This repository: committed FR-1122 authoring brief, revised FR/judgement artifacts, implementation record, and Distill entry; target-repo changelog only if that repository's policy requires it |
| D-7 | One authorized manual smoke if Q-1 permits it, plus the next ordinary scheduled-run witness |

Not authorized: any change under `yamlgraph/`; any change under this repository's `examples/daily_digest/`; changes to map, timeout, overflow, concurrency, linter, or schema-loader semantics; a `min_success` threshold; `flatten_output`; ranker schema/error-policy work owned by FR-1121; source or `sources/*.tool.yaml` changes; a second digest binding; nested repositories or generated digest artifacts in this repository; CI, hook, judge, review, or other enforcement-infrastructure changes.

## Revised acceptance criteria

- [ ] AC-01: The external graph's `analyze_all` declares `max_items: 100`, `on_overflow: truncate`, `timeout: 120`, `failures: analysis_failures`; its nested node declares `state_key: analysis` and `on_error: skip`; no map-level `on_error` remains.
- [ ] AC-02: The external `prompts/rank_stories.yaml` contains no `_map_` token; rendering it with two flat `ArticleAnalysis` dictionaries includes both titles and accesses no generated wrapper.
- [ ] AC-03: A compiled consumer-graph fixture with three articles and one nested LLM skip returns two flat `analyzed` rows, one `MapFailure(tolerated=true)`, and a met verdict; removing nested `on_error` makes the same branch untolerated and raises `MapCompletenessError`.
- [ ] AC-04: A compiled consumer-graph fixture with one branch exceeding the configured timeout records `MapFailure(tolerated=false)` and raises `MapCompletenessError` even though the nested node declares `on_error: skip`.
- [ ] AC-05: A compiled consumer-graph fixture with 101 inputs under `max_items: 100` and `on_overflow: truncate` runs exactly the first 100 and emits exactly one warning naming `analyze_all`, 101, and 100.
- [ ] AC-06: The runner validates actual `MapVerdict` and `MapFailure` instances, prints `Analysed N of M - K skipped`, lists each failure through typed attributes, and raises loudly when the `analyze_all` verdict is absent.
- [ ] AC-07: `gate` declares `output`; on the exact target release, `yamlgraph graph lint graph.yaml` reports no E601, W013, W017, or W022.
- [ ] AC-08: Loading the real external graph retains `config.max_concurrency == 8`; its compile check passes with the collector bound.
- [ ] AC-09: The external workflow names the exact published minimum yamlgraph release carrying FR-1073 and FR-939; an isolated installation of that release passes AC-03 through AC-08 before merge.
- [ ] AC-10: FR-1121 is merged beneath this change or the stacked PR records the shared `prompts/rank_stories.yaml` and `run_digest.py` resolution; tests prove the FR-1121 error guard runs before normal post-invoke reporting, while raised map joins propagate non-zero.
- [ ] AC-11: The committed FR-1122 authoring brief names the external checkout and artifacts; the canonical route produces a non-empty target-local report with the required headings and exact lint/smoke outcomes.
- [ ] AC-12: RED and GREEN are separate commits; focused external tests pass; the FR records final status, decisions, deviations, exact target version, commit/PR identity, and artifact ownership; the Distill entry contains `**Seed:**`.
- [ ] AC-13: If Q-1 authorizes it, one manual workflow run records its run ID and relevant verdict line. After merge, the next ordinary scheduled run records its run ID and `Analysed N of M` line; this post-merge witness does not gate the merge commit.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold R-1 through R-5 verbatim in substance and record Q-1's operator decision before implementation authority activates. | GATE |
| C-2 | Do not merge or deploy against a placeholder version; the exact minimum release carrying FR-1073 and FR-939 must exist on PyPI and pass the isolated target-release checks. | GATE |
| C-3 | FR-1121 must be merged beneath FR-1122 or the stacked change must explicitly reconcile and test the shared prompt and runner surfaces. | GATE |
| C-4 | All material graph and prompt edits must use the canonical authoring route with a committed brief and verified report rooted in the external target checkout. | GATE |
| C-5 | Keep implementation inside D-1 through D-7; no YAMLGraph core, local example, source binding, ranker-policy, or enforcement-infrastructure change may ride along. | GATE |
| C-6 | The runner must consume typed map records and fail on a missing verdict; no dictionary-only assumption or success-shaped fallback is permitted. | GATE |
| C-7 | Overflow, timeout, skip/strict, flat-item, lint, concurrency, and typed-report witnesses must pass against the exact release used by the workflow. | GATE |
| C-8 | A manual provider-backed smoke may run only if Q-1 explicitly authorizes its spend and side effects; otherwise record it as blocked without weakening deterministic acceptance. | GATE |

Authority granted: after all revisions and gates are satisfied, the enforcer may migrate only the external daily digest's `analyze_all` consumer, flat ranker input, typed verdict reporting, minimum release floor, necessary gate lint repair, and focused witnesses within D-1 through D-7.
