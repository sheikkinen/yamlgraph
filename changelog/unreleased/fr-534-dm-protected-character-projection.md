---
type: feat
scope: examples
---
- **FR-534 DM v2 protected-character projection**: The chapter-open precedence
  that already blocks contradictory lifecycle states (`chapter_memory >
  live_synopsis > seam_packet`) is now also projected into prose generation, so
  the narrator and final-cut composer can no longer kill a character the story
  plan requires to survive. A new `api/lifecycle_resolver.py` becomes the single
  source of truth for that precedence (shared by the open-gate and the prose
  side), and derives a `protected_cast` (highest-precedence state alive AND named
  by a plan guard). The turn director must not retire a protected character, and
  the final-cut prompt carries a may-not-die constraint symmetric to the existing
  dead-within-chapter rule (FR-519). Closes the asymmetry the FR-533 spike found:
  the gate refused the resurrection but the composer was never told the character
  was protected.
