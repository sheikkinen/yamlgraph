# Reflection: fail-closed is the same rule three times — FR-1033

**Arc.** A question about GitHub's repository count became a study of what
makes an agent instruction file worth its context, which became a census graph
binding. FR-1031 was rejected (a graph-owned wrapper cannot invoke a bound
slot). FR-1032 was approved with seven revisions. FR-1033 was rejected once on
input closure, then approved with four. Enforced: two adapters, 16 witnesses,
one recorded deviation, and a live run over 150 real `CLAUDE.md` files.

## What the raw record says

- The FR-1033 judgement returned four revisions and **three were one defect**:
  a directory over the ceiling returned the first 200 files; a file over the
  ceiling returned its first 65,536 characters; provenance below the pattern's
  standard was *disclaimed* rather than closed. Three different surfaces, one
  habit — shrink the result and keep going.
- The judge's sharpest line was not about any of the three. It was that my
  rationale argued against my own mechanism: I justified the population cap by
  citing the earlier finding that *the tail is the object*, then implemented a
  **lexicographic prefix**. An alphabetical slice is the opposite of a tail. The
  citation made the design read as reasoned.
- On provenance I had told the operator and the FR that the digest was missing,
  and treated the disclosure as sufficient. The judgement: admitting a gap is
  not closing one. The fix fitted inside the two new functions and changed
  neither graph nor ledger. The disclosure cost more words than the repair.
- Three claims across FR-1032 and FR-1033 were confidently wrong and each
  carried a citation or a number that made it read as verified: that
  `gh_repo_extract` re-fetches 620 files (it fetches repository metadata);
  that all census extractors are co-located (`diary_extract` is not); that
  CAP-249 lists `corpus_census` in `modules` (the string appears in a prose
  line I had grepped). All three were load-bearing. All three were caught by
  retrieval, not by judgement.
- Enforcement surfaced a rule the judgement had not considered: adding the
  adapters to `corpus_adapters.py` took it from 364 to **461** lines, past the
  450 ceiling. Frozen scope and Commandment 8 both bind. I split to
  `markdown_adapters.py` on the `diary_adapters.py` precedent and recorded the
  deviation rather than absorbing it.
- The live run over 150 commit-ranked files: 97 invariant-store, 38
  description, 8 state-log, 7 lost to provider errors. Within the
  invariant-store evidence spans, **49% state a prohibition, 12% name an
  enforcing test, 9% cite an incident**. The demo fixture discriminated 3/3.

## The trap

**`bound_as_silent_shrink`.** A limit is the honest response to a resource
constraint, and truncation is the dishonest one wearing its clothes. Both
produce a result; only one tells you the result is partial. `first(200)`,
`text[:N]`, and "we acknowledge the digest is missing" are the same move at
three altitudes — the caller receives something well-formed and cannot see what
was dropped. This is `plausible_wrong_answer` at the boundary rather than in
the model: the shape check passes because the shape was never the thing at
risk.

The recurring tell is that each shrink had a *reason* attached. Ceilings exist;
files are long; provenance is expensive. The reason is what makes the shrink
feel like engineering. `diary_discover` had already chosen the other branch —
reject the over-cap batch and make the operator narrow the source — and I did
not look before writing the prefix.

Companion: **`citation_as_verification`**. Three false claims all carried an
anchor. The anchor is what let them pass my own review, and each was refuted by
opening the file it pointed at. A cited claim is not a checked claim, and the
citation raises the reader's confidence exactly where the author's is
unearned — the written form of the operator's note that competent, precise
language signifies uncertainty rather than certainty.

## Heuristic

When a bound is needed, write the refusal first and see whether the truncation
still looks necessary. If a caller cannot distinguish a complete result from a
shrunken one, the bound is not a bound.

Two mechanical consequences, both cheap:

1. **Any expression of the shape `x[:N]`, `first(N)`, or `head(N)` on a
   population or a document is a candidate defect** until the alternative
   branch — raise, naming the observed value and the limit — has been
   considered and rejected in writing. `md_discover` and `pdf_discover` now sit
   in the same file taking opposite branches; the difference is the whole
   finding.
2. **A claim carrying a file, line, or number is the cheapest thing to verify
   and the most expensive to get wrong.** Reconciling anchors against their
   sources is retrieval, not judgement, and it caught three defects here that
   two rounds of my own reading did not.

**Seed:** the three false claims were each refuted by fetching the thing they
cited — no model needed beyond a diff. The outsider already reads a PR body
*given nothing else*, which is the right seat: its inability to confirm a claim
is the signal. Should the outsider gain a claim/anchor reconciliation pass that
fetches every cited `file:line` and asks only "does this support the sentence
that cites it?" — and does the same pass belong on the doctrine itself, where
30 traps and 20 cures make claims that nobody has re-fetched in months?
