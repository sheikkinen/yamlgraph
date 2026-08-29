---
type: feat
scope: examples
---
- **FR-881 Image Pipeline v3**: local-model prompt generator example — the FR-876 trained deviant-daily model proposes prompts offline via a `--json` subprocess contract (no `llm` node in the graph), the generation boundary gates them, and Replicate z-image renders only the first top-k passers.
