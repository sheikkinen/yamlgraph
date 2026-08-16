# Feature Request: Route Evidence Record Hardening — Run Header, Timestamps, Loss Counter

**Priority:** HIGH
**Type:** Enhancement
**Status:** Enforced 2026-08-16 - AC-01..AC-08 delivered; route/OTEL/overlay regression suite green
**Effort:** 1.5 days
**Requested:** 2026-08-15
**First consumer / first event:** `yamlgraph graph export --overlay` refusing a route log whose run-header artifact hash does not match the exported graph — the first time a conformance diff can *prove* rather than presume that the executed artifact is the approved one. Second consumer: csap teardown artifact (NC-376) correlating `call_sid` → artifact version from the header.

## Summary

Harden the route decision log (FR-723) from a routing trace into a conformance evidence record: emit a run-header line binding the log to the executed artifact by content hash, add an ISO-8601 UTC timestamp to every event, and count (instead of silently discarding) emission failures.

## Value Statement

Auditors and downstream consumers get a route log that proves *which* artifact produced it and *when* each decision happened, closing findings M2/m1/m2 of the whitepaper review (docs/whitepaper-auditable-by-construction.md, footnote [^5]).

## Problem

The independent review of the auditable-by-construction whitepaper found three record-level gaps in `yamlgraph/utils/route_log.py`:

1. **No artifact identity (review M2; Scripture seed `artifact_carries_code_identity`, now at its second consumer).** The event schema `{event, node, value, target, thread_id}` carries no graph content hash, judgement reference, or framework version. The conformance diff presumes executed == approved; binding today is deployment pinning by inference, confessed in whitepaper footnote [^5].
2. **Silent evidence loss (review m1).** `emit_route` wraps emission in `with suppress(Exception)`. "Never break the run" is right; "never count the loss" is not — it is in tension with Commandment 6 (no silent fallbacks).
3. **No timestamps (review m2).** Route events are undated. AI Act Art. 12(3) requires period-of-use recording for some Annex III systems; Art. 73 incident timelines need it generally.

## Ideal Result

A route log file is self-authenticating: its first line names the exact artifact (content hash over graph + prompts), the framework version, and the run identity; every subsequent event is timestamped; and the log itself states how many events, if any, were lost. Provenance is checked by hash equality, not inferred from impossibility (`artifact_carries_code_identity`).

## Proposed Solution

**1. Run-header line** — emitted once per run by the run entrypoints (the same seam that sets the thread-id contextvar):

```json
{"event":"run","run_id":"01917…","artifact_hash":"sha256:…","graph":"graphs/foo.yaml",
 "yamlgraph_version":"0.5.19","thread_id":"…","started_at":"2026-08-15T18:04:11Z",
 "judgement":"FR-XXX"}
```

- **Run identity (R-1):** the header and `run_end` carry a required `run_id`, generated as UUIDv7 with the same run-identity semantics as FR-759's `yamlgraph.run.id`. When OTel is enabled for the same `graph run` invocation, the route-log `run_id` and the OTel `yamlgraph.run.id` are **identical** (one helper, one value). `thread_id` stays optional checkpoint/session correlation and is never the run identity. Header, route lines, and `run_end` are emitted inside one run context so `run_id`, `thread_id`, and counters cannot leak across runs.
- **`artifact_hash` (R-2):** `sha256:` + SHA-256 of a canonical JSON manifest (sorted keys), one entry per included artifact: `{"path": <graph-root-relative POSIX path>, "sha256": <hash of raw file bytes>}`. Included set: the top-level graph YAML plus every prompt artifact resolved through the same prompt-resolution rules used at load time; subgraph/graph-tool artifacts included transitively where executed. Any unresolvable referenced artifact **fails hash generation with a clear error and no header is emitted** — never an incomplete hash. Implemented as a shared helper used by both run-header emission and `graph export --overlay` (export must not re-derive the artifact via its own `yaml.safe_load` path).
- `judgement`: optional, populated from graph YAML `observability.judgement_ref` when the author declares it; never fabricated.

**2. Per-event timestamp** — additive `"ts"` field, ISO-8601 UTC with seconds precision, on every `route` line.

**3. Loss counter (R-4)** — a route-log run context initializes `dropped_events = 0` at header emission; every failed serialization or sink-delivery attempt for a `run`, `route`, or `run_end` record increments it exactly once for that record; the graph run itself never raises from evidence failure. `route_log_dropped_count()` returns the active run's counter during the run and the last completed run's counter after exit; `reset_route_log()` clears it. `run_end` reports `dropped_events` best-effort — if `run_end` itself cannot be emitted, the counter still increments and remains observable via `route_log_dropped_count()`. Fail-fatal behavior is FR-808's strict mode, not this FR.

