# Judgement: FR-807 Route Evidence Record Hardening

**Prior art:** dispositioned in the body and in the FR's own Prior art line — FR-723/FR-753/FR-759 are the substrate consumed, not duplicated; FR-808-regulated-evidence-profile.judgement.md is the companion policy layer; FR-774/FR-775/FR-776 book-summary judgements share only the hardening/evidence vocabulary (book pipeline, no route-record overlap).

**Verdict:** APPROVED WITH REVISIONS — the problem is real and belongs at the route-evidence boundary, but authority activates only after the FR pins the single run-identity contract, the artifact-hash algorithm, and the per-run loss-accounting semantics.

**Reviewed against:** `feature-requests/FR-807-route-evidence-record-hardening.md`; `docs/whitepaper-auditable-by-construction.md`; `yamlgraph/utils/route_log.py`; `yamlgraph/routing.py`; `yamlgraph/cli/graph_run_helpers.py`; `yamlgraph/executor_async.py`; `yamlgraph/cli/graph_commands.py`; `yamlgraph/cli/export_commands.py`; `yamlgraph/mermaid_export.py`; `yamlgraph/compile/graph_loader.py`; `yamlgraph/models/graph_schema.py`; `yamlgraph/observability/otel.py`; `reference/otel-observability.md`; `tests/unit/test_route_log.py`; `feature-requests/FR-723-execution-path-visualization.md`; `feature-requests/FR-723-execution-path-visualization.judgement.md`; `feature-requests/FR-753-route-overlay-example-cli-mmdc.md`; `feature-requests/FR-759-otel-observability-boundary.md`; `feature-requests/FR-759-otel-observability-boundary.judgement.md`; `feature-requests/FR-803-pipecat-flows-architecture-reassessment.md`; `feature-requests/FR-809-api-discovery-orchestrator-v2-recon-browser-sniff.md`; `feature-requests/020-soup-generator.md`; `feature-requests/FR-384-cost-profile-model-tiering.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`.

## What is sound

The FR names a genuine evidence defect, not a cosmetic logging change. The whitepaper says the current conformance diff presumes the executed artifact is the approved one and needs a run header with artifact content hash and judgement reference checked by equality (`docs/whitepaper-auditable-by-construction.md` L209-L215, L487-L492). It also names the same regulated-profile hardening points this FR implements: counted or fatal evidence loss, timestamps, and artifact hash/judgement reference in each run record (L360-L369). That matches the repo doctrine seed to stamp archived measurement artifacts with code identity (`.github/copilot-instructions.md` L170) and Commandment 6's ban on hidden/silent failures (L218).

The substrate exists and the change is feasible. Route emission is already centralized behind `emit_route()` (`yamlgraph/routing.py` L41-L48, L78-L89), route logging already has opt-in file/logger surfaces (`yamlgraph/utils/route_log.py` L6-L16), and the existing grammar is exactly the five-field route line FR-807 promises not to change (L18-L24). Emission currently suppresses all exceptions (`yamlgraph/utils/route_log.py` L112-L129), so the loss-counter target is source-true. Overlay parsing already skips non-route JSON objects (`yamlgraph/mermaid_export.py` L154-L169), so additive `run` and `run_end` records can coexist with the frozen route-line grammar.

The proposal is strategically a framework primitive. The first consumer is `graph export --overlay` proving the route log matches the graph under review, and the second consumer is the csap teardown artifact (`feature-requests/FR-807-route-evidence-record-hardening.md` L8). FR-808 is named as a strict regulated profile that composes this record rather than replacing it (L64-L72). Existing prior art is dispositioned rather than duplicated: FR-723 is the route log/export substrate (FR-723 L54-L78, L176-L188), FR-753 is a separate image-rendering example with no core export changes (FR-753 L65-L72), and FR-759 already owns the OTEL run identity (`reference/otel-observability.md` L53-L62, L68-L75).

Scope is mostly single-responsibility: record hardening only. The FR explicitly defers fail-fatal behavior to FR-808 (`feature-requests/FR-807-route-evidence-record-hardening.md` L45-L46, L64) and preserves the frozen route grammar for ninchat_voice/NC-374 by additive fields and event types only (L47-L48).

## Required revisions

### R-1: Pin one run identity and reuse it across route and OTEL surfaces

Fold this run-identity contract into the Proposed Solution and ACs: every route-log run header and run-end record carries required `run_id`, generated as UUIDv7 using the same run-identity semantics as FR-759's `yamlgraph.run.id`; when OTEL is enabled for the same `yamlgraph graph run` invocation, the route-log `run_id` and OTEL `yamlgraph.run.id` are identical. `thread_id` remains optional checkpoint/session correlation and must not be treated as the run identity. The header, every route line, and `run_end` must be emitted inside one run context so `run_id`, `thread_id`, and counters do not leak across runs.

