---
type: feat
scope: examples
---
- **FR-539 Seam-Aware Final Cut**: The dungeon_master Final Cut narrator now
  composes each chapter with peripheral vision across the seam. A new
  `cast_entrances` deriver leaf computes the candidate entrance manifest
  (`resolve_chapter_cast(cid) − on_page(prev)`, new/returning/continuing, with the
  entrant's own inherited ledger row), and the prior chapter's bounded closing
  prose is fed into the next chapter's Final Cut prompt as `PREVIOUS CHAPTER — HOW
  IT ENDED`. The narrator is instructed to open by establishing each entrant. The
  manifest is narrator input only — it never suppresses FR-538's prose-outcome
  `seam_entrance_gap` (paired B1).
