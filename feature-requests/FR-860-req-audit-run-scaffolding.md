# Feature Request: Scripted Scaffolding for the Real Requirement-Witness Audit Run

**Priority:** MEDIUM
**Type:** Tooling
**Status:** Enforced 2026-08-23 — real run complete (see Implementation
Status); judged APPROVED WITH REVISIONS (see
`FR-860-req-audit-run-scaffolding.judgement.md`); R-1..R-5 folded below
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
- FR-851 first run (durable record:
  `feature-requests/evidence/FR-851-req-witness-audit.md`, run summary
  table): verdicts 167 yes / 235 partial / 10 no — and nine of the ten
  `[no]` REQs are `no-link-unrecorded` with empty `resolved_files`.
  These are the recording gap wearing an audit-verdict costume, not
  stale witnesses.

Triaging 235 partials by hand before closing the instrument gap wastes
judge effort on what a re-recording clears mechanically. The recording
environment is also easy to get wrong silently: Py3.14 + coverage 7.15
sysmon core breaks `--cov-context=test` without warning (repo memory,
2026-08-22) — `ctrace` + sequential is mandatory and must be encoded in
a script, not remembered.

## Raw Output Read (R-1)

- **Samples read:** raw model responses of the FR-851 first run
  (`tmp/req-audit/raw/batch-*.json`, 41 files), read before the ranked
  report was trusted; durable citations committed in
  `feature-requests/evidence/FR-851-req-witness-audit.md`
  (Raw-response citations section, ≥5 entries).
