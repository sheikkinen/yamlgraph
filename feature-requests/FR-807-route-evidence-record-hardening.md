# Feature Request: Route Evidence Record Hardening — Run Header, Timestamps, Loss Counter

**Priority:** HIGH
**Type:** Enhancement
**Status:** Proposed
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
{"event":"run","artifact_hash":"sha256:…","graph":"graphs/foo.yaml",
 "yamlgraph_version":"0.5.19","thread_id":"…","started_at":"2026-08-15T18:04:11Z",
 "judgement":"FR-XXX"}
```

- `artifact_hash`: SHA-256 over the canonical bytes of the graph YAML plus every prompt file it references, in sorted path order. Computed at load time in `graph_loader` and carried on the compiled graph.
- `judgement`: optional, populated from graph YAML `observability.judgement_ref` when the author declares it; never fabricated.

**2. Per-event timestamp** — additive `"ts"` field, ISO-8601 UTC with seconds precision, on every `route` line.

**3. Loss counter** — replace bare `suppress(Exception)` in `emit_route` with a counter increment (`dropped_events`); expose `route_log_dropped_count()`; the run entrypoints emit a trailing `{"event":"run_end","dropped_events":N}` line (best-effort). Fail-fatal behavior is FR-808's strict mode, not this FR.

**Frozen-grammar constraint (NC-374):** ninchat_voice's parser consumes these lines. All changes are *additive fields* and *new event types*; the five existing `route`-line fields keep name, type, and meaning. The parser ignores unknown fields and unknown `event` values by contract.

## Acceptance Criteria

- [ ] Route log run under any opt-in surface starts with a `{"event":"run"}` header carrying `artifact_hash`, `graph`, `yamlgraph_version`, `thread_id`, `started_at`
- [ ] `artifact_hash` changes when any referenced prompt file changes and is stable across runs of an unchanged artifact (test with two graphs)
- [ ] Every `route` line carries `ts` in ISO-8601 UTC
- [ ] `graph export --overlay` fails with a clear error when the log's `artifact_hash` does not match the graph being exported; succeeds on match
- [ ] Emission failure (e.g. unwritable sink injected in test) increments the dropped counter; `run_end` line reports it; the run itself never raises
- [ ] Existing route-line fields unchanged (grammar regression test)
- [ ] Tests tagged `@pytest.mark.req(...)` against the routing/observability requirement
- [ ] Changelog fragment in `changelog/unreleased/`

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
