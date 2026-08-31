# The Contract Written Twice

FR-937 began as a research run that would not run. The brief was "how to get the
operator a cup of coffee" — deliberately a topic with no prior art in a Python
framework repo. It failed twice. The failure was not in the coffee.

## The route is least reliable where research is most needed

The research route works well on briefs about the repo, because the corpus
retrieval comes back full and every persona can cite a real FR. It fails on
briefs about anything else, because the honest answer — "nothing in this corpus
supports this" — was the one answer the preflight refused to accept. The reducer
accepted it. The preflight rejected it. Two halves of one contract, implemented
twice, drifting silently because nothing compared them.

That inverts the value curve. A research tool that only works on subjects
already researched is a search engine over its own history. The novel brief —
the one you actually need help with — is exactly the input the gate kills.

## Naive substring matching, four times in one day

The bug family repeated at four sites within a single session:

- The preflight matched `none-retrieved` with `in`, so a row whose prose merely
  *discussed* the marker was accepted as claiming it.
- The classification check matched an enum value anywhere in the cell, so a row
  saying "this is not an extension" was scored as an extension.
- My own test excluded `librarian_structure.yaml` by exact filename, silently
  treating the *other* librarian prompt as an internal persona.
- The earlier renumber sweep matched `FR-932` in files that legitimately meant
  a different FR-932.

Four instances, one shape: a predicate that asks "does this string appear?"
where the question is "is this string claimed?" Mention is not assertion. The
cure is a named predicate — `is_marker_claim()` — defined once and shared by
both halves of the contract, so the next drift is a test failure rather than a
silent divergence.

## The judge read the code; the author remembered it

The judgement returned SPLIT and cited four defects. One of them: my FR
described a function `_precedent_kind` that does not exist. The real symbol is
`_classify_precedent`. I had not misread it — I had *remembered* it, confidently,
from a file I wrote days earlier. The judge, having no memory, opened the file.

That is the whole argument for input closure in one line. The judge's advantage
is not intelligence; it is amnesia. It cannot substitute recollection for
reading. Every time I plan from memory instead of from the file, I am the less
reliable of the two.

The operator overrode the split — one FR, corrections folded, no re-judge — and
that was right: the three proposed FRs shared one root cause and would have
tripled the merge cost, which is the standing handicap. But the four substantive
findings were all real, and all came from reading rather than reasoning.

## The no-op that reported success

`for f in $FILES; do sed -i '' ... "$f"; done` — in zsh, an unquoted variable
does not word-split. The loop ran exactly once, on a single string of
concatenated filenames, matched nothing, and exited 0. Every command reported
success and nothing changed. I only caught it because a later grep found the
strings I believed I had replaced.

A shell that reports success for work it did not do is the same failure class as
a gate that checks presence rather than substance: the signal confirms the
ritual, not the outcome.

**Seed:** The preflight and the reducer drifted because two modules encoded one
contract and no test compared them to each other. How many other pairs in this
repo hold the same shape — a validator and an executor that must agree, verified
only against fixtures and never against one another? Could a cheap test generator
assert *agreement between implementations* rather than agreement with expected
values, so drift fails loudly at the seam instead of quietly at the boundary?
