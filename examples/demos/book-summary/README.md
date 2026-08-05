# Book Summary Cursor-Loop Demo (FR-775)

Summarize a PDF book one page at a time, then combine the ordered page
summaries into a final book summary. The demo keeps per-page LLM calls small
while showing how YAMLGraph can orchestrate a finite cursor loop.

## Component tour

```text
START -> probe -> gate_probe -> prepare_batch -> fetch_batch -> gate_fetch
      -> summarize_pages -> accumulate -> advance
      -> prepare_batch while cursor <= total, else combine -> END
```

- **Tool manifest**: `split_document` is declared through
  `examples/shared/split_document.tool.yaml`, so the graph consumes the shared
  PDF splitter without importing Python in YAML.
- **`tool_call` nodes**: `probe` calls `split_document` in `mode: info`;
  `fetch_batch` calls it in `mode: page` with state-derived batch bounds.
- **Python nodes**: `gate_probe`, `prepare_batch`, `gate_fetch`, `accumulate`,
  and `advance` live in demo-local `tools.py` because the hyphenated directory
  name is not importable as a Python module path.
- **Map fan-out with `collect`**: `summarize_pages` maps over the current
  `chunks` window, injects each item as `chunk`, and collects structured page
  summaries into `page_summaries`. Its LLM subnode uses `on_error: retry` so a
  transient malformed response is retried instead of aborting a 400-call run.
- **`add` reducer**: `all_summaries` accumulates only the new per-window
  fragment returned by `accumulate`.
- **`loop_limits` / `loop_exits`**: `advance` has a 100-iteration budget and
  exits to `combine` if the loop budget is reached.
- **Conditional edges**: `advance` routes back to `prepare_batch` while
  `cursor <= total`, otherwise it routes to `combine`.
- **Inline prompt schemas**: `summarize_page.yaml` defines the structured
  `{page, summary}` page output directly in the prompt file.

## Page identity and accumulation

The map node adds `_map_index` values starting at zero for each batch. In a
loop, that means `_map_index` restarts for pages 1-10, 11-20, 21-30, and so on.
Sorting or filtering by `_map_index` cannot identify which batch a result came
from. The shared splitter therefore adds absolute page metadata to every
single-page chunk, and the page prompt echoes `chunk.page` back in the
structured output. `accumulate` selects only summaries whose absolute page is
inside the current `batch_start..batch_end` window before appending them to
`all_summaries`.

The finite budget is 100 loop iterations times 10 pages per window, covering up
to 1000 pages before `loop_exits` routes to `combine` with the summaries already
accumulated.

## Run

```bash
yamlgraph graph run examples/demos/book-summary/graph.yaml \
  --var pdf=examples/demos/book-summary/fixture.pdf --full
```

Requires poppler (`brew install poppler`) for `pdfinfo` and `pdftotext`, plus a
configured LLM provider for the page and combine prompts.

## Fixture provenance

`fixture.pdf` is a committed 2-page PDF generated from the repo-owned
`examples/book_translator/sample_book.txt` (Grimm's Rotkäppchen, public
domain), tripled to force a page break, via macOS cupsfilter:

```bash
for i in 1 2 3; do cat examples/book_translator/sample_book.txt; printf '\n'; done > tmp/book3x.txt
cupsfilter -i text/plain -m application/pdf tmp/book3x.txt > examples/demos/book-summary/fixture.pdf
```