- **What I saw** (per the committed evidence artifact):
  1. REQ-YG-001 `[yes]`, batch-000 — the model volunteered
     "resolved files include 29 modules but the declared modules list
     only 3": unprompted declared-vs-resolved drift detection.
  2. REQ-YG-072 `[partial]`, batch-013 — "resolved_files lists only
     logging.py": a coverage link that is itself a false witness;
     execution reach ≠ evidence relevance.
  3. REQ-YG-492–495 all `[partial]`, batch-031 — a worldgen batch
     uniformly downgraded with "witness plausibility depends entirely
     on test names": the Stage-1 framing demonstrably constrained
     verdict semantics.
  4. REQ-YG-575 `[no]` — "the witness is purely nominal", plus the
     model guessed where the implementation likely lives — a grade
     that doubled as a repair pointer.
  5. REQ-YG-601–603 `[partial]`, batch-040 — doc-witness REQs *not*
     punished for touching zero source (the resolution-class label did
     its load-bearing job) while thinness stayed visible.

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
scripts/req_audit.sh [--out DIR] [--skip-record] [--model M] [--provider P]
```

**CLI contract (R-2, frozen):**

- `--out DIR` — output directory; default `tmp/req-audit-<shortsha>`
  (short SHA of HEAD at launch).
- `--skip-record` — reuse the existing `.coverage` (still loaded via
  the FR-850 boundary; refusal propagates).
- `--model M` / `--provider P` — defaults `claude-haiku-4-5` /
  `anthropic` (the FR-851 real-run pin). No environment-variable
  precedence: flags or defaults only — the manifest must record what
  actually ran, and env indirection makes that lie-prone.
- The SAME resolved model/provider values are passed to both the graph
  run (`--var model=… --var provider=…` if the graph accepts them, else
  the graph's pinned model is read back from its YAML) and
  `req_audit_report.py --model … --provider …`; the manifest records
  the exact pair used per phase.
- `--help` documents all of the above.

Four phases, each tee'd to a log in the output dir:

1. **record** — full framework suite, honest instrument:
   `COVERAGE_CORE=ctrace pytest tests/unit tests/integration -q
   --cov-report= --cov=yamlgraph --cov-context=test` — sequential (no
   `-n auto`), *including* `slow` and `process` marks (they are the
   unrecorded 64). Integration tests missing API keys skip as usual;
   the manifest records the skip count. `--skip-record` reuses an
   existing `.coverage` for constructor/prompt iteration.
   *(Deviation recorded at enforce: the judgement's `--no-cov-report`
   is not a pytest-cov flag; the real report-suppression spelling is
   `--cov-report=` — first real run failed exit 4 proving it.)*
2. **construct** — `python scripts/req_audit_questions.py --out $OUT`
   (loads via the FR-850 boundary; hard refusal propagates).
3. **audit** — `yamlgraph graph run
   examples/demos/req_witness_audit/graph.yaml --var
   batches_dir=$OUT/batches --var raw_dir=$OUT/raw --full`.
4. **report** — `python scripts/req_audit_report.py --audit-dir $OUT
   --model $MODEL --provider $PROVIDER`.

**Manifest schema (R-3, frozen):** `$OUT/run-manifest.json` with exactly
these keys — *(deviation from the judgement's `manifest.json` name,
recorded at enforce: `$OUT/manifest.json` is already the FR-851 batch
manifest written by `req_audit_questions.py` and read by
`req_audit_report.py`; the provenance file is therefore
`run-manifest.json` — schema below unchanged)* —

```json
{
  "git_sha": "<full sha>",
  "git_dirty": false,
  "output_dir": "tmp/req-audit-<shortsha>",
  "skip_record": false,
  "pytest_command": "COVERAGE_CORE=ctrace pytest ...",
  "coverage_core": "ctrace",
  "recorded_context_count": 0,
  "tagged_test_count": 0,
  "skip_count": 0,
  "python_version": "3.x.y",
  "coverage_version": "x.y",
  "provider": "anthropic",
  "model": "claude-haiku-4-5",
  "phases": {
    "record":    {"command": "…", "exit_code": 0, "log": "record.log"},
    "construct": {"command": "…", "exit_code": 0, "log": "construct.log"},
    "audit":     {"command": "…", "exit_code": 0, "log": "audit.log"},
    "report":    {"command": "…", "exit_code": 0, "log": "report.log"}
  }
}
```

`git_dirty: true` is allowed (single-dev flow runs mid-work), but the
`report.md` header must display it plainly (`DIRTY TREE`). No
`report.md` is produced when any phase fails — the report's existence
is itself the all-phases-green witness (graduates
`artifact_carries_code_identity` for this artifact family).

Script follows automation doctrine: `set -euo pipefail`, quoted paths,
no `--no-verify`, fails on first phase error, sequential phases, logs
tee'd not swallowed.

**Durable evidence artifact (R-5, frozen):**
`feature-requests/evidence/FR-860-req-audit-run-scaffolding.md` —
manifest excerpt, report header, batch count,
audited/unaudited/rejected/duplicate counts, verdict counts,
before/after resolution-class counts vs the 1,279
`no-link-unrecorded` baseline, skip count, and ≥5 raw-response
observations read before any aggregate claim. Bulk raw responses stay
in `tmp/`, uncommitted.

## Acceptance Criteria (judge-revised; R-4 folded — aggregate
distribution is evidence, not a gate)

- [x] AC-01 `scripts/req_audit.sh` runs phases record → construct →
      audit → report in order, writes one log per phase under `$OUT`,
      exits non-zero on the first failed phase.
- [x] AC-02 CLI supports `--out`, `--skip-record`, `--model`,
      `--provider`; defaults and precedence documented in the FR and
      reflected in `--help`.
- [x] AC-03 Recording command is exactly the full sequential
      framework-suite coverage command (`COVERAGE_CORE=ctrace pytest
      tests/unit tests/integration -q --cov-report= --cov=yamlgraph
      --cov-context=test`; no `-n`, no mark exclusions) — asserted by
      a test on the constructed command.
- [x] AC-04 `--skip-record` reuses `.coverage` only through the FR-850
      boundary; missing/context-free/poisoned coverage exits non-zero,
      prints the boundary remedy, produces no `report.md`.
- [x] AC-05 `$OUT/run-manifest.json` conforms to the frozen schema (all
      keys above, per-phase command/exit/log).
- [x] AC-06 `$OUT/report.md` header embeds git SHA, dirty flag,
      instrument line, provider, model from the manifest.
- [x] AC-07 One real full run recorded in
      `feature-requests/evidence/FR-860-req-audit-run-scaffolding.md`;
      bulk raw responses remain in `tmp/`, uncommitted.
- [x] AC-08 Evidence artifact records before/after resolution-class
      counts vs the 1,279 baseline, skip count,
      batch/audited/unaudited/rejected/duplicate counts, verdict
      counts, and ≥5 raw-response observations read before aggregate
      claims.
- [x] AC-09 Implementation status classifies residual
      `[no]`/`[partial]` rows into instrument-gap vs SIM117-class
      phantom vs genuinely thin witness, with counts; if
      `no-link-unrecorded` does not fall by an order of magnitude, the
      FR records that fact without treating the runner as failed.
- [x] AC-10 Tests tagged to a new/updated audit-capability REQ;
      registry, changelog fragment, diary entry included.

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

## Implementation Status (2026-08-23 — Enforced)

- RED 8810f8f3 (10 script-contract tests, REQ-YG-609) → GREEN c4cbc999
  (`scripts/req_audit.sh`) → flag fix 7abb586f (deviation: pytest-cov
  has no `--no-cov-report`; the frozen command uses `--cov-report=`).
- Deviation: provenance manifest is `run-manifest.json`, not
  `manifest.json` — the latter is FR-851's batch manifest.
- Real run (AC-07): `tmp/req-audit-daf87e24`, all four phases exit 0;
  6323 passed / 103 skipped record, 414/414 REQs audited, 0 rejected
  batches. Evidence:
  `feature-requests/evidence/FR-860-req-audit-run-scaffolding.md`.
- Verdicts: 160 yes / 242 partial / 12 no.
- AC-09: `no-link-unrecorded` 1,279 → 1,262 — did NOT fall by an order
  of magnitude. The FR-850 hypothesis is refuted: these tests execute
  no `yamlgraph/` source (bash, CI YAML, markdown, `examples/` via
  subprocess — outside `--cov=yamlgraph`). Runner not failed for this.
- Residual triage of 12 [no]: 9 instrument-gap (.chaplain/examples
  subjects outside the instrument), 3 genuinely thin (REQ-YG-066,
  -194, -506), 0 SIM117-class phantoms.
- Blockers cleared en route (own commits, condemned first):
  coverage-DB clobbering by 9 nested pytest spawns in slow-marked
  tests (RED 7370769e guard, GREEN 326b9695 `--no-cov`); exact-case
  live-LLM assertion in fr342 (`tolerant_matching`, daf87e24). Four
  failed run attempts preceded these — two venv-less terminals, one
  bad flag, one clobbered DB.
