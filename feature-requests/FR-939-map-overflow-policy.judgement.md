# Judgement: FR-939 Map Overflow Policy — Typed `on_overflow` Contract

**Verdict:** APPROVED WITH REVISIONS — the overflow contract is a sound, single-responsibility correction, but authority activates only after the research substance, configuration paths, runtime wiring, and witnesses are made mechanically explicit and this draft is human-reviewed.

**Prior art:** FR-936 and its judgement are the SPLIT parent — this judges its deliverable D-2. `027-execution-safety-guards.md` holds the superseded truncate-and-warn contract, dispositioned in the body. FR-851 (requirement-witness audit) and FR-733 (CWE classifier) share only generic tokens; no contract overlap.

**Reviewed against:** `feature-requests/FR-939-map-overflow-policy.md`; `feature-requests/FR-939-map-overflow-policy.research.md`; `feature-requests/research-briefs/fr939-map-overflow-brief.md`; `feature-requests/FR-936-map-node-hardening.md`; `feature-requests/FR-936-map-node-hardening.judgement.md`; `feature-requests/027-execution-safety-guards.md`; `feature-requests/069-map-node-timeout.md`; `capabilities/CAP-11-subgraph-map.yaml`; `docs/plan-web-toolkit.md`; `yamlgraph/compile/map_compiler.py`; `yamlgraph/compile/graph_loader.py`; `yamlgraph/compile/node_compiler.py`; `yamlgraph/models/node_schema.py`; `yamlgraph/models/graph_schema.py`; `tests/unit/test_fr027_execution_safety.py`; `reference/graph-yaml.md`; `.github/copilot-instructions.md`; `CLAUDE.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`.

## What is sound

The defect is real and severe: `map_edge` resolves a cap, logs, slices, and returns `Send` objects for only the retained prefix (`yamlgraph/compile/map_compiler.py:352-365`), while the existing tests explicitly protect truncate-and-succeed behavior (`tests/unit/test_fr027_execution_safety.py:37-69`). A successful partial result is the repository's `plausible_wrong_answer` case, and fail-by-default aligns with the ban on silent fallbacks (`.github/copilot-instructions.md:79,220`).

The FR is properly split from payload projection, timeout lifecycle, and retry ownership. It implements only FR-936 deliverable D-2 (`feature-requests/FR-936-map-node-hardening.judgement.md:35-38,60,73-74`) and explicitly excludes the other three contracts (`feature-requests/FR-939-map-overflow-policy.md:17-24,113-115`). Scope and single responsibility are therefore sound.

The proposed boundary is architecturally appropriate. Node configuration is already validated by `NodeConfig`, whose map fields and cap live in `yamlgraph/models/node_schema.py:84-93,208-211`; runtime fan-out is already centralized in `map_edge`. A typed policy validated at load and enforced before `Send` construction conforms to the existing schema/compiler split rather than introducing another node type.

Strategically, this is a framework-primitive correction, not a contrib example or documentation-only pattern. The existing map abstraction lacks any in-band overflow disposition, and the cited plan names the fi-catalog census, the API-spec map stage, and the weekly-bulletin collection as consumers of the map path (`docs/plan-web-toolkit.md:59-62,146-171`). The contract is directly testable through schema rejection, edge invocation, emitted `Send` count and payload order, warning capture, and a branch-call counter.

The migration decision is also internally coherent: FR-027 deliberately chose truncate-and-warn (`feature-requests/027-execution-safety-guards.md:39-57`), and FR-939 explicitly supersedes it while retaining truncation as an opt-in policy (`feature-requests/FR-939-map-overflow-policy.md:17-24,64-73`). The parent judgement already froze `error` as the default and required both cap levels and the explicit truncate path.

## Required revisions

### R-1: Replace persona duplication with substantive alternatives research

Rewrite the committed research table to compare four to six genuine solution classes, each with its own mechanism, precedent, cost/risk, and disposition. At minimum distinguish: unconditional fail-on-overflow; optional typed policy defaulting to error; mandatory explicit policy with no default; in-band partial-success metadata; and removing or relocating the cap to bounded scheduling. Keep bounded scheduling rejected as outside FR-939 if that remains the decision.

