# Judgement: FR-808 Regulated Evidence Profile — On-by-Default Emission and Strict Mode (DRAFT)

**Prior art:** dispositioned in the body and in the FR's own Prior art line — FR-807 (+ its judgement) is the hard mechanism dependency; FR-723/FR-753/FR-759 substrate consumed, not duplicated; FR-803 pipecat reassessment and 020-soup-generator share vocabulary only (voice-stack architecture / SOUP documentation, no profile-policy overlap).

**Verdict:** APPROVED WITH REVISIONS — the regulated evidence profile is the right policy layer over FR-723/FR-807, but authority activates only after the FR pins the FR-807 dependency, required profile fields, sink semantics, override precedence, and strict-failure contract.

**Reviewed against:** `feature-requests/FR-808-regulated-evidence-profile.md`; cited evidence `feature-requests/FR-807-route-evidence-record-hardening.md`; `feature-requests/FR-807-route-evidence-record-hardening.judgement.md`; `feature-requests/FR-723-execution-path-visualization.md`; `feature-requests/FR-723-execution-path-visualization.judgement.md`; `feature-requests/FR-753-route-overlay-example-cli-mmdc.md`; `feature-requests/FR-759-otel-observability-boundary.md`; `feature-requests/FR-759-otel-observability-boundary.judgement.md`; `docs/whitepaper-auditable-by-construction.md`; `feature-requests/FR-803-pipecat-flows-architecture-reassessment.md`; `feature-requests/FR-803-pipecat-flows-architecture-reassessment.judgement.md`; `feature-requests/FR-809-api-discovery-orchestrator-v2-recon-browser-sniff.md`; `feature-requests/FR-809-api-discovery-orchestrator-v2-recon-browser-sniff.judgement.md`; `feature-requests/020-soup-generator.md`; `feature-requests/FR-384-cost-profile-model-tiering.md`; repo doctrine `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`.

## What is sound

The problem is real and belongs above the route-evidence substrate. FR-723 deliberately made route logging opt-in (`feature-requests/FR-723-execution-path-visualization.md:70-76`), while the whitepaper now states that the regulated profile is required work, not shipped behavior (`docs/whitepaper-auditable-by-construction.md:296-301`). FR-808 names the exact gap: a deployment can forget the env/config switch and produce no evidence, and FR-807's counted loss still completes green (`feature-requests/FR-808-regulated-evidence-profile.md:20-23`).

The strategic classification is **framework primitive**. The behavior is not a one-off example: the whitepaper defines regulated profiles as an enforceable framework subset with mandatory route logging and record-level version binding (`docs/whitepaper-auditable-by-construction.md:220-229`), the runtime reference architecture puts route emission in the framework layer (`docs/whitepaper-auditable-by-construction.md:277-283`), and the first consumer is a named regulated deployment event (`feature-requests/FR-808-regulated-evidence-profile.md:8`). That satisfies the first-consumer discipline in repo doctrine (`.github/copilot-instructions.md:125-130`).

The scope is mostly single-responsibility: policy defaults for evidence emission and fail-fatal handling, not record hardening itself. FR-807 explicitly leaves fail-fatal behavior to FR-808 (`feature-requests/FR-807-route-evidence-record-hardening.md:46`, `:69`) and freezes the non-strict dropped-event counter that strict mode should consume (`feature-requests/FR-807-route-evidence-record-hardening.md:46-50`). FR-808 correctly rejects global route logging because it would force file I/O and retention posture onto hello-world graphs (`feature-requests/FR-808-regulated-evidence-profile.md:54-58`).

The proposal honors existing precedent if it stays on the route-log surface. FR-723 owns the public `yamlgraph.route` / `YAMLGRAPH_ROUTE_LOG` route-record mechanism (`feature-requests/FR-723-execution-path-visualization.md:54-78`, `:176-188`); FR-759 is only a run-identity precedent and explicitly parks route spans for later (`feature-requests/FR-759-otel-observability-boundary.md:64-69`; `feature-requests/FR-759-otel-observability-boundary.judgement.md:46-69`); FR-753 is an example renderer and not core runtime behavior (`feature-requests/FR-753-route-overlay-example-cli-mmdc.md:65-72`). The other cited prior art is properly dispositioned as vocabulary-only or unrelated (`feature-requests/FR-808-regulated-evidence-profile.md:68`).

