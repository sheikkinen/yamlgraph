---
type: feat
scope: graph
req: REQ-YG-235
---
- **FR-235 Compile-Time Pipeline Templates**: Added `type: pipeline` meta-node that expands at compile time into concrete sequential nodes. Supports `{item.field}` interpolation in prompts, variables, and state keys; non-string fields copied verbatim; external edges rewritten to first/last expanded node. Lint rules E401–E404 validate pipeline structure. (REQ-YG-235)
