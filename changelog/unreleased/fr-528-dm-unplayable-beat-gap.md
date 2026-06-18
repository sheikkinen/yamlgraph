---
type: fix
scope: examples
---
- **DM v2 unplayable-epilogue outline gate (FR-528)**: The whole-book partitioner
  could author a chapter's FINAL beat as a time-skip epilogue ("By autumn, ... a
  settlement that ends the blood-feud"). A chapter resolves only when its director
  computes `scene_complete = (k == n)` over `n = len(beats)`; a beat that resolves
  only after a season passes can never be enacted inside the 16-turn cap (FR-501),
  so `scene_complete` never fires and the chapter rides the cap replaying its
  already-resolved confrontation -- the no-progress tail FR-527 mis-treated as a
  play-loop symptom. The cure normalizes at the partitioner boundary
  (`the_one_law`): a deterministic `unplayable_beat_gap` witness fires when a
  chapter's last beat LEADS with a future-time-skip marker, and `outline_chapters`
  re-rolls with the violation fed back (instructing an in-scene resolution or a
  summary fold), then RAISES after the bounded retry rather than emitting a
  cap-riding chapter (Commandment 6). The leading-anchor discriminator (not mere
  co-occurrence of "settlement"/"feud") was validated against the 10025-BC CH8
  epilogue versus the clean present-tense resolutions of 10020/10022/10023/10024-BC.