Do not count three differently named enum proposals as three solution classes (`feature-requests/FR-939-map-overflow-policy.research.md:21-23`). Correct the claim that runtime item-count overflow can be rejected at graph-load time: load-time validation can reject an invalid policy value, but the overflow comparison cannot occur until `over` resolves from state (`feature-requests/FR-939-map-overflow-policy.research.md:20`; `yamlgraph/compile/map_compiler.py:338-354`). Treat the Airflow row as external precedent for one solution class rather than as a separate YAMLGraph candidate. Preserve the disagreement over default-error, default-truncate, and mandatory declaration, and give one explicit `is_this_a_graph` conclusion for the chosen scope.

### R-2: Correct and type both configuration paths

Amend the FR to distinguish the existing cap path from the new policy path:

- cap: node `max_items` > graph `config.max_map_items` > `DEFAULT_MAX_MAP_ITEMS`;
- policy: node `on_overflow` > graph `defaults.on_overflow` > `"error"`.

Add `on_overflow: Literal["error", "truncate"] | None` to `NodeConfig`. Add load-time Pydantic validation for `defaults.on_overflow` in `GraphConfigSchema`; the current `defaults` field is an untyped `dict[str, Any]`, and its only value-specific validator covers `thinking_budget` (`yamlgraph/models/graph_schema.py:66-100`). Invalid values at either level must fail `load_graph_config`, not survive until `map_edge`.

### R-3: Repair graph-level cap propagation inside this contract

Fold the actual runtime wiring into the implementation plan. `GraphConfig` parses `config.max_map_items` into `GraphConfig.max_map_items` (`yamlgraph/compile/graph_loader.py:83-85`), but map compilation receives only a copy of `config.defaults` (`yamlgraph/compile/node_compiler.py:173-181,338-342`), and `map_edge` looks for `max_map_items` in that defaults mapping (`yamlgraph/compile/map_compiler.py:350-354`). Thus the documented `config.max_map_items` path is not presently connected to compiled map behavior.

Pass the authoritative graph cap and graph policy into `compile_map_node` explicitly, or otherwise connect those exact values without moving `max_map_items` into `defaults`. Add an end-to-end witness that loads and compiles YAML containing `config.max_map_items`; a direct unit call that injects `{"max_map_items": ...}` as the `defaults` argument is not sufficient.

### R-4: Replace ambiguous acceptance language with observable contracts

Specify `ValueError` as the default-error overflow exception. Define the warning contract as WARNING level containing node name, observed count, and cap; define truncation as retaining exactly `items[:max_items]` in original order. Add policy-precedence witnesses in both directions, invalid-value witnesses at both schema levels, and a compiled-graph or instrumented-edge witness proving overflow creates no `Send` and invokes no sub-node.

Replace “preserves slice-and-warn exactly,” “clear message,” and “existing map tests otherwise green” (`feature-requests/FR-939-map-overflow-policy.md:98-115`) with the revised criteria below and the exact focused test command.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Revised FR and substantive research record: `feature-requests/FR-939-map-overflow-policy*.md` |
| D-2 | Node and graph-default policy validation: `yamlgraph/models/node_schema.py`, `yamlgraph/models/graph_schema.py` |
| D-3 | Graph cap/policy propagation: `yamlgraph/compile/graph_loader.py`, `yamlgraph/compile/node_compiler.py` |
| D-4 | Pre-dispatch overflow enforcement: `yamlgraph/compile/map_compiler.py` |
| D-5 | Focused RED witnesses and updated FR-027 contract tests under `tests/unit/` |
| D-6 | One new CAP-11 requirement and its `@pytest.mark.req` mappings |
| D-7 | Map reference update, one unreleased changelog fragment, and one diary reflection |

