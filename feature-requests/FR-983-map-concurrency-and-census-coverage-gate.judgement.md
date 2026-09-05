# Judgement: FR-983 expose `max_concurrency` for map fan-out and gate the census brief on classification coverage

**Verdict:** SPLIT — the LangGraph run-configuration primitive and the person-profile census artifact-integrity policy are independently useful, deployable, and testable concerns; neither requires the other, so no implementation authority is granted until each re-enters judgement as its own FR.

**Prior art:** [FR-983-map-concurrency-and-census-coverage-gate.md](FR-983-map-concurrency-and-census-coverage-gate.md) — the subject; its own `**Prior art:**` line dispositions FR-962, FR-943, FR-939/FR-027, FR-069, FR-895 and the `recursion_limit` plumbing. [FR-967-unwitnessed-acceptance-criteria.judgement.md](FR-967-unwitnessed-acceptance-criteria.judgement.md) — the same SPLIT shape two days earlier on the same demo (retrospective witness vs. repository-wide gate); precedent for apportioning one incident across two successors. No REJECTED FR touches map concurrency or census coverage.

**Reviewed against:** `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `feature-requests/FR-983-map-concurrency-and-census-coverage-gate.md`; `feature-requests/FR-962-person-profile-census-authored-prs.md`; `feature-requests/FR-943-census-row-failure-containment.md`; `feature-requests/FR-895-census-synthesize-tail.md`; `yamlgraph/compile/graph_loader.py`; `yamlgraph/cli/__init__.py`; `yamlgraph/cli/graph_run_helpers.py`; `examples/demos/person_profile_census/graph.yaml`; `examples/demos/person_profile_census/tools.py`. The FR-cited `research-briefs/fr983-map-concurrency-coverage-gate-brief.md` was also checked in the committed tree but is absent, despite the claim at FR-983 lines 13-20 that it is committed.

## What is sound

The incident and causal chain are concrete. FR-983 lines 42-108 distinguishes population size from fan-out width, records the observed 159/259 completion and 56.8% classification coverage, and identifies the artifact-integrity failure: the ledger reports coverage while the human-facing brief does not. The existing graph corroborates the seam: `judge_items` is a map with `on_error: skip` (`examples/demos/person_profile_census/graph.yaml:104-123`), followed by reducer, preparation, synthesis, and rendering as distinct stages (`graph.yaml:125-150`).

The proposed concurrency implementation is deliberately thin and follows established architecture. Graph-level execution settings are already loaded from `config:` (`yamlgraph/compile/graph_loader.py:83-88`), CLI precedence is already implemented for `recursion_limit` (`yamlgraph/cli/graph_run_helpers.py:140-143`), and the corresponding option is declared in the graph-run parser (`yamlgraph/cli/__init__.py:99-104`). FR-983 AC-01 through AC-04 (lines 172-185) provide both plumbing witnesses and a real behavioral concurrency witness rather than merely asserting config shape.

The coverage policy is also located at the correct deterministic boundary. The reducer already computes `classification_coverage` (`examples/demos/person_profile_census/tools.py:302-344`) and calls the canary before opening artifact paths (`tools.py:458-460`); `prepare_brief_input` then deliberately excludes non-judged rows and truncates to `BRIEF_TOP_N` (`tools.py:544-573`). A code-generated population stamp in `render_brief` avoids asking the model to reconstruct arithmetic it never receives. This preserves FR-943 containment while governing its aggregate consequence, as FR-983 lines 144-168 intends.

The alternatives record has substance: it compares eight actual solution classes, preserves disagreement, dispositions precedent, and answers `is_this_a_graph` (FR-983 lines 220-237). Scope exclusions such as per-map concurrency, a yamlgraph-owned semaphore, second-pass retries, `max_items` changes, and prompt-authored coverage are appropriately rejected or deferred.

Measurability and testability are strong overall. Most criteria name an exact input, output, assertion, or command (FR-983 lines 172-217), and the proposed failure paths can be condemned without an LLM. Architecture alignment is likewise strong: D-1 exposes an existing LangGraph primitive rather than duplicating it, while D-2 remains local to the demo reducer and renderer.

## Required revisions

### R-1: Split the proposal into two independently judged feature requests

Create one successor FR containing only D-1, the graph-level and CLI `max_concurrency` plumbing, documentation, behavioral map witness, first-consumer graph setting, capability/requirement registration, and its changelog/diary obligations. Create a second successor FR containing only D-2, the person-profile census coverage floor, pre-artifact failure, deterministic population header, demo documentation, containment regression witnesses, capability/requirement registration, and its changelog/diary obligations.

The incident may cross-reference both successors, but neither successor may make its acceptance depend on implementation of the other. The split is mandatory under the single-responsibility rule at `.github/skills/judge-fr/doctrine.md:49-50`: the runtime knob can ship without the census gate, and the census can refuse misleading partial output under today's concurrency behavior.

### R-2: Classify each successor honestly

Classify D-1 as **Contrib/example** unless its successor cites at least three concrete use cases. The current FR names one actual consumer, while the rubric reserves **Framework primitive** for three or more use cases (`.github/skills/judge-fr/doctrine.md:52-55`). The implementation may still be a small core exposure because the existing abstraction has a configuration gap; the strategic classification must not claim evidence the FR does not contain.

Classify D-2 as **Contrib/example**: it is a policy and rendering correction for the person-profile census, built on the existing reducer/synthesize-tail abstractions.

### R-3: Repair the committed-evidence audit trail

Commit `research-briefs/fr983-map-concurrency-coverage-gate-brief.md` with the content and preflight properties claimed at FR-983 lines 13-20 before either successor is judged, and cite that committed artifact from both successor FRs where relevant. A stated-but-absent evidence artifact cannot be part of the judge's closed input. Preserve the in-body alternatives table; it is substantive and should be apportioned between successors rather than discarded.

### R-4: Freeze the coverage value contract and render data path

In the coverage successor, define `min_coverage` as an invocation value accepted from `--var`, defaulting in the reducer to `1.0`. Parse it once at the reducer boundary and reject booleans, non-numeric values, non-finite values, and values outside inclusive `[0.0, 1.0]` with an error naming `min_coverage`.

Specify that the coverage gate runs after `_canary_gate` and before any ledger, JSONL, metadata, claims, or brief artifact is opened or written. Specify that `render_brief` reads `judged`, `total`, and `row_failed` from `state["ledger"]["rollup"]` or an equivalently typed reducer-owned structure; it must not recompute those values from the bounded top-N `brief_input`. This closes the currently implicit data path between FR-983 lines 144-168 and `tools.py:544-573`.

### R-5: Correct the acceptance witness for stage ordering

Replace current AC-06. `reduce_pr_ledger` does not produce `brief_input`; `prepare_brief_input` is a later graph node (`examples/demos/person_profile_census/graph.yaml:125-133`). The revised witness must invoke the compiled graph or explicitly spy on `prepare_brief_input` and prove that sub-threshold coverage raises in `reduce_pr_ledger`, no downstream prepare/synthesize/render stage runs, and no output artifact exists.

### R-6: Validate both YAML and CLI concurrency inputs

In the concurrency successor, require the same positive-integer contract at both entry points. YAML `0`, negative values, booleans, and non-integers must fail during graph loading with `max_concurrency` in the message. CLI `0` and negative values must fail argument validation before graph invocation with `--max-concurrency` in the diagnostic. An absent value must omit the key from `RunnableConfig`; a CLI value must override YAML.

### R-7: Put the paid corp rerun behind an explicit human decision

Do not silently make provider spend and private-corpus access an implementation gate. In each successor, separate deterministic acceptance from the optional combined operational witness. Record this explicit question for the operator: **Does the operator authorize the paid private-corpus rerun after both successors are enforced?**

If authorized, retain the sanitized evidence requirements from current AC-10 and record exact 429 count, discovered/classified/failed counts, coverage, configured concurrency, and whether the run completed or failed closed. If not authorized, deterministic tests remain the enforcement gate and the FR must state that the live witness was not run; it must not claim operational quota improvement.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| Successor A — concurrency config | `yamlgraph/compile/graph_loader.py`, `yamlgraph/cli/__init__.py`, `yamlgraph/cli/graph_run_helpers.py`, focused unit tests, one compiled-map behavioral fixture, `reference/graph-yaml.md`, the person-profile census `max_concurrency: 4` setting and invocation documentation, one capability/REQ, changelog fragment, FR status, diary |
| Successor B — census coverage integrity | `examples/demos/person_profile_census/tools.py`, the minimum graph state/configuration needed to expose `min_coverage`, focused reducer and compiled-path tests, person-profile census README/demo output, one capability/REQ, changelog fragment, FR status, diary |
| Shared evidence only | Committed FR-983 research brief and sanitized optional operational witness; no shared production implementation |

Not authorized: implementation under FR-983; per-map-node concurrency; a yamlgraph semaphore or sleep-based throttle; changes to LangGraph; retry-policy or retry-count changes; second-pass failed-row replay; `max_items` changes; removal or weakening of FR-943 row containment; synthesis-prompt changes; coverage inferred by the LLM; changes to `BRIEF_TOP_N` selection; coverage gates in other census demos; or any private/corp identifier committed to the repository.

## Revised acceptance criteria

### Successor A — map fan-out concurrency

- [ ] AC-A01: RED first: a `GraphConfig` test proves absent `config.max_concurrency` yields `None`, a positive integer is retained, and YAML `0`, negative, boolean, string, and fractional values fail at load with `max_concurrency` in the message.
- [ ] AC-A02: `_build_run_config` omits `max_concurrency` when neither CLI nor YAML supplies it, uses the YAML value when CLI is absent, and uses the CLI value when both are present.
- [ ] AC-A03: `--max-concurrency` accepts a positive integer; `0` and negative values fail parser validation before invocation and name the option.
- [ ] AC-A04: a compiled yamlgraph map over at least 40 Python-tool items records peak parallelism through a thread-safe counter; configured `N` produces peak `<= N`, the unconfigured control produces peak `> N`, and both produce all expected results without an LLM.
- [ ] AC-A05: sync and async invocation paths are covered if they have separate run-config builders; otherwise a test proves they share the one tested builder.
- [ ] AC-A06: `reference/graph-yaml.md` documents scope, positive-integer validation, YAML/CLI precedence, and absence semantics.
- [ ] AC-A07: the person-profile census graph sets `config.max_concurrency: 4`, and its documented invocation includes `--max-concurrency` override syntax.
- [ ] AC-A08: the graph change has the required graph-authoring report, lint, and smoke evidence.
- [ ] AC-A09: one successor-specific capability and REQ cover the production branches; every test carries that REQ marker; regenerated `ARCHITECTURE.md` and `python scripts/req_coverage.py --strict` pass.
- [ ] AC-A10: successor FR status/implementation record, one fix changelog fragment, and diary reflection are committed.

### Successor B — person-profile census coverage gate

- [ ] AC-B01: RED first: a 10-row reducer fixture with 3 `row_failed` rows fails at the default floor `1.0`, passes at `min_coverage="0.7"`, and its failure names coverage, floor, failed count, and total count.
- [ ] AC-B02: `min_coverage` defaults to `1.0`; booleans, non-numeric strings, NaN, infinities, negatives, and values above `1.0` fail with `min_coverage` in the diagnostic; inclusive `0.0` and `1.0` boundaries are tested.
- [ ] AC-B03: the coverage gate runs after the existing canary and before opening or writing ledger, JSONL, run metadata, claims, or brief artifacts.
- [ ] AC-B04: a compiled-path witness with 100 of 259 rows failed proves `reduce_pr_ledger` raises, `prepare_brief_input`, `synthesize`, and `render_brief` do not run, and no output artifact exists.
- [ ] AC-B05: when coverage meets the floor, `render_brief` reads reducer-owned population statistics rather than bounded `brief_input` and writes this exact first-line shape: `> Population: {judged}/{total} PRs classified ({coverage:.1%}); {failed} row_failed. Brief synthesized from top {BRIEF_TOP_N} judged rows by delta.`
- [ ] AC-B06: a known-count fixture asserts the exact first line and proves the header precedes model-authored content.
- [ ] AC-B07: existing FR-943 witnesses remain green: one attributable map failure still becomes one `row_failed` ledger row and does not abort fan-out; structural failures remain fatal.
- [ ] AC-B08: person-profile census documentation states the default fail-closed behavior and shows explicit `--var min_coverage=...` acceptance of a partial population; smoke output is regenerated without corp identifiers.
- [ ] AC-B09: the graph change has the required graph-authoring report, lint, and smoke evidence.
- [ ] AC-B10: one successor-specific capability and REQ cover the production branches; every test carries that REQ marker; regenerated `ARCHITECTURE.md` and `python scripts/req_coverage.py --strict` pass.
- [ ] AC-B11: successor FR status/implementation record, one fix changelog fragment, and diary reflection are committed.
- [ ] AC-B12: only after explicit operator authorization, a combined private-corpus run records sanitized configured concurrency, 429 count, discovered/classified/failed counts, coverage, and terminal result; without authorization, the implementation record explicitly says the operational witness was not run and makes no quota-improvement claim.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Both successor FRs exist, contain the apportioned research and prior-art dispositions, and receive independent judgements before their respective implementation begins. | GATE |
| C-2 | The missing committed research brief is repaired before successor judgement. | GATE |
| C-3 | RED witnesses are committed before each successor's GREEN implementation; import or fixture failures do not count as RED. | GATE |
| C-4 | Any material edit to `examples/demos/person_profile_census/graph.yaml` follows the repository's graph-authoring route and carries its report. | GATE |
| C-5 | The coverage successor fails before all artifact writes and obtains population statistics from reducer-owned full-population data, never from top-N synthesis input. | GATE |
| C-6 | The concurrency successor delegates throttling to LangGraph and introduces no yamlgraph-owned executor, semaphore, sleep, or retry mechanism. | GATE |
| C-7 | No paid private-corpus rerun occurs without explicit operator authorization, and no corp identifier appears in committed evidence. | GATE |

Authority granted: none under FR-983; only the two frozen successor scopes may seek authority through separate plan → judge → enforce cycles.

## Human review — 2026-09-04

Draft rendered by the sole route (`scripts/judge.sh`, backend `copilot`,
`gpt-5.6-sol`, session `cb7b8cc5`) in the FR worktree; folded verbatim
above with these dispositions:

- **SPLIT accepted.** Successor A is filed as
  [FR-984-map-fan-out-max-concurrency.md](FR-984-map-fan-out-max-concurrency.md);
  Successor B as
  [FR-985-census-coverage-floor-and-population-header.md](FR-985-census-coverage-floor-and-population-header.md).
  Each carries its apportioned alternatives rows, R-2 classification
  (Contrib/example), and the revised AC list from this judgement.
- **R-3 falsified.** The brief
  `research-briefs/fr983-map-concurrency-coverage-gate-brief.md` is
  committed at `9a490c8c` on the FR branch (`git ls-files` lists it;
  `git log -1 -- <path>` returns that commit). The judge read the main
  checkout, where an unmerged branch's files are invisible. C-2 is
  therefore already satisfied; no repair action. Recorded as a judge
  input-closure hazard: a judge run inside a worktree must resolve
  "committed" against that worktree's HEAD, not the repository root.
- **R-7 answered by the operator:** the paid private-corpus rerun is
  **authorized**, to run once after both successors are enforced;
  AC-A/AC-B12 evidence requirements stand.
- Every other revision (R-1, R-2, R-4, R-5, R-6) is adopted without
  change; R-5 corrects a real error in the original AC-06 (wrong stage
  named).
