# Storyboard Generator

Generates a visual story with 3-5 panels from a concept using LLM + Replicate image generation.

## Usage

```bash
# Default (z-image model - photorealistic)
showcase graph run examples/storyboard/graph.yaml \
  --var concept="A wizard's apprentice discovers a hidden library"

# HiDream model (cartoon/illustration style)
showcase graph run examples/storyboard/graph.yaml \
  --var concept="A robot learning to paint" \
  --var model="hidream"
```

## Models

| Model | Style | Best For |
|-------|-------|----------|
| `z-image` (default) | Photorealistic, cinematic | Realistic scenes, photography |
| `hidream` | Cartoon, illustration | Stylized art, comics, anime |

The LLM automatically adapts prompts based on the selected model.

## How It Works

```
concept ──► expand_story (LLM) ──► generate_images (Python) ──► outputs/
```

1. **expand_story** - LLM expands concept into title, narrative, and 3-5 panel prompts
2. **generate_images** - Calls Replicate API to generate images for each panel

## Output

Results are saved to `outputs/storyboard/{timestamp}/`:

```
outputs/storyboard/20260117_120000/
├── panel_1.png
├── panel_2.png
├── panel_3.png
├── panel_4.png   # if LLM generated 4+ panels
└── story.json    # metadata with prompts and paths
```

## Requirements

- `REPLICATE_API_TOKEN` in `.env`

## Files

| File | Purpose |
|------|---------|
| `graph.yaml` | Graph definition |
| `prompts/expand_story.yaml` | LLM prompt with schema |
| `nodes/image_node.py` | Python node for image generation |
| `nodes/replicate_tool.py` | Replicate API wrapper |

---

## Animated Storyboard

Generates animation-ready storyboards with 3 frames per panel (original, first_frame, last_frame).

### Usage

```bash
showcase graph run examples/storyboard/animated-character-graph.yaml \
  --var concept="A detective solving a mystery" \
  --var model="hidream"
```

### How It Works

```
concept ──► expand_story ──► animate_panels (map) ──► generate_images
                │                    │                      │
                ▼                    ▼                      ▼
         character_prompt    3 panels × 3 prompts    9 images total
```

For each panel:
1. **Original** - Generated via `generate_image(character_prompt + panel.original)`
2. **First frame** - Generated via `edit_image(original, first_frame)` (img2img)
3. **Last frame** - Generated via `edit_image(original, last_frame)` (img2img)

This ensures each panel's animation frames are visually coherent.

### Output

```
outputs/storyboard/{thread_id}/animated/
├── panel_1_original.png
├── panel_1_first_frame.png
├── panel_1_last_frame.png
├── panel_2_original.png
├── panel_2_first_frame.png
├── panel_2_last_frame.png
├── panel_3_original.png
├── panel_3_first_frame.png
├── panel_3_last_frame.png
└── animated_character_story.json
```

### Files

| File | Purpose |
|------|---------|
| `animated-character-graph.yaml` | Animated graph with map node |
| `prompts/expand_character_story.yaml` | Story + character prompt |
| `prompts/animate_character_panel.yaml` | Panel → 3 frame prompts |
| `nodes/animated_character_node.py` | Image generation with img2img |