**4. Overlay validation (R-3)** — `graph export --overlay` requires exactly one leading `{"event":"run"}` record before any `route` records; exits 1 with a clear diagnostic on missing, duplicate, malformed, or mismatched `artifact_hash`; on success compares the graph's computed hash with the header and passes only `event:"route"` records to the existing renderer. `parse_route_lines()` stays tolerant for downstream parsers.

**5. Covered entrypoints (R-5)** — every invocation path that installs `route_thread_id_from_config()` also installs the run context and emits header/`run_end` when route logging is enabled: at minimum the CLI `graph run` helper path (`cli/graph_run_helpers.py`) and the async executor path (`executor_async.py`). Direct `emit_route()` calls outside a run context emit legacy route records only (unit seams) — they are not a supported evidence-record surface.

**Frozen-grammar constraint (NC-374):** ninchat_voice's parser consumes these lines. All changes are *additive fields* and *new event types*; the five existing `route`-line fields keep name, type, and meaning. The parser ignores unknown fields and unknown `event` values by contract.

## Acceptance Criteria

- [x] AC-01: With route logging enabled on each R-5 entrypoint path, the first persisted JSON record is `{"event":"run"}` carrying `run_id` (UUIDv7), `artifact_hash`, `graph`, `yamlgraph_version`, `thread_id` (nullable), `started_at` (ISO-8601 UTC seconds); `judgement` appears only when `observability.judgement_ref` is declared
- [x] AC-02: With OTel enabled, route-log `run_id` equals OTel `yamlgraph.run.id`; with OTel disabled, the route log still gets a UUIDv7 `run_id` from the same helper
- [x] AC-03: Artifact-hash helper is stable across runs of an unchanged graph, changes on graph or referenced-prompt change, and fails clearly (no incomplete hash) on unresolvable referenced artifacts
- [x] AC-04: Every `route` record carries `ts` (ISO-8601 UTC seconds) and preserves the five existing fields' names/types/meanings; grammar regression test proves existing consumers ignore `run`, `run_end`, and additive fields
- [x] AC-05: `graph export --overlay` succeeds only with exactly one leading run header whose `artifact_hash` matches the graph's computed hash; clear diagnostics for missing/malformed/duplicate/mismatched headers
- [x] AC-06: Injected serialization and sink-delivery failures increment `dropped_events` exactly once per failed record, never raise from the run, and are reported best-effort in `{"event":"run_end","run_id":…,"dropped_events":N}`; tests prove reset / no cross-run leakage
- [x] AC-07: Tests tagged `@pytest.mark.req(...)`; `python scripts/req_coverage.py --strict` closes; changelog fragment in `changelog/unreleased/`
- [x] AC-08: Reference docs describe the record grammar, hash-manifest algorithm, header validation, and the non-strict relationship to FR-808

## Alternatives Considered

- **Hash only the graph YAML, not prompts:** rejected — a prompt edit changes behavior without changing the graph file; the approved artifact is graph + prompts (whitepaper §4 P1).
- **Embed git SHA instead of content hash:** rejected — runs from uncommitted trees or installed packages have no meaningful SHA; content hash is provenance by equality regardless of VCS state. Git SHA may be added as an optional extra field later.
- **Fail the run on evidence loss now:** deferred to FR-808 strict mode — default posture stays "forensic channel must not break the run".

## Related

- FR-723 (route decision log), FR-753 (`graph export --overlay`), FR-759 (OTel run identity — reuse its run-identity notion, do not invent a second one)
- Whitepaper review findings M2, m1, m2 — docs/whitepaper-auditable-by-construction.md footnote [^5]
- Scripture seed `artifact_carries_code_identity`; Commandment 6
- csap NC-374 (frozen line grammar), NC-376 (teardown artifact consumer)
- FR-808 (regulated evidence profile — composes this record)

**Prior art:** FR-723/FR-753/FR-759 are the substrate this extends (route log, overlay, run identity) — built upon, not duplicated. FR-803 pipecat-flows reassessment [Enforced] shares only the regulated/evidence vocabulary (voice-stack architecture, no route-record overlap). FR-809 api-discovery-orchestrator-v2 [Proposed, sister session] — noun collision only (evidence = recon findings). 020-soup-generator [Proposed] — IEC 62304 SOUP dependency documentation, not runtime evidence. FR-384 cost-profile-model-tiering [Proposed] — "profile" as cost tier, unrelated domain.

## Implementation Notes (2026-08-16)

- Added a shared canonical graph/prompt artifact hash used by run headers and overlay validation.
- Added UUIDv7 run context, timestamped additive route fields, best-effort run-end records, and exact loss accounting without changing the five frozen route fields.
- CLI and async entrypoints establish evidence contexts; CLI route and OTEL records share one generated run ID.
- Overlay export now fails closed on missing, malformed, duplicate, or mismatched headers while downstream `parse_route_lines()` remains tolerant.
