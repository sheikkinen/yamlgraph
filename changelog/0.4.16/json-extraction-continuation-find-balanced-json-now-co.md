---
type: fix
scope: json
---
- **JSON extraction continuation** - `find_balanced_json()` now continues searching after finding invalid balanced candidates, so valid JSON later in the text is discovered
