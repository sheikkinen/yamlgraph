# Two Adversaries: One Who Knows Nothing, One Who Knows Everything

**Date:** 2026-09-05
**Trigger:** operator, after FR-995 enforcement: "important pattern / process
improvement: two adversarial feedbacks — outsider who knows nothing and
reviewer who has it all. if outsider was not yet executed on the pr —
dogfood." It had not been. It is now: PR #592, derived NO, six items, first
row in the ledger, comment posted, six glosses applied.

## The pattern

The repository already had two adversarial readers, both maximally informed:
the judge (FR + all doctrine) and the reviewer (PR diff + FR + judgement +
files). Today added a third whose defining property is the opposite: **it is
given nothing**. Title, body, no files, no rules, a working directory outside
the repo so it cannot even find the instructions file.

Put together, a change now passes two readers at the two ends of the
knowledge axis:

| reader | knows | catches |
|---|---|---|
| outsider | nothing | what only an insider could follow; claims without a pointer; the description's failure to say what changed for whom |
| reviewer | everything | scope drift against the frozen FR; missing tests; the wrong file touched; the thing the description says that the diff does not do |

Neither can do the other's job. The reviewer cannot un-know the vocabulary;
its private language is exactly the author's, so jargon is invisible to it.
The outsider cannot partition "missing" into *unlinked* and *absent*; it has
no files. The handoff is the design: the outsider's "would still need" list is
input to the reviewer, who has the files to close each item.

## Why it is a process improvement, not a tool

The failure it closes was not a missing check. It was a missing *position*.
Every reader in the loop stood at the informed end, including the author's
own re-reads. Yesterday's four unreadable recaps happened with the rule "who
reads this when" already in Scripture; the rule had no reader standing where
it could fire. Adding a reader at the far end of the axis is what makes the
rule executable. That is `detection_without_enforcement` resolved by
*positioning*, not by another gate.

The two-adversary shape generalises beyond PRs. Any artifact with a reader
outside the team — a release note, a README, an FR's problem statement, a
brochure — has an informed reviewer already and lacks the uninformed one.
The outsider is the same graph pointed at a different text; the FR kept FR
bodies out of scope by decision, not by difficulty.

## What the dogfood run showed, in one pass

Six items on a body I had just rewritten *for* an outsider: "judge route",
"folded revisions", "CAP-263 / REQ-YG-660…663", "inverted input closure",
"the three readers of its output", "the dogfood comment below". Every one is
a phrase I would defend as plain inside the team. That is the point: the
author cannot see them, the reviewer would not flag them, the outsider lists
them in sixty seconds. Its section 4 also asked a question the informed
readers had not: *how do the tests accept two contradictory results for the
same fixture without masking a regression?* — answerable (they assert two
specific committed files, not live runs), but nobody had written the answer
down until an ignorant reader asked.

## Heuristic

`two_ends_of_the_knowledge_axis`: for any artifact meant to be read outside
its authors, run two adversaries — one with everything, one with nothing —
and hand the second's "would still need" list to the first. A single
informed reviewer cannot detect private language; a single uninformed reader
cannot verify claims. Candidate for Scripture `process:` on second
recurrence; the FR-body target is the obvious next witness.

## Seed

**Seed:** The outsider's output is advisory and one-shot because the model is
a nagger that flickers at the border. The reviewer's output is advisory for a
different reason — the human merge decision is the gate. If both adversaries
are advisory, where does the *signal* accumulate? The ledger has one row.
What does the twenty-row picture need to contain for the human to see, in
seconds, whether descriptions are getting readable — and is that a
per-PR verdict at all, or a trend of item counts with the verdict column
removed?
