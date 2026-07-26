# Judgement: FR-759 OpenTelemetry Observability Boundary

**Verdict:** APPROVED WITH REVISIONS — the FR identifies a real framework observability boundary, but authority activates only after the optional-extra failure mode, span schema, and first-increment execution surface are made mechanically testable.

**Reviewed against:** `feature-requests/FR-759-otel-observability-boundary.md`; `docs/plan-research-dependency-negative-space.md`; `feature-requests/FR-723-execution-path-visualization.md`; `feature-requests/FR-723-execution-path-visualization.judgement.md`; `feature-requests/FR-760-declare-langchain-core-dependency.md`; `feature-requests/FR-761-reproducible-dependency-governance.md`; `feature-requests/FR-762-example-dependency-taxonomy.md`; `docs/dependency-rationale.yaml`; `scripts/dependency_rationale.py`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `CLAUDE.md`.

## What is sound

The problem is real and belongs at the framework boundary. The research evidence says YAMLGraph has LangSmith integration but no OpenTelemetry dependency or semantic event boundary, making traces LangSmith/LangChain-shaped rather than YAMLGraph-shaped (`docs/plan-research-dependency-negative-space.md` L41-L55). It also ranks an OpenTelemetry boundary and optional OTEL extra first, with the explicit instruction to define spans/events before adding exporters broadly (L193-L195), and the proposed minimal path names exactly this two-span start plus one opt-in exporter (L220-L224).

The scope is mostly disciplined. FR-759 limits the first schema to graph-run and node-execution spans (L47-L49) and explicitly parks LLM/tool/route/checkpoint/interrupt/verification spans, metrics, and LangSmith exporter migration for later FRs (L54). That avoids colliding with FR-723's completed route decision log, whose public surface is `YAMLGRAPH_ROUTE_LOG` / `yamlgraph.route` route JSON (`feature-requests/FR-723-execution-path-visualization.md` L54-L78, L176-L188) and whose judgement rejected LangSmith-derived routes as the mechanism (L48-L50).

The proposal is a framework primitive: local, CI, hosted, and replacement scenarios all need the same run/node trace contract, and existing route logs, LangSmith traces, and CLI output lack a common run identity (`docs/plan-research-dependency-negative-space.md` L47-L55; `feature-requests/FR-759-otel-observability-boundary.md` L20-L25). Commandment 9 supports making operational truth observable and cited (`.github/copilot-instructions.md` L222).

**Prior art:** `106-otel-observability.md` (Proposed, undeveloped) and `FR-467-mission-control-unified-observability.md` (Proposed, a consuming dashboard layer) do not overlap this FR's frozen two-span schema scope. `FR-363-per-node-otel-scoping-in-copilot-node.md` (Implemented) is a narrower per-node copilot-CLI file exporter already superseded as "not the spine" in this FR's own Alternatives Considered section. `FR-231-model-provider-timing-comparison.md` (Implemented) is a one-off timing tool, not a standing trace boundary. No disposition changes required.

## Required revisions

### R-1: Separate disabled no-op from enabled missing-extra failure

Replace the ambiguous "no-op when the extra is not installed" rule (`feature-requests/FR-759-otel-observability-boundary.md` L51, L60) with this explicit contract: when OTEL is not enabled, a core install performs no OTEL import and changes no behavior; when `YAMLGRAPH_OTEL_EXPORT=otlp` or equivalent config explicitly enables OTEL but the `otel` extra is absent, the run fails before graph execution with a clear installation error naming the `otel` extra. Silent success with missing requested telemetry is not authorized.

### R-2: Freeze the span schema as an attribute table before enforcement

Fold a concrete schema table into the FR or the referenced `reference/` document before implementation. For each of `yamlgraph.graph.run` and `yamlgraph.node.execute`, list exact attribute names, value types, required/optional status, source, and privacy rule. The table must define the run identity attribute, graph identifier, thread id handling, node name/type, state-key-written representation, outcome/error fields, duration unit, and the deterministic variables-hash algorithm. "Follow OpenTelemetry GenAI semantic conventions where they apply" (`feature-requests/FR-759-otel-observability-boundary.md` L50) is not mechanically enforceable until the names and exceptions are pinned.

### R-3: Name the first-increment execution surface and test matrix

