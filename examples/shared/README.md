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
# In a graph
tools:
  describe_image:
    type: python
    module: examples.shared.vision_tool
    function: describe_image
    description: "Describe an image: title, description, tags"
```

| Provider | Default model | Required env |
|----------|---------------|--------------|
| `google` (default) | `GOOGLE_MODEL` or `gemini-2.0-flash` | `GOOGLE_API_KEY` |
| `anthropic` | `ANTHROPIC_MODEL` or `claude-haiku-4-5` | `ANTHROPIC_API_KEY` |

**Failure modes:** unsupported providers raise `ValueError` (naming the
supported set) before any LLM call; missing local files raise
`FileNotFoundError`; malformed model output raises a Pydantic validation
error — there is no success-shaped fallback.

## Scripts

### `scripts/set_fly_secrets.sh`

Helper for setting Fly.io secrets (used by `daily_digest/`).
