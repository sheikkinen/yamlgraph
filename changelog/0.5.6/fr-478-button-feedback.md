---
type: feat
scope: examples
---
- **FR-478 DM v2 button-press feedback**: every slow press in the Dungeon Master web UI (Iterate, Accept, and breadcrumb nav links) now shows a uniform busy overlay and locks out double-presses while the LLM draft is in flight. A single full-viewport `#busy` overlay in `base.html` (outside `#app-body`) replaces the per-card `#gen-spinner`; `hx-disabled-elt` is avoided because it is a no-op on `<a>` anchors.
