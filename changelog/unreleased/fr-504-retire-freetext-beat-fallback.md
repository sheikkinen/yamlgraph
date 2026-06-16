---
type: removal
scope: examples
---
- **FR-504 Retire the free-text beat fallback**: The DM v2 director now has a
  single beat-judgement regime. A non-empty, ordered `beats` list is a validated
  boundary contract (`chapter_ops._require_beats`) — a chapter outline that emits
  no beats is rejected at the parse boundary instead of silently falling back. The
  FR-491 free-text path (`_canonicalize_beats`, `_clamp_phase`, `_PHASE_ORDER`, and
  the `_apply_beat_ledger` `N == 0` branch) is deleted; `phase`/`scene_complete`
  are always computed from the finite `k / N` ledger.
