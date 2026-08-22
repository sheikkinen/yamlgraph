# Judgement: FR-850 Make the Existing Implementation-Traceability Report Trustworthy and Usable

**Verdict:** APPROVED WITH REVISIONS — the problem is real and correctly rescoped after FR-851, but authority activates only after the FR freezes the coverage-context tripwire, module-reconciliation denominator, derivation disposition, and traceability registration.

**Reviewed against:** `feature-requests/FR-850-req-coverage-usable-form.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/copilot-instructions.md`; `docs/2026-08-21-plan-architecture-claims-pipeline.md`; `docs/diary/diary-2026-08-22-the-spine-is-a-claim-store.md`; `feature-requests/FR-851-requirement-witness-audit.md`; `feature-requests/evidence/FR-851-req-witness-audit.md`; `feature-requests/FR-450-judge-demo-hardening.md`; `feature-requests/FR-269-cli-inter-run-state-chaining.md`; `feature-requests/FR-490-dm-v2-chapter-outline-ui.md`; `feature-requests/FR-364-copilot-instrumentation-gap-closure.md`; `scripts/req_coverage.py`; `scripts/req_audit_questions.py`; `scripts/req_audit_report.py`; `tests/unit/test_req_coverage.py`; `tests/unit/test_fr851_req_audit_red.py`; `capabilities/CAP-243-requirement-witness-audit.yaml`; `capabilities/CAP-18-testing-quality.yaml`.

**Prior art:** dispositioned in the FR's own Prior art line — FR-851 (partial-coverage sibling; this judgement's R-1/R-3 govern the shared-loader and merge disposition), FR-450, FR-269, FR-490, FR-364, FR-593 (noun-level matches only; none touches `req_coverage.py` output or coverage-context integrity — no scope intersection).

## What is sound

The FR names a concrete first consumer and first event: the operator manually running the existing `python scripts/req_coverage.py --implementation` report before deciding whether a later drift-report script is worth building (`feature-requests/FR-850-req-coverage-usable-form.md:8-13`). That satisfies the repo's `would_you_use_this` discipline and avoids building the deferred snapshot/cron machinery prematurely (`feature-requests/FR-850-req-coverage-usable-form.md:34-38`, `docs/2026-08-21-plan-architecture-claims-pipeline.md:548-569`).

The raw-output read is substantive enough for a metric/tooling FR: it cites three full runs, direct SQLite inspection, a Python 3.14/sys.monitoring first-test-wins symptom, the ctrace contrast, the no-link residual, doc-witness reality, and parametrized context mismatches (`feature-requests/FR-850-req-coverage-usable-form.md:65-99`). That meets the local judge requirement to withhold authority until surprising raw samples are read (`.github/skills/judge-fr/doctrine.md:112-117`, `.github/copilot-instructions.md:232-232`).

The diagnosis is confirmed by current code. `req_coverage.py` warns and returns `{}` for missing or context-free `.coverage` DBs (`scripts/req_coverage.py:299-324`), filters coverage links to `yamlgraph/` source only (`scripts/req_coverage.py:345-348`), and prints only AST/unresolved counts in its implementation summary (`scripts/req_coverage.py:495-498`). `req_audit_questions.py` has a separate `_load_recorded_contexts` reader (`scripts/req_audit_questions.py:257-275`), proving the duplicated boundary the FR wants to normalize.

The FR also correctly accounts for FR-851 instead of pretending the earlier scope is unchanged. FR-851 now owns the five-class derivation and documented that FR-850 may later absorb shared logic (`feature-requests/FR-851-requirement-witness-audit.md:121-125`), while its implementation status shows the actual five-class live distribution (`feature-requests/FR-851-requirement-witness-audit.md:212-215`). FR-850's remaining residue is therefore narrower and real.

## Required revisions

### R-1: Freeze the shared coverage-context loader contract

