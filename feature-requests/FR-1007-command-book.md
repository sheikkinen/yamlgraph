# Feature Request: Command book — what each one-word operator verdict obliges

**Priority:** LOW
**Type:** Enhancement (documentation)
**Status:** Proposed
**Effort:** 0.5 day
**Requested:** 2026-09-05
**First consumer / first event:** the agent in the next interactive session, at the moment the operator types a bare sequence such as `wt, fr, judge, doc pr, outsider, merge` — it resolves each word to a gate, an artifact and a route without asking. Second: a successor session reconstructing what a past session skipped (the artifact column makes a skipped step visible as an absent file).
**Research:** `docs/development-process.md` §3.1 — the manual loop runs on one-word verdicts ("reflect", "diary", "commit push"); the Sermon of the Chaplain in `.github/copilot-instructions.md` names the stages but not the words. Today's FR-1001 session ran the full sequence and exposed two gaps: `review` was never run on a `feat` PR because auto-merge was armed at `pr` time, and `retire` was not proposed. `is_this_a_graph: No` — a reference table, no model call.
**Prior art:** `docs/development-process.md` §3 (the rite, its stages, why the manual loop dominates) — this FR adds the word-level contract it lacks; `reference/onepager-development-process.md` — one page on the process, no command vocabulary; `reference/release-checklist.md` — the `release` word in full, linked not duplicated; FR-995 / FR-1001 — the two `outsider` routes the book names. No REJECTED FR in this territory.

## Summary

One reference page, `reference/command-book.md`: the fifteen-word sequence
`research, wt, fr, judge, doc pr, outsider, enforce, pr, outsider, dogfood, review, diary, merge, release, retire`,
and for each word the gate it names, the artifact that proves it was passed, and the sole route where doctrine has one. Plus the four orderings that matter and the aliases (`reflect`, `commit push`, `plan`, `enforce. tdd`).

## Value Statement

The operator's five-word corrections work because the words are precise. The book makes the vocabulary explicit so a session that has never seen it executes the same gates, and a skipped gate shows as a missing artifact rather than a missing memory.

## Problem

The stages live in the Sermon; the routes live in five skills; the words live in the operator's habit. An agent assembles them per session from context, and the assembly drifts: today `review` was omitted from a `feat` PR and `merge` was armed before the reader gates could run. Nothing in the repo said the words, in order, with the proof each demands.

## Ideal Result

The operator types the sequence; the agent runs it; every word leaves the named artifact; a reader of the PR can tick the sequence off against files without asking anyone.

## Proposed Solution

1. `reference/command-book.md` — the table (word · gate · artifact · route), the four orderings, the aliases, a Related list. Derived from the Sermon and the five skill doctrines; adds no rule that is not already in one of them, except the three the FR-1001 session paid for: arm auto-merge at `merge` not `pr`; `outsider` before `review`; `retire` after `release`.
2. One line in `reference/README.md` (if it indexes reference pages) pointing at the book. No change to `.github/copilot-instructions.md` (byte ceiling; and a reference page is not Scripture until it recurs).

## Acceptance Criteria

- [ ] AC-01: `reference/command-book.md` exists; its table has exactly the fifteen words in the stated order, and every row names an artifact path or file pattern and cites a route or rule already present in the repo.
- [ ] AC-02: Every sole route named in the book (`scripts/judge.sh`, `scripts/review.sh`, `scripts/outsider.sh`, `scripts/author.sh`, `scripts/worktree.sh`) exists at that path.
- [ ] AC-03: The book adds no gate that does not exist elsewhere in the repo, except the three orderings named in Proposed Solution 1; the FR lists them.
- [ ] AC-04: The PR carrying this FR passes the `outsider` step itself and glosses what it flags.
- [ ] AC-05: This repository's diff: the book, this FR and its judgement, and at most one index line. No Scripture change.

## Alternatives Considered

| # | Alternative | Disposition |
|---|---|---|
| 1 | Add the sequence to `.github/copilot-instructions.md` | REJECTED for now — the instruction byte ceiling (FR-942) is 14 bytes from full; and Scripture graduation needs recurrence. Propose after the book has been used from two sessions. |
| 2 | Encode the sequence as a script (`scripts/rite.sh wt fr judge …`) | REJECTED — each word already has its script; the missing thing is the contract between them, which is a document. A meta-script would hide the human verdict between steps that the manual loop exists to keep. |
| 3 | Put it in `docs/development-process.md` §3.1 | REJECTED — that section explains *why* the manual loop wins; the book is *how* to run it. Linked from there instead. |

## Related

- `docs/development-process.md`, `reference/onepager-development-process.md`, `reference/release-checklist.md`
- [FR-995](FR-995-outsider-reader.md), [FR-1001](FR-1001-yamlgraph-outsider-demo-repo.md)
- diary `2026-09-05-reflection-fr-1001-the-expectations-were-about-the-other-model.md` ("arm auto-merge after the last push")
