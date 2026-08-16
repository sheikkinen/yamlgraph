# Feature Request: Regulated Evidence Profile — On-by-Default Emission and Strict Mode

**Priority:** MEDIUM
**Type:** Feature
**Status:** Enforced 2026-08-16 - FR-807 dependency satisfied; AC-01..AC-10 delivered
**Effort:** 1 day
**Requested:** 2026-08-15
**First consumer / first event:** the csap VoiceBot deployment (Tervola pilot, autumn 2026) declaring `observability.profile: regulated` in its graph YAML — the first run where route-log emission cannot be silently absent, well ahead of the AI Act Annex III application date (2 December 2027, as amended by Regulation (EU) 2026/1744) for the deployer's Art. 26(6) log-retention duty.

## Summary

Add a `regulated` observability profile: route-log emission is on by default, disabling it is a recorded exception, and (in strict mode) evidence loss fails the run. Turns the whitepaper's §7 "on-by-default regulated profile" from specified work into shipped behavior.

## Value Statement

Deployers of high-risk-adjacent systems get conformance evidence that is present by construction rather than by remembered configuration — an opt-in evidence channel is found disabled during exactly the incident that mattered (whitepaper review M3).

## Problem

Route logging (FR-723) is opt-in via `YAMLGRAPH_ROUTE_LOG` or `observability.route_log`. The whitepaper review (M3) found the paper's "auto-emitted" claim described aspiration, not implementation; the fold (commit 3b7fbac7) downgraded the claim honestly, and this FR restores it by implementation. Two policy gaps remain after FR-807 hardens the record itself:

1. **Opt-in evidence** — nothing in the artifact plane forces emission; a deployment that forgets the env var produces no evidence and no error.
2. **Best-effort loss handling** — FR-807 counts dropped events but the run still completes green; a regulated deployment may need evidence loss to be fatal, not footnoted.

## Ideal Result

A graph author writes one line — `observability.profile: regulated` — and every run of that artifact emits a complete, self-authenticating route log (FR-807 record) to a declared sink, or refuses to run. Absence of evidence becomes impossible to produce silently; the exception, not the default, is what requires configuration.

## Proposed Solution

**Dependency gate (R-1):** enforcement is blocked until FR-807 is Enforced and its run header, artifact hash, run identity, run-end, and dropped-event counter contracts are available. This FR consumes those contracts; it must not reimplement missing FR-807 record hardening.

```yaml
# graph.yaml
observability:
  profile: regulated          # implies route_log: true; route_log: false is invalid under the profile
  route_log_sink: logs/route/ # REQUIRED: filesystem directory; preflighted writable before execution
  judgement_ref: FR-XXX       # REQUIRED under the profile (feeds the FR-807 header judgement field)
  strict_evidence: true       # optional, default false: dropped_events > 0 fails the run
```

- **Profile schema (R-2):** under `profile: regulated`, `route_log_sink` and `judgement_ref` are required; `route_log` is implied true and `route_log: false` fails validation. Failure phases are pinned: schema/load validation for missing or contradictory fields, then sink preflight before graph execution — fail at startup, not mid-incident, with no header emitted.
- **Sink semantics (R-3):** `route_log_sink` is a filesystem *directory*. Preflight requires it resolvable and writable; missing, file-valued, or non-writable sinks fail before execution. Each run writes a single per-run JSONL file named `<run_id>.route.jsonl` (FR-807 `run_id`) — a per-run retention target, never a shared file or logger-only surface.
- **Override precedence (R-4):**
  1. Under the profile, `YAMLGRAPH_ROUTE_LOG=0` alone is ignored for emission; the run still writes to `route_log_sink`.
  2. The ignored disable emits a stable WARNING with structured fields (profile, graph, sink, env source) assertable via `caplog`.
  3. `YAMLGRAPH_ROUTE_LOG=0` + `YAMLGRAPH_ROUTE_LOG_OVERRIDE=1` disables emission **only when `strict_evidence` is false**, emitting the same stable WARNING plus `override=true` / `recorded_exception=true` markers.
  4. With `strict_evidence: true`, any disable request — including the override pair — is a startup failure: a strict run with knowingly absent evidence must not exist.
