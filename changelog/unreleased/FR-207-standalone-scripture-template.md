---
type: feat
scope: scripture
req: REQ-YG-201
---
- **FR-207 Standalone Scripture Template**: Extracted governance methodology (Scripture, Chaplain workflow, diary discipline, changelog fragments, pre-commit gates, CI enforcement) into a standalone, language-agnostic template repository under `projects/scripture-dev/`. Features: `scripture.yaml` parameterization, `render.sh` with `_templates/` source-of-truth pattern (Option A from Judge), shell-based changelog aggregator, configurable `req_coverage.py --prefix`, knowledge graph template. Zero framework-specific references in rendered output. (REQ-YG-201, REQ-YG-202, REQ-YG-203, REQ-YG-204, REQ-YG-205)
