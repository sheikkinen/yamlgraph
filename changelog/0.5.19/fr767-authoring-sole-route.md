---
type: feat
scope: hooks
req: REQ-YG-527
---
- **FR-767 Graph-Authoring Sole Route**: PreToolUse guard denies unsentineled writes to governed graph artifacts (`examples/**/graph.yaml`, `examples/**/prompts/*.yaml`, `graphs/*.yaml`, `.chaplain/graphs/*.yaml`) across file-write tools and terminal write shapes, failing closed on ambiguity; `scripts/author.sh` arms a per-run sentinel token scoped to the adapter execution; doctrine collapsed to one route; pre-commit backstop requires authoring-report proof for new governed artifacts. (REQ-YG-527)
