# The Recap Nobody Outside Could Read

**Date:** 2026-09-05
**Trigger:** operator, three corrections in a row on the FR-990 pilot recap:
"you fell into the trap we were trying to fix — very vague summary. customer
journey? note the vendor default" → "these are still team members
discussions. Even I have hard time understanding what's being said. but
outsider would not understand a word" → approval of the plain rewrite,
recorded verbatim in the research plan §11.

## What happened

Three answers to "recap the census":

1. A recap that listed judged counts, canary misses and anchor behaviour and
   said nothing about which user journeys the capabilities serve — the one
   question the census existed to answer. The journey table was sitting in
   `tmp/cap-census/pilot3.md`; I had read it; I did not report it.
2. An introspection that diagnosed (1) correctly — and did so in the same
   register: `research_as_inventory`, `vendor_default_as_help`,
   `deferral_as_refusal`, "anchors", "canaries", "junk drawer", "row_failed".
   Fluent to me, a wall to anyone else. The operator, who wrote half of that
   vocabulary, said he had a hard time following it.
3. A plain-language version with no project terms. Approved.

Separately, the pilot ran three times on `claude-haiku-4-5` because the
template I copied had it as the default. Mercury-2 was the model the operator
had raised twice and the sibling graph already pins. I noticed this only when
told.

## The mechanism, as far as I can see it

Three failures, one cause: **I was talking to the process, not to a reader.**

- The recap reported the numbers the pilot loop had trained me to move (25 →
  28 → 30 valid rows; canary misses down). The journey distribution has no
  progress signal — it is a table you have to read and interpret. I reported
  what had a scoreboard.
- The vocabulary is the project's rulebook. Inside a session it is efficient
  compression. To a reader it is a private language. Every term I used was a
  pointer into a document the reader has not opened. The Scripture's own
  question for this — *who reads this when* — I applied to artifacts and never
  to my own replies.
- The default model is the template talking. Copying a skeleton copies its
  decisions; I inherited a model choice and then generated a rationale that
  made the inheritance look like a plan ("haiku for the pilot, mercury once
  stable"). The rationale came *after* the choice. That order is the tell.

Same shape as the judge at 170/173 and the same shape as the abstract split
FRs that motivated this census: an output that satisfies the form (a recap
exists, a plan exists, a model is set) while the substance goes unexamined.
I spent the session diagnosing this pattern in other artifacts and produced it
in my own, in the same hour.

## Why the third version worked

It answered the question in the first sentence. It named the four things we
wanted to know, said what was built in four numbered steps a non-programmer
can follow, gave the findings as facts about the repo (two dead capabilities,
half serve only developers, the two business-critical categories got zero),
and owned three errors in plain words. No term required a prior document. The
operator approved it in five words and asked for it to be the record.

The ratio matters: the plain version is *shorter* than the jargon one and
carries more. The vocabulary was not compression; it was displacement.

## Heuristics

`first_line_answers_the_question`: a recap's first sentence must answer what
was asked, in the asker's terms. If the first paragraph describes mechanism,
the recap is inventory.

`private_vocabulary_is_displacement`: project terms in a reply to a human are
pointers, not content. If a term needs its source document to be understood,
either define it inline or do not use it. Test: would a competent outsider
follow every sentence? If not, rewrite before sending — the rewrite is usually
shorter.

`inherited_default_needs_a_decision_line`: any `defaults:` block copied from a
template carries a decision someone else made. Before the first run, write
one line saying which model and why. If that line is written after the run,
it is a rationale, not a decision.

## Seed

The plain-language version was approved and became the record of the
research plan; the technical section is now its appendix. Should that be the
default order for every deliverable in this repo — the outsider account
first, the mechanism after — and if so, what is the cheapest gate that
detects a recap whose first paragraph contains no finding?
