---
type: fix
scope: plot-modeller
req: REQ-YG-020
---
- **FR-601 L7 close-op kind discrimination**: Add a per-kind close-op resolution-signature cue to the `affect_throughline` classifier so a `close` names the feeling being *resolved* (loss recovered, guilt atoned, betrayal exposed, hope vindicated) instead of the resolving beat's surface action or valence. The four close-op KIND-WRONG confusions (`betrayal->retaliation`, `hope->loss`, `guilt->betrayal`, `loss->hope`) became hits; deterministic before/after on the re-annotated GT: (c) KIND-WRONG 6->3 (close 4->1), affect_recall 0.107->0.214, affect_precision 0.064->0.122, (a) ABSENT 17->14. Open-op path byte-identical (16 insertions, 0 deletions); frozen FR-578 gate untouched. (REQ-YG-020)
