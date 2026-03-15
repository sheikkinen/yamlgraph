# Image Generation Pipeline

End-to-end style-driven image generation: from a style description to generated images on disk.

## Pipeline

```
START → generate_concepts → [map: batch_image_prompts per concept] → save_prompts → generate_images → END
```

1. **generate_concepts** (LLM) — Takes a style description and generates M distinct concept themes
2. **generate_prompts** (map + subgraph) — For each concept, invokes `batch_image_prompts` to decompose it into N individual image prompts
3. **save_prompts** (Python) — Writes all prompts to `outputs/image_pipeline/{timestamp}/prompts.txt`
4. **generate_images** (Python) — Generates images via Replicate `z-image` model, saves PNGs with sidecar `.txt` files

**Total images: M concepts × N prompts = M×N images**

## Usage

```bash
# Generate 3 concepts × 5 prompts = 15 images
yamlgraph graph run examples/image_pipeline/graph.yaml \
  --var style="dark fantasy, ink painting, luis royo" \
  --var concepts_count="3" \
  --var count="5" --full

# Generate 2 concepts × 3 prompts = 6 images
yamlgraph graph run examples/image_pipeline/graph.yaml \
  --var style="art nouveau, alphonse mucha" \
  --var concepts_count="2" \
  --var count="3" --full
```

### Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `style` | Art style description (e.g., "dark fantasy, ink painting") | Required |
| `concepts_count` | Number of distinct concept themes (M) | `"3"` |
| `count` | Number of image prompts per concept (N) | `"5"` |

## Requirements

- `REPLICATE_API_TOKEN` environment variable set for image generation
- `ANTHROPIC_API_KEY` (or other LLM provider key) for concept/prompt generation

## Output Structure

```
outputs/image_pipeline/{timestamp}/
├── prompts.txt          # One prompt per line (zimage-replicate.mjs compatible)
├── image_01.png         # Generated image
├── image_01.txt         # Sidecar: prompt used for image_01
├── image_02.png
├── image_02.txt
└── ...
```

## Optional: EXIF Metadata

If `exiftool` is installed on the system, the pipeline embeds each prompt in the image's EXIF `Description` field. This is best-effort — the pipeline works without `exiftool`.

Install on macOS:
```bash
brew install exiftool
```

Install on Ubuntu/Debian:
```bash
sudo apt-get install libimage-exiftool-perl
```

## Related

- [`examples/batch_image_prompts/`](../batch_image_prompts/) — Subgraph reused for prompt generation
- [`examples/shared/replicate_tool.py`](../shared/replicate_tool.py) — Shared Replicate API client
- [`examples/storyboard/`](../storyboard/) — Prior art for Replicate integration
