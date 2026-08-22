# Task: Add retry resilience to book-summary map subnode (FR-775, AC-10 witness fix)

Governing FR: feature-requests/FR-775-book-summary-loop-redesign.md (judged,
authority active). Scope: ONE minimal edit to
examples/demos/book-summary/graph.yaml plus a README sentence.

## Problem (observed on the 418-page real-book witness run)

The provider (deepseek) rejects structured output, so every per-page call
falls back to JSON extraction (FR-464). Across ~418 calls, one response came
back with truncated JSON; the subnode error became a `_error` collect entry
and the accumulate gate correctly aborted the run:

```
page summary failed in window 21-30: Structured output fallback failed:
could not extract JSON from LLM response: {"page": 24, "summary": "Sivulla
kuvataan Pyhäjärven kahakkaa ... (cut mid-string)
```

## Required change

In examples/demos/book-summary/graph.yaml, on the `summarize_pages` map
subnode (the `node:` block), add:

```yaml
      on_error: retry
      max_retries: 3
```

Do NOT change anything else in the graph: node names, args, edges,
loop_limits, loop_exits, state, and prompts are pinned by
tests/unit/test_fr775_loop_redesign.py and must stay as committed in the
working tree.

In README.md, in the component tour, add one sentence noting the subnode
uses `on_error: retry` so a transient malformed response is retried instead
of aborting a 400-call run. Keep the existing budget wording; do not add
the words "unbounded" or "any book".

## Validation (required)

- `yamlgraph graph lint examples/demos/book-summary/graph.yaml`
- `pytest tests/unit/test_fr775_loop_redesign.py tests/unit/test_fr773_document_splitter.py tests/unit/test_fr774_scale_hardening.py -q --no-cov` — all must pass.
- Smoke: `yamlgraph graph run examples/demos/book-summary/graph.yaml --var pdf=examples/demos/book-summary/fixture.pdf --full 2>&1 | tee examples/demos/book-summary/demo-output.log` — must succeed with non-empty all_summaries and book_summary.

Constraints: examples/** only; no yamlgraph/ core changes; do not touch
tmp/book1.pdf; leave files uncommitted.

**Prior art:** historical authoring brief migrated from tmp/ by FR-852; dispositions in `feature-requests/FR-852-preserve-authoring-briefs.md`.
