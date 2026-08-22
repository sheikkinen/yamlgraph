# Task: FR-776 — add the vision-fallback branch to the book-summary demo graph

Modify ONLY `examples/demos/book-summary/graph.yaml`. Do NOT change any prompt
files (prompts/summarize_page.yaml and prompts/combine_summaries.yaml stay
exactly as they are), do NOT change tools.py (all python helper functions
already exist), do NOT create new demos. This is a wiring change to an
existing, working graph — preserve everything not listed below byte-compatibly
where possible.

Governing FR: feature-requests/FR-776-vision-fallback-scanned-pdf.md
(judged APPROVED WITH REVISIONS; R-1..R-5 folded). The frozen artifact
contract is tests/unit/test_fr776_vision_fallback.py — after authoring,
these tests decide correctness:

    pytest tests/unit/test_fr776_vision_fallback.py -q --no-cov

## Existing graph (keep)

The FR-775 cursor loop: START → probe → gate_probe → … → prepare_batch →
fetch_batch → gate_fetch → … → summarize_pages (map) → accumulate → advance
→ (loop back to prepare_batch | exit) → combine → END. Keep recursion_limit,
prompts_dir, existing tools, existing nodes, and the summarize_pages map
node exactly as-is.

## Required changes

### 1. State additions (all new keys)

```yaml
  vision_fallback: bool
  text_chunks: list
  empty_chunks: list
  render_results: list
  renders: list
  transcriptions: list
  text_seen: bool
  vision_route: str
  render_result: dict
  render: dict
  transcription: dict
```

### 2. Tool declarations (add to tools:)

```yaml
  render_page:
    manifest: ../../shared/render_page.tool.yaml
```
(EXACTLY this shape — the test asserts `set(entry) == {"manifest"}`.)

Plus python tools, all `path: tools.py` (functions already exist):
- `preflight_vision` (function preflight_vision)
- `partition` (function partition_chunks)
- `gate_render` (function gate_render)
- `transcribe_render` (function transcribe_render)
- `merge_vision` (function merge_vision)
- `guard_extractable` (function guard_extractable)

### 3. New nodes

```yaml
  preflight_vision:
    type: python
    tool: preflight_vision

  partition:
    type: python
    tool: partition

  render_pages:
    type: map
    over: "{state.empty_chunks}"
    as: echunk
    max_items: 10
    node:
      type: tool_call
      tool: render_page
      args:
        path: "{state.pdf}"
        page: "{state.echunk.page}"
      state_key: render_result
      on_error: retry
      max_retries: 3
    collect: render_results

  gate_render:
    type: python
    tool: gate_render

  transcribe_pages:
    type: map
    over: "{state.renders}"
    as: render
    max_items: 10
    node:
      type: python
      tool: transcribe_render
      state_key: transcription
      on_error: retry
      max_retries: 3
    collect: transcriptions

  merge_vision:
    type: python
    tool: merge_vision

  guard_extractable:
    type: python
    tool: guard_extractable
```

The tests assert literally: `nodes.render_pages.type == map`, `max_items == 10`,
`collect == "render_results"`, `"empty_chunks" in over`,
`node.on_error == "retry"`; same for transcribe_pages with
`collect == "transcriptions"`. The render subnode must be a valid tool_call
config (the test compiles it standalone with create_tool_call_node and asserts
args resolve: path → the pdf, page → echunk.page).

### 4. Edge rewiring

Replace `gate_probe → prepare_batch` with:
```yaml
  - from: gate_probe
    to: preflight_vision
  - from: preflight_vision
    to: prepare_batch
```

Replace `gate_fetch → summarize_pages` with:
```yaml
  - from: gate_fetch
    to: partition
  - from: partition
    to: render_pages
    condition: "vision_route == 'vision'"
  - from: partition
    to: summarize_pages
    condition: "vision_route == 'direct'"
  - from: render_pages
    to: gate_render
  - from: gate_render
    to: transcribe_pages
  - from: transcribe_pages
    to: merge_vision
  - from: merge_vision
    to: summarize_pages
```
(Tests assert: partition routes to exactly {render_pages, summarize_pages},
every partition edge condition contains "vision_route", and
merge_vision → summarize_pages exists.)

Replace `advance → combine (condition "cursor > total")` with:
```yaml
  - from: advance
    to: guard_extractable
    condition: "cursor > total"
  - from: guard_extractable
    to: combine
```
Keep `advance → prepare_batch (condition "cursor <= total")` unchanged.

### 5. loop_exits and loop_limits

```yaml
loop_exits:
  advance: guard_extractable
```

Add loop_limits entries (value 100, matching existing style) for the new
loop-body nodes: `partition`, `render_pages`, `gate_render`,
`transcribe_pages`, `merge_vision`.

## Validation

- `yamlgraph graph lint examples/demos/book-summary/graph.yaml`
- `pytest tests/unit/test_fr776_vision_fallback.py -q --no-cov` — the graph
  artifact tests and compiled witnesses must pass (some already pass; do not
  regress them).
- Do NOT run the demo against a real provider; unit tests mock poppler and
  the LLM.

**Prior art:** historical authoring brief migrated from tmp/ by FR-852; dispositions in `feature-requests/FR-852-preserve-authoring-briefs.md`.
