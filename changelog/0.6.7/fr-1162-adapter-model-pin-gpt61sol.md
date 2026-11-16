---
type: fix
scope: adapters
req: REQ-YG-632
---
- **FR-1162 Adapter model pins move to gpt-6.1-sol**: the judge, review, outsider and authoring adapter graphs, and `scripts/outsider.sh`, pin `gpt-6.1-sol`. The Copilot CLI no longer serves `gpt-5.6-sol` or `gpt-5.5`, so every governed route failed from a clean checkout. (REQ-YG-632)
