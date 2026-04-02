---
type: fix
scope: template
req: REQ-YG-216
---
- **FR-214 Fix extract_variables nested set false positive**: `extract_variables()` now correctly excludes `{% set %}` assignment targets at any nesting depth, preventing loop-local variables from appearing as required template inputs. (REQ-YG-216)
