---
type: fix
scope: examples
req: REQ-YG-586
---
- **FR-795 Endpoint-Probe Prompt Schema Dialect Repair**: Converted the shipped endpoint-probe prompt from a mixed native/JSON schema declaration to the supported `output_schema` dialect, preserving nested endpoint guidance and allowing the graph to compile and run. (REQ-YG-586)
