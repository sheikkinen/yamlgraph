---
type: feat
scope: python
req: REQ-YG-020
---
- **FR-252 Python Node Variables**: `type: python` nodes now resolve `variables:` expressions before calling the function, consistent with all other node types. Obsolete linter rule W020 removed. (REQ-YG-020)
