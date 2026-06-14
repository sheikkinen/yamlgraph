---
type: feat
scope: examples
---
- **FR-485 DM v2 turn-structured Final Cut**: A sibling of the FR-484 Final Cut
  that **keeps the turn skeleton** instead of dissolving it — once a Dungeon
  Master scene plays to completion, a terminal **Final Cut (Turns)** leaf composes
  one polished segment per played turn, aligned 1:1 to the play-by-play, spending
  the whole-arc knowledge on de-repetition (each standing fact established once,
  in the turn that introduces it) and climax emphasis. Its centre is a
  deterministic alignment validator that asserts exactly one segment per played
  turn and **raises** on any divergence — never silently re-keying, padding, or
  truncating — which turns FR-484's eyeball-only de-repetition into a checkable
  post-condition. A separate `final_cut_turns` artifact gated identically on the
  scene being complete; the played turns and the FR-484 continuous cut are left
  untouched, so the two finishes coexist.
