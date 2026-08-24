# Authoring brief: FR-875 memory-corpus curation graph

**Governing FR:** feature-requests/FR-875-memory-corpus-curation-graph.md
**Judgement:** feature-requests/FR-875-memory-corpus-curation-graph.judgement.md
(APPROVED WITH REVISIONS; R-1…R-6 folded; C-3 requires this brief + the
sole authoring route.)

**Prior art:** fr-796-authoring-brief.md, fr-782-author-brief*.md — noun
collisions only (brief/memory/curation); unrelated briefs for other
graphs, no territorial overlap. Governing precedent for this brief is
FR-875's own judgement and the FR-868 disposition shape it cites.

## Task

Author `examples/memory-curation/graph.yaml` + prompts: a pipeline that
judges every note in a frozen memory-corpus snapshot and renders a
per-note disposition draft for human review (selective amnesia).

## Pipeline shape

Deterministic code stages already exist as CLI tools (do NOT reimplement
their logic in prompts):

- `examples/memory-curation/nodes/collect.py --memory-root R --out-dir tmp/memory-curation`
  → writes `manifest.json` + `notes/` copies (repo scope only, sanitized).
- `examples/memory-curation/nodes/reconcile.py --manifest M --dispositions D --out-dir O`
  → validates rows (Pydantic), count-in == count-out, renders
  `disposition.md` + `disposition.json` stamped with the manifest hash.

Graph flow:

1. `collect` — shell/python node invoking collect.py with
   `{state.memory_root}` (graph var, REQUIRED — no default in tests) and
   the fixed out-dir `tmp/memory-curation`.
2. `load_notes` — python node reading manifest + note bodies into a list
   of `{path, body}` items.
3. `judge_notes` — **map node** over the items. Per-note prompt: ONE
   judgement, closed inputs (note body, `{state.audience_premise}` graph
   var, today's date). Output schema (inline YAML schema, exact enums):
   - `verdict: keep | redact | forget`
   - `audience: public | peer | customer_private | machine_local`
   - `rationale: str` (one line)
   - `redacted_draft: str | null` — non-empty iff verdict=redact
   - `staleness: fresh | dated | expired`
   - `staleness_evidence: str | null` — non-empty iff dated/expired,
     citing the expiring fact
   The prompt must be BOUNDED: judge meaning (sensitivity, audience,
   staleness), do NOT serialize, do NOT self-correct, do NOT summarize
   the note.
4. `reconcile` — shell/python node invoking reconcile.py on the map
   output.

## Variables

- `memory_root` (required) — path to the memory root to snapshot.
- `audience_premise` (required) — e.g. "public repo workspace;
  worst-case reader: internet".

## Constraints (from the judgement — GATE conditions)

- Outputs ONLY under `tmp/memory-curation/`.
- Repo scope only (collect.py enforces; graph must not widen it).
- No apply/destructive step in the graph — apply.py is separate and
  human-gated.
- Provider: fixture smoke may use any test-safe provider; real corpus
  only vertex/azure per the FR's recorded R-1 approval.

## Validation

- `yamlgraph graph lint examples/memory-curation/graph.yaml` clean.
- Smoke: run against `examples/memory-curation/fixtures/memories` (3-note
  fixture corpus), assert disposition.json covers all 3 notes with zero
  unknown verdicts.

## Precedent

- examples with map nodes over collected items (precedent search per
  doctrine); FR-868 salvage_classify disposition shape.
