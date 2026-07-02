---
type: feat
scope: novel_fandom
req: REQ-YG-508
---
- **FR-656 Tighten Genesis Prompt**: Added type annotations for list fields, valence examples, cross-reference rules, and "one item per entry" instruction to `structure_world.yaml`. Fixed Jinja2 template collision (bare `{to, kind, valence}` parsed as Jinja2 set literal). Updated tests to match new genesis IDs. (REQ-YG-508)