## Required revisions

### R-1: Make FR-807 Enforced a hard activation gate

Fold this dependency into the Proposed Solution, Acceptance Criteria, and Conditions: FR-808 enforcement is blocked until FR-807 is Enforced and its run header, artifact hash, run identity, run-end, and dropped-event counter contracts are available. FR-808 may consume those contracts; it must not reimplement missing FR-807 record hardening under this authority.

Rationale: FR-808's strict criterion depends on the FR-807 counter (`feature-requests/FR-808-regulated-evidence-profile.md:49`) and its ideal result promises the "complete, self-authenticating route log" that FR-807 defines (`feature-requests/FR-808-regulated-evidence-profile.md:25-27`; `feature-requests/FR-807-route-evidence-record-hardening.md:26-50`). FR-807 is still recorded as judged, not completed (`feature-requests/FR-807-route-evidence-record-hardening.md:5`), so treating it as present would authorize implementation against a moving substrate.

### R-2: Complete the regulated profile schema and required evidence fields

Amend the profile contract to require these graph-level fields under `observability.profile: regulated`: `route_log_sink` and `judgement_ref`. `route_log` is implied true; `route_log: false` under the regulated profile is invalid and fails load/preflight with a clear diagnostic. `strict_evidence` remains optional and defaults false. The FR must state the exact schema surface to modify and the exact failure phase: schema/load validation for missing or contradictory fields, followed by sink preflight before graph execution.

Rationale: the whitepaper's regulated-profile requirement includes both artifact content hash and judgement reference in the run record (`docs/whitepaper-auditable-by-construction.md:359-369`, `:487-492`), while FR-807 makes `judgement` optional unless `observability.judgement_ref` is declared (`feature-requests/FR-807-route-evidence-record-hardening.md:40-43`). FR-808's sample requires a sink but omits `judgement_ref` (`feature-requests/FR-808-regulated-evidence-profile.md:31-37`), so the FR currently under-specifies the very binding its evidence claim relies on.

### R-3: Pin route-log sink semantics before implementation

Define `observability.route_log_sink` as a filesystem directory for regulated profile runs. At run preflight, the directory must be resolvable and writable; missing, file-valued, or non-writable sinks fail before graph execution and before any run header is emitted. Each run writes a single route JSONL file under that directory named from the FR-807 `run_id` (for example `<run_id>.route.jsonl`) or another exact deterministic per-run name stated in the FR. Do not leave directory/file/append behavior to the enforcer.

Rationale: FR-808 shows `route_log_sink: logs/route/` and says the profile refuses to start without a writable sink (`feature-requests/FR-808-regulated-evidence-profile.md:31-40`), but the earlier FR-723 implementation record only established path-target semantics for `YAMLGRAPH_ROUTE_LOG=<path>` as a raw JSONL file handler (`feature-requests/FR-723-execution-path-visualization.md:185-188`). Regulated evidence needs a per-run retention target, not an ambiguous shared file or logger-only surface.

### R-4: Freeze override precedence and strict-mode interaction

Replace the env override prose with this precedence contract:

1. Under `profile: regulated`, `YAMLGRAPH_ROUTE_LOG=0` alone is ignored for emission, and the run still writes route evidence to `route_log_sink`.
2. The ignored disable request emits a WARNING with a stable message and structured fields naming the profile, graph, sink, and env source, so tests can assert it with `caplog`.
3. `YAMLGRAPH_ROUTE_LOG=0` plus `YAMLGRAPH_ROUTE_LOG_OVERRIDE=1` disables route logging only when `strict_evidence` is false; it emits the same stable WARNING plus an explicit `override=true` / `recorded_exception=true` marker.
4. With `strict_evidence: true`, any route-log disable request is a startup failure, including the override pair, because disabling the evidence channel contradicts fail-fatal evidence posture.

