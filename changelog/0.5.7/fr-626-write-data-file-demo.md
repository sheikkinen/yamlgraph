---
type: feat
scope: demos
req: REQ-YG-475
---
- **FR-626 Write Data File Demo**: Adds `examples/demos/write_data_file/` demonstrating the read→augment→write-back cycle. A world bible accumulates structured knowledge (characters, locations, events) across CLI invocations — zero custom Python. Also fixes Pydantic model serialization in `write_data_file` tool (`.model_dump()` normalization at boundary). (REQ-YG-475)
