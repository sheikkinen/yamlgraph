---
type: feat
scope: examples
req: REQ-YG-573
---
- **FR-764 Style-Convert Pipeline**: New `examples/style_convert/` — the inverse-front twin of `image_pipeline`. It loads an existing prompt file (one prompt per nonblank line, stripping only leading `N. ` enumerators, never mutating the source), restyles each prompt into a target art style via a Mistral-pinned map node with a structured `prompt_text` schema, and reuses `image_pipeline`'s `save_prompts_node` unchanged. A `validate_conversions` gate runs before the sink so a failed conversion branch aborts the run before any file is written (fail-fast: N in == N out or nothing written). (REQ-YG-573)