Revise "Every graph run" (`feature-requests/FR-759-otel-observability-boundary.md` L30) into a first-increment boundary the enforcer can prove: the path exercised by `yamlgraph graph run examples/demos/hello/graph.yaml` must produce one graph-run span and child node-execution spans under one run identity, and unit tests must use an in-memory exporter to assert parent/child linkage, span names, key attributes, success outcome, and error outcome. Async, streaming, route-span, tool-span, checkpoint-span, interrupt-span, verification-span, and LangSmith-exporter work remains outside this FR unless separately named with its own tests.

### R-4: Disposition the sibling dependency-governance boundary

Add one sentence to the FR clarifying that this FR may add only the `otel` optional dependency group and its rationale entries. It must not implement FR-760's `langchain-core` declaration, FR-761's lockfile/direct-import scan/pip-audit governance, or FR-762's example taxonomy (`feature-requests/FR-760-declare-langchain-core-dependency.md` L30-L37; `feature-requests/FR-761-reproducible-dependency-governance.md` L32-L39; `feature-requests/FR-762-example-dependency-taxonomy.md` L40-L53). The existing rationale registry requires every core and optional dependency to be documented (`docs/dependency-rationale.yaml` L1-L4), and its strict checker is already the relevant local gate (`scripts/dependency_rationale.py` L1-L9).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `pyproject.toml` optional dependency group named `otel` containing OTEL API, SDK, and OTLP exporter packages |
| D-2 | `docs/dependency-rationale.yaml` entries for each new OTEL package |
| D-3 | OTEL instrumentation boundary for graph-run and node-execution spans on the first-increment graph run path |
| D-4 | Opt-in exporter configuration behind `YAMLGRAPH_OTEL_EXPORT=otlp` or an explicitly documented equivalent |
| D-5 | Unit tests using an in-memory exporter for emitted and disabled behavior |
| D-6 | `reference/` span schema documentation with the frozen attribute table |
| D-7 | Hello demo output showing a visible trace |
| D-8 | CAP/REQ updates, pytest requirement markers, and changelog fragment |

Not authorized: LLM spans, tool spans, route spans, checkpoint spans, interrupt spans, verification spans, metrics, LangSmith-as-exporter migration, replacement or removal of LangSmith support, changes to FR-723 route-log semantics, dependency lockfile/governance work from FR-761, `langchain-core` declaration from FR-760, example dependency taxonomy work from FR-762, or broad OpenTelemetry auto-instrumentation outside the named graph/node boundary.

## Revised acceptance criteria

- [ ] AC-01: `pyproject.toml` defines an `otel` extra with OTEL API, SDK, and OTLP exporter packages; core install remains OTEL-free when the feature is disabled.
- [ ] AC-02: `docs/dependency-rationale.yaml` documents each added OTEL package; `python scripts/dependency_rationale.py --strict` passes.
- [ ] AC-03: With OTEL disabled, tests assert no OTEL import is required, no spans are emitted, and existing graph execution behavior is unchanged.
- [ ] AC-04: With OTEL explicitly enabled and the extra unavailable, graph execution fails before running nodes with a clear error naming the missing `otel` extra.
- [ ] AC-05: With OTEL enabled and an in-memory exporter configured, a hello graph run emits one `yamlgraph.graph.run` span and child `yamlgraph.node.execute` spans sharing one run identity.
- [ ] AC-06: Unit tests assert required graph/node span attributes, parent/child linkage, success outcome, error outcome, duration unit, state-key-written representation, and deterministic variables hash behavior.
- [ ] AC-07: `reference/` documents the frozen span schema as an attribute table matching the tests.
- [ ] AC-08: Hello-graph demo output includes a visible trace artifact or log, committed per demo-gate.
- [ ] AC-09: Tests are tagged with `@pytest.mark.req(...)`; a new or updated CAP file defines the governing REQ IDs.
- [ ] AC-10: A changelog fragment exists in `changelog/unreleased/`.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold R-1 through R-4 into `feature-requests/FR-759-otel-observability-boundary.md` before implementation authority activates. | GATE |
| C-2 | Preserve FR-723 route-log behavior; route spans are future work, not an implementation shortcut in this FR. | GATE |
| C-3 | Do not silently report success when an operator explicitly requests OTEL export but the required extra is missing. | GATE |
| C-4 | Do not emit raw variable values, state contents, prompts, completions, or tool payloads in graph/node span attributes; this FR authorizes metadata and deterministic hashes only. | GATE |
| C-5 | Do not implement sibling dependency-governance or taxonomy FRs under this authority. | GATE |

Authority granted: after the required revisions are folded into the FR, the enforcer may implement the opt-in OTEL extra and the first graph-run/node-execution span boundary exactly as frozen above.
