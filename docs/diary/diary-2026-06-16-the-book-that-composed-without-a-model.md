# The Book That Composed Without a Model

*Diary — 2026-06-16 — FR-492 retrospective (Phases 2–3), the corrective arc to the 06-16 prune-overshoot entry*

## What happened

This session executed the cure the previous day's diary prescribed. The
06-16 entry (`the-capability-pruned-with-the-duplication`) named the mistake:
FR-491's clean N→1 collapse had swept up two values `final_cut` carried that the
new book pass did not replace — **beat-fidelity** and **per-chapter final text** —
and handed `book.yaml` two jobs in one overloaded LLM node (elevate recap-summary
into prose **and** stitch chapters into one arc), the exact node that hit the
empty-book token bug.

FR-492 split those two jobs back apart along the seam the reviewer drew:

- **Phase 2 — generation at the chapter seam.** Rolled back the over-pruned
  finish, re-scoped `final_cut` onto the *live chapter-play doc*
  (`chapters.cards[cid].turns`), and folded it into `close_chapter` so each
  chapter stores a beat-faithful final `text` — not concatenated recaps. The
  fidelity path was *re-sourced, not re-parsed*: `parse_beats(key_scene)` is inert
  on a free-text chapter summary, so the beats now come from the `beats_satisfied`
  the director already accumulates per turn. Re-pruned the three genuinely-mutual
  siblings (`final_cut_turns`, `walkthrough`, `staging`), this time naming each
  one's destination in the commit (the `prune_overshoot` discipline).
- **Phase 3 — assembly at the book seam.** `compose_book_deterministic(doc)`: a
  pure walk of `chapters.order` that heads each played chapter's final text, with
  **no model on the path to a first book**. Wired as a seedless, graph-less
  terminal Book stage, gated on `all_chapters_played`, reachable via a "The Book"
  breadcrumb crumb. Net for the surgery: −1476 / +172 lines, then the deterministic
  compose added back small and tested.

## The insight: the generation/assembly boundary is a real seam, not a layer label

The thesis that survived the whole FR is one sentence: **generation belongs at
the chapter seam; assembly belongs at the book seam.** A per-turn finish would
duplicate the recap writer (`false_duplicate`); a whole-book LLM finish overloads
one node with both elevation and stitching. The chapter is the *only* floor small
enough to verify one arc's beats and large enough to weight a climax. Once each
chapter holds its own final text, the book is **assembly, not generation** — and
assembly that has inputs already final is deterministic by nature. The token
budget had been screaming this before the design saw it: the most overloaded node
was the one composing from non-final inputs.

## The trap I actually fell into: the stale `-F` message

The process bug this session was not in the code — it was at the **commit
boundary**. I commit multi-line messages via a heredoc to `tmp/msg.txt` then
`git commit -F tmp/msg.txt`. Twice the friction bit:

1. A `cat > tmp/msg.txt` heredoc was bundled into a command that a PreToolUse
   hook **denied** (it matched `pytest` + `tail` elsewhere in the chain). The
   denial meant the heredoc never ran — but `tmp/msg.txt` still held the *previous*
   phase's message. The next `git commit -F` then landed `EXIT=0` with a
   **plausible-but-wrong** subject describing a different change. The artifact
   passed the shape check (a commit exists) and was semantically wrong (it named
   the wrong phase). I caught it only because the hash and subject didn't match my
   expectation — then fixed it with `--amend`.

This is `plausible_wrong_answer` relocated to the commit boundary: a gate that
checks "did a commit happen?" never checks "does the message describe *this*
diff?" The cure is the same shape as everywhere else — **assert substance, not
presence**: after `git commit -F`, verify the subject line matches the change, or
write the message file in its own isolated step and confirm `head -1` before
committing. Never let a `-F` file outlive the change it was written for.

A second, smaller note: `git commit -F` re-runs `ruff-format`, which reformats
and aborts the commit; the staged content is now stale, so a blind retry would
re-commit unformatted. Re-`git add` after every format-hook abort.

## Heuristic

- **Generation belongs where one arc is visible; assembly belongs where inputs
  are already final.** When a node composes from non-final inputs, it is doing two
  jobs — split it at the seam where the lower job's output becomes final. The token
  budget of an overloaded node is the early warning.
- **A `-F` commit-message file is external state at the commit boundary; treat a
  stale message as a wrong answer, not a cosmetic slip.** Write it isolated, verify
  `head -1`, and never reuse a file across changes.

## Seed

The Book now composes deterministically, but nothing yet *proves* the beat the
director recorded in turn 3 actually survived into the chapter's final text, nor
that the manuscript contradicts no forward-carried `world_state`. Phase 4 imagines
an LLM revision pass driven by verification (compose → check fidelity / continuity
→ revise on the failing check). **What would a purely deterministic fidelity gate
look like — one that fails the book when a canonical beat phrase is absent from the
chapter text it belongs to, with no model in the loop?** If that gate can be
written, the LLM revision pass becomes optional polish rather than load-bearing
correctness — and the `verification_checkpoint_primitive` seed gets its first
concrete, model-free instance.
