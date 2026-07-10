---
type: feat
scope: examples
req: REQ-YG-494
---
- **FR-643v2 World Expansion Pipeline**: Deepening loop that enriches thin canon entities and grows the wiki via red links. Adds `backstory` field to Character, `depth` field to all page models, 5 deterministic python nodes (reload_canon, select_thin, collect_red_links, validate_pages, persist_pages), 2 YAML prompts (deepen_entity, generate_skeleton), and worldgen.yaml graph. Seed canon pages changed to lane:dynamic. (REQ-YG-494, REQ-YG-495)