Rationale: FR-808 says disabling is recorded in the "normal log" and route emission continues unless a second override env is set (`feature-requests/FR-808-regulated-evidence-profile.md:39-41`, `:48`), but it does not state how that interacts with `strict_evidence`. The whitepaper separates "disabling as recorded exception" from "fatal in strict mode" (`docs/whitepaper-auditable-by-construction.md:359-369`); the FR must choose a mechanically testable precedence rather than leave the safety decision to implementation.

### R-5: Specify strict evidence failure at the run boundary

Fold this strict-mode contract into the FR: when `strict_evidence: true`, after graph execution and after the best-effort FR-807 `run_end` emission attempt, if the active run's dropped-event count is greater than zero, the run raises a `PipelineError` whose message includes the count and sink. If `run_end` itself fails, that failure increments the counter and strict mode raises. With `strict_evidence` false, the same injected failure must complete the graph run and leave `dropped_events` observable through the FR-807 run-end/counter surface.

Rationale: FR-808 says "`dropped_events > 0` raises a `PipelineError`" (`feature-requests/FR-808-regulated-evidence-profile.md:41`) but does not pin whether the run-end record is attempted first, how the error is surfaced, or how non-strict behavior proves it still composes with FR-807. Commandment 6 requires explicit error surfacing rather than silent fallbacks (`.github/copilot-instructions.md:218`).

### R-6: Remove the vague AI-Act-flavored lint sweep or replace it with exact static diagnostics

Delete the broad `graph lint` claim, or replace it with exact static diagnostics tied only to fields introduced by this FR. Authorized diagnostics are limited to regulated-profile contradictions such as `profile: regulated` with `route_log: false`, missing `route_log_sink`, missing `judgement_ref`, or `strict_evidence`/`route_log_sink` used without the regulated profile. Do not implement a generic scanner for "AI-Act-flavored metadata."

Rationale: "AI-Act-flavored metadata ... inconsistently" is not mechanically checkable (`feature-requests/FR-808-regulated-evidence-profile.md:42`) and risks an advisory-only compliance theater that repo doctrine explicitly warns against (`.github/copilot-instructions.md:152-158`). The profile needs exact validation and exact tests, not a vocabulary heuristic.

### R-7: Keep documentation claims bounded to engineering evidence, not legal compliance

Revise the whitepaper/docs acceptance criterion so the docs are updated only after behavior ships, and the wording says the regulated profile provides on-by-default route-evidence emission and strict-fatal evidence-loss behavior for YAMLGraph artifacts. Do not claim AI Act compliance, conformity, or legal sufficiency; preserve the whitepaper's disclaimer that the mapping is regulatory interpretation, not legal advice.

Rationale: FR-808 wants whitepaper §5/§7 re-upgraded from "specified work" to shipped (`feature-requests/FR-808-regulated-evidence-profile.md:51`), which is appropriate only if it remains bounded by the whitepaper's own disclaimer (`docs/whitepaper-auditable-by-construction.md:455-461`) and scope limits on control-plane conformance (`docs/whitepaper-auditable-by-construction.md:470-477`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Graph schema/config support for `observability.profile: regulated`, `observability.route_log_sink`, `observability.strict_evidence`, and required `observability.judgement_ref` under the regulated profile |
| D-2 | Regulated-profile route-log enablement/preflight wiring at the same run-entrypoint surfaces covered by FR-807 |
| D-3 | Filesystem sink preflight and deterministic per-run route JSONL path generation under `route_log_sink` |
| D-4 | Env override resolution and stable warning diagnostics for ignored/recorded disable requests |
| D-5 | Strict-evidence run-boundary `PipelineError` when FR-807 dropped-event count is non-zero |
| D-6 | Unit tests for profile defaults, missing/invalid sink, missing judgement ref, env override precedence, strict vs non-strict dropped-event behavior, and non-regulated regression |
| D-7 | Reference/whitepaper updates bounded to shipped engineering behavior and the existing legal disclaimer |
| D-8 | CAP/REQ traceability, pytest requirement markers, `scripts/req_coverage.py --strict`, changelog fragment, and diary reflection required by repo gates |

