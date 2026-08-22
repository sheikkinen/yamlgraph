# Requirement Witness Audit Demo

Grades requirement-witness batches with a haiku-tier LLM (FR-851).
The LLM half of a three-step pipeline; the deterministic halves live in
`scripts/req_audit_questions.py` (constructor) and
`scripts/req_audit_report.py` (boundary reconciliation + ranked report).

## Usage

```bash
# 1. Deterministic: construct questions + batches (no LLM)
python scripts/req_audit_questions.py --out tmp/req-audit

# 2. LLM: grade batches (this demo)
yamlgraph graph run examples/demos/req_witness_audit/graph.yaml \
  --var batches_dir=tmp/req-audit/batches \
  --var raw_dir=tmp/req-audit/raw --full

# 3. Deterministic: reconcile + ranked report
python scripts/req_audit_report.py --audit-dir tmp/req-audit \
  --model claude-haiku-4-5 --provider anthropic
```

## What It Does

1. **list_batches** — enumerates `batch-NNN.json` files deterministically
2. **audit_batches (map)** — one LLM call per batch; typed verdicts
   (`req_id`, `witnessed: yes|partial|no`, `gap`, `suggestion`)
3. **persist_raw** — writes each batch's structured result verbatim to
   `raw_dir` for the deterministic report script

No reconciliation happens in the graph: returned `req_id`s are verified
against batch inputs afterwards in Python (`two_strike_split`).
Names-only payloads (`evidence_depth: names`) yield witness
*plausibility* verdicts, not entailment proofs — the prompt says so.

First real run evidence: `feature-requests/evidence/FR-851-req-witness-audit.md`
(412 REQs, 41 batches, 0 hallucinated ids).
