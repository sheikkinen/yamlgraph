---
type: feat
scope: examples
---
- **FR-481 DM v2 Director card & monotonic phase**: The Dungeon Master play turn
  now always shows the director's structured judgement as a compact, read-only
  Director card (phase badge, satisfied beats, narrator steer, scene-complete, and
  the continuity flags folded in) instead of discarding all but two signals. The
  director's `phase` is clamped to never run backwards across turns
  (`opening<rising<climax<resolved`), so the recorded arc is monotonic regardless
  of what the model returns.
