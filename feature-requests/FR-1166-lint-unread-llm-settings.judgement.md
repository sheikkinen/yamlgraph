# Judgement: FR-1166 Lint LLM settings written where yamlgraph never reads them

**Prior art:** dispositioned in the subject FR header ([FR-1166](FR-1166-lint-unread-llm-settings.md) — FR-1144, FR-1165, FR-071); FR-1124 (on_error default), FR-854 (WITHDRAWN, subagent classification) and FR-898 (video) share only generic nouns; no REJECTED FR in this territory.

**Verdict:** APPROVED WITH REVISIONS — the lint-only correction is justified, but research disposition, runtime-preserving sharing, diagnostic fixes, and unconditional acceptance witnesses must be folded into the FR before authority activates.

**Reviewed against:** Committed inputs at `c7f3ff31977cd6a988da6b99ebf19d49646911f0`: `feature-requests/FR-1166-lint-unread-llm-settings.md`; `feature-requests/FR-1166.research.md`; `feature-requests/research-briefs/lint-unread-llm-keys.md`; `feature-requests/FR-1144-race-node-thinking-budget.md` (lines 150-205) and its judgement; `feature-requests/FR-1165-config-max-tokens-refused.md` (lines 100-157) and its judgement; `feature-requests/FR-071-thinking-budget-graph-level.md` (lines 1-80); `feature-requests/FR-230-google-vertex-thinking-budget.md` (lines 1-80); `feature-requests/FR-232-race-node-type.md` (lines 1-150); `feature-requests/FR-272-router-node-race-candidates.md` (lines 1-160); `yamlgraph/node_factory/llm_nodes.py` (lines 1-260); `yamlgraph/node_factory/race_node.py` (lines 175-420); `yamlgraph/node_factory/router_race_node.py` (lines 1-95); `yamlgraph/models/node_schema.py` (lines 330-415); `yamlgraph/executor_base.py` (provider/model references and lines 180-219); `yamlgraph/linter/checks_providers.py`; `yamlgraph/linter/checks_prompts.py` (lines 1-270); `yamlgraph/linter/checks.py` (lines 1-138); `yamlgraph/linter/graph_linter.py` (lines 111-220); `reference/graph-yaml.md` (metadata/lint-code search); `docs/demos/linter.md` (lines 1-170); `.importlinter`; `.github/copilot-instructions.md`; `CLAUDE.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`. The working tree was clean when inputs were checked. No csap checkout, author transcript, uncommitted notes, external website, or additional judge execution was consumed. Downstream observations are assessed as committed FR/brief evidence, not independently reproduced facts.

## What is sound

The strongest case against this proposal is that free-form metadata may deliberately contain descriptive settings, while lint-only enforcement does not protect authors who skip lint. A csap-only migration would be smaller. Nevertheless, the FR identifies a repeated misplaced-setting incident and dispositions the earlier prose-only follow-up (`FR-1166:44-65,164-177`). A warning, not a new metadata configuration route or a load failure, is proportionate to that evidence. The judgement does not treat the reported 95% race-win rate as a measured causal proof.

| Rubric criterion | Finding and evidence |
|---|---|
| Scope | The three locations share one silent-placement defect; new warning codes and shared setting names are bounded (`FR-1166:28-36,111-135`). The universal Ideal Result and implementation-time escape branches overstate that boundary (`FR-1166:73-79,90-93`); R-2 narrows them. |
| Consistency | The no-runtime-change promise is valuable (`FR-1166:134-135`), but `max_tokens` and `effort` are not forwarded by the shared race builder (`race_node.py:189-207`; `router_race_node.py:67-71`). A generic node/default fix must not imply that they are. R-3/R-4 resolve this. |
| Measurability | Warning codes, locations, and negative controls are assertable (`FR-1166:139-148`). Optional prompt coverage and an unspecified external checkout prevent a stable acceptance contract (`FR-1166:141-153`); R-2/R-5 remove those ambiguities. |
| Feasibility | Existing prompt checks already resolve paths and parse referenced YAML (`checks_prompts.py:150-174`), and public lint already runs those checks (`graph_linter.py:134-146`). No standalone prompt-lint command or dependency is needed. |
| Architecture alignment | Reuse `LintIssue`, raw-YAML checks, and prompt-path helpers (`checks.py:51-106`). A linter import of the proposed runtime module would reach forbidden executor/factory dependencies (`llm_nodes.py:15`; `.importlinter:16-33`); a pure lower-layer declaration is required. |
| Single responsibility | W072 and W073 both expose ignored configuration at author time. Sharing names, documentation, and traceability support that concern; no SPLIT is required. Load refusal or new race-setting support would be a different contract change (`FR-1166:172-191`). |
| Strategic classification | **Pattern documentation / existing-linter contract extension**, not a new framework primitive. Existing lint, prompt discovery, and candidate traversal abstractions suffice; three placements are not three independently evidenced use cases (`FR-1166:44-71`; `checks_prompts.py:150-174`). This classification still permits the narrowly scoped check implementation. |
| Testability | Direct RED witnesses can call public lint on temporary YAML without providers. The current setting-list witness covers only regular LLM resolution, not race forwarding or truthful fixes (`FR-1166:147-148`); R-3 through R-5 close those false-green paths. |

