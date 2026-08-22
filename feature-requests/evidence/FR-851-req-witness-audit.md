# FR-851 Evidence — Requirement Witness Audit, First Real Run

**Date:** 2026-08-22
**Tree:** 33043358 (GREEN commit of the constructor/reconciliation)
**Model:** claude-haiku-4-5 (anthropic), via `examples/demos/req_witness_audit/`
**Stage:** 1 — witness *plausibility* from names and declared links
(`evidence_depth: names`); no entailment claims.

## Run summary

| Metric | Value |
|--------|-------|
| Questions constructed | 412 (one per registry REQ; not hard-coded) |
| Batches | 41 (chars/4 estimator, 8000-token budget) |
| Audited | 412 |
| Unaudited | 0 |
| Rejected batches (hallucinated req_id) | 0 |
| Duplicates | 0 |
| Verdicts | 167 yes / 235 partial / 10 no |

Reconciliation was clean on the first pass: every returned `req_id` was
a verbatim member of its batch's input set. The boundary guard
(`scripts/req_audit_report.py`) fired zero times in anger — but it is
what makes the 412/412 claim checkable rather than assumed.

Raw responses: `tmp/req-audit/raw/batch-*.json` (41 files, not
committed). Ranked report: `tmp/req-audit/report.md`. Reproduce with:

```bash
COVERAGE_CORE=ctrace pytest tests/unit -q --cov=yamlgraph \
  --cov-context=test -m "not slow" -p no:cacheprovider
python scripts/req_audit_questions.py --out tmp/req-audit
yamlgraph graph run examples/demos/req_witness_audit/graph.yaml \
  --var batches_dir=tmp/req-audit/batches --var raw_dir=tmp/req-audit/raw --full
python scripts/req_audit_report.py --audit-dir tmp/req-audit \
  --model claude-haiku-4-5 --provider anthropic
```

## The ten "no" verdicts (worst-witnessed REQs)

REQ-YG-194, REQ-YG-428, REQ-YG-506, REQ-YG-516, REQ-YG-519, REQ-YG-521,
REQ-YG-527, REQ-YG-575, REQ-YG-587, REQ-YG-589.

Pattern: nine of ten are `no-link-unrecorded` REQs with empty
`resolved_files` — mostly example/demo capabilities (novel_fandom,
genesis, shared_vision_tool) whose tests never run under the unit
coverage instrument. The audit's first actionable output is therefore a
*linkage* worklist, not only a test-quality worklist.

## Raw-response citations (read_raw_output_first; ≥5, read before the report)

1. **REQ-YG-001 [yes], batch-000:** the model volunteered "resolved
   files include 29 modules but the declared modules list only 3" — an
   unprompted declared-vs-resolved drift signal. We never asked for
   module-list reconciliation; the payload made it visible and the model
   grabbed it.
2. **REQ-YG-072 [partial], batch-013:** "resolved_files lists only
   logging.py" — the coverage link itself can be a false witness: the
   only source file the diary-feed test touched at runtime was the
   logging module. Coverage linkage measures execution reach, not
   evidence relevance, and the model caught the difference.
3. **REQ-YG-492–495 [all partial], batch-031:** an entire worldgen batch
   of `no-link-unrecorded` tests was uniformly downgraded to partial
   with the exact phrasing "witness plausibility depends entirely on
   test names" — the Stage-1 plausibility framing in the prompt
   demonstrably constrained the verdict semantics.
4. **REQ-YG-575 [no], batch mid-run:** "the witness is purely nominal" —
   nine tests, empty resolved_files; the model went further and guessed
   where the implementation likely lives ("examples/shared_vision_tool/
   nodes.py or similar"), turning a grade into a repair pointer.
5. **REQ-YG-601–603 [partial], batch-040:** doc-witness REQs (FR
   knowledge graph) were *not* graded "no" for touching zero source —
   the resolution-class label did its load-bearing job — yet the model
   still flagged "by name alone; no resolved files confirm the naming
   logic," keeping thinness visible without punishing the class.

## Interpretation caveats

- Stage-1 verdicts are plausibility judgements from names and declared
  links. A "yes" here is not an entailment proof; a "no" on a
  `no-link-unrecorded` REQ is often an instrument gap, not a test gap.
- 245 flagged rows (10 no + 235 partial) at 412 REQs is consistent with
  the payload being names-only; Stage-2 (bodies) escalation via
  `build_stage2_question` exists for the flagged set when a deeper pass
  is warranted.
- No aggregate threshold is applied (`threshold_encodes_forecast`); the
  deliverable is this ranked list.
