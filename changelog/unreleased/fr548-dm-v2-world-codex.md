---
type: feat
scope: examples
---
- **FR-548 DM v2 World Codex**: Add an outline-time World Codex stage to the Dungeon Master
  example. A non-visitable side-effect graph (`world_codex.yaml`) derives faction + location
  backstory from the accepted synopsis as a `parse_json` `{factions, locations}` object;
  `doc_ops.expand_codex` normalizes it at the boundary (missing string fields default to `""`,
  unknown keys dropped, non-list arrays coerced, unnamed entries dropped) and persists it as
  immutable reference under `doc["codex"]` -- no `reviewed` gate, idempotent on re-accept,
  sequenced on synopsis-accept after `expand_roster`. `final_cut` weaves it as grounding texture
  through a `{% if world_codex %}`-guarded block, so a doc with no codex renders a byte-identical
  compose. Backstory is additive: it states a world, it never reverses one, so it adds zero
  cross-seam reversible state.