The research is not absent or a strawman: it contains shared declarations, source introspection, migration-only, and location-schema alternatives, with load refusal added in the FR (`FR-1166.research.md:22-26`; `FR-1166:172-177`). However, duplicate persona rows, erroneous subtractionist placement advice, conflicting graph answers, and missing precedent line references need a disposition note before authority. This is not measurement tooling; the metric raw-output gate does not apply.

## Required revisions

### R-1: Disposition solution classes and correct research claims

Fold a five-class alternatives table into the FR or linked research record: shared declarative names with narrow lint warnings; source introspection; csap-only migration with no new check; broad location-schema validation; load-time refusal. Merge the os-infra and data-process rows as one class, preserve their original text and disagreement, and add adopt/reject/park decisions with concrete committed file/line precedents.

Explicitly reject the subtractionist row's suggestion to put tuning on candidate dictionaries: only provider/model are read there (`FR-1166.research.md:25`; `race_node.py:201-206`). Correct the disposition of the `is_this_a_graph` answers: this work extends a deterministic analyzer, not an LLM orchestration graph; analyzing graph-shaped input does not require implementing a graph. Do not count persona convergence labels as independent solution classes or treat the actionlint URL as verified implementation evidence. Existing committed code and FR precedents suffice; no new research run is required. This satisfies the substance requirement in `judge-fr/doctrine.md:118-127`.

### R-2: Freeze warning severity and referenced-prompt coverage

Keep W072 and W073 as warnings. Remove the candidate-load-refusal branch and record refusal as rejected for this FR because it changes loading behavior beyond the selected lint-only correction (`FR-1166:93,172-185`). No-known-csap-user evidence is not proof that other consumers do not exist.

Remove the prompt-reachability deferral branch and conditional AC (`FR-1166:87,92,141-142`): existing discovery parses referenced prompts already (`checks_prompts.py:150-174`). Require graph metadata and metadata of existing prompts referenced by the graph's nodes, using the current prompt-path resolution rules. Leave standalone/unreferenced prompt scanning, recursive discovery beyond existing traversal, and undocumented top-level prompt tuning keys to separate work. Narrow the Ideal Result to the four named tuning keys at the two metadata locations and all extra candidate keys at the two race forms; do not promise every written setting is applied or diagnosed everywhere.

### R-3: Share names without importing runtime modules or changing resolution

Replace the tentative runtime-module placement with one pure declaration in `yamlgraph/constants.py`, consumed by the new lint check and the existing regular-LLM/direct-race resolution sites. Do not import `llm_nodes`, `race_node`, an executor, or `llm_factory` into lint, and do not weaken `.importlinter` (`.importlinter:16-33`).

Keep the initial tuning set exactly `thinking_budget`, `temperature`, `max_tokens`, and `effort`. Record the scope inventory: regular LLM resolution handles all four (`llm_nodes.py:120-125,155-158`); direct and router races forward only temperature and thinking budget (`race_node.py:201-206,347-353`; `router_race_node.py:67-71`). Do not add race forwarding for max_tokens/effort.

Require behavior witnesses, not source-text matching, for the sharing change. Preserve absent values, explicit zero, explicit null, and node/default overrides exactly as current code treats them. In particular, `max_tokens` uses `dict.get(key, default)` and explicit node null suppresses the default, whereas thinking budget and effort use null-as-inherit resolution (`llm_nodes.py:156-158`). Preserve each path's temperature fallback behavior instead of replacing every setting with one generic precedence policy. A registry rename/removal must break a behavior witness; a test that only loops over the remaining registry cannot detect omissions.

