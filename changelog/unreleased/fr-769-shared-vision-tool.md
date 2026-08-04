---
type: feat
scope: examples
req: REQ-YG-575
---
- **FR-769 Shared Vision Tool**: `describe_image()` in `examples/shared/vision_tool.py`
  sends a local image or URL plus an instruction through a `create_llm()` chat
  model and returns a validated `ImageDescription` (title, description, tags,
  optional QA verdict). Provider allowlist (google, anthropic) enforced before
  invocation. First read-direction complement to `replicate_tool.py` —
  consumers: image pipeline QA and DeviantArt caption generation. (REQ-YG-575)
