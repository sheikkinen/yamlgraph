# Judgement: FR-1028 `graph run --provider/--model` Override of Graph Defaults

**Verdict:** APPROVED WITH REVISIONS — the load-boundary override is a small, feasible framework primitive, but authority activates only after the FR supplies substantive equivalent research, reconciles FR-231's existing override contract, narrows the loader API, and specifies truthful research-run provenance.

**Reviewed against:** `feature-requests/FR-1028-graph-run-provider-model-override.md`; `feature-requests/FR-1027-org-ai-dossier-census.md`; `feature-requests/FR-890-research-sole-route-closed-input-alternatives.md`; `feature-requests/FR-119-lint-provider-model-toplevel.md`; `feature-requests/FR-263-azure-openai-provider.md`; `feature-requests/FR-071-thinking-budget-graph-level.md`; `feature-requests/FR-230-google-vertex-thinking-budget.md`; `feature-requests/FR-231-model-provider-timing-comparison.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `CLAUDE.md`; `yamlgraph/cli/__init__.py`; `yamlgraph/cli/graph_commands.py`; `yamlgraph/cli/bench_commands.py`; `yamlgraph/compile/graph_loader.py`; `yamlgraph/compile/node_compiler.py`; `yamlgraph/node_factory/llm_nodes.py`; `yamlgraph/node_factory/copilot_node.py`; `yamlgraph/node_factory/copilot_runtime.py`; `yamlgraph/node_factory/copilot_runtime_claude.py`; `yamlgraph/tools/agent.py`; `examples/demos/research-route/graph.yaml`; `examples/demos/research-route/nodes/research_tools.py`; `scripts/research.sh`; `scripts/research_preflight.py`.

## What is sound

- **Scope:** The primary change is narrow and located at the correct boundary: two `graph run` inputs alter the root graph's declared defaults before compilation while explicit node pins retain precedence (`FR-1028`, lines 24-31, 62-74). That is smaller and safer than editing a committed graph for each run.
- **Consistency:** The summary, value statement, and main precedence rule agree: node pin → overridden graph default (`FR-1028`, lines 24-36, 64-69). FR-119 confirms that `defaults:` and per-node configuration are the established declaration surfaces (`FR-119`, lines 11-21, 89-96).
- **Measurability:** The core behaviors—defaults-only override, per-node pin preservation, and independent provider/model flags—can be asserted directly (`FR-1028`, lines 76-86). The live research run supplies a meaningful integration witness (`FR-1028`, lines 87-90).
- **Feasibility:** `load_graph_config()` already owns the parsed mapping before `GraphConfig` construction (`graph_loader.py`, lines 119-168). Compilation copies `config.defaults` into effective defaults (`node_compiler.py`, lines 338-342); LLM nodes resolve node values before defaults (`llm_nodes.py`, lines 150-158), and agent nodes use the same precedence (`agent.py`, lines 257-267). The research graph therefore has a workable seam for both its LLM nodes and its librarian agent (`research-route/graph.yaml`, lines 11-14, 86-145).
- **Architecture alignment:** The proposal preserves YAML as the declared baseline and treats the CLI as an invocation override rather than adding a second YAML declaration location. Azure is already a supported provider with explicit deployment-name precedence (`FR-263`, lines 79-89).
- **Single responsibility:** The CLI/loader change and `research.sh` forwarding are one concern: exposing and exercising a runtime override. Artifact provenance is acceptable as evidence for that same invocation, provided it remains a small wrapper concern.
- **Strategic classification:** **Framework primitive.** The primitive serves operator outage recovery, scripted sole-route execution, and model/provider comparison. No current load-boundary abstraction supplies this behavior; the similarly named FR-231 invocation keys require explicit reconciliation under R-2.
- **Testability:** Failing tests can be derived after the revisions below. The runtime path is mockable, while the Azure run remains a separately identifiable live witness.

## Required revisions

### R-1: Make the equivalent research record substantive

Replace the current three-column alternatives table with a committed in-body equivalent record containing 4-6 genuine solution classes and the columns `candidate`, `source/position`, `class`, `verdict`, `precedent`, `is_this_a_graph`, and `effort/risk`. Preserve any conflicting positions as separate rows rather than collapsing them. State the graph answer explicitly: this is **not** a graph-shaped solution because provider/model selection must occur before the graph's LLM and agent nodes are constructed. Cite the already named FR precedents in the relevant rows and correct the FR-119 summary from “top level or per node” to “inside `defaults:` or per node.”

The present field points only to a table lacking solution-class labels, precedent cells, disagreement provenance, and any `is_this_a_graph` answer (`FR-1028`, lines 12-22, 92-100). That does not satisfy the prospective research gate, which requires 4-6 genuine classes, precedent, preserved disagreement, and the graph answer (`judge-fr/doctrine.md`, lines 118-130; `FR-890`, lines 70-79, 161-170). No implementation authority exists until this revision is folded.

### R-2: Reconcile FR-231 and narrow the loader contract

Correct the prior-art disposition: FR-231 did not run comparisons by editing YAML; it authorized provider/model overrides and allowed either configurable invocation or recompilation (`FR-231`, lines 20-30, 111-119). The current bench implementation writes `configurable.provider_override` and `configurable.model_override` after compilation (`bench_commands.py`, lines 195-220), while the cited LLM and agent resolution paths consume node/default mappings, not those invocation keys (`llm_nodes.py`, lines 150-158; `agent.py`, lines 257-267).

Freeze the new loader API as keyword-only `provider_override: str | None = None` and `model_override: str | None = None`; do not expose an unrestricted `defaults_override: dict`. `load_graph_config()` must copy the parsed root mapping and its `defaults` mapping, replace only non-`None` provider/model values before `GraphConfig` validation/construction, and leave the source mapping unmutated. State that the override applies only to the root graph loaded by `graph run`; child graph tools retain their own declarations. Repair of `graph bench` is not authorized by this FR and must be filed separately.

### R-3: Specify the complete precedence witness

Replace “constructs LLM nodes” with tests covering both node kinds used by the blocked consumer: a defaults-only `type: llm` node and a defaults-only `type: agent` node must resolve the CLI pair; explicit provider and model pins on either node must win independently. Add a mixed-pin case where only one node field is pinned, proving the other field still inherits its overridden default. This follows the actual two resolution paths (`llm_nodes.py`, lines 150-158; `agent.py`, lines 257-267) and the research graph's mixed LLM/agent topology (`research-route/graph.yaml`, lines 86-145).

### R-4: Define truthful, atomic research provenance

For `scripts/research.sh`, require `RESEARCH_PROVIDER` and `RESEARCH_MODEL` as a pair: both unset preserves today's invocation, both set appends both CLI flags, and exactly one set fails before launching the graph with a tested non-zero exit and actionable message. On an override run, the wrapper must atomically add exactly one `- provider/model: <provider>/<model>` line to the generated artifact before verification. `research_preflight.py --verify-artifact` must reject an empty, duplicate, or malformed provider/model header when one is present; it must continue accepting legacy artifacts without the optional line.

This closes the currently unspecified producer seam: the artifact is created inside `reduce_findings()` with only brief/date/persona headers (`research_tools.py`, lines 755-783), while the wrapper invokes the graph and verifies that artifact afterward (`research.sh`, lines 58-68). Merely saying that the header “gains” a line and that the verifier “accepts” it (`FR-1028`, lines 70-73, 83-86) neither identifies the writer nor proves the value is the pair actually requested.

### R-5: Replace placeholders and make every acceptance check executable

Allocate and record concrete unused `REQ-YG-*` and `CAP-*` identifiers before RED. Replace the current acceptance list with the criteria below, name the targeted test files, and add the implementation-status/decisions section plus diary deliverable required by repo doctrine. `REQ-YG-XXX` is not a mechanically checkable traceability target (`FR-1028`, lines 89-90).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Revised FR research record, prior-art disposition, concrete requirement/capability IDs, and implementation record in `feature-requests/FR-1028-graph-run-provider-model-override.md` |
| D-2 | `--provider` and `--model` arguments for `graph run` in `yamlgraph/cli/__init__.py` and forwarding in `yamlgraph/cli/graph_commands.py` |
| D-3 | Root-only, provider/model-only load-boundary override in `yamlgraph/compile/graph_loader.py` |
| D-4 | Unit/CLI tests for parsing, root-default replacement, non-mutation, independent fields, LLM/agent inheritance, and explicit/mixed node pins |
| D-5 | Paired environment forwarding and atomic provenance stamping in `scripts/research.sh`, plus optional-header validation in `scripts/research_preflight.py` and shell/unit tests |
| D-6 | Azure live witness and promoted `feature-requests/FR-1027.research.md` |
| D-7 | Concrete capability record, `ARCHITECTURE.md` requirement row, changelog fragment, and `docs/diary/` Distill entry |

Not authorized: edits to `examples/demos/research-route/graph.yaml` or its prompts; new graph artifacts; loader reads of provider/model environment variables; arbitrary overrides of other `defaults` keys; mutation or bypass of explicit per-node pins; recursive propagation into graph-tool child graphs; linter changes; provider-factory or dependency changes; repair/refactor of `graph bench`; CI, hook, judge, review, or other enforcement-doctrine changes.

## Revised acceptance criteria

- [ ] AC-01: Parser tests prove `graph run` accepts optional `--provider` and `--model` strings and leaves both as `None` when omitted.
- [ ] AC-02: A RED-first loader test proves a root graph with declared defaults resolves an explicit provider/model override pair, and the source mapping plus a second unoverridden load retain the YAML values.
- [ ] AC-03: Provider-only and model-only tests prove each non-`None` argument replaces only its named root default.
- [ ] AC-04: Factory-mocked tests prove defaults-only `type: llm` and `type: agent` nodes both receive the overridden pair.
- [ ] AC-05: Explicit provider/model pins win independently for both LLM and agent nodes; a mixed-pin fixture proves the unpinned field still inherits its overridden default.
- [ ] AC-06: A graph-tool child fixture proves the root override is not forwarded recursively to the child graph.
- [ ] AC-07: No-flag `graph run` retains existing behavior, and `graph lint` continues validating the committed YAML declarations without considering runtime flags.
- [ ] AC-08: Shell tests prove `scripts/research.sh` forwards neither flag when both research variables are unset, forwards both flags in stable order when both are set, and fails before executor invocation when exactly one is set.
- [ ] AC-09: On an override run, the wrapper atomically inserts exactly one `- provider/model: <provider>/<model>` line before artifact verification; tests prove verifier acceptance of one valid line, legacy acceptance with no line, and rejection of empty, duplicate, or malformed lines.
- [ ] AC-10: A live `RESEARCH_PROVIDER=azure RESEARCH_MODEL=<deployment> scripts/research.sh feature-requests/research-briefs/org-ai-dossier.md` run completes all research personas, records the exact pair in the draft header, passes artifact verification, and is promoted to `feature-requests/FR-1027.research.md`.
- [ ] AC-11: Tests carry the concrete requirement marker; the concrete capability record and `ARCHITECTURE.md` row agree; `python scripts/req_coverage.py --strict` passes.
- [ ] AC-12: The changelog fragment, FR implementation record, and diary Distill entry with a `Seed:` are present.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold R-1 through R-5 into the FR before implementation begins; until then this judgement grants no authority. | GATE |
| C-2 | The loader override accepts only provider/model and does not mutate parsed YAML data, explicit node configuration, or child graph declarations. | GATE |
| C-3 | Preserve the frozen precedence `explicit node field → overridden root default → existing provider fallback`; provider and model are resolved independently. | GATE |
| C-4 | Do not modify governed graph or prompt artifacts; any need to do so returns the plan for a new judgement and the graph-authoring route. | GATE |
| C-5 | Commit RED witnesses before GREEN implementation, including both the LLM and agent paths used by the research route. | GATE |
| C-6 | The live witness must expose no credential value, private organization identifier, or other secret in the promoted research artifact. | GATE |
| C-7 | Do not repair or refactor FR-231 benchmarking under this authority; record that defect for a separate FR. | GATE |

Authority granted: after R-1 through R-5 are folded and human-reviewed, implement only the frozen root `graph run` provider/model override, its research-wrapper forwarding/provenance witness, and the listed traceability artifacts.

---
**Prior art:** inherits the FR-1028 prior-art disposition (FR-119, FR-263, FR-071/230, FR-231 reconciled per R-2).
**Folded:** 2026-09-07 by the operator session from `tmp/draft-judgement-copilot-FR-1028-*.md` (backend copilot, gpt-5.6-sol); R-1..R-5 folded into the FR the same day. Advisory until human-reviewed.
**Renumbering note (2026-09-08):** the blocked consumer this judgement calls
"FR-1027" was renumbered to **FR-1029** (org AI dossier) after a parallel
session merged an unrelated FR-1027 (recap pull-request axis, #637) to main
first. Read every `FR-1027` above as FR-1029; the FR itself has been updated.
FR-1029 is Shelved in this repo — its implementation moved to a private
YAMLGraph consumer — so `FR-1029.research.md` lives on the archived branch
`feat/fr1027-org-ai-dossier`, not on main.
