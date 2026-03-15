# Feature Request: FR-202 End-to-End Image Generation Pipeline

**Priority:** MEDIUM
**Type:** Feature
**Status:** Implemented
**Effort:** 2 days
**Requested:** 2026-03-15

## Summary

Create an end-to-end YAML graph at `examples/image_pipeline/` that takes a style description, generates thematic concepts via LLM, produces image prompts (reusing `batch_image_prompts` as a subgraph), saves prompts to a file, and generates images via Replicate using `z-image` — all orchestrated in YAML.

## Value Statement

Graph authors get a single-command pipeline that goes from "dark fantasy, ink painting" to generated images on disk, demonstrating subgraph composition, file I/O tools, and Replicate integration as a cohesive example.

## Problem

Today the image workflow is fragmented across three disconnected pieces:

1. **`batch_image_prompts`** — generates prompts but stops there (no image generation)
2. **`storyboard`** — generates images but takes story panels, not style-driven concepts
3. **`zimage-replicate.mjs`** — standalone Node.js script outside YAMLGraph entirely

A user wanting to go from a style description to generated images must manually glue these together: run `batch_image_prompts`, copy the output to a file, then run `zimage-replicate.mjs`. This is exactly the kind of pipeline YAMLGraph should express as a single graph.

## Proposed Solution

A new example at `examples/image_pipeline/` with a graph that chains:

```
START → generate_concepts → [subgraph: batch_image_prompts] → save_prompts → generate_images → END
```

### Graph Structure

```yaml
# examples/image_pipeline/graph.yaml
name: image-pipeline
version: "1.0"
description: End-to-end style-driven image generation pipeline
prompts_relative: true
prompts_dir: prompts

state:
  style: str
  count: str
  concept: str
  prompts: list
  prompt_file: str
  output_dir: str
  images: list

tools:
  save_prompts:
    type: python
    module: examples.image_pipeline.nodes.save_prompts
    function: save_prompts_node
    description: Save generated prompts to a text file (one per line)

  generate_images:
    type: python
    module: examples.image_pipeline.nodes.generate_images
    function: generate_images_node
    description: Generate images via Replicate z-image from prompts

nodes:
  generate_concepts:
    type: llm
    prompt: generate_concepts
    state_key: concept
    variables:
      style: "{state.style}"
      count: "{state.count}"

  generate_prompts:
    type: subgraph
    mode: invoke
    graph: ../batch_image_prompts/graph.yaml
    input_mapping:
      concept: concept
      style: style
      count: count
    output_mapping:
      prompts: prompts

  save_prompts:
    type: python
    tool: save_prompts
    state_key: prompt_file
    requires: [prompts]

  generate_images:
    type: python
    tool: generate_images
    state_key: images
    requires: [prompts]

edges:
  - from: START
    to: generate_concepts
  - from: generate_concepts
    to: generate_prompts
  - from: generate_prompts
    to: save_prompts
  - from: save_prompts
    to: generate_images
  - from: generate_images
    to: END
```

### Node Details

**1. `generate_concepts` (new LLM prompt)**

Takes the style and generates a single overarching concept theme as a plain string. The `batch_image_prompts` subgraph's `decompose` node handles breaking the concept into individual scene briefs — no `seeds` field needed here. No Pydantic schema is used: a single-field model would require dot-notation unwrapping in the subgraph `input_mapping`, which `_map_input_state()` does not support (flat `dict.get()` only).

```yaml
# examples/image_pipeline/prompts/generate_concepts.yaml
name: generate_concepts
description: Generate a thematic image concept matching a style

system: |
  You are a visual concept designer. Given an art style reference,
  generate a single overarching concept theme that would produce
  {{ count | default("5") }} striking scenes in that style.

  Reply with ONLY the concept — an evocative phrase (5-15 words) describing
  a theme, world, or narrative moment that naturally decomposes into
  multiple visual scenes. No explanation, no preamble.

user: |
  Style: {{ style }}
  Number of scenes to support: {{ count | default("5") }}
```