Replace the optional wording "hard refusal or explicit degraded-mode banner" with a single binding policy: for `--implementation` and `req_audit_questions.py`, missing `.coverage`, zero non-empty contexts, or a poisoned coverage-context database is a hard refusal. Non-implementation `req_coverage.py` modes, including `--strict`, must not read this loader.

Define the loader API in the FR before implementation. It must be a single shared helper under `scripts/` used by both consumers, return both normalized `test_id -> source files` and normalized recorded context ids, strip parametrized suffixes such as `[param]` from the final test-id component, and raise one explicit exception type whose message includes `COVERAGE_CORE=ctrace`, `--cov-context=test`, and "sequential" or "no -n auto".

Define the poisoning predicate mechanically in the FR. The predicate must be testable from a synthetic SQLite `.coverage` fixture plus the collected marker set; "contexts << tagged tests" is not precise enough for enforcement (`feature-requests/FR-850-req-coverage-usable-form.md:118-125`, `feature-requests/FR-850-req-coverage-usable-form.md:170-173`).

### R-2: Define the module-reconciliation denominator before reporting anomalies

`req_coverage.py` currently records only `yamlgraph/` files from a `--cov=yamlgraph` database (`scripts/req_coverage.py:345-348`), while capability declarations can point at `scripts` and tests infrastructure (`capabilities/CAP-243-requirement-witness-audit.yaml:19-20`, `capabilities/CAP-18-testing-quality.yaml:4-6`). The FR must state exactly which declared module prefixes are measured.

For this FR, freeze the minimal rule: declared-module-never-hit reconciliation is limited to declared modules that normalize to measured `yamlgraph/` paths. Non-`yamlgraph/` declarations must be reported, if at all, as "unmeasured by this coverage run", not as "declared module never hit." Expanding the coverage source set beyond `yamlgraph/` is not authorized here unless the FR explicitly updates the recording command, loader, and tests for every newly measured prefix.

### R-3: Choose merge over retirement for the 3-class vs 5-class derivation

Remove the option to retire `req_coverage.py --implementation` in this FR. The title, first consumer, first event, summary, and value statement are all about making the existing command usable (`feature-requests/FR-850-req-coverage-usable-form.md:1-13`, `feature-requests/FR-850-req-coverage-usable-form.md:28-38`, `feature-requests/FR-850-req-coverage-usable-form.md:101-108`). Therefore the authorized disposition is: keep `req_coverage.py --implementation`, make it consume the shared five-class derivation, and remove the weaker local three-class truth.

### R-4: Register the new traceability requirement explicitly

AC-06 must name the registry work, not just say "tests tagged with the ADR-001 REQ." Add or update a capability/requirement entry for this FR's implementation-traceability report behavior, covering the shared loader, poisoning refusal, parametrized-context normalization, five-class implementation split, and module-reconciliation question. Tests for this FR must use that REQ id. Existing CAP-243 covers the FR-851 witness audit constructor/report (`capabilities/CAP-243-requirement-witness-audit.yaml:22-48`); CAP-18 covers generic marker enforcement (`capabilities/CAP-18-testing-quality.yaml:8-16`). Neither is a precise standing claim for this FR's `req_coverage.py --implementation` behavior.

### R-5: Move the drift-report delay from acceptance criteria to a follow-up gate

AC-07 is a future-process constraint, not an implementation criterion for this FR: the enforcer cannot prove "before any drift-report FR is filed" inside this change (`feature-requests/FR-850-req-coverage-usable-form.md:185-187`). Move it to a "Deferred follow-up gate" or "Not authorized until" section. The implementation acceptance criteria should check only artifacts this FR can create or modify now.

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | Shared coverage-context loader helper under `scripts/`, used by `scripts/req_coverage.py` and `scripts/req_audit_questions.py` |
| D-2 | `scripts/req_coverage.py --implementation` consumes the shared five-class derivation and reports the full resolution split with denominators |
| D-3 | `scripts/req_audit_questions.py` consumes the shared loader; output changes only for parametrized-context normalization and tripwire-refused cases |
| D-4 | One anomaly-first/question-first implementation report surface, including the measured module-reconciliation question |
| D-5 | Unit tests with synthetic coverage SQLite fixtures and parametrized-context fixtures under `tests/unit/` |
| D-6 | Capability/architecture traceability registration and a changelog fragment |
| D-7 | FR-850 updated with implementation status, decisions, and deviations after enforcement |