Not authorized: implementing FR-807 record hardening if it is not already Enforced; changing the five existing `event:"route"` field names/types/meanings; making route logging globally on by default; changing tolerant route parsing or overlay rendering semantics beyond consuming FR-807 records; new OTEL spans/exporters; retention policy engines; legal/compliance certification claims; route-overlay image-rendering work from FR-753; SOUP/cost/API-discovery/pipecat work; graph/prompt authoring; CI, hook, judge/review doctrine, or other enforcement-infrastructure changes.

## Revised acceptance criteria

- [ ] AC-01: With FR-807 Enforced, a fixture graph declaring `observability.profile: regulated`, `observability.route_log_sink: <tmp_dir>`, and `observability.judgement_ref: FR-808-test` emits a per-run route JSONL file with no env var set; the file begins with the FR-807 `event:"run"` header and includes the declared judgement reference.
- [ ] AC-02: Regulated profile validation fails before graph execution, with clear diagnostics and no emitted header, when `route_log_sink` is missing, file-valued, or non-writable, or when `judgement_ref` is missing.
- [ ] AC-03: `observability.profile: regulated` implies route logging; `route_log: false` under the profile fails validation, while non-regulated graphs retain the existing opt-in/off behavior.
- [ ] AC-04: Under the regulated profile, `YAMLGRAPH_ROUTE_LOG=0` alone does not disable route emission and emits the stable ignored-disable WARNING; `YAMLGRAPH_ROUTE_LOG=0` plus `YAMLGRAPH_ROUTE_LOG_OVERRIDE=1` disables route emission only when `strict_evidence` is false and emits the stable recorded-exception WARNING.
- [ ] AC-05: Under `strict_evidence: true`, any route-log disable request fails startup; injected serialization or sink-delivery failure during an enabled run raises `PipelineError` at the run boundary after best-effort `run_end`, and the error names the dropped-event count.
- [ ] AC-06: With the same injected emission failure and `strict_evidence` false, the graph run completes and the FR-807 run-end/counter surface reports `dropped_events > 0`.
- [ ] AC-07: Existing FR-723 non-regulated route-log tests still pass for env logger-only, env file path, graph `observability.route_log: true`, and disabled zero-overhead behavior; no global route logging is introduced.
- [ ] AC-08: Any lint change is limited to exact regulated-profile static diagnostics named in R-6, with tests; no generic AI Act metadata scanner is added.
- [ ] AC-09: Reference docs and `docs/whitepaper-auditable-by-construction.md` describe the shipped regulated-profile behavior and preserve the control-plane and legal-advice disclaimers.
- [ ] AC-10: Tests are marked with `@pytest.mark.req(...)`; a new or updated capability file defines the governing requirement; `python scripts/req_coverage.py --strict` passes; the diff includes required changelog and diary artifacts.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | Fold R-1 through R-7 into `feature-requests/FR-808-regulated-evidence-profile.md` before implementation authority activates. | GATE |
| C-2 | Do not enforce FR-808 until FR-807 is Enforced and available; if FR-807 changes its run-header/counter contract, revise FR-808 before coding. | GATE |
| C-3 | Do not emit regulated-profile evidence without both a writable per-run sink and declared `judgement_ref`. | GATE |
| C-4 | Do not allow route-log disable requests under `strict_evidence: true`; strict mode must fail before execution rather than produce a run with knowingly absent evidence. | GATE |
| C-5 | Preserve non-regulated route-log behavior and FR-723 grammar; regulated defaults must not leak into ordinary graphs. | GATE |
| C-6 | Documentation must not claim regulatory compliance or legal sufficiency; it may claim only the implemented engineering evidence behavior. | GATE |

Authority granted: after the required revisions are folded and FR-807 is Enforced, the enforcer may implement only the regulated observability profile defaults, sink preflight, override diagnostics, and strict dropped-evidence failure behavior frozen above.
