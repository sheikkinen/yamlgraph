# Diary — The Bottleneck That Moved

**Date:** 2026-06-16
**Arc:** FR-503 finalize · FR-505 draft · FR-504 enforce

## What happened

FR-503 gave the DM v2 director a finite, computed beat ledger. Its J4 azure
witness (10005-BC) passed both criteria cleanly: the FR-501 turn cap dropped from
a 4/6 majority to a 2/8 minority, and `book_reviewer` engagement rose 1.83 → 2.00.
The structural plot stall was, by its own acceptance terms, fixed.

And yet the overall verdict barely moved: still 2/5, continuity still 1/5. So
before declaring victory I did what the user asked — *checked the book myself*.
Reading the actual prose of 10005-BC, every one of the reviewer's sharpest
findings was **true**: Chapter 1's body paragraphs are a verbatim
`Hilde → Gunnar → Reinmar → Oda` round-robin, ~6× running; Arnulf is a
placeholder; the syntax is monotonous parallel construction. The reviewer was not
hallucinating — it was an accurate oracle pointing at a *different* defect than
the one FR-503 fixed.

That reframed the whole session. FR-503 did not fail; it **moved the bottleneck
one layer downstream** — from the director's phase stall to the Final Cut
composer's one-paragraph-per-turn transcription. The same score (2/5) now condemns
a different thing. So I drafted FR-505 (de-grid the Final Cut by re-keying
composition to the finite beat spine FR-503 already produces), and enforced FR-504
(retire the free-text fallback FR-503 kept as a blast-radius shim, making `beats`
a validated boundary contract so there is exactly one beat regime).

## The trap

**`audit_as_ritual` inverted — trusting the green light instead of the artifact.**
FR-503's witness was green, and the easy path was to stamp "Enforced" and move on.
The user's instinct — "check the book yourself; is the reviewer working as
supposed?" — caught the thing the metrics hid: a *passing* structural witness
sitting on top of *failing* prose. The metric measured what FR-503 changed (cap
rate, phase progression); it did not measure what the reader experiences
(paragraph variety). A witness that passes can still sit above an unsolved
problem, because the witness only sees the axis the FR moved.

This is `composition_bug` seen from the oracle's side: every component passed its
own check (director escalates, cap fires rarely, reviewer reports accurately) and
the *system* still reads as mediocre — because the defect lives in the composition
seam (turn grid → prose), which no single component's green light covers.

## The cure that worked

**Read the artifact, not just the score.** Before promoting a generation-quality
FR, open the generated text and verify the oracle's located findings against it.
This did two things at once: it *validated the oracle* (the reviewer is
trustworthy, so its future verdicts can gate) and it *located the next
constraint* (Final Cut prose, FR-505) — which a glance at the score alone would
have missed.

And FR-504's enforce confirmed the FR-503 judgement's foresight: keeping the
free-text fallback as a one-change shim was correct (it bounded FR-503's blast
radius), and retiring it was a clean, separately-judged removal once the J4
witness proved every chapter reliably emits beats. The mock outline had to learn
to emit beats in the *same* commit as the contract (the whole suite flowed through
it) — exactly the `refactor_orphans_secondary` radius the judge flagged. The
director mock had to switch from free-text phrases to 1-based beat numbers so the
*computed* phase/completion reproduced the old opening→rising→resolved timeline;
that was the real work, not the deletions.

## Seed

The witness for FR-505 needs a *deterministic* round-robin metric (fraction of
body paragraphs whose clause-subjects are the full cast in fixed order), not just
the reviewer's engagement score. **When an LLM oracle and a cheap structural
counter disagree about the same artifact, which one should gate the FR — and can
their disagreement itself be the signal that the bottleneck is about to move
again?**
