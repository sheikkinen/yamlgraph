# Judgement: FR-1165 Refuse the graph-level config.max_tokens that was never applied

**Route:** scripts/judge.sh (copilot gpt-6.1-sol), draft folded verbatim; revisions R-1..R-3 folded into the FR.
**Prior art:** feature request 027 (027-execution-safety-guards.md), FR-223, FR-984 dispositioned in the FR's Prior art line; R-1 alternatives table records the research classes.


**Verdict:** APPROVED WITH REVISIONS — refusal is the minimal sound fix, but research disposition, the remaining documentation claim, and acceptance witnesses must be corrected before authority activates.

**Reviewed against:** Committed inputs at `e885d952`: `feature-requests/FR-1165-config-max-tokens-refused.md`; `feature-requests/FR-1165.research.md`; `feature-requests/research-briefs/fr1165-config-max-tokens-ignored-brief.md`; `feature-requests/027-execution-safety-guards.md`; `feature-requests/FR-223-refactor-create-node-function.md`; `feature-requests/FR-984-map-fan-out-max-concurrency.md` (lines 1-100); `yamlgraph/compile/graph_loader.py`; `yamlgraph/compile/node_compiler.py` (defaults and LLM dispatch); `yamlgraph/node_factory/llm_nodes.py` (token resolution and executor call); `yamlgraph/models/graph_schema.py` (lines 85-145); `yamlgraph/schemas/graph-v1.json` (config block); `tests/unit/test_fr027_execution_safety.py` (token tests and references); `reference/graph-yaml.md` (config/node token references and lines 135-230); `capabilities/CAP-17-execution-safety-guards.yaml`; `.github/copilot-instructions.md`; `CLAUDE.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`. Working tree was clean. No author transcript or working notes were consumed.

## What is sound

The strongest case against refusal is the published promise: FR-027 explicitly authorized graph-level token limits and marked their wiring complete (`027-execution-safety-guards.md:107-119,185`). Wiring would fulfill that promise rather than make an external graph fail. Nevertheless, the existing defaults route already supplies the promised behavior: the compiler copies `config.defaults` (`node_compiler.py:342-346`), resolution selects node then defaults (`llm_nodes.py:156`), and execution passes the result onward (`llm_nodes.py:347-360`). The FR explicitly dispositions the old promise and chooses one graph-wide spelling instead of another precedence level (`FR-1165:13-16,116-124`). Refusal is defensible; absence of repository users is not proof that external users do not exist, so the actionable error and release note matter.

| Rubric criterion | Finding and evidence |
|---|---|
| Scope | Minimal runtime change: reject one key and remove its unused attribute, rather than alter token resolution (`FR-1165:80-86`; `graph_loader.py:83-88`). Preserve this boundary. |
| Consistency | Direction is consistent, but the FR miscounts research votes and omits a still-false node-table default (`FR-1165:116`; research lines 22-26; `graph-yaml.md:279`). R-1/R-2 address these defects. |
| Measurability | Loader and executor assertions are concrete (`FR-1165:103-106`); documentation inspection and "vulture clean" need explicit assertions or commands (`FR-1165:107-111`). R-3 closes that gap. |
| Feasibility | Existing loader, compiler, and token tests provide workable seams (`graph_loader.py:122-192`; `node_compiler.py:251-256`; `test_fr027_execution_safety.py:629-744`). No dependency is needed. Pydantic currently permits extra graph fields (`graph_schema.py:112`); broad validation replacement is unnecessary. |
| Architecture alignment | Normalize at the load boundary, keep node/default resolution unchanged, and narrow REQ-YG-060 rather than create a capability (`FR-1165:80-86`; CAP-17 REQ-YG-060). |
| Single responsibility | Runtime refusal, schema advertising, documentation, and requirement wording are one contract correction. Prompt-file token handling is explicitly parked (`FR-1165:97-99`). No split is warranted. |
| Strategic classification | **Pattern documentation / existing-contract repair**, not a framework primitive: existing defaults suffice and no new abstraction is required (`FR-1165:52-56,118-124`). This classification does not eliminate the necessary loader guard. |
| Testability | AC-01 and schema removal can fail for the actual defect; defaults propagation is a preservation witness, not a required RED failure (`FR-1165:87-95,103-112`). The membership guard also promises refusal for null and for redundant config/default declarations; make those witnesses explicit in R-3. |

## Required revisions

### R-1: Disposition the actual alternatives without counting personas as solution classes

Correct `FR-1165:116` from four wiring personas to three. Fold a committed, dispositioned alternatives table into the FR or linked research record that distinguishes: wiring the alias; deletion with lint-only enforcement; deletion with load-time refusal; broad config-field prohibition. These are the existing research options plus the FR's selected enforcement boundary, not a request for a new pipeline run. Give each a pursue/reject/park decision, concrete precedent file/line evidence, and the reason it does or does not address load-time silent acceptance. Preserve the original research disagreement; explain why the selected refusal differs from the subtractionist's linter proposal. Correct the blanket `convergent x5` characterization in a disposition note rather than treating five persona rows as five independent solutions (`FR-1165.research.md:22-26`).

The current linked record contains real alternatives, not a strawman, but does not yet meet the local requirement for 4-6 genuine, dispositioned solution classes and precedent lines (`judge-fr/doctrine.md:118-127`). No authority is granted while this remains incomplete.

### R-2: Correct the surviving documentation claim and bound schema expectations

