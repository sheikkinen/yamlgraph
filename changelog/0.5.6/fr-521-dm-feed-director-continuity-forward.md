---
type: fix
scope: examples
---
- **FR-521 DM v2 drop a within-chapter exited actor from the running cast**: When
  a chapter killed or swept away a character mid-chapter, the per-character intent
  map kept generating intents for them (a drowned brother hauling himself back up
  the bank turn after turn), because the only signal — the director's free-text
  `continuity` flag — was advisory and the intent map ignored it. The director now
  emits a **structured** `cast_exits` field naming rostered characters who have left
  the scene this chapter (they may act up to and including their exit turn). The
  turn's roster filter accumulates those exits across the chapter's prior turns and
  drops the actor from the cast for every later turn — turning detection into
  enforcement. Never empties the cast (the chapter's turn cap closes it instead).
  Also widens within-chapter death detection so `missing_presumed_dead` is treated
  as a chapter-scoped death-point (the swept-away state the confirmed-only filter
  excluded), while the cross-chapter before-open bar stays `confirmed_dead`-only so
  a synopsis return is never barred (Arnulf ch6). Witnessed on 10022-BC Ch3: Arnulf
  re-flags dropped 8/16 → 0/16, with Arnulf acting through his exit turn then
  benched. Supersedes the rejected FR-520 and the reverted advisory feed-forward
  (which raised the break 8/16 → 13/16: asking a generator not to is not a gate).
