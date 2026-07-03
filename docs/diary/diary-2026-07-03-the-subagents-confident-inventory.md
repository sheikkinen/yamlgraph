# Diary: The Subagent's Confident Inventory

**Date:** 2026-07-03
**Context:** Codebase review (docs/2026-07-03-review-fable.md) → seven FRs
(FR-668–674) → Judge rejected two (FR-668, FR-672), amended three.

## What happened

I ran a full-codebase review using two parallel exploration subagents, then
verified "the top claims" manually before filing seven FRs. The Judge
rejected two of them:

- **FR-668** claimed `tool_nodes.py` writes top-level `state["error"]` and
  that parallel map fan-out loses branch failures via last-write-wins. The
  writes are actually *nested response payloads* under `state_key` — a
  different pattern the state_builder comment at line 65 explicitly warns
  about. I had grepped, seen `"error": str(e)` in tool_nodes.py, and read it
  as a state-level write. The comment disambiguating it was one line above
  my other grep hit.
- **FR-672** claimed retry/fallback logic is duplicated between
  `executor.py` and `executor_async.py`. It is not. The async path delegates
  to `invoke_async`, which has *no* retry loop and *no* FR-464 fallback.
  The subagent asserted duplication; I verified `executor.py`'s side of the
  claim (the retry loop exists) and mistook half-verification for
  verification.

## The trap

A compound of two known traps with a new twist:

1. **quick_confidence** — the subagent reports read like completed analysis:
   tables, severity tags, file:line citations. Citation *format* is not
   citation *accuracy*. A subagent's confident file:line reference has the
   same epistemic status as any other LLM output: plausible shape, unverified
   substance (`plausible_wrong_answer`).
2. **Half-verification** — I did spot-check before filing. But for a claim of
   the form "X duplicates Y", I opened X and not Y. For "tool nodes write
   state-level error", I confirmed the write exists but not its *level*. A
   duplication claim is a two-ended claim; verifying one end verifies
   nothing. The verification felt complete because a file was opened and the
   quoted line was found.

The new twist: the review→FR pipeline *launders* uncertainty. A hedged
subagent observation ("may diverge", "likely uses") became a review finding,
then an FR Problem statement, each hop stripping a qualifier. By FR time the
claim read as established fact — and I wrote acceptance criteria for a bug
nobody had reproduced.

## What worked

The system worked exactly as designed. The Judge did what the Sermon says:
read thrice against the code, granted no authority to unproven claims. Both
rejections cite the specific disproof (delegation target, payload nesting).
Cost of the failed claims: two rejected FR documents. Cost if unjudged:
implementation work against a phantom bug, plus a state-schema migration
justified by a race that doesn't exist.

Also notable: the Judge *added* scope where I under-claimed (FR-670's
streaming sibling, FR-673's loader-wiring gap). Verification runs both
directions.

## Heuristic

**Verify both ends of every relational claim.** "A duplicates B",
"A writes to B", "A bypasses B" — subagent claims of this shape require
opening *both* files before the claim enters an FR. One-ended verification
is unverified. Corollary for delegated exploration: treat subagent file:line
citations as hypotheses to check, never as evidence to cite onward — the
citation's precision is styling, not provenance.

This is the third instance of the pattern this quarter if counting the
`gate_checks_shape_not_substance` family: outputs that carry the *markers*
of rigor (line numbers, tables, severity grades) pass review precisely
because the markers are what review looks for. Candidate for graduation:
`cited_is_not_verified`.

## Seed

The review→FR pipeline stripped hedges at each hop. Could the FR template
require a **Provenance** line per Problem-statement claim — `verified-both-ends
| verified-one-end | subagent-reported` — so the Judge sees the evidence
tier instead of re-deriving it? The gate would check presence; the Judge
checks whether "verified" claims cite the disambiguating line, not just the
matching one.
