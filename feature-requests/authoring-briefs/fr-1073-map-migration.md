# FR-1073 Map Migration: Move Unread Map-Level `on_error` Into Sub-Nodes

Governing FR: `feature-requests/FR-1073-map-result-contract.md` (holdings H-1,
H-2; AC-18). Under FR-1073 a map is strict by default: every dispatched item
must succeed unless the failing branch is *tolerated*. Tolerance comes only
from the **sub-node's** `on_error: skip` (or retry exhaustion under it). The
map-level `on_error` and `max_retries` keys were never read by the map
compiler, so the declared skip/retry never took effect.

## Edits (exact; nothing else)

For each map node below, **move** `on_error` (and `max_retries` where
present) from the map level into the map's `node:` block, same values.
Remove them from the map level. Leave every other key, comment, prompt,
variable, edge, and file unchanged.

| Row | File | Map node | Keys moved into `node:` |
|---|---|---|---|
| 2 | `examples/batch_image_prompts/graph.yaml` | `enrich` | `on_error: skip`, `max_retries: 1` |
| 5 | `examples/book_translator/graph.yaml` | `extract_glossary` | `on_error: skip` |
| 6 | `examples/book_translator/graph.yaml` | `translate_all` | `on_error: retry`, `max_retries: 2` |
| 7 | `examples/book_translator/graph.yaml` | `proofread_all` | `on_error: skip` |
| 10 | `examples/daily_digest/graph.yaml` | `analyze_all` | `on_error: skip` |
| 50 | `examples/diary_digest/graph.yaml` | `analyze_all` | `on_error: skip` |
| 59 | `examples/ocr_cleanup/graph.yaml` | `cleanup_pages` | `on_error: skip`, `max_retries: 2` |

Row 27 (H-1): in `examples/demos/map-timeout/graph.yaml`, add
`min_success: 2` to the `process` map node (map level, next to `timeout`).
The demo exists to show one of three tasks timing out; strict would make it
raise. Do not change `tasks.yaml`, `tools.py`, or `timeout`.

Do NOT edit `examples/image_pipeline/graph.yaml` (row 53 stays strict).

## Validation

Lint each edited graph:

```bash
yamlgraph graph lint examples/batch_image_prompts/graph.yaml
yamlgraph graph lint examples/book_translator/graph.yaml
yamlgraph graph lint examples/daily_digest/graph.yaml
yamlgraph graph lint examples/diary_digest/graph.yaml
yamlgraph graph lint examples/ocr_cleanup/graph.yaml
yamlgraph graph lint examples/demos/map-timeout/graph.yaml
```

Narrow smoke: run `examples/demos/map-timeout/graph.yaml` (no LLM) per its
README and record the exact outcome (expected: two results, one
non-tolerated `TimeoutError` failure recorded in `results_failures`, verdict
met via `min_success: 2`, no raise). For the LLM graphs, record a compile check
(`yamlgraph graph info <path>`) and state honestly that no live run was made.

**Prior art:** FR-1073 census table rows 2, 5, 6, 7, 10, 27, 50, 53, 59
(dispositions in the FR); FR-052 `flatten_output` comments preserved.