### R-4: Make fixes truthful for the specific key and execution path

Require W072 to name the graph or referenced prompt, the metadata key, and `defaults.<key>` as the canonical location, with applicability wording for max_tokens/effort that does not promise race support. Require W073 to identify node, zero-based candidate index, and every extra key, including non-setting keys.

For candidate temperature/thinking_budget, suggest moving the key onto the node or under defaults. For candidate max_tokens/effort, say the current race path does not apply that setting and remove the unsupported candidate key; do not claim moving it to a race node/defaults will fix it. For arbitrary keys, suggest removal and state the provider/model-only contract, not `defaults.<arbitrary-key>`. These cases follow directly from the all-extra-key promise (`FR-1166:124-129`) and current forwarding (`race_node.py:201-206`).

Do not fix the adjacent missing race max_tokens/effort support here. Add it to the FR's parked findings if desired; this judgement authorizes diagnostics only.

### R-5: Define traceability, witnesses, and reproducible validation

Name `docs/demos/linter.md` as the lint-code reference and `reference/graph-yaml.md` as the metadata contract document (`FR-1166:131-132`; `docs/demos/linter.md:126-146`). Before production edits, select and record an unused CAP/REQ pair in the FR, create its capability YAML, regenerate `ARCHITECTURE.md`, and tag every new test with that REQ. A new REQ entry alone is insufficient (`FR-1166:154-155`; `.github/copilot-instructions.md:170-172`).

Assign focused new lint witnesses to `tests/unit/test_fr1166_lint_unread_llm_settings.py`; use the existing LLM, direct-race, and router-race test files for resolution/forwarding preservation. Require public-lint/CLI registration witnesses in addition to check-function tests, and parameterize the cases below.

Specify the csap read-only validation command, exact graph path, yamlgraph revision, csap revision, prompt root, and outcome in Implementation Status. Resolve the FR's four-graph inventory versus three-graph probe by naming the three probe targets explicitly (`FR-1166:44-49,89`). If that committed csap revision is unavailable, record the missing dependency plainly and use a committed, self-contained reproducer of the cited placement for local acceptance; do not access or report another repository's dirty working tree as the cited revision. No csap edits are authorized.

Record before/after lint census results per graph, not an aggregate clean-suite requirement: list each new W072/W073 as fixed or explicitly dispositioned. Governed example fixes must use the authoring route already required by the FR; an intentional metadata annotation may remain with an explicit rationale, without changing warning detection. Add the exact verification commands below and a scoped Distill entry with **Seed:** to the implementation deliverables.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `yamlgraph/constants.py`: one pure tuning-name declaration; minimal name-sharing edits to `yamlgraph/node_factory/llm_nodes.py` and `yamlgraph/node_factory/race_node.py`, preserving runtime values and forwarding |
| D-2 | `yamlgraph/linter/checks_providers.py` and/or `yamlgraph/linter/checks_prompts.py`, with registration in `yamlgraph/linter/graph_linter.py`: W072/W073 using existing path helpers |
| D-3 | `tests/unit/test_fr1166_lint_unread_llm_settings.py`; focused preservation witnesses in existing LLM/direct-race/router-race test files |
| D-4 | One new `capabilities/CAP-<unused-id>-lint-unread-llm-settings.yaml`, its recorded REQ, and regenerated `ARCHITECTURE.md` |
| D-5 | `docs/demos/linter.md` and `reference/graph-yaml.md`: warning codes, non-config metadata, and truthful candidate guidance |
| D-6 | FR/research disposition and implementation record; one `changelog/unreleased/` fragment; one scoped `docs/diary/` Distill entry with **Seed:** |
| D-7 | Only census-proven misplaced settings in shipped examples, through the sole graph-authoring route, with exact paths and outcomes recorded |

Not authorized: reading metadata at runtime; candidate/schema/load refusal; per-candidate tuning; adding max_tokens/effort forwarding to races; provider factories or setting semantics; new introspection machinery; standalone prompt lint; broad unknown-key validation; top-level prompt tuning remediation; new provider/model metadata warnings; csap migrations or pin changes; CI/hooks/import-contract changes; unrelated example cleanup.