Extend the documentation operation to change the node-property table's `max_tokens` default from "from config" to "from defaults" (`reference/graph-yaml.md:279`). Document `defaults.max_tokens` as the graph-wide setting and node `max_tokens` as its override; retain the intended node/default/provider behavior. Include the refusal and replacement spelling in the required changelog fragment.

Clarify AC-03: removing the named JSON-schema property stops advertising it, but does not make the permissive schema reject unknown properties (`graph-v1.json:287-320`, especially `additionalProperties: true`). The loader owns refusal. Do not introduce broad `extra="forbid"`, close unrelated schema properties, or promise schema-only rejection.

### R-3: Specify direct witnesses and exact verification commands

Fold the revised criteria below into the FR. Replace "vulture clean" as proof of attribute absence with a direct assertion on a successfully loaded graph. Patch `yamlgraph.node_factory.llm_nodes.execute_prompt`, the imported call site (`llm_nodes.py:15,347`), and invoke a compiled graph so the defaults witness crosses loader, compiler, and node execution rather than merely calling the resolver.

Keep the remaining provider/cache tests in `test_fr027_execution_safety.py`; replace only the three tests named in the FR. Tag every new test `REQ-YG-060`. Require RED failures caused by acceptance of the forbidden key and the advertised schema property, not missing files, imports, or fixtures. Record exact commands and outcomes for targeted tests, the unit suite, requirement coverage, existing lint/format checks, and scoped structural analysis; no new tooling or repository-wide cleanup is authorized.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `yamlgraph/compile/graph_loader.py`: refuse presence of `config.max_tokens`; remove `GraphConfig.max_tokens`. |
| D-2 | `yamlgraph/schemas/graph-v1.json`: remove only the advertised config token property; use an existing generator source only if the planned probe proves one owns this block. |
| D-3 | `reference/graph-yaml.md`: remove the config example/table entry, correct the node default, and identify the graph-wide replacement. |
| D-4 | `capabilities/CAP-17-execution-safety-guards.yaml`: narrow REQ-YG-060 wording to node/default propagation. |
| D-5 | `tests/unit/test_fr027_execution_safety.py` and `tests/unit/test_fr1165_config_max_tokens_refused.py`: replace obsolete parsing/schema witnesses and add the focused contract witnesses below. |
| D-6 | FR/research disposition and implementation record; one `changelog/unreleased/` fragment; a scoped Distill entry with **Seed:** under `docs/diary/`. |

Not authorized: a config alias or precedence level; token-resolution changes; prompt-YAML token handling; new linter rules; broad config validation; provider, timeout, concurrency, or other safety refactors; enforcement-infrastructure changes. No graph/prompt artifact edit is authorized on the current no-user evidence. If the planned scan finds a real graph user, record the specific path and follow the graph-authoring contract before migration; this judgement does not waive that route.

## Revised acceptance criteria

- [ ] AC-01: Parameterized `load_graph_config` tests reject `config.max_tokens: 4096` and `config.max_tokens: null` with `ValueError` naming both `config.max_tokens` and `defaults.max_tokens`. A graph containing both config and defaults token values also fails instead of silently choosing one.
- [ ] AC-02: With the imported executor patched and no network calls, load, compile, and invoke a minimal LLM graph using `defaults.max_tokens: 123`; assert the executor is called and receives `max_tokens=123`. A node override of `456` receives `456`; omission of both receives `None`. Keep existing node/provider/cache tests passing.
- [ ] AC-03: An assertion on parsed `yamlgraph/schemas/graph-v1.json` finds no `max_tokens` in `properties.config.properties`. Scoped inspection of `reference/graph-yaml.md` finds no config token example/row, the node default says "from defaults", and the graph-wide replacement is documented. Schema permissiveness for unrelated keys is unchanged.
- [ ] AC-04: A successfully loaded graph without the forbidden key has no `max_tokens` attribute; the loader assignment and obsolete test expectations are removed. CAP-17 REQ-YG-060 describes node/default propagation, not graph-level config propagation.
- [ ] AC-05: Git history records RED before GREEN, with the forbidden-key and schema-property tests failing for the defect before implementation; defaults/override preservation tests need not fail in RED. Every new test carries `@pytest.mark.req("REQ-YG-060")`.
- [ ] AC-06: Record passing `pytest tests/unit/test_fr027_execution_safety.py tests/unit/test_fr1165_config_max_tokens_refused.py -q --no-cov`, `pytest tests/unit/ -q --no-cov`, and `python scripts/req_coverage.py --strict`, plus existing lint/format checks for changed Python files. Record scoped vulture/radon findings as structural context, not as a substitute for AC-04.
- [ ] AC-07: The FR records implementation status, decisions, validation outcomes, and any deviations; the changelog fragment names refusal and `defaults.max_tokens`; the Distill entry contains **Seed:**. The planned repository-user scan records its result and any governed migration is separately routed.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold R-1 through R-3 into committed FR/evidence before production edits; incomplete research disposition grants no authority. | GATE |
| C-2 | Preserve node/default/provider resolution and refuse the forbidden key by presence, including null; no alias, fallback, or warning-only acceptance. | GATE |
| C-3 | Commit the defect-specific RED witnesses before GREEN and satisfy AC-01 through AC-07 before submission. | GATE |
| C-4 | Stay within D-1 through D-6. Any discovered graph/prompt migration must obey the sole graph-authoring route; enforcement-infrastructure edits require separate scope and explicit human review. | GATE |

Authority granted: **None yet.** After the numbered revisions are folded into committed artifacts, authority covers only the frozen single-key refusal and its directly coupled tests, schema, documentation, requirement wording, and process records.
