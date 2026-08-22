# Feature Request: Scripted Scaffolding for the Real Requirement-Witness Audit Run

**Priority:** MEDIUM
**Type:** Tooling
**Status:** Proposed
**Effort:** 0.5–1 day
**Requested:** 2026-08-22
**First consumer / first event:** the operator, running one command to
produce the first *deflated* audit report — the FR-851 rerun on an
honest full-suite coverage DB, which separates genuine SIM117-class
phantoms from the 235 `[partial]` verdicts currently dominated by the
recording gap.

**Prior art:** FR-851-requirement-witness-audit.md [Enforced] — built
the three-step pipeline this FR scripts (constructor → audit graph →
report); it deliberately left orchestration manual for the first run.
FR-850-req-coverage-usable-form.md [Implemented] — built the shared
coverage-context boundary (hard refusal, 0.25 tripwire) this script
inherits; its census quantified the gap this script closes (1,279
no-link-unrecorded pairs, 64 REQs with unrecorded-only witnesses).
Neither is competing scope: this FR is the runner both assumed.

## Summary

One script (`scripts/req_audit.sh`) runs the FR-851 audit for real:
record an honest full-suite coverage DB (`COVERAGE_CORE=ctrace`,
`--cov-context=test`, sequential), construct questions, map the audit
graph over batches, reconcile the ranked report — and stamp the
artifact set with the git SHA and instrument line so the report can
never outlive the tree it measured.

## Value Statement

The operator gets a re-runnable (monthly-cadence) audit whose verdicts
are about witness substance, not instrument gaps; the 851 pipeline
stops being a one-shot ritual reconstructed from README archaeology.

## Problem

The first FR-851 run (2026-08-22, 412/412 audited) was executed as four
manual steps against a **fast-suite** coverage DB. Consequences, proven
by two instruments the same day:

- FR-850 census: 1,279 of 6,593 test-req pairs are
  `no-link-unrecorded`; 64 REQs have *only* unrecorded witnesses.
- FR-851 report (`tmp/req-audit/report.md`): 10 `[no]` + 235
  `[partial]` verdicts — the majority citing "no-link-unrecorded ...
  resolved_files empty". These are the recording gap wearing an
  audit-verdict costume, not stale witnesses.

Triaging 235 partials by hand before closing the instrument gap wastes
judge effort on what a re-recording clears mechanically. The recording
environment is also easy to get wrong silently: Py3.14 + coverage 7.15
sysmon core breaks `--cov-context=test` without warning (repo memory,
2026-08-22) — `ctrace` + sequential is mandatory and must be encoded in
a script, not remembered.

## Ideal Result

`scripts/req_audit.sh` on a clean tree produces
`tmp/req-audit-<shortsha>/report.md` in one invocation: recorded
contexts ≈ tagged tests for the framework suite, `no-link-unrecorded`
near zero, every artifact (manifest, batches, raw responses, report)
carrying the git SHA and instrument line, and the boundary's hard
refusal (FR-850) aborting the run — not warning — if the recording is
missing, context-free, or poisoned.

## Proposed Solution

```bash
scripts/req_audit.sh [--skip-record] [--out tmp/req-audit-<shortsha>]
```

Four phases, each tee'd to a log in the output dir:

1. **record** — full framework suite, honest instrument:
   `COVERAGE_CORE=ctrace pytest tests/unit tests/integration -q
   --no-cov-report --cov=yamlgraph --cov-context=test` — sequential (no
   `-n auto`), *including* `slow` and `process` marks (they are the
   unrecorded 64). Integration tests missing API keys skip as usual;
   the manifest records the skip count. `--skip-record` reuses an
   existing `.coverage` for constructor/prompt iteration.
2. **construct** — `python scripts/req_audit_questions.py --out $OUT`
   (loads via the FR-850 boundary; hard refusal propagates).
3. **audit** — `yamlgraph graph run
   examples/demos/req_witness_audit/graph.yaml --var
   batches_dir=$OUT/batches --var raw_dir=$OUT/raw --full`.
4. **report** — `python scripts/req_audit_report.py --audit-dir $OUT
   --model ... --provider ...`.

Provenance (graduates the `artifact_carries_code_identity` seed for
this artifact family): the script writes `$OUT/manifest.json` with git
SHA (+ dirty flag), recorded-context count vs tagged-test count,
Python/coverage versions, model, and phase exit codes. `report.md`
header embeds the same line. A report whose SHA does not match the
tree it is read against is self-evidently stale.

Script follows automation doctrine: no `--no-verify`, fails on first
phase error, sequential phases, logs tee'd not swallowed.

## Acceptance Criteria

- [ ] AC-01 `scripts/req_audit.sh` runs phases record→construct→audit→
      report end-to-end; non-zero exit on any phase failure.
- [ ] AC-02 Recording phase uses `COVERAGE_CORE=ctrace`, sequential,
      `--cov-context=test`, and includes slow/process marks — asserted
      by a test on the script's command construction, not by prose.
- [ ] AC-03 `$OUT/manifest.json` carries git SHA + dirty flag,
      instrument line (recorded contexts / tagged tests), model,
      versions; `report.md` header embeds SHA + instrument line.
- [ ] AC-04 FR-850 hard refusal propagates: with a poisoned or missing
      `.coverage` and `--skip-record`, the script exits non-zero
      printing the boundary's remedy — no report is produced.
- [ ] AC-05 One real full run committed as evidence: instrument line
      shows the framework suite recorded (no-link-unrecorded pairs
      reduced by an order of magnitude vs the 1,279 baseline), report
      read raw before aggregates are cited (`read_raw_output_first`).
- [ ] AC-06 Post-run disposition recorded in the FR: residual
      `[no]`/`[partial]` REQs triaged into instrument-gap vs
      SIM117-class phantom vs genuinely thin witness, with counts.
- [ ] Tests tagged to a new REQ under the audit capability; changelog
      fragment; diary entry.

## Alternatives Considered

- **Document the four commands in the README (status quo):** the
  README already does; the first run still happened against the wrong
  DB. Environment-critical invariants (ctrace, sequential) must live
  in executable form — `automation_inherits_doctrine`.
- **A yamlgraph graph orchestrating all four phases:** phases 1/2/4
  are deterministic subprocess/Python steps with no LLM; wrapping them
  in a graph adds framework ceremony around what is one shell contract
  (`is_this_a_graph`: only phase 3 is a graph, and it already is one).
- **Make the pre-commit req-coverage gate consume the full DB:** wrong
  cadence — the full sequential recording takes minutes and belongs to
  a scheduled/manual audit, not every commit. The commit-time gate
  keeps its fast-suite tripwire; the audit script owns honesty.

## Implementation Notes

Squash-merge title: `feat(req-audit): FR-860 scripted scaffolding for
the real witness-audit run`. Enforce order: RED (script-contract
tests) → GREEN (script) → the real run (AC-05) → disposition (AC-06).
