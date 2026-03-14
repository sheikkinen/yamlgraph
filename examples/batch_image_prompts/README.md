# Batch Image Prompt Generator

Generates a batch of stylistically consistent image prompts from a single seed concept. Each prompt is individually enriched with composition, lighting, mood, and artist style details — suitable for feeding into Replicate models (z-image, hidream, Flux, SDXL).

## Usage

```bash
# Generate 5 prompts (default)
yamlgraph graph run examples/batch_image_prompts/graph.yaml \
  --var concept="Angel of Death in a dead forest" \
  --var style="Beksinski, oil painting, chiaroscuro, melancholic" \
  --full

# Generate 8 prompts with custom style
yamlgraph graph run examples/batch_image_prompts/graph.yaml \
  --var concept="Underwater cathedral with bioluminescent coral" \
  --var style="Art Nouveau, Alphonse Mucha, stained glass, ethereal" \
  --var count="8" \
  --full

# Validate graph
yamlgraph graph lint examples/batch_image_prompts/graph.yaml
```

## How It Works

```
concept + style + count
        │
        ▼
   decompose (LLM)
   Break concept into N distinct scene briefs
        │
        ▼
   enrich (map, parallel)
   Each brief → detailed image generation prompt
        │
        ▼
   prompts (list[str])
   N enriched prompts ready for image generation
```

1. **decompose** — LLM decomposes the seed concept into N scene briefs, each describing a unique visual moment with distinct composition and mood
2. **enrich** — Map node processes each brief in parallel, expanding it into a full image generation prompt encoding artist style, composition, lighting, mood, subject detail, and quality markers

## Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `concept` | Yes | — | Seed concept for image generation |
| `style` | Yes | — | Artist/style reference (e.g., "Beksinski, oil painting") |
| `count` | No | `"5"` | Number of prompts to generate |

## Example Output

```json
{
  "prompts": [
    {
      "prompt_text": "Dark surrealist oil painting in the style of Zdzisław Beksinski, low-angle shot of a towering skeletal angel with tattered wings standing among dead twisted trees, chiaroscuro lighting with deep amber and ashen gray palette, melancholic atmosphere, detailed bone texture and decaying bark, dramatic volumetric fog, cinematic composition"
    },
    {
      "prompt_text": "Beksinski-inspired surreal landscape, wide establishing shot of an endless dead forest under a blood-red sky, oil painting technique with heavy impasto brushwork, rim lighting from a dying sun casting long shadows through skeletal branches, desolate mood with muted earth tones, hyper-detailed gnarled roots and cracked earth, dramatic depth of field"
    }
  ]
}
```

## Cost & Time Estimates

| Model | ~Time | ~Cost (5 prompts) |
|-------|-------|--------------------|
| `claude-haiku-4-5` | 5-10s | ~$0.005 |
| `claude-sonnet-4-5` | 10-20s | ~$0.05 |

## Error Handling

- **`on_error: skip`** — If enrichment fails for a scene brief, it is skipped and remaining prompts are still collected
- **`max_retries: 1`** — Each failed enrichment is retried once before skipping
- **`flatten_output: true`** — Results are flattened (no `_map_xxx_sub` wrappers)

## Files

| File | Purpose |
|------|---------|
| `graph.yaml` | Pipeline: decompose → enrich (map) → collect |
| `prompts/decompose_concept.yaml` | Seed concept → N scene briefs |
| `prompts/enrich_prompt.yaml` | Scene brief → detailed image prompt |

## Related

- `examples/storyboard/` — Image generation pipeline (uses generated prompts downstream)
- `reference/map-nodes.md` — Map node documentation
- FR-052 — Map output flattening (`flatten_output: true`)
