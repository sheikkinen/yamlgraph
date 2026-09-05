# Judgement: FR-984 expose LangGraph `max_concurrency` for map fan-out from `graph.yaml` and the CLI

**Verdict:** APPROVED WITH REVISIONS — the existing LangGraph primitive is the smallest viable fix, but authority activates only after the FR dispositions the rejected FR-030 precedent, completes the public schema and graph-authoring surfaces, and removes the sibling-dependent operational run from enforcement acceptance.

**Prior art:** [FR-984-map-fan-out-max-concurrency.md](FR-984-map-fan-out-max-concurrency.md) — the subject; after this fold its `**Prior art:**` line dispositions FR-983, FR-027, FR-939, FR-069, FR-985 and [FR-030](030-map-concurrency-control.md) [Won't Fix] — the rejected precedent this judgement surfaced (R-1), distinguished by evidence: LangGraph now carries the semaphore FR-030 assumed absent. [FR-983-map-concurrency-and-census-coverage-gate.judgement.md](FR-983-map-concurrency-and-census-coverage-gate.judgement.md) — the parent SPLIT whose Successor A scope this FR inherits.

**Reviewed against:** `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `.github/skills/graph-authoring/doctrine.md`; `feature-requests/FR-984-map-fan-out-max-concurrency.md`; `feature-requests/research-briefs/fr983-map-concurrency-coverage-gate-brief.md`; `feature-requests/FR-983-map-concurrency-and-census-coverage-gate.md`; `feature-requests/FR-983-map-concurrency-and-census-coverage-gate.judgement.md`; `feature-requests/FR-985-census-coverage-floor-and-population-header.md`; `feature-requests/027-execution-safety-guards.md`; `feature-requests/030-map-concurrency-control.md`; `feature-requests/069-map-node-timeout.md`; `feature-requests/FR-939-map-overflow-policy.md`; `feature-requests/TEMPLATE.md`; `yamlgraph/compile/graph_loader.py`; `yamlgraph/compile/map_compiler.py`; `yamlgraph/cli/__init__.py`; `yamlgraph/cli/graph_run_helpers.py`; `yamlgraph/models/graph_schema.py`; `yamlgraph/utils/validators.py`; `yamlgraph/schemas/graph-v1.json`; `tests/unit/test_fr027_execution_safety.py`; `tests/unit/test_graph_commands.py`; `reference/graph-yaml.md`; `examples/demos/person_profile_census/graph.yaml`; `examples/demos/person_profile_census/README.md`; `pyproject.toml`. No operator-local logs, private-corpus artifacts, or author chat narrative were consumed.

## What is sound

The problem is real and the proposed mechanism is smaller than every alternative. The committed research record identifies a 40-task probe in which the unconfigured run peaked at 12 workers while `max_concurrency: 4` peaked at four and retained all results (`feature-requests/research-briefs/fr983-map-concurrency-coverage-gate-brief.md:54-60,135-137`). FR-984 preserves that distinction: `max_items` continues to bound population size while the new key bounds whole-invoke parallelism (`feature-requests/FR-984-map-fan-out-max-concurrency.md:40-47,89-92`). Delegating the behavior to LangGraph, rather than adding a YAMLGraph executor, semaphore, sleep, or retry path, conforms to the repository's `does_the_platform_already_do_this` and entropy rules.

The implementation seam follows established architecture. Execution-safety values already enter through the graph-level `config` mapping (`yamlgraph/compile/graph_loader.py:83-88`), CLI-over-YAML precedence already exists for `recursion_limit` (`yamlgraph/cli/graph_run_helpers.py:140-143`), and both `invoke` and `ainvoke` receive the same constructed config (`yamlgraph/cli/graph_run_helpers.py:170-184`). The proposed change therefore extends an existing boundary instead of inventing a map-specific scheduling abstraction.

Scope and strategic classification are otherwise honest. The person-profile census is a named first consumer, its `judge_items` map currently has only a population cap (`examples/demos/person_profile_census/graph.yaml:104-116`), and one demonstrated consumer correctly places the proposal in **Contrib/example** under the rubric (`.github/skills/judge-fr/doctrine.md:52-55`). The sibling coverage policy remains independently deployable, so this successor has one production concern.

The core criteria are directly testable without an LLM: load-time type rejection, parser rejection, precedence and absence semantics, and observed peak parallelism all admit deterministic witnesses (`feature-requests/FR-984-map-fan-out-max-concurrency.md:105-129`). The FR also correctly requires booleans to fail even though Python treats `bool` as an `int`, and it preserves the absent-key behavior rather than manufacturing a YAMLGraph default.

## Required revisions

### R-1: Disposition the rejected FR-030 precedent

Add `feature-requests/030-map-concurrency-control.md` to FR-984's `Prior art` field and to the alternatives disposition. State the material change in evidence: FR-030 rejected a per-map field because it believed `Send()` had no native concurrency control and therefore proposed a YAMLGraph semaphore, batching, or sequential fallback (`030-map-concurrency-control.md:31-55,77-96`); FR-984 instead exposes LangGraph's now-witnessed whole-invoke `RunnableConfig["max_concurrency"]` and adds no scheduling implementation. Also state why retry remains a workaround rather than the fix. The current claim that no rejected FR touches map concurrency is false, and rejected precedent must be dispositioned before authority (`.github/skills/judge-fr/doctrine.md:116-117`).

### R-2: Add the public graph schema to the frozen implementation surface

Add `yamlgraph/schemas/graph-v1.json` to the Proposed Solution, deliverables, and acceptance criteria. Its execution `config` block currently advertises `recursion_limit`, `max_map_items`, `max_tokens`, and `timeout` but not `max_concurrency` (`yamlgraph/schemas/graph-v1.json:289-312`). Require `max_concurrency` to be documented there as an integer with minimum `1`, and add a focused schema assertion alongside the existing FR-027 schema witnesses. Runtime loading must still explicitly reject booleans, strings, fractional values, zero, and negatives with `max_concurrency` in the diagnostic; JSON Schema publication does not replace load-boundary validation.

### R-3: Close the graph-authoring input contract before editing the census graph

Add a committed task brief under `feature-requests/authoring-briefs/fr-984-<slug>-brief.md`, cite it from FR-984, and include it in frozen scope. The graph-authoring doctrine requires an FR-bound committed brief cited by the governing FR (`.github/skills/graph-authoring/doctrine.md:26-30`), not only an invocation of `scripts/author.sh` and a temporary report. Revise AC-A08 to require that cited brief, the route-produced report, graph lint, and the narrow census smoke attempt with every blocked validation recorded honestly.

### R-4: Decouple enforcement acceptance from FR-985

Remove current AC-A11 from the acceptance checklist and record it as an authorized, non-gating post-enforcement operational observation. The parent split requires that neither successor make acceptance depend on the other (`feature-requests/FR-983-map-concurrency-and-census-coverage-gate.judgement.md:27`), while current AC-A11 can run only after both FR-984 and FR-985 are enforced (`feature-requests/FR-984-map-fan-out-max-concurrency.md:139-145`). Preserve the operator's authorization and sanitized fields, but FR-984 must be enforceable and complete on its deterministic witnesses alone. The observation may be appended later to both implementation records and must not be used to claim that FR-984 guarantees elimination of provider 429s.

### R-5: Make the behavioral concurrency witness portable and cover both invocation paths

Fix the behavioral test at `N = 2` and parameterize the compiled map witness over sync `invoke` and async `ainvoke`. For each path, use at least 40 Python-tool items and a thread-safe active/peak counter; assert configured peak `<= 2`, unconfigured peak `> 2`, and exact result completeness. Current AC-A04 leaves `N` unconstrained, so an implementation could choose an `N` that makes the control assertion impossible, and AC-A05 proves only that one builder supplies both paths even though LangGraph executes those paths through separate runtime executors (`yamlgraph/cli/graph_run_helpers.py:170-184`). The revised witness must test the promised behavior, not merely config shape.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 — load-boundary contract | `yamlgraph/compile/graph_loader.py`; focused `GraphConfig` tests for absent, valid, and invalid values |
| D-2 — CLI and run config | `yamlgraph/cli/__init__.py`; `yamlgraph/cli/graph_run_helpers.py`; parser, omission, YAML fallback, and CLI-precedence tests |
| D-3 — behavioral witness | One focused compiled-map test fixture covering sync and async execution with Python tools only |
| D-4 — published configuration schema | `yamlgraph/schemas/graph-v1.json`; focused schema assertion |
| D-5 — reference documentation | `reference/graph-yaml.md`, documenting whole-invoke scope, positive-integer contract, CLI precedence, and absent-key semantics |
| D-6 — first consumer | `examples/demos/person_profile_census/graph.yaml` with `config.max_concurrency: 4`; `examples/demos/person_profile_census/README.md` with override syntax |
| D-7 — governed graph authoring | Cited committed `feature-requests/authoring-briefs/fr-984-<slug>-brief.md`; route-produced `tmp/draft-authoring-report.md`; lint and smoke evidence |
| D-8 — traceability and lifecycle | `capabilities/CAP-262-map-fan-out-concurrency.yaml`; `REQ-YG-645`; regenerated `ARCHITECTURE.md`; one fix changelog fragment; FR implementation record; diary reflection |
| D-9 — non-gating observation | One authorized combined corp run after FR-984 and FR-985, recorded only when available with sanitized concurrency, 429, population, coverage, and terminal-result fields |

Not authorized: a per-map-node `concurrency` field; a YAMLGraph-owned executor, semaphore, batching loop, sleep, or retry mechanism; provider retry-policy or retry-count changes; changes to LangGraph; `max_items` or overflow-policy changes; census coverage-floor, reducer, renderer, prompt, or artifact-integrity changes; dependency-floor changes; concurrency defaults when the key is absent; any other demo migration; or any committed private/corp identifier.

## Revised acceptance criteria

- [ ] AC-01: RED first: loading a graph with absent `config.max_concurrency` yields `GraphConfig.max_concurrency is None`, and a positive integer is retained; YAML boolean, string, fractional, zero, and negative values fail during load with `max_concurrency` in the diagnostic.
- [ ] AC-02: the run-config builder omits `max_concurrency` when neither CLI nor YAML supplies it, uses the YAML value when CLI is absent, and uses the CLI value when both are present.
- [ ] AC-03: `--max-concurrency` accepts a positive integer; zero and negative values fail argument parsing before graph invocation and the diagnostic names `--max-concurrency`.
- [ ] AC-04: `yamlgraph/schemas/graph-v1.json` publishes `config.max_concurrency` as an integer with minimum `1`, and a focused test asserts that contract.
- [ ] AC-05: one compiled YAMLGraph map over at least 40 Python-tool items is parameterized over sync `invoke` and async `ainvoke`; with `N = 2`, a thread-safe counter records peak `<= 2`, the unconfigured control records peak `> 2`, and both paths return every expected result without an LLM.
- [ ] AC-06: `reference/graph-yaml.md` documents that the key applies to the whole invocation and all parallel branches, accepts only positive integers, is overridden by the CLI value, and is omitted entirely when absent.
- [ ] AC-07: the person-profile census graph sets `config.max_concurrency: 4`, and its documented invocation shows `--max-concurrency 2` as override syntax without changing census policy.
- [ ] AC-08: FR-984 cites a committed graph-authoring task brief; the graph edit is produced through the governed route; the report names the graph and README artifacts; graph lint passes; the narrow smoke is attempted and its exact outcome or blocker is recorded.
- [ ] AC-09: `CAP-262-map-fan-out-concurrency.yaml` and `REQ-YG-645`, re-verified against `origin/main` at push, cover every changed production branch; every new test carries the REQ marker; regenerated `ARCHITECTURE.md` and `python scripts/req_coverage.py --strict` pass.
- [ ] AC-10: FR status and implementation decisions, one `fix` changelog fragment, and `docs/diary/diary-<date>-reflection-fr-984-<slug>.md` with a `Seed:` are committed.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | R-1 through R-5 are folded into FR-984 and the status records human review of this judgement before implementation authority activates. | GATE |
| C-2 | RED witnesses are committed before GREEN implementation; import, collection, or missing-fixture failures do not count as RED. | GATE |
| C-3 | An absent YAML and CLI value produces no `max_concurrency` key in `RunnableConfig`; no YAMLGraph default is introduced. | GATE |
| C-4 | Runtime validation and the published JSON schema agree on a positive integer contract, with booleans explicitly rejected at load. | GATE |
| C-5 | The compiled-map witness exercises both sync and async behavior and proves result completeness as well as the concurrency ceiling. | GATE |
| C-6 | Throttling remains wholly delegated to LangGraph; no YAMLGraph scheduling, semaphore, sleep, pool, batching, or retry implementation is added. | GATE |
| C-7 | The census graph edit follows the graph-authoring doctrine using the cited committed brief, report, lint, and smoke record. | GATE |
| C-8 | The authorized private-corpus observation does not gate FR-984 completion, does not occur before both successors are enforced, commits no private identifier, and is reported without promising a particular 429 or coverage outcome. | GATE |

Authority granted: after human review and mechanical folding of R-1 through R-5, implementation is authorized only for the frozen whole-invoke `max_concurrency` exposure, its schema/docs/tests, and the named census first-consumer configuration.

## Human review — 2026-09-04

Draft rendered by the sole route (`scripts/judge.sh`, backend `copilot`,
`gpt-5.6-sol`) in the FR worktree; folded verbatim above. Each revision
was verified against the cited file before folding:

- **R-1 verified.** `feature-requests/030-map-concurrency-control.md`
  exists, `Status: Won't Fix`, closed 2026-02-14, and states "LangGraph's
  `Send()` doesn't natively support concurrency limits." The author's
  REJECTED sweep grepped `FR-*.md` and missed early FRs named `0NN-*.md`
  — a real sweep defect, now recorded in the FR. Distinguishing fact
  folded: the platform primitive exists in v1.2.9 and this FR adds no
  scheduler.
- **R-2 verified.** `yamlgraph/schemas/graph-v1.json:289-312` lists
  four `config` keys, no `max_concurrency`. Added to scope and AC-04.
- **R-3 done.** Brief committed at
  `feature-requests/authoring-briefs/fr-984-census-max-concurrency-brief.md`,
  cited from the FR; AC-08 revised.
- **R-4 done.** AC-A11 removed from criteria; retained as a non-gating
  observation with the operator's 2026-09-04 authorization intact.
- **R-5 done.** AC-05 fixes `N = 2` and parameterizes over `invoke` /
  `ainvoke`.
- No finding falsified. Authority is active for the frozen scope.
