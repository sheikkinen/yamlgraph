---
type: fix
scope: enforce
---
- **Enforce Pipeline Routing**: Disable broken score-based routing in critique loop. Copilot node returns string output (not structured object with `.score`), causing both conditions to fail and graph to terminate early. Critique now unconditionally proceeds to `distill_reflection`.
