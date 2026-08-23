# Judgement: FR-860 Scripted Scaffolding for the Real Requirement-Witness Audit Run

**Verdict:** APPROVED WITH REVISIONS — the runner is the right next tool, but authority activates only after the FR replaces volatile evidence with a raw-output-read section, freezes model/provenance semantics, and removes the forecast-shaped no-link reduction gate.

**Reviewed against:** `feature-requests/FR-860-req-audit-run-scaffolding.md`; `feature-requests/FR-850-req-coverage-usable-form.md`; `feature-requests/FR-850-req-coverage-usable-form.judgement.md`; `feature-requests/FR-851-requirement-witness-audit.md`; `feature-requests/evidence/FR-851-req-witness-audit.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`.

**Prior art:** dispositioned in the parent FR (FR-851 [Enforced] built the pipeline this runner scripts; FR-850 [Implemented] built the boundary it inherits — see FR-860's Prior art section); this artifact judges that FR, it does not compete with either.

## What is sound

The FR names a real first consumer and first event: the operator running one command to produce the first deflated FR-851 audit report from an honest full-suite coverage DB (`feature-requests/FR-860-req-audit-run-scaffolding.md:8-12`). That satisfies the repo's value-proposition discipline and avoids abstract automation.

The scope is mostly minimal. It scripts the already-built FR-851 constructor -> graph -> report sequence (`feature-requests/FR-860-req-audit-run-scaffolding.md:25-30`, `feature-requests/FR-851-requirement-witness-audit.md:195-206`) instead of inventing new audit logic, new graph semantics, or scheduled drift machinery. The prior-art section correctly distinguishes FR-850 and FR-851 from this runner (`feature-requests/FR-860-req-audit-run-scaffolding.md:14-21`).

The architectural split is also sound: deterministic shell/Python orchestration remains outside YAMLGraph, while the existing LLM audit stage stays a graph (`feature-requests/FR-860-req-audit-run-scaffolding.md:83-89`, `feature-requests/FR-860-req-audit-run-scaffolding.md:130-133`). That aligns with the local `is_this_a_graph` doctrine without wrapping subprocess plumbing in a graph costume (`.github/copilot-instructions.md:128-133`).

The proposal carries forward important safety boundaries: FR-850's hard refusal for missing/context-free/poisoned coverage (`feature-requests/FR-850-req-coverage-usable-form.md:118-129`), provenance stamping (`feature-requests/FR-860-req-audit-run-scaffolding.md:91-96`), fail-fast phase behavior (`feature-requests/FR-860-req-audit-run-scaffolding.md:98-99`), and traceability/changelog/diary work (`feature-requests/FR-860-req-audit-run-scaffolding.md:121-122`).

## Required revisions

### R-1: Add a raw-output-read section and replace volatile evidence citations

This is a measurement/tooling FR. Local judge law withholds authority until the FR evidences `read_raw_output_first`: cited samples with concrete surprising details, not only aggregate counts (`.github/skills/judge-fr/doctrine.md:112-117`, `.github/copilot-instructions.md:229-233`). FR-860 cites the old report at `tmp/req-audit/report.md` (`feature-requests/FR-860-req-audit-run-scaffolding.md:46-49`), but the durable FR-851 evidence says that ranked report and raw responses lived under `tmp/` and were not committed (`feature-requests/evidence/FR-851-req-witness-audit.md:26-27`).

Fold a `## Raw Output Read` section into FR-860 before enforcement. It must cite committed evidence for the old run, preferably `feature-requests/evidence/FR-851-req-witness-audit.md`, including at least five raw-response observations with details like the declared-vs-resolved drift, logging-only false witness, worldgen names-only partials, pure nominal witness, and doc-witness handling (`feature-requests/evidence/FR-851-req-witness-audit.md:50-75`). If the FR wants to rely on the old `235 partial / 10 no` claim, cite the durable evidence line carrying that count (`feature-requests/evidence/FR-851-req-witness-audit.md:19`) and stop presenting the uncommitted `tmp/req-audit/report.md` as evidence.

### R-2: Freeze model/provider and command-line semantics

The proposed script signature exposes only `--skip-record` and `--out` (`feature-requests/FR-860-req-audit-run-scaffolding.md:70-72`), but the report phase contains unresolved `--model ... --provider ...` placeholders (`feature-requests/FR-860-req-audit-run-scaffolding.md:88-89`) and the manifest is required to record the model (`feature-requests/FR-860-req-audit-run-scaffolding.md:91-95`). That is not mechanically enforceable.

Revise the FR to define the exact CLI contract: accepted flags, defaults, environment-variable precedence if any, and how the same provider/model values are passed to both graph execution and report assembly. The default may follow the FR-851 real run (`claude-haiku-4-5` / `anthropic`, `feature-requests/evidence/FR-851-req-witness-audit.md:3-6`), but the FR must say so explicitly. Tests must assert that the manifest records the exact provider/model used.

### R-3: Make provenance and artifact schema mechanically checkable

The FR names `manifest.json`, git SHA, dirty flag, instrument line, versions, model, and phase exit codes (`feature-requests/FR-860-req-audit-run-scaffolding.md:91-96`), but does not freeze keys, failure behavior, or stale-artifact policy. That leaves AC-03 open to shape-only compliance, a known local trap (`.github/copilot-instructions.md:87-90`).

Add a manifest schema to the FR. At minimum it must define keys for `git_sha`, `git_dirty`, `output_dir`, `skip_record`, `pytest_command`, `coverage_core`, `recorded_context_count`, `tagged_test_count`, `skip_count`, `python_version`, `coverage_version`, `provider`, `model`, and a per-phase object containing command, exit code, and log path. Define whether `git_dirty: true` is allowed; if allowed, the report header must display it plainly. Define that no `report.md` is produced when any phase fails.

### R-4: Replace the order-of-magnitude acceptance gate with an observation-and-disposition gate

AC-05 requires the full run to show `no-link-unrecorded` reduced by an order of magnitude versus 1,279 (`feature-requests/FR-860-req-audit-run-scaffolding.md:114-117`). That is a forecast about the current test corpus and local credentials, not a property of the runner. The same FR acknowledges integration tests may skip when API keys are absent and only records skip count (`feature-requests/FR-860-req-audit-run-scaffolding.md:76-82`). The doctrine warns that aggregate gates on multi-defect surfaces test a forecast of residual distribution instead of the fix under review (`.github/copilot-instructions.md:95-96`).

Revise AC-05 to gate on honest recording, provenance, and disposition. The evidence artifact must record before/after `no-link-unrecorded` counts and compare them to the 1,279 baseline, but implementation authority must not depend on a promised order-of-magnitude improvement. If the reduction does not occur, the FR must record that result and classify the residual causes instead of letting the script fail a correct run.

### R-5: Freeze the durable evidence artifact and residual triage shape

AC-05 says a real full run is "committed as evidence" and AC-06 says post-run disposition is recorded in the FR (`feature-requests/FR-860-req-audit-run-scaffolding.md:114-120`), but neither defines the evidence path or required content. FR-851 established the durable pattern: bulk raw stays in `tmp/`, while a curated evidence markdown under `feature-requests/evidence/` carries run metadata, reconciliation summary, and raw-response citations (`feature-requests/FR-851-requirement-witness-audit.md:143-148`, `feature-requests/evidence/FR-851-req-witness-audit.md:1-37`).

Revise FR-860 to require `feature-requests/evidence/FR-860-req-audit-run-scaffolding.md` as the committed evidence artifact. It must include the manifest excerpt, report header, batch count, audited/unaudited/rejected/duplicate counts, verdict counts, before/after resolution-class counts, skip count, and at least five raw-response observations read before aggregate claims. The FR's implementation status must then summarize residual `[no]`/`[partial]` rows into instrument-gap, SIM117-class phantom, and genuinely thin-witness counts.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `scripts/req_audit.sh` orchestration script |
| D-2 | Targeted tests for script command construction, failure propagation, `--skip-record`, and manifest/report-header behavior under `tests/unit/` |
| D-3 | Minimal changes to `scripts/req_audit_report.py` only if needed to embed/report provenance already produced by the runner |
| D-4 | Committed evidence artifact `feature-requests/evidence/FR-860-req-audit-run-scaffolding.md` |
| D-5 | FR-860 implementation status/disposition update |
| D-6 | Capability/requirement traceability registration, changelog fragment, and diary entry |

Not authorized: new YAMLGraph graphs or prompt files; graph-authoring-route changes; judge/review doctrine changes; CI, pre-commit, cron, scheduler, or claims-drift machinery; `claims_report.py`; provider factory changes; changes to FR-850's coverage-context boundary beyond invoking its existing refusal; expansion of coverage source scope beyond the FR-850 measured-`yamlgraph/` contract; committing bulk raw model responses from `tmp/`.

## Revised acceptance criteria

- [ ] AC-01: `scripts/req_audit.sh` runs phases `record -> construct -> audit -> report` in order, writes one log per phase under `$OUT`, and exits non-zero on the first failed phase.
- [ ] AC-02: The script CLI supports `--out`, `--skip-record`, `--model`, and `--provider`; defaults and environment-variable precedence are documented in the FR and reflected in `--help`.
- [ ] AC-03: The recording command is exactly the full sequential framework-suite coverage command: `COVERAGE_CORE=ctrace pytest tests/unit tests/integration -q --no-cov-report --cov=yamlgraph --cov-context=test`, with no `-n` and no mark exclusions; a test asserts the constructed command.
- [ ] AC-04: `--skip-record` reuses the existing `.coverage` only through the FR-850 coverage-context boundary; missing, context-free, or poisoned coverage exits non-zero, prints the boundary remedy, and produces no `report.md`.
- [ ] AC-05: `$OUT/manifest.json` conforms to the frozen manifest schema and records git SHA, dirty flag, output dir, skip-record state, pytest command, coverage core, recorded-context/tagged-test counts, skip count, Python/coverage versions, provider, model, and per-phase command/exit/log path.
- [ ] AC-06: `$OUT/report.md` header embeds the git SHA, dirty flag, instrument line, provider, and model from the manifest.
- [ ] AC-07: A real full run is recorded in `feature-requests/evidence/FR-860-req-audit-run-scaffolding.md`; bulk raw responses remain under `tmp/` and are not committed.
- [ ] AC-08: The evidence artifact records before/after resolution-class counts against the 1,279 `no-link-unrecorded` baseline, skipped-test count, batch/audited/unaudited/rejected/duplicate counts, verdict counts, and at least five raw-response observations read before aggregate claims.
- [ ] AC-09: FR-860's implementation status classifies residual `[no]`/`[partial]` rows into instrument-gap, SIM117-class phantom, and genuinely thin-witness counts; if `no-link-unrecorded` does not fall by an order of magnitude, the FR records that fact without treating the runner as failed.
- [ ] AC-10: Tests are tagged to a new or updated audit-capability REQ; the capability registry, changelog fragment, and diary entry are included.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | R-1 through R-5 must be folded into the FR before implementation begins. | GATE |
| C-2 | The enforcer must not modify graph or prompt artifacts under `examples/demos/req_witness_audit/`; this FR invokes the existing graph only. | GATE |
| C-3 | `--skip-record` must not bypass the FR-850 hard-refusal boundary or provenance recording. | GATE |
| C-4 | Aggregate outcome distribution is evidence, not an implementation gate; do not fail a correct runner because the corpus remains legitimately thin or skipped. | GATE |
| C-5 | Any need to change CI, pre-commit hooks, judge/review doctrine, graph-authoring doctrine, scheduled automation, or claims-drift machinery stops this FR and requires a separate human-reviewed FR. | GATE |
| C-6 | Shell execution must be fail-fast and path-safe: `set -euo pipefail`, quoted user-controlled paths/arguments, and no swallowed phase failures. | GATE |

Authority granted after revisions: implement the single scripted runner for the existing FR-851 audit pipeline, with frozen provenance, honest full-suite recording, durable evidence, and residual-disposition reporting only within the surfaces listed above.