- **Strict failure contract (R-5):** with `strict_evidence: true`, after graph execution and after the best-effort FR-807 `run_end` emission attempt, `dropped_events > 0` raises a `PipelineError` naming the count and sink. If `run_end` itself fails, that failure increments the counter and strict mode raises. With `strict_evidence` false, the same injected failure completes the run and leaves `dropped_events` observable through the FR-807 counter surface. (Commandment 6.)
- **Lint (R-6):** exact static diagnostics only, scoped to fields this FR introduces: `profile: regulated` with `route_log: false`; missing `route_log_sink`; missing `judgement_ref`; `strict_evidence`/`route_log_sink` used without the regulated profile. No generic "AI-Act-flavored metadata" scanner.
- **Documentation bound (R-7):** docs update only after behavior ships; wording claims on-by-default route-evidence emission and strict-fatal evidence-loss behavior — never AI Act compliance, conformity, or legal sufficiency; the whitepaper's disclaimers (notes 1, 3) are preserved.

## Acceptance Criteria

- [x] AC-01: With FR-807 Enforced, a fixture graph declaring `profile: regulated`, `route_log_sink: <tmp_dir>`, `judgement_ref: FR-808-test` emits a per-run route JSONL with no env var set; the file begins with the FR-807 `event:"run"` header including the declared judgement reference
- [x] AC-02: Validation fails before execution, with clear diagnostics and no emitted header, when `route_log_sink` is missing/file-valued/non-writable or `judgement_ref` is missing
- [x] AC-03: The profile implies route logging; `route_log: false` under it fails validation; non-regulated graphs retain existing opt-in/off behavior
- [x] AC-04: `YAMLGRAPH_ROUTE_LOG=0` alone does not disable emission under the profile (stable ignored-disable WARNING); the env pair disables only when `strict_evidence` is false (stable recorded-exception WARNING)
- [x] AC-05: Under `strict_evidence: true`, any disable request fails startup; injected serialization/sink failure during an enabled run raises `EvidenceLossError` carrying a structured `PipelineError` at the run boundary after best-effort `run_end`, naming the dropped-event count
- [x] AC-06: Same injected failure with `strict_evidence` false: run completes; FR-807 run-end/counter surface reports `dropped_events > 0`
- [x] AC-07: Existing FR-723 non-regulated route-log tests pass unchanged (env logger-only, env file path, graph flag, disabled zero-overhead); no global route logging introduced
- [x] AC-08: Validation changes are limited to the exact R-6 regulated-profile diagnostics; no generic AI Act metadata scanner
- [x] AC-09: Reference docs and the whitepaper describe shipped behavior and preserve the control-plane and legal-advice disclaimers
- [x] AC-10: Tests marked `@pytest.mark.req(...)`; capability file defines the governing requirement; `python scripts/req_coverage.py --strict` passes; changelog and diary artifacts in diff

## Alternatives Considered

- **Make route logging on-by-default globally:** rejected — forces file I/O and retention concerns on every hello-world run; the profile scopes the posture to artifacts that declare the need.
- **Env-only profile (`YAMLGRAPH_PROFILE=regulated`):** rejected as the primary surface — the evidence posture is a property of the approved artifact, not the deployment shell; env stays as an override channel only. (Config is truth — Commandment 3.)
- **Fold into FR-807:** rejected — record hardening is mechanism with zero policy risk; on-by-default and strict-fatal are policy choices worth their own judgement. Sequencing: FR-807 first.

## Related

- FR-807 (route evidence record hardening — hard dependency for strict mode and header)
- FR-723 (route log), FR-753 (overlay), FR-759 (OTel export precedent for fail-fast-on-missing-extra startup validation)
- Whitepaper review finding M3; docs/whitepaper-auditable-by-construction.md §5, §7
- AI Act Art. 12 (record-keeping), Art. 26(6) (deployer log retention ≥ 6 months)
- csap NC-376 (teardown artifact), Tervola pilot deployment

## Implementation Notes (2026-08-16)

- FR-807 is Enforced and supplies the bound run header, per-run identity, run-end, and loss counter consumed here.
- Added typed regulated-profile validation, required judgement/sink fields, per-run sink preflight, and deterministic `<run_id>.route.jsonl` output.
- Added stable env-disable warnings and strict precedence. Strict loss raises `EvidenceLossError` with the repository's structured `PipelineError` record because `PipelineError` itself is a Pydantic state model, not a throwable exception.
- Existing non-regulated opt-in and frozen route grammar remain unchanged.

**Prior art:** FR-807 route-evidence-record-hardening [Enforced] — hard dependency, mechanism/policy split deliberate (see Alternatives). FR-803 pipecat-flows reassessment [Enforced] — vocabulary overlap only. FR-809 api-discovery-orchestrator-v2 [Enforced, sister session] — noun collision only. 020-soup-generator [Proposed] — SOUP documentation, different artifact class. FR-384 cost-profile-model-tiering [Proposed] — "profile" as cost tier, unrelated.