Not authorized: `claims_report.py`; weekly snapshot or drift machinery; cron/workflow changes; CI or pre-commit gates; judge/review/graph-authoring doctrine edits; new YAMLGraph graphs or prompts; provider/model changes; broad coverage-source expansion outside the declared module-reconciliation rule; changes to unrelated FR-851 LLM audit behavior beyond consuming the shared loader.

## Revised acceptance criteria

- [ ] AC-01: A single shared coverage-context loader under `scripts/` is used by both `req_coverage.py --implementation` and `req_audit_questions.py`; the duplicated `_load_recorded_contexts` DB read is removed.
- [ ] AC-02: `req_coverage.py` summary, `--detail`, and `--strict` behavior are byte-identical when `--implementation` is not requested.
- [ ] AC-03: Missing `.coverage`, zero non-empty contexts, and the FR-defined poisoned-context predicate hard-fail both `req_coverage.py --implementation` and `req_audit_questions.py`, with an error naming `COVERAGE_CORE=ctrace`, `--cov-context=test`, and sequential/no-`-n auto` recording.
- [ ] AC-04: Synthetic SQLite coverage fixtures cover missing DB, context-free DB, poisoned DB, and healthy DB cases for both consumers.
- [ ] AC-05: Parametrized coverage context ids with `[param]` suffixes normalize to the same marker keys in both consumers, covered by a parametrized test fixture.
- [ ] AC-06: `req_coverage.py --implementation` reports the full five-class split `coverage|ast|doc-witness|no-link-ran|no-link-unrecorded` with totals whose sum equals the implementation-mode test-REQ pair denominator.
- [ ] AC-07: The local three-class derivation is removed or reduced to a thin call into the shared five-class derivation; no second resolution truth remains.
- [ ] AC-08: Declared-module reconciliation is emitted in exactly one question-headed output section and applies only to measured `yamlgraph/` module declarations; unmeasured non-`yamlgraph/` declarations are not reported as never-hit anomalies.
- [ ] AC-09: Every implementation report section is headed by the human question it answers; no unheaded data block remains in the `--implementation` output.
- [ ] AC-10: FR-851 constructor output is unchanged except where parametrized contexts normalize or the shared loader correctly refuses an invalid coverage DB.
- [ ] AC-11: Capability/ARCHITECTURE registry entries describe the new implementation-traceability behavior, and all new/changed tests are tagged with the corresponding REQ id.
- [ ] AC-12: The script help or adjacent documented command shows the correct recording command with `COVERAGE_CORE=ctrace`, `--cov-context=test`, and sequential execution; a changelog fragment is included.

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | R-1 through R-5 must be folded into the FR before implementation begins. | GATE |
| C-2 | The enforcer must not modify `--strict` semantics or the non-implementation report path. | GATE |
| C-3 | Module reconciliation must not turn unmeasured module prefixes into false "never hit" findings. | GATE |
| C-4 | No drift-report, snapshot, cron, CI/pre-commit, or claims-store machinery may be built under this FR. | GATE |
| C-5 | Any need to change enforcement infrastructure, repository doctrine, or judge/review routes must stop this FR and be filed separately for human review. | GATE |

Authority granted after revisions: implement the shared coverage-context boundary and the usable `req_coverage.py --implementation` reporting improvements described above, preserving strict traceability gates and leaving deferred claims-drift automation unbuilt.
