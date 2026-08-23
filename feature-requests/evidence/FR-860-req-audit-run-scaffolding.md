# FR-860 Evidence — Real Witness-Audit Run (AC-07/AC-08/AC-09)

**Prior art:** FR-851-requirement-witness-audit.md [Enforced] — this is
the first real run of the pipeline FR-851 built; evidence artifact, not
competing scope. Disposition inherited from FR-860 §Prior art.

Run of `scripts/req_audit.sh` (defaults), 2026-08-23. Bulk raw
responses remain in `tmp/req-audit-daf87e24/raw/` (42 files),
uncommitted per AC-07.

## Provenance (run-manifest.json excerpt)

```json
{
  "git_sha": "daf87e2483bbcc55ecaccf58e749cb17c18a04eb",
  "git_dirty": true,
  "output_dir": "tmp/req-audit-daf87e24",
  "skip_record": false,
  "pytest_command": "COVERAGE_CORE=ctrace pytest tests/unit tests/integration -q --cov-report= --cov=yamlgraph --cov-context=test",
  "coverage_core": "ctrace",
  "recorded_context_count": 3205,
  "tagged_test_count": 6206,
  "skip_count": 103,
  "python_version": "3.14.6",
  "coverage_version": "7.15.2",
  "provider": "anthropic",
  "model": "claude-haiku-4-5"
}
```

All four phases exited 0. Record: 6323 passed, 103 skipped, 1 xfailed
(11m08s). Dirty tree = this FR's own in-progress edits plus a sibling
session's staged brief; recording itself touched nothing.

## Report header (report.md)

```
- Stage: 1 (witness plausibility from names and declared links)
- Model: claude-haiku-4-5 (anthropic)
- Batches: 42
- Reconciliation: 414 audited, 0 unaudited, 0 rejected batches, 0 duplicates
- Provenance: git daf87e24… (DIRTY TREE)
- Instrument: 3205 recorded contexts / 6206 tagged tests
```

## Raw-response observations (read before any aggregate)

Five observations from `raw/batch-*.json`, each with a detail a
generated dump could not produce:

1. **batch-000, REQ-YG-001 [yes]:** verdict cites "30 coverage/ast
   tests directly exercise YAML loading … across cli/helpers,
   graph_loader, and data_loader" — the model counts the evidence rows
   it was given rather than gesturing at the requirement text.
2. **batch-000, REQ-YG-002 [partial]:** flags batch pollution the
   construct stage created, not a witness gap: "commitlint, gitignore,
   precommit hooks" tests bundled into a schema-validation REQ. The
   auditor is grading our question construction as a side effect.
3. **REQ-YG-575 [no]:** catches a nominal witness precisely —
   "resolved files (llm_factory.py, llm_providers.py, logging.py) are
   utility modules, not the describe_image function itself". This is
   the Stage-1 failure mode the audit exists to detect.
4. **REQ-YG-609 [partial]:** the auditor graded this FR's own runner
   REQ and found the honest limit: doc-witness tests against a bash
   script cannot be coverage-linked ("no resolved files and one
   no-link-unrecorded test"). Self-referential and correct.
5. **Response sizes 938–8095 bytes/batch**, all parse as the frozen
   `{verdicts:[{req_id,witnessed,gap,suggestion}]}` shape — no FR-598
   "658-token novel" pathology; 0 rejected batches, 0 hallucinated
   req_ids, 0 duplicates at the reconciliation boundary.

## Aggregates (evidence, not gate — judgement C-4)

- Verdicts: **160 yes / 242 partial / 12 no** (414 audited = 414
  registry REQs; zero unaudited).
- Resolution classes (test-link rows, total 6609):

| class | before (FR-851 fast-suite baseline) | after (full sequential run) |
|---|---|---|
| coverage | — | 3556 |
| doc-witness | — | 1464 |
| no-link-unrecorded | **1279** | **1262** |
| ast | — | 327 |

- Skip count: 103 (integration tests without keys/services; sentinel
  worked — count came from record.log, not assumed).

## AC-09: no-link-unrecorded did NOT fall by an order of magnitude

1,279 → 1,262. The FR-850-era hypothesis — that recording under the
full sequential suite would resolve most unlinked tests — is refuted:
these tests genuinely execute no `yamlgraph/` source. They exercise
shell scripts, CI workflow YAML, markdown doctrine, and `examples/`
code via subprocess — all outside `--cov=yamlgraph`. The runner is not
failed for this (AC-09); the class is renamed honestly by the triage
below.

## Residual triage (12 [no] rows)

- **Instrument-gap (9):** REQ-YG-309 (.chaplain scripts), 516, 519,
  530, 532, 533 (examples/novel_fandom gates/tools), 575 (shared
  vision tool), 587, 589 (fi_domain_crawl graphs) — subject code lives
  outside the coverage instrument; witnesses exist but cannot link.
- **Genuinely thin (3):** REQ-YG-066 (MCP: only `test_list_tools_schema`,
  no per-tool tests), REQ-YG-194 (node-count test claimed as world-context
  witness), REQ-YG-506 (persist test claimed as stub-generation witness).
- **SIM117-class phantom (0):** none among [no] rows this run.

The 242 [partial] rows are dominated by the same instrument-gap class
(doc-witness with empty `resolved_files` on bash/YAML/markdown
subjects) plus batch-pollution noise from construct-stage bundling
(observation 2).

## Blockers cleared en route (owned, condemned, fixed)

- **Coverage-DB clobbering:** 9 nested `python -m pytest` spawns in
  slow-marked tests activated pytest-cov via addopts; the nested
  session combine-deleted the outer run's parallel data file →
  `no such table: context` mass-error wall from ~20%. RED guard
  `tests/unit/test_nested_pytest_cov_guard.py` (7370769e) + `--no-cov`
  at all 9 callsites (326b9695).
- **Exact-case LLM assertion:** fr342 hello contract test required
  `"World"` verbatim from a live model; `tolerant_matching` fix
  (daf87e24) — this failure killed an otherwise-clean 6322-pass run
  at 99%.