Not authorized: timeout or thread-lifecycle changes; retry policy or exception-ownership changes; `Send` payload projection; concurrency, batching, chunking, durability, caching, checkpoint, Store, or progress-log changes; a new map node type; changes to non-map error handling; demo graph or prompt edits; provider or LLM behavior changes; removal of `max_items` or `config.max_map_items`.

## Revised acceptance criteria

- [ ] AC-01: The committed research record compares four to six genuine solution classes, dispositions precedent, preserves the default-policy disagreement, corrects the load-time/runtime distinction, and gives one explicit `is_this_a_graph` answer.
- [ ] AC-02: `load_graph_config` accepts node and graph-default `on_overflow` values `"error"` and `"truncate"` and rejects every other value through Pydantic validation.
- [ ] AC-03: Runtime policy resolves in this order: node `on_overflow` > `defaults.on_overflow` > `"error"`; tests exercise both node-overrides-default directions and the implicit default.
- [ ] AC-04: Runtime cap resolves in this order: node `max_items` > `config.max_map_items` > `DEFAULT_MAX_MAP_ITEMS`; an end-to-end YAML load/compile test proves `config.max_map_items` controls fan-out.
- [ ] AC-05: When `len(items) > max_items` under policy `"error"`, `map_edge` raises `ValueError` before constructing a `Send` or invoking the sub-node.
- [ ] AC-06: The overflow exception message contains the map node name, observed item count, and configured cap, asserted as values rather than a full brittle sentence.
- [ ] AC-07: Under explicit policy `"truncate"`, fan-out contains exactly the original prefix `items[:max_items]` in order and emits one WARNING containing node name, observed count, and cap.
- [ ] AC-08: Inputs at and below the cap emit one `Send` per item, preserve order, and emit no overflow warning under either policy.
- [ ] AC-09: `tests/unit/test_fr027_execution_safety.py` no longer asserts implicit truncation; it pins fail-by-default and explicit truncation, while a focused `tests/unit/test_fr939_map_overflow_policy.py` covers validation, precedence, pre-dispatch failure, messages, warnings, and end-to-end graph-cap propagation.
- [ ] AC-10: One new CAP-11 requirement identifies overflow disposition; every new test carries its `@pytest.mark.req` marker, and `python scripts/req_coverage.py --strict` succeeds.
- [ ] AC-11: RED and GREEN are separate commits, and the RED commit fails for missing overflow-policy behavior rather than an import, fixture, or malformed graph.
- [ ] AC-12: `pytest tests/unit/test_fr027_execution_safety.py tests/unit/test_fr939_map_overflow_policy.py tests/unit/test_graph_schema.py -q --no-cov` succeeds.
- [ ] AC-13: `reference/graph-yaml.md` documents both `config.max_map_items` and node/default `on_overflow`, including resolution order, fail-by-default behavior, explicit sampling, and error/warning fields; one changelog fragment and one diary entry record the contract change.
- [ ] AC-14: The implementation diff contains none of the not-authorized surfaces.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | No implementation authority exists until R-1 through R-4 are folded into the FR/research record and this draft judgement is human-reviewed. | GATE |
| C-2 | Never report success on a partial map result unless `"truncate"` was selected explicitly at node or graph-default level. | GATE |
| C-3 | Reject invalid policies during graph loading; runtime string checks alone do not satisfy the typed contract. | GATE |
| C-4 | Prove `config.max_map_items` through the real load/compile path; do not preserve the disconnected defaults-only test seam. | GATE |
| C-5 | Overflow policy must be resolved and enforced before any `Send` construction or sub-node execution. | GATE |
| C-6 | Do not cross into timeout, retry, payload projection, scheduling, durability, caching, checkpoint, Store, progress, provider, or non-map error-handling work. | GATE |
| C-7 | Preserve explicit truncate-and-warn as the only authorized partial-processing path; do not remove the cap or sampling capability. | GATE |
| C-8 | Commit a genuine failing RED witness before production changes, then commit GREEN separately. | GATE |

Authority granted: after human review and mechanical completion of R-1 through R-4, implement only the typed map overflow policy, the necessary graph cap/policy propagation repair, its focused witnesses and traceability, and the listed documentation artifacts.
