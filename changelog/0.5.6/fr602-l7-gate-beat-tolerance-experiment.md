---
type: feat
scope: plot-modeller
req: REQ-YG-020
---
- **FR-602 L7 gate beat-tolerance experiment (CLOSED UNSTARTED)**: Add a deterministic `--sweep` mode to `probe_l7_misses.py` that scores the re-annotated GT against the classifier at match windows +/-0..+/-3, reporting `affect_recall` AND `affect_precision` at each (window 0 ties out to the frozen gate per genre; canonical `evaluate.py` imported read-only and untouched). Decision: relaxing the FR-578 gate to +/-1 recovers exactly **one** GT delta (a single one-beat-late `open loss` tail displacement), far below the >=3 evidentiary bar the AC requires before any loosening. The beat-off misses that motivated this FR were already absorbed by FR-600 (re-anchoring) and FR-601 (kind discrimination). **Exact-beat matching stays; the frozen gate is not loosened.** Committed measurement dump at `fixtures/affect-licensing/fr602-window-sweep.md`. (REQ-YG-020)
