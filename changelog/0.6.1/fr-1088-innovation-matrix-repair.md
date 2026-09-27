---
type: fix
scope: demos
req: REQ-YG-690
---
- **FR-1088 innovation_matrix pipeline repair**: `pipeline.yaml` declares `domain`, so `--var domain=...` reaches state. The dimensions schema bounds each list to 3–5 entries, a test pins their product to the map's `max_items: 25`, and cell IDs come from the real list lengths. An empty dimension raises. `synthesize` receives every dispatched pair, states the real counts, and marks any cell without exactly one expansion `MISSING` or `DUPLICATE`. (REQ-YG-690)