**2. `generate_prompts` (subgraph reuse)**

Invokes `batch_image_prompts` graph, which already handles concept → decompose → enrich → prompts. The concept string is mapped into the subgraph's `concept` input, and the subgraph's `prompts` list is mapped back.

**3. `save_prompts` (new Python tool)**

Writes all prompts to `outputs/image_pipeline/{timestamp}/prompts.txt`, one per line. Compatible with `zimage-replicate.mjs` format for manual re-runs.

```python
# examples/image_pipeline/nodes/save_prompts.py
def save_prompts_node(state: dict) -> dict:
    """Save prompts to a text file, one per line."""
    prompts = state.get("prompts", [])
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path("outputs/image_pipeline") / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)
    prompt_file = output_dir / "prompts.txt"
    prompt_file.write_text("\n".join(prompts) + "\n")
    return {"prompt_file": str(prompt_file), "output_dir": str(output_dir)}
```

**4. `generate_images` (new Python tool)**

Reuses `examples/shared/replicate_tool.py`'s `generate_image()` function. Iterates over prompts, generates images via `z-image`, saves to `outputs/image_pipeline/{timestamp}/`. Saves a sidecar `.txt` file alongside each image containing its prompt. If `exiftool` is available on the system, also embeds the prompt in EXIF metadata; otherwise proceeds without it.

```python
# examples/image_pipeline/nodes/generate_images.py
def generate_images_node(state: dict) -> dict:
    """Generate images via Replicate from prompts."""
    prompts = state.get("prompts", [])
    output_dir = Path(state.get("output_dir", "outputs/image_pipeline"))
    image_paths = []

    for i, prompt in enumerate(prompts, 1):
        image_path = output_dir / f"image_{i:02d}.png"
        result = generate_image(prompt, image_path, model_name="z-image")
        if result.success:
            image_paths.append(str(image_path))
            # Sidecar file (always written)
            sidecar = image_path.with_suffix(".txt")
            sidecar.write_text(prompt)
            # EXIF embedding (optional, best-effort)
            _embed_exif(image_path, prompt)

    return {"images": image_paths}
```

### EXIF Embedding Strategy

EXIF embedding via `exiftool` is optional. The `_embed_exif()` helper attempts to run `exiftool` and silently skips if the binary is not found. The sidecar `.txt` file is always written as the primary prompt-to-image linkage. This keeps the pipeline functional on any system while preserving the feature when `exiftool` is available.

```python
def _embed_exif(image_path: Path, prompt: str) -> None:
    """Best-effort EXIF embedding. Requires exiftool on PATH."""
    try:
        subprocess.run(
            ["exiftool", "-overwrite_original",
             f"-Description={prompt}", str(image_path)],
            capture_output=True, timeout=10, check=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        pass  # Sidecar .txt is the primary linkage
```

### Usage

```bash
yamlgraph graph run examples/image_pipeline/graph.yaml \
  --var style="dark fantasy, ink painting, luis royo" \
  --var count="5" --full
```

## Acceptance Criteria

- [x] `generate_concepts` prompt produces a single concept theme as a plain string (unit test with mock LLM) (REQ-YG-198)
- [x] `batch_image_prompts` is invoked as a subgraph (not copy-pasted) (REQ-YG-198)
- [x] `save_prompts` writes `prompts.txt` to output dir, one prompt per line (REQ-YG-198)
- [x] `generate_images` calls Replicate via `shared/replicate_tool.py` with model name `z-image`, saves PNGs to output dir (REQ-YG-198)
- [x] Sidecar `.txt` file saved alongside each generated image containing its prompt (REQ-YG-198)
- [x] EXIF embedding via `exiftool` is best-effort: works when available, silently skips otherwise (REQ-YG-198)
- [x] Graph lints cleanly: `yamlgraph graph lint examples/image_pipeline/graph.yaml` (REQ-YG-198)
- [ ] End-to-end integration test with `--var style="dark fantasy" --var count="3"` (requires API keys) (REQ-YG-198)
- [x] Unit tests for `save_prompts_node` and `generate_images_node` with mocked Replicate (REQ-YG-198)
- [x] README.md in `examples/image_pipeline/` with usage examples and optional `exiftool` documentation (REQ-YG-198)
- [x] Tests tagged with `@pytest.mark.req("REQ-YG-198")` (REQ-YG-198)

