---
type: feat
scope: node-compiler
req: REQ-YG-220
---
- **FR-220 Refactor God Factory**: Replace 15-branch if/elif dispatch chain in `compile_node()` with a `NODE_TYPE_HANDLERS` registry pattern and `NodeCompileContext` dataclass. Unknown node types now raise `ValueError` instead of silently falling through. (REQ-YG-220)