## Revised acceptance criteria

- [ ] AC-01: Through public `lint_graph` and a CLI registration witness, each of the four tuning keys in graph metadata produces warning W072 with graph location, key, and `defaults.<key>`. Values `0` and `null` are detected by key presence, not truthiness.
- [ ] AC-02: Each of those keys in an existing node-referenced prompt's metadata produces W072 with prompt identity, key, and canonical location. Witnesses cover graph-relative configured prompts and the existing project-root prompt resolution. Prompt coverage is not optional.
- [ ] AC-03: Non-setting metadata keys such as owner/description and legitimate prompt top-level provider/model produce no W072/W073. Existing missing-prompt diagnostics remain intact, without a new setting warning fabricated for an absent file.
- [ ] AC-04: Direct race and router-with-candidates each emit W073 for every extra candidate key, including thinking_budget, temperature, max_tokens, effort, and an arbitrary key. Messages identify node and candidate index. Provider-only, model-only, and provider-plus-model candidates produce no W073.
- [ ] AC-05: W073 fixes relocate temperature/thinking_budget; max_tokens/effort fixes state current race non-support; arbitrary-key fixes request removal. W072 guidance does not promise race support for max_tokens/effort. Both new codes remain warnings and introduce no load refusal.
- [ ] AC-06: One pure shared tuning-name declaration drives lint membership and the named runtime resolution sites. Behavior witnesses verify all four regular-LLM settings independently, plus temperature/thinking_budget forwarding through direct and router races. Absent/default/node/null/zero cases retain current semantics, and no additional setting is forwarded to candidates.
- [ ] AC-07: Defect-specific tests fail in RED because W072/W073 are absent, not because imports/fixtures fail; git history records RED before GREEN. Runtime-preservation witnesses need not fail in RED. Every new test uses the recorded REQ, the capability YAML exists, and strict requirement coverage passes.
- [ ] AC-08: `lint-imports` passes without contract edits. Record passing focused pytest selectors for the new lint file and touched resolver/race tests, `pytest tests/unit/ -q --no-cov -m "not slow" -n 4`, and `python scripts/req_coverage.py --strict`. Existing ruff check/format checks pass for touched Python; record scoped radon/vulture findings as context, not an unrelated cleanup mandate.
- [ ] AC-09: Enumerate and lint all graph configurations under examples/ and graphs/ before and after; record new W072/W073 by path/key as fixed or dispositioned. Any governed artifact correction has authoring-route and lint/smoke evidence; no suppression of the new checks is introduced.
- [ ] AC-10: Record read-only lint of the cited csap graph/revision with W072 and its defaults.thinking_budget fix, or explicitly record csap unavailability and provide the committed self-contained placement reproducer and its public-lint result. Do not claim external validation when only the reproducer ran.
- [ ] AC-11: The named docs contain W072/W073 and their placement/applicability guidance; a changelog fragment names FR-1166 and the recorded REQ. The FR folds R-1 through R-5 and records implementation status, scope inventory, validation outcomes, and deviations; the Distill entry contains **Seed:**.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold R-1 through R-5 into committed FR/evidence before production implementation; research disagreement and concrete precedent lines must be dispositioned, not silently rewritten. | GATE |
| C-2 | Implement warning-only diagnostics at the frozen locations; referenced-prompt coverage cannot be deferred by the enforcer. | GATE |
| C-3 | Keep lint offline and deterministic; share a pure declaration without runtime imports, changed import contracts, or altered resolution/forwarding semantics. | GATE |
| C-4 | Commit defect-specific RED before GREEN and satisfy AC-01 through AC-11, including truthful fix messages and capability traceability. | GATE |
| C-5 | Freeze the human-facing policy as warnings, not upgrade-breaking refusal. Any proposed change to CI/hooks/enforcement infrastructure is outside this authority and requires a separately judged scope plus explicit human review before implementation. | GATE |
| C-6 | Keep csap read-only; validate only identified committed revisions or honestly labeled local reproducers. Route every governed shipped-example correction through graph authoring and record its witnesses. | GATE |

Authority granted: **None yet.** After the numbered revisions are folded, authority covers only W072/W073, runtime-preserving shared names, and the frozen directly supporting surfaces; this draft must be promoted through the existing judge workflow before it serves as the committed authority artifact.
