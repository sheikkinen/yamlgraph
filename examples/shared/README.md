# Shared Utilities

Reusable tools for YAMLGraph examples.

## Available Tools

### `websearch.py` - Web Search

DuckDuckGo-based web search. No API key required.

```yaml
# In agent node
tools:
  search_web:
    type: python
    module: examples.shared.websearch
    function: search_web
    description: "Search the web for information"
```

**Requirements:** `pip install ddgs`

### `replicate_tool.py` - Image Generation

Replicate API for image generation with multiple model presets.

| Model | Best For | Speed |
|-------|----------|-------|
| `z-image` | Realistic/photographic (default) | Fast |
| `hidream` | Cartoons, illustrations, stylized | Fast |

```python
from examples.shared.replicate_tool import generate_image, ImageResult

result: ImageResult = generate_image(
    prompt="A mystical forest at dawn",
    output_dir="outputs/images",
    model="z-image"  # or "hidream"
)
```

**Requirements:** `pip install replicate` + `REPLICATE_API_TOKEN` env var

### `vision_tool.py` - Image Understanding (FR-769)

Multimodal image→text: describe, tag, or QA-check an image with a
vision-capable LLM. The read-direction complement to `replicate_tool.py`.

```python
from examples.shared.vision_tool import describe_image, ImageDescription

result: ImageDescription = describe_image(
    "outputs/images/concept_3.png",     # local path or https:// URL
    "Title, 2-sentence description, and 8 DeviantArt tags.",
)
```

```yaml
# In a graph — via manifest (FR-768, preferred for shared tools)
tools:
  describe_image:
    manifest: ../../shared/describe_image.tool.yaml

# Or inline
tools:
  describe_image:
    type: python
    module: examples.shared.vision_tool
    function: describe_image
    description: "Describe an image: title, description, tags"
```

Committed consumer: [demos/shared-vision-tool](../demos/shared-vision-tool/)
declares the tool via [describe_image.tool.yaml](describe_image.tool.yaml).

| Provider | Default model | Required env |
|----------|---------------|--------------|
| `google` (default) | `GOOGLE_MODEL` or `gemini-2.0-flash` | `GOOGLE_API_KEY` |
| `anthropic` | `ANTHROPIC_MODEL` or `claude-haiku-4-5` | `ANTHROPIC_API_KEY` |

**Failure modes:** unsupported providers raise `ValueError` (naming the
supported set) before any LLM call; missing local files raise
`FileNotFoundError`; malformed model output raises a Pydantic validation
error — there is no success-shaped fallback.

**Typed page transcription (FR-776):** `transcribe_page(image, page)`
returns a `PageTranscription` (`page`, `text`, `is_blank`) for a rendered
PDF page, with `validate_vision_provider()` enforcing the same allowlist
before any LLM call. Failure modes: unsupported provider raises
`ValueError` before the LLM; missing image raises `FileNotFoundError`;
missing/malformed model output raises `ValueError`; a page-echo mismatch
(model returns a different `page` than requested) raises `ValueError` —
an unverifiable transcription is never accepted.

### `render_page.py` - PDF Page Renderer (FR-776)

Renders exactly one PDF page to PNG via poppler's `pdftoppm` — the render
half of the book-summary vision fallback. Returns
`{"page": page, "image": png_path}`; PNGs default to ignored `tmp/pages/`
and must never be committed.

```python
from examples.shared.render_page import render_page

result = render_page("book.pdf", 7)          # -> {"page": 7, "image": "tmp/pages/p7-7.png"}
```

```yaml
# In a graph — via manifest (FR-768)
tools:
  render_page:
    manifest: ../../shared/render_page.tool.yaml
```

Committed consumer: [demos/book-summary](../demos/book-summary/) maps
`render_page` over each window's OCR-less pages when
`vision_fallback=true`.

**Requirements:** poppler (`brew install poppler`) for `pdftoppm`.

**Failure modes:** missing PDF and missing `pdftoppm` binary raise
`FileNotFoundError`; page < 1, nonzero `pdftoppm` exit, and absent PNG
output raise `ValueError` naming the condition. The function always
raises — the `tool_call` node owns the success/error envelope.

### `split_document.py` - Document Splitter (FR-773)

Splits a PDF into per-page text chunks shaped for map-node fan-out — the
feeder half of the *feeder tool → map → reduce* pattern.

```python
from examples.shared.split_document import split_document

result = split_document("book.pdf")                 # all pages
result = split_document("book.pdf", start=2, end=5) # 1-indexed page range
# {"chunks": [{"index": 0, "text": "..."}, ...], "total": 12}
# index is 0-based within the selection; total is the whole document
```

```yaml
# In a graph — via manifest (FR-768)
tools:
  split_document:
    manifest: ../../shared/split_document.tool.yaml
```

Committed consumer: [demos/book-summary](../demos/book-summary/) feeds the
chunks to a map node via `over: "{state.split_result.result.chunks}"`.

**Requirements:** poppler (`brew install poppler`) for `pdfinfo`/`pdftotext`.

**Failure modes:** unknown `mode` (only `page` is supported), missing
file, missing poppler binaries, nonzero `pdfinfo`/`pdftotext` exit, and
unparseable page count all raise `ValueError` naming the condition —
there is no fallback-to-all-pages.

### `toolbelt/` - Shared Agent Toolbelt (FR-777)

Tool manifests (FR-768) for the read-and-search tools every repo-exploring
agent needs. The toolbelt holds shared agent tools of any manifest runtime
type — the first four are shell-runtime:

| Manifest | Command | Purpose |
|----------|---------|---------|
| `toolbelt/read_file.tool.yaml` | `cat {file}` | Read a project file in full |
| `toolbelt/search.tool.yaml` | `rg -n --glob {glob} {pattern} .` | Glob-scoped ripgrep search |
| `toolbelt/list_dir.tool.yaml` | `ls {dir}` | List directory contents |
| `toolbelt/git_log.tool.yaml` | `git log --oneline --all --grep={pattern}` | Search git history for prior art |

```yaml
# In an agent node — reference by manifest, never re-inline
tools:
  read_file:
    manifest: ../../shared/toolbelt/read_file.tool.yaml
  search:
    manifest: ../../shared/toolbelt/search.tool.yaml
```

Committed consumers: [demos/planner](../demos/planner/),
[demos/enforcer](../demos/enforcer/), [demos/judge](../demos/judge/).

**Fit boundary:** verbatim two-plus-consumer contracts earn manifests;
demo-local variants (different command, parse mode, or description
semantics) stay inline in their graph. The `search` description's glob
example list is the canonical union across consumers — extend it in the
manifest, never re-fork a per-demo copy.

## Scripts

### `scripts/set_fly_secrets.sh`

Helper for setting Fly.io secrets (used by `daily_digest/`).
