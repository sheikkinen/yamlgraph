# Task Brief: Requirement-Witness Audit Graph (FR-851)

## Task

Author a yamlgraph demo that grades requirement-witness batches with a
haiku-tier LLM. This is the LLM half of FR-851; the deterministic halves
(question construction, reconciliation) already exist as
`scripts/req_audit_questions.py` and `scripts/req_audit_report.py` and
must NOT be reimplemented in the graph.

## Target

- Directory: `examples/demos/req_witness_audit/`
- Artifacts: `graph.yaml`, `prompts/audit_batch.yaml` (names may vary if
  the route's conventions differ; record in the report)

## Contract

Input (graph vars):

- `batches_dir` — directory of batch files (default
  `tmp/req-audit/batches/`). Each file `batch-NNN.json` is a JSON list
  of question payloads. Each payload has: `req_id`, `req_text`,
  `cap_id`, `cap_name`, `declared_modules`, `tests` (list of
  `{test_id, resolution}` where resolution ∈
  coverage|ast|no-link-ran|no-link-unrecorded|doc-witness),
  `resolved_files`, `evidence_depth`, `question`.
- `raw_dir` — output directory for raw verdicts (default
  `tmp/req-audit/raw/`).

Behavior:

1. Enumerate batch files in `batches_dir` (deterministic order).
2. Map over batches (parallel map node; `on_error: retry` per item).
3. Per batch: one LLM call. The prompt instructs the model to grade each
   requirement in the batch: is the requirement properly witnessed by
   the listed tests and resolved files? The resolution class is
   load-bearing context: `doc-witness` tests assert documentation
   contracts and legitimately touch zero source; `no-link-*` means the
   linkage instrument recorded nothing, not that the test is worthless.
   Verdicts from names-only payloads (`evidence_depth: names`) are
   witness *plausibility* judgements, not entailment proofs — the
   prompt must say so.
4. Structured output per batch (inline Pydantic schema in the prompt
   YAML): `verdicts` — list of `{req_id: str,
   witnessed: "yes"|"partial"|"no", gap: str, suggestion: str}`.
   One verdict per input requirement; `req_id` must be copied verbatim
   from the input.
   Keep `gap` and `suggestion` to one sentence each.
5. Persist each batch's structured result verbatim to
   `<raw_dir>/<batch-stem>.json` (same stem as the input batch file).
   Do NOT aggregate, filter, or reconcile in the graph — the
   deterministic report script consumes the raw files afterwards.

Model: haiku-tier (e.g. `claude-haiku-4-5`), provider `anthropic` via
the standard factory defaults; do not hardcode a provider import.

## Precedent

`examples/demos/map` (map node fan-out). Prefer its state/map idioms.

## Validation

- `yamlgraph graph lint examples/demos/req_witness_audit/graph.yaml`
- Smoke: run against a 2-batch fixture dir (author may generate two tiny
  batch files under `tmp/req-audit-smoke/batches/` with 1–2 question
  payloads each) and confirm raw output files appear with parseable
  verdicts.

## Out of scope

Reconciliation, report rendering, retries beyond per-item `on_error`,
CI wiring, scheduled automation, changes to scripts/.

**Prior art:** historical authoring brief migrated from tmp/ by FR-852; dispositions in `feature-requests/FR-852-preserve-authoring-briefs.md`.
