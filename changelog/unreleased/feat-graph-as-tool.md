---
type: feat
scope: tools
req: REQ-YG-510
---
- **FR-658 Graph-as-Tool**: New `type: graph` tool that invokes a YAMLGraph pipeline in-process as an opaque tool. Agent and tool_call nodes can call graph pipelines without knowing the implementation. Child graphs are compiled once at parse time. Includes circular reference detection and error surfacing. (REQ-YG-510)
