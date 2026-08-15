# Feature Request: Regulated Evidence Profile — On-by-Default Emission and Strict Mode

**Priority:** MEDIUM
**Type:** Feature
**Status:** Proposed
**Effort:** 1 day
**Requested:** 2026-08-15
**First consumer / first event:** the csap VoiceBot deployment (Tervola pilot, autumn 2026) declaring `observability.profile: regulated` in its graph YAML — the first run where route-log emission cannot be silently absent, ahead of the AI Act Annex III application date of 2 Aug 2026 for the deployer's Art. 26(6) log-retention duty.

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

```yaml
# graph.yaml
observability:
  profile: regulated          # implies route_log: true
  route_log_sink: logs/route/ # required under the profile; refuses to start without a writable sink
  strict_evidence: true       # optional: dropped_events > 0 fails the run at run_end
```

- `profile: regulated` sets `route_log: true` at compile time and **validates at load** that a sink is resolvable and writable — fail at startup, not mid-incident.
- Env `YAMLGRAPH_ROUTE_LOG=0` under the regulated profile does **not** silently disable: it logs a WARNING `regulated profile: route log disable requested via env — recorded exception` and keeps emitting, unless `YAMLGRAPH_ROUTE_LOG_OVERRIDE=1` is also set (the recorded exception: both lines land in the normal log).
- `strict_evidence: true`: at run end, `dropped_events > 0` raises a `PipelineError` — evidence loss is a run failure, per Commandment 6.
- `graph lint` warns when a graph names AI-Act-flavored metadata (judgement ref, regulated profile fields) inconsistently — advisory only, no new gate in this FR.

## Acceptance Criteria

- [ ] `observability.profile: regulated` enables route logging with no env var set (test: run graph, log exists)
- [ ] Startup fails with a clear error when the profile is set and no writable sink resolves
- [ ] `YAMLGRAPH_ROUTE_LOG=0` alone does not disable emission under the profile; warning line recorded; override env pair disables and records the exception
- [ ] `strict_evidence: true` + injected emission failure → run fails; without the flag the same run completes and reports `dropped_events` (depends on FR-807 counter)
- [ ] Non-regulated graphs are byte-for-byte unaffected (opt-in behavior regression test)
- [ ] Whitepaper §5/§7 updated: on-by-default claims re-upgraded from "specified work" to shipped, citing this FR
- [ ] Tests tagged `@pytest.mark.req(...)`; changelog fragment in `changelog/unreleased/`

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

**Prior art:** FR-807 route-evidence-record-hardening [Proposed] — hard dependency, mechanism/policy split deliberate (see Alternatives). FR-803 pipecat-flows reassessment [Enforced] — vocabulary overlap only. FR-809 api-discovery-orchestrator-v2 [Proposed, sister session] — noun collision only. 020-soup-generator [Proposed] — SOUP documentation, different artifact class. FR-384 cost-profile-model-tiering [Proposed] — "profile" as cost tier, unrelated.
