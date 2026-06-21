---
type: feat
scope: examples
req:
---
- **FR-558 DM v2 Gate-on-Write Funnel (Contract C)**: Bound the per-card playability battery to the one typed write seam so no authoring path can commit an un-playable chapter card ungated. Added `examples/dungeon_master/api/card_gate.py` with `ChapterGateError` and `gate_chapter_card` (composes `reversal_pack_gap` + `unplayable_beat_gap`, tagging gaps by kind). `chapter_nav.write_chapter_card` now runs the gate after structural validation and raises before committing (the funnel; `card_gate` imported lazily to keep the static graph acyclic). Routed `outline_ops._packed_chapters`, `_unplayable_chapters`, and `reoutline_chapter_beats` through `gate_chapter_card` -- the detectors are no longer wired directly in `outline_ops` -- while keeping each caller's bounded retry loop (J3, passing path byte-identical). The sequence-level `composition_gap` stays outline-level (J1 arity split). The generalization tightens `reoutline_chapter_beats` to also reject an unplayable time-skip-epilogue final beat, witnessed by a new condemning test. 413 DM tests pass.