## Alternatives Considered

1. **Single monolithic graph** — copy `batch_image_prompts` nodes inline instead of subgraph. Rejected: violates DRY and misses the opportunity to demonstrate subgraph composition.

2. **Shell tool for image generation** — wrap `zimage-replicate.mjs` as a shell tool (`type: shell`). Rejected: introduces Node.js runtime dependency; Python tool using `shared/replicate_tool.py` keeps the stack uniform.

3. **Map node for image generation** — use `type: map` over prompts instead of a single Python tool that loops. Worth considering as a follow-up: map node gives parallelism via LangGraph, but sequential generation respects Replicate rate limits and matches the proven `storyboard/image_node.py` pattern. Map node parallelism with `max_items` concurrency control is a natural enhancement.

4. **Include `seeds` in concept schema** — generate both a concept theme and individual scene seeds from the concept LLM node. Rejected: `batch_image_prompts.decompose` already handles scene decomposition. Producing `seeds` only to discard them violates "no dead state."

5. **Require `exiftool` as hard dependency** — mandate EXIF embedding with no fallback. Rejected: introduces undocumented system dependency. Sidecar `.txt` files provide the same prompt-to-image linkage without external tooling.

## Implementation Notes

- The `generate_concepts` node is the only new LLM prompt; everything else is composition of existing pieces.
- The `save_prompts` tool is trivial (~20 lines) but valuable: it creates `zimage-replicate.mjs`-compatible files for manual re-runs.
- `generate_images` node mirrors `storyboard/nodes/image_node.py` but simplified (no panel/metadata structure).
- Concurrency for image generation should respect Replicate rate limits. Start sequential; map node parallelism is a follow-up.
- The `output_dir` is passed via state from `save_prompts` to `generate_images` so both tools write to the same timestamped directory.

## Related

- **FR-109**: `batch_image_prompts` — reused as subgraph
- **`examples/storyboard/`** — prior art for Replicate integration in YAMLGraph
- **`examples/shared/replicate_tool.py`** — shared image generation utility (model name: `z-image`)
- **`../my-replicate-app/zimage-replicate.mjs`** — reference implementation for batch generation
- **`reference/map-nodes.md`** — map node documentation (future parallelism enhancement)

## Amendments Applied

This FR resolves all four issues from the Judge's review of the original proposal:

| # | Issue | Resolution |
|---|-------|------------|
| 1 | `seeds` field produced but never consumed | Removed `seeds` from schema; simplified to `concept: str`. Decomposition delegated to `batch_image_prompts.decompose` as designed. |
| 2 | Model name inconsistency (`z-image-turbo` vs `z-image`) | All references use `z-image` (the `replicate_tool.py` public API name). |
| 3 | `exiftool` undocumented external dependency | EXIF embedding is best-effort with sidecar `.txt` fallback (option b). Documented in example README. |
| 4 | REQ-YG ID unassigned | Assigned REQ-YG-198. All acceptance criteria reference it explicitly. |
| 5 | `input_mapping` used `concept.concept` dot-notation | `_map_input_state()` does flat `dict.get(parent_key)` — dot-notation resolves to `None`. Removed Pydantic schema from `generate_concepts`; node now returns a plain string. Mapping simplified to `concept: concept`. |
| 6 | `output_dir` missing from state definition | `save_prompts_node` returns `output_dir` and `generate_images_node` reads it, but it was undeclared. Added `output_dir: str` to `state:` section. |
| 7 | `concept` state type was `any` | Changed to `str` to match the schema-free plain string output. |
