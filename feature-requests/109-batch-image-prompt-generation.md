# Feature Request: FR-109 Batch Image Prompt Generation Graph

**Priority:** MEDIUM
**Type:** Feature
**Status:** In Progress
**Effort:** 2 days
**Requested:** 2026-03-14

## Summary

A YAML graph that takes a seed concept and art style reference, then generates a batch of detailed image prompts in a consistent style — suitable for feeding into Replicate image generation models (z-image, hidream, etc.).

## Value Statement

Graph authors can produce cohesive sets of image prompts from a single concept, eliminating the manual crafting of per-image prompt text and ensuring stylistic consistency across a batch.

## Problem

Creating high-quality image prompts is time-consuming and inconsistent when done manually. The existing `image-generator-fsm` project demonstrates a backstory-enrichment pipeline (ReAct → SDXL → 4-step validation) but it's implemented as a bespoke Python FSM, not as a reusable YAMLGraph.

Meanwhile `examples/storyboard/` shows that YAMLGraph already supports map-node parallelism over image prompts, but the prompts themselves are generated as a flat list inside a single LLM call (`expand_story.yaml`). There is no graph that focuses specifically on **batch generation of stylistically coherent prompts** with per-prompt enrichment.

The art style references in `../my-replicate-app/zimage.txt` show the pattern: each prompt encodes artist style, composition, lighting, mood, and subject detail. Generating these programmatically — with style consistency — is the gap.

## Proposed Solution

A new example graph: `examples/batch_image_prompts/graph.yaml`.

### Pipeline

```
seed_concept ──► decompose ──► map(enrich) ──► collect
     │                │              │               │
   concept +      N scene         backstory       final
   style ref      briefs          per scene       prompts
```

### Graph YAML

```yaml
name: batch-image-prompts
version: "1.0"
description: Generate a batch of stylistically consistent image prompts from a seed concept
prompts_dir: examples/batch_image_prompts/prompts

defaults:
  provider: anthropic
  model: claude-haiku-4-5

state:
  concept: str              # Input: seed concept ("Angel of Death in a dead forest")
  style: str                # Input: artist/style reference ("Beksinski, oil painting, chiaroscuro")
  count: str                # Input: number of prompts to generate (default "5")
  scenes: any               # Intermediate: decomposed scene briefs
  prompts: list             # Output: list of enriched image prompts

nodes:
  decompose:
    type: llm
    prompt: decompose_concept
    state_key: scenes
    variables:
      concept: "{state.concept}"
      style: "{state.style}"
      count: "{state.count}"

  enrich:
    type: map
    over: "{state.scenes.briefs}"
    as: brief
    node:
      type: llm
      prompt: enrich_prompt
      state_key: enriched
      variables:
        # brief is auto-injected by map compiler from `as: brief`
        style: "{state.style}"
        concept: "{state.concept}"
    collect: prompts
    flatten_output: true
    on_error: skip
    max_retries: 1

edges:
  - from: START
    to: decompose
  - from: decompose
    to: enrich
  - from: enrich
    to: END
```

### Prompt: `decompose_concept.yaml`

```yaml
name: decompose_concept
description: Break a seed concept into N distinct scene briefs

schema:
  name: SceneBriefs
  fields:
    briefs:
      type: list[str]
      description: >
        List of scene briefs, each a 1-2 sentence description
        of a distinct visual moment derived from the concept

system: |
  You are a visual concept designer. Given a seed concept and target style,
  decompose it into {{ count | default("5") }} distinct scene briefs.

  Each brief should:
  - Describe a unique visual moment or angle on the concept
  - Be compositionally distinct (vary: angle, distance, lighting, mood)
  - Stay within the thematic universe of the concept
  - Be suitable for expansion into a full image generation prompt

  Style reference: {{ style }}

template: |
  Concept: {{ concept }}
  Style: {{ style }}
  Number of scenes: {{ count | default("5") }}

  Generate {{ count | default("5") }} distinct scene briefs.
```

### Prompt: `enrich_prompt.yaml`

```yaml
name: enrich_prompt
description: Expand a scene brief into a full image generation prompt

schema:
  name: EnrichedPrompt
  fields:
    prompt_text:
      type: str
      description: >
        A detailed image generation prompt (200-400 chars) encoding
        artist style, composition, lighting, mood, subject, and technique

system: |
  You are an expert image prompt engineer for AI art generation models
  (Flux, SDXL, Stable Diffusion). Given a scene brief and style reference,
  produce a single detailed image prompt.

  The prompt must encode:
  - **Artist/style**: Named artists, art movements, techniques
  - **Composition**: Camera angle (low angle, close-up, wide), framing
  - **Lighting**: Chiaroscuro, rim lighting, golden hour, etc.
  - **Mood/atmosphere**: Emotional tone, color palette
  - **Subject detail**: Pose, expression, clothing, environment
  - **Quality markers**: "detailed", "dramatic", "dynamic"

  Stay consistent with the overall concept and style reference.
  Output the prompt as a single paragraph — no line breaks, no metadata.

  Style reference: {{ style }}

template: |
  Scene brief: {{ brief }}
  Overall concept: {{ concept }}
  Style: {{ style }}

  Write one detailed image generation prompt for this scene.
```

### CLI Usage

```bash
yamlgraph graph run examples/batch_image_prompts/graph.yaml \
  --var concept="Angel of Death in a dead forest" \
  --var style="Beksinski, oil painting, chiaroscuro, melancholic" \
  --var count="5" \
  --full
```

## Acceptance Criteria

- [x] `yamlgraph graph lint examples/batch_image_prompts/graph.yaml` passes
- [ ] `yamlgraph graph run` produces N prompts (matching `count` variable) from a seed concept
- [ ] Each output prompt encodes style, composition, lighting, mood, subject (verified by integration test field inspection)
- [x] Map node processes scene briefs in parallel with `on_error: skip`
- [x] `flatten_output: true` delivers clean prompt list (no `_map_xxx_sub` wrappers)
- [x] Unit test for graph lint validation (`@pytest.mark.req("REQ-YG-003")`)
- [ ] Integration test with real LLM verifying prompt count and field presence
- [x] README.md with usage, example output, and cost/time estimates

## Alternatives Considered

1. **Single LLM call generating all prompts at once** — simpler, but no per-prompt enrichment and quality degrades with large batches. The storyboard `expand_story.yaml` uses this approach for 3-5 panels; it doesn't scale to 10-50 prompts.

2. **Python script outside YAMLGraph** — the `image-generator-fsm` approach. Works, but loses YAML declarativeness, LangSmith tracing, checkpointing, and error handling. Defeats the purpose of YAMLGraph.

3. **Agent node with ReAct pattern** — the backstory workflow uses ReAct for prompt enrichment. Overkill here: the enrichment task is well-defined and doesn't need tool use or iterative reasoning. A simple LLM node in a map suffices.

4. **Adding image generation to this graph** — intentionally excluded. This FR focuses on prompt generation only. Image generation can be piped downstream (the storyboard example already demonstrates that pattern). Keeping prompt generation separate follows single responsibility and avoids Replicate API coupling.

## Related

- `examples/storyboard/` — existing image generation pipeline (map + Replicate)
- `examples/storyboard/prompts/expand_story.yaml` — single-call story panel generation
- `../image-generator-fsm/docs/backstory-workflow-implementation-plan.md` — ReAct backstory enrichment
- `../my-replicate-app/zimage.txt` — art style prompt reference corpus
- `examples/shared/replicate_tool.py` — Replicate image generation wrapper
- FR-052 — map output flattening (implemented, used here)
- FR-069 — per-node timeout (approved, complementary for long LLM calls)
