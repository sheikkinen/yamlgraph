# Five FRs, One Function: The Delta Was the Whole Design

**Date:** 2026-06-17
**Context:** Enforced FR-514–518 (the ledger-as-memory roadmap) in one pass.
**Incident:** Five separately-judged FRs, four of which turned out to be features
*of a single function*. `apply_ledger_delta` is FR-514; its type-change branch is
FR-515; its closing decay loop is FR-517; FR-516 is one sibling function; FR-518
is one more. The decomposition was honest at judge time, but enforcement revealed
the seams were thinner than the FR boundaries implied.

## The Trap I Avoided: Enforcing the Boundary Instead of the Code

The tempting path was five RED→GREEN cycles, five commits, five wirings — honoring
the FR count as if it were the code's natural joint count. But the judgement had
already frozen J1–J4 *across* all five FRs precisely because they share one apply
path. Writing FR-515's reconciliation as a separate function from FR-514's apply
would have meant a second pass over the same edge list, a second source of truth
for "what is the current edge for this pair." The contracts said: same function,
different branch. I let the frozen contracts, not the FR filenames, dictate the
module shape.

This is the inverse of the usual scope-creep trap. The risk here was *scope
fragmentation*: treating an administrative decomposition (five FRs for five review
units) as an architectural one (five functions for five concerns). The cure was
already written down — J3 said the apply signature carries the ordinal *because*
515 and 517 both need it. The judgement anticipated the convergence.

## What Earned Its Own Surface

Not everything collapsed. The functions that stayed separate are the ones at
different *boundaries*:

- `apply_lane_floor` — the non-relationship lanes (J4). Different data, different
  rule (full-emit vs delta), genuinely separate.
- `rank_relationships` — retrieval, not encode. Reads the ledger, never writes it.
- `apply_merges` — consolidation, second-order, reads many edges to write one.

The test: does it write the relationship ledger at the close boundary? Then it is
`apply_ledger_delta`. Otherwise it is its own function. Four write-path concerns,
one function; three other-boundary concerns, three functions.

## The Honest Deferral

FR-518's A4 (cadence) is unchecked. The deterministic `apply_merges` is shipped and
tested, but the LLM proposal prompt and the wiring that calls it are not. I almost
wired a no-op call to "complete" it — that would have been compliance theatre, a
gate satisfied by presence not substance. The truth is cleaner: J1+FR-515 already
make the Ch8 same-pair duplicate impossible (a second `add` for a pair becomes an
update, which on a type change closes-and-opens — never two concurrent edges). The
defect FR-518 was written to fix is dead before FR-518 runs. So the primitive
ships (it is cheap and correct), the wiring waits for a defect that demands it, and
the FR says so in plain words rather than a checked box.

## The Heuristic

When a judged plan freezes shared contracts across several FRs, the contracts —
not the FR count — predict the function count. Enforce the contract's joints. A
decomposition made for *review* (small, judgeable units) is not automatically a
decomposition for *code* (cohesive functions); re-derive the module shape from the
shared invariants, and let FRs that converge on one boundary converge on one
function.

## Seed

I deferred FR-518's wiring because J1+515 killed its defect — but that means a
chunk of the original five-part plan was made redundant by the *first two* parts.
How much of any roadmap is load-bearing only until the earlier items land? Should
judgement, when freezing a multi-FR sequence, explicitly mark which later FRs are
*conditional* — "enforce only if the earlier fix does not subsume the defect" —
so enforcement knows in advance which items are hypotheses awaiting a survivor,
not commitments?
