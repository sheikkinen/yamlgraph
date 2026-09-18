# FR-1050 demo migration brief — remove inert `loop_limits` entries

**Prior art:** `fr-775-book-summary-loop-brief.md` and
`fr-773-book-summary-brief.md` authored the book-summary cursor loop and its
`loop_limits` block; this brief subtracts the entries they added on unsupported
node types and does not otherwise touch their design. `fr-827-gitclaw-authoring-brief.md`,
`fr-790-authoring-brief.md` and `fr-1034-census-brief-model-brief.md` match only
on the shared "authoring brief" vocabulary — different graphs, no overlap.

## Task

Two in-repo demo graphs declare graph-level `loop_limits` entries on node
types that never enforce them. FR-1050 makes such an entry a compile error,
so these graphs no longer load. Remove exactly the inert entries, and record
in each graph that the removed bound was never live.

## Target artifacts

1. `examples/demos/multi-turn/graph.yaml`
   - Remove the `wait_for_user: 50` entry from `loop_limits`.
     `wait_for_user` is an `interrupt` node; the interrupt factory never reads
     `loop_limit`, so the bound was inert.
   - Keep `respond: 50` (an `llm` node — enforced).

2. `examples/demos/book-summary/graph.yaml`
   - Remove these four `loop_limits` entries:
     - `fetch_batch` (type `tool_call` — no counter)
     - `render_pages` (type `map` — compiled without a counter)
     - `transcribe_pages` (type `map`)
     - `summarize_pages` (type `map`)
   - Keep every remaining entry (all `python` nodes — enforced).
   - Do not touch `loop_exits` (`advance: guard_extractable`), node
     definitions, edges, tools, or state.

## Required comment

In each graph, above the `loop_limits` block, add one short comment line
stating that the removed entries were never enforced (FR-1050), so a future
author does not re-add them. Do not add any other prose.

## Constraints

- Change ONLY the `loop_limits` blocks and add the one comment line per graph.
- No behavior change is intended: the removed entries never bound anything.
- Both graphs must pass `yamlgraph graph lint <path>`.
- Smoke runs of these demos require a PDF/provider and interactive input; if a
  smoke run is not possible, record that honestly under `Blocked validation`
  rather than claiming success.

## Governing FR

`feature-requests/FR-1050-loop-limits-bind-or-fail.md` (D-4, AC-10) and its
judgement `feature-requests/FR-1050-loop-limits-bind-or-fail.judgement.md`
(gate C-5).