Rationale: FR-807 says to reuse FR-759's run identity and not invent a second one (`feature-requests/FR-807-route-evidence-record-hardening.md` L68), but the proposed header only shows `thread_id` and `started_at` (L34-L38). FR-759's frozen schema already defines `yamlgraph.run.id` as required UUIDv7 and shared by child spans (`reference/otel-observability.md` L53-L62), and the CLI currently creates that run id inside `graph_run_span()` (`yamlgraph/observability/otel.py` L213-L220) around the `graph run` invocation (`yamlgraph/cli/graph_commands.py` L177-L183). Leaving route evidence to generate a separate identity would break the correlation this FR claims to preserve.

### R-2: Replace "canonical bytes" with an exact artifact manifest hash algorithm

Fold this algorithm into the FR: `artifact_hash` is `sha256:` plus the SHA-256 of a canonical JSON manifest with sorted keys. The manifest contains one entry per included artifact: `{ "path": <repo- or graph-root-relative POSIX path>, "sha256": <sha256 of raw file bytes> }`. The included set is the top-level graph YAML plus every graph-local prompt YAML file resolved through the same prompt-resolution rules used at load/execution time; if the graph references a prompt or graph artifact that cannot be resolved, hashing fails with a clear error and no run header is emitted. If the implementation supports subgraph or graph-tool execution artifacts in this FR, they must be included transitively in the same manifest; otherwise graphs with such unresolved executable graph references must fail hash generation rather than receive an incomplete "executed artifact" hash.

Rationale: "SHA-256 over the canonical bytes of the graph YAML plus every prompt file it references, in sorted path order" is not mechanically enough to prevent delimiter/path-collision ambiguity or prompt-resolution drift (`feature-requests/FR-807-route-evidence-record-hardening.md` L40). The loader currently preserves `source_path` and raw config (`yamlgraph/compile/graph_loader.py` L85-L90), while export currently reads YAML directly with `yaml.safe_load()` instead of the loader (`yamlgraph/cli/export_commands.py` L44-L48). A shared helper is therefore required so run-header emission and `graph export --overlay` compare the same artifact definition.

### R-3: Define overlay-header validation, including missing and malformed headers

Add the overlay validation contract explicitly: `yamlgraph graph export --overlay <route.jsonl>` must require exactly one leading `{"event":"run"}` record before any `route` records. It fails with exit code 1 and a clear diagnostic when the route log has no run header, has multiple run headers, has a malformed/missing `artifact_hash`, or has an `artifact_hash` that differs from the graph being exported. The success path must compare the graph's computed artifact hash with the header hash and then pass only `event:"route"` records to the existing overlay renderer. `parse_route_lines()` remains tolerant and continues to skip non-route records for downstream parsers.

Rationale: FR-807 only pins mismatch failure (`feature-requests/FR-807-route-evidence-record-hardening.md` L54), but a missing or malformed header is the same evidence-binding failure. The current export command accepts any parsed route list and does no header validation (`yamlgraph/cli/export_commands.py` L44-L49), while the parser intentionally skips non-route records (`yamlgraph/mermaid_export.py` L154-L169). Without this revision, the hardening can be bypassed by a legacy route-only file.

### R-4: Specify per-run dropped-event accounting and reset semantics

Replace the bare "counter increment" wording with this contract: a route-log run context initializes `dropped_events = 0` at header emission; every failed attempt to serialize or deliver a `run`, `route`, or `run_end` record to an enabled sink increments the counter exactly once for that record; the graph run itself never raises because of route-log evidence failure; `route_log_dropped_count()` returns the current run's counter while the context is active and the last completed run's counter after exit for tests/diagnostics; `reset_route_log()` clears the counter for test isolation. `run_end` reports `dropped_events` best-effort; if `run_end` itself cannot be emitted, the counter still increments and remains observable through `route_log_dropped_count()`.

Rationale: current emission wraps file-sink setup, serialization, and logging in one `suppress(Exception)` block (`yamlgraph/utils/route_log.py` L112-L129), and tests only assert "never raises" (`tests/unit/test_route_log.py` L244-L252). The FR's AC names an "unwritable sink injected in test" (FR-807 L55), but Python logging handlers may swallow handler errors unless the implementation owns the delivery boundary. The loss contract must be pinned before enforcement or the counter can pass superficial tests while still missing real file-sink failures.

### R-5: Name the exact route-log run entrypoints covered by "any opt-in surface"

Revise "under any opt-in surface" into a testable surface list: every invocation path that currently installs `route_thread_id_from_config()` must also install the route-log run context and emit the header/run_end when route logging is enabled. At minimum this covers the CLI `yamlgraph graph run` helper path (`yamlgraph/cli/graph_run_helpers.py` L170-L184) and the async executor path (`yamlgraph/executor_async.py` L205-L226); direct calls to `emit_route()` outside a run context are not a supported evidence-record surface and must either emit only legacy route records for unit seams or increment the dropped counter with a documented diagnostic. The FR must state which behavior is chosen.

