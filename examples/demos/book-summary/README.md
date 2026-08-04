# Book Summary Demo (FR-773)

Summarize a PDF book page-by-page, then combine the page summaries into
one book summary — the canonical *feeder tool → map → reduce* pattern
using the shared document splitter declared via a tool manifest (FR-768)
with inline kwargs (FR-772).

## Pipeline

```
split (tool_call: split_document) → summarize_pages (map over chunks) → combine_summaries (llm)
```

- `split` calls the shared splitter with `args: {path: "{state.pdf}", mode: page}`
  and stores the envelope in `split_result`.
- `summarize_pages` fans out over `{state.split_result.result.chunks}`,
  summarizing each page's `{chunk.text}` into `page_summaries`.
- `combine_summaries` reduces the page summaries into `book_summary`.

## Run

```bash
yamlgraph graph run examples/demos/book-summary/graph.yaml \
  --var pdf=examples/demos/book-summary/fixture.pdf --full
```

Requires poppler (`brew install poppler`) for `pdfinfo`/`pdftotext`.

## Fixture provenance

`fixture.pdf` is a committed 2-page PDF generated from the repo-owned
`examples/book_translator/sample_book.txt` (Grimm's Rotkäppchen, public
domain), tripled to force a page break, via macOS cupsfilter:

```bash
for i in 1 2 3; do cat examples/book_translator/sample_book.txt; printf '\n'; done > tmp/book3x.txt
cupsfilter -i text/plain -m application/pdf tmp/book3x.txt > examples/demos/book-summary/fixture.pdf
```

## Shared tool

- Manifest: `examples/shared/split_document.tool.yaml`
- Implementation: `examples/shared/split_document.py` —
  `split_document(path, mode="page", start=None, end=None)` returning
  `{"chunks": [{"index": int, "text": str}], "total": int}`. All
  failures raise `ValueError` naming the condition; no silent fallback.