Rationale: the FR says the run header is emitted once per run by "the run entrypoints (the same seam that sets the thread-id contextvar)" (`feature-requests/FR-807-route-evidence-record-hardening.md` L32), but the AC says "any opt-in surface" (L51). The existing route-log opt-ins include env logger-only, env file path, directory path, and graph YAML flag (`yamlgraph/utils/route_log.py` L6-L16); not all of those define a run boundary by themselves.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Route-log run context in `yamlgraph/utils/route_log.py`: run header, per-route `ts`, run-end record, `run_id`, dropped-event counter, reset/test helpers |
| D-2 | Shared artifact-hash helper used by both run-header emission and export-overlay validation |
| D-3 | Run-entrypoint wiring at the existing route-thread-id seams, including CLI graph run and async executor paths named in R-5 |
| D-4 | `graph export --overlay` header/hash validation before rendering |
| D-5 | Graph schema/config support for optional `observability.judgement_ref`, emitted only when declared |
| D-6 | Unit tests for run/header ordering, timestamp shape, hash stability/sensitivity, overlay mismatch/missing-header failures, loss counting, and route-line grammar preservation |
| D-7 | Reference documentation for the expanded route evidence record grammar |
| D-8 | CAP/REQ traceability, pytest requirement markers, and changelog fragment |

Not authorized: fail-fatal route-log strict mode (FR-808); changes to the five existing `event:"route"` field names, types, or meanings; removal of tolerant `parse_route_lines()` behavior for downstream route parsers; LangSmith changes; new OTEL spans or exporter behavior beyond sharing the FR-759 run identity value; regulated-profile defaults/retention policy; image rendering or route-overlay example app work from FR-753; unrelated cost/profile, SOUP, or API-discovery evidence features; broad graph authoring/prompt refactors beyond what the shared artifact-hash helper requires.

## Revised acceptance criteria

- [ ] AC-01: With route logging enabled on each R-5 run-entrypoint path, the first persisted JSON record is `{"event":"run"}` carrying `run_id` (UUIDv7), `artifact_hash`, `graph`, `yamlgraph_version`, `thread_id` (nullable), and `started_at` in ISO-8601 UTC seconds; `judgement` appears only when `observability.judgement_ref` is declared.
- [ ] AC-02: When OTEL is enabled for `yamlgraph graph run`, the route-log `run_id` equals the OTEL `yamlgraph.run.id`; when OTEL is disabled, the route log still gets a UUIDv7 `run_id` using the same helper/semantics.
- [ ] AC-03: The artifact-hash helper is stable across repeated runs of an unchanged graph, changes when the graph YAML changes, changes when any referenced prompt YAML changes, and fails clearly rather than emitting an incomplete hash when a referenced executable graph/prompt artifact cannot be resolved.
- [ ] AC-04: Every `event:"route"` record carries `ts` in ISO-8601 UTC seconds and preserves the existing `event`, `node`, `value`, `target`, and `thread_id` field names, types, and meanings; a grammar regression test proves existing route-line consumers can ignore `run`, `run_end`, and additive fields.
- [ ] AC-05: `yamlgraph graph export --overlay` succeeds only when the route log has exactly one leading run header whose `artifact_hash` matches the graph's computed hash; it fails with a clear diagnostic for missing, malformed, duplicate, or mismatched headers.
- [ ] AC-06: Injected serialization and sink-delivery failures increment `dropped_events` exactly once per failed record, do not raise from the graph run, and are reported in a best-effort `{"event":"run_end","run_id":...,"dropped_events":N}` record; tests prove counter reset/no cross-run leakage.
- [ ] AC-07: Tests are tagged with `@pytest.mark.req(...)` against the routing/observability requirement, traceability closes under `python scripts/req_coverage.py --strict`, and the diff includes the required changelog fragment.
- [ ] AC-08: Reference docs describe the route evidence record grammar, artifact-hash manifest algorithm, header validation behavior, and the explicit non-strict relationship to FR-808.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold R-1 through R-5 into `feature-requests/FR-807-route-evidence-record-hardening.md` before implementation authority activates. | GATE |
| C-2 | Do not emit a run header with an incomplete artifact hash; unresolved referenced artifacts must fail hash generation clearly. | GATE |
| C-3 | Do not treat `thread_id` as a run identity; route evidence and OTEL must share one `run_id` when both are enabled. | GATE |
| C-4 | Preserve the five existing route-line fields and tolerant route-line parsing semantics; NC-374 grammar consumers must not be forced to change for this FR. | GATE |
| C-5 | Do not implement FR-808 fail-fatal strict mode or regulated-profile defaults under this authority. | GATE |

Authority granted: after the required revisions are folded into the FR, the enforcer may implement the additive route evidence record hardening exactly within the surfaces frozen above.
