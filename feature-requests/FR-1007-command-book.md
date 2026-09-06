# Feature Request: Command book — what each one-word operator verdict obliges

**Priority:** LOW
**Type:** Enhancement (documentation)
**Status:** Judged — APPROVED WITH REVISIONS (2026-09-05, [judgement](FR-1007-command-book.judgement.md)); R-1…R-7 folded; R-5 human decision recorded below
**Effort:** 0.5 day
**Requested:** 2026-09-05
**First consumer / first event:** the agent in the next interactive session, at the moment the operator types a bare sequence such as `wt, fr, judge, doc pr, outsider, merge` — it resolves each word to a gate, an artifact and a route without asking. Second: a successor session reconstructing what a past session skipped (the artifact column makes a skipped step visible as an absent file).
**Research:** [FR-1007-command-book.research.md](FR-1007-command-book.research.md) — six solution classes dispositioned (reference page chosen; Scripture, driver script, §3.1 expansion, prompt files, do-nothing rejected), exact precedent lines, the two 2026-09-05 incidents (#597 merged ahead of its amendments; #603 `feat` PR with auto-merge armed before review), and the preserved disagreements (merge authority; durable witnesses; how many rules are new). `is_this_a_graph: No`.
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

1. `reference/command-book.md`. **Grammar (R-3):** fifteen ordered *entries*; `doc pr` is one entry; `outsider` appears twice (plan PR, implementation PR); aliases add no entries; mandatory subsets named for plan-only, documentation-only and implementation sequences. **Per-entry contract (R-6):** obligation · witness marked durable or transient (path, Git ref, GitHub object or status) · verification command · authority citation · route class. **Route classes (R-2):** D canonical doctrine with declared sole route (`judge.sh`, `review.sh`, `author.sh`, outsider) · P operational/recommended (`worktree.sh`, release checklist, PR conventions) · C FR-1007 local convention with incident evidence · A alias. Only D rows say "sole". **Four orderings (R-4):** (1) judge before implementation, re-judge after material amendment — doctrine; (2) outsider before review — doctrine (`.github/copilot-instructions.md` Submit step; FR-995); (3) auto-merge armed at `merge`, never at `pr` — **new local convention**, evidence PR #597; (4) `retire` after `release` — **new local convention**, evidence FR-1004 / FR-1001. `retire` produces a keep/merge/retire *disposition*, never a deletion.
2. **Authorization (R-5).** The book states the sequence is an ordering reference, not batch authorization, and preserves review as advisory — with the operator's recorded decision: *"merge — if given as in the example is permission to proceed. agent may abort based on review or fix the implementation. anyhow full authorization given"* (2026-09-05; judge's option B, stronger). The book therefore lists the abort predicates: blocking review finding unfixed; outsider item neither glossed nor dispositioned; diary not committed; CI not green.
3. Exactly one index row in `reference/README.md` (Examples & Guides). No change to `.github/copilot-instructions.md`, `docs/development-process.md` or `reference/onepager-development-process.md`.

## Acceptance Criteria

- [ ] AC-01: `feature-requests/FR-1007-command-book.research.md` is committed and linked from the FR; it records four to six genuine solution classes, exact precedent lines, preserved disagreement, and `is_this_a_graph: No`; every prior-art hit in that record is dispositioned in the FR.
- [ ] AC-02: `reference/command-book.md` contains exactly fifteen table body rows in this order: `research`, `wt`, `fr`, `judge`, `doc pr`, `outsider`, `enforce`, `pr`, `outsider`, `dogfood`, `review`, `diary`, `merge`, `release`, `retire`. It states that `doc pr` is one entry and explains the two distinct `outsider` occurrences.
- [ ] AC-03: Every table row names an obligation, durable-or-transient witness, exact verification method, authority citation, and route classification. Every relative file link and named repository path resolves at HEAD.
- [ ] AC-04: Only commands whose governing source explicitly declares a sole route are labelled “sole.” `scripts/author.sh`, `scripts/judge.sh`, `scripts/outsider.sh`, `scripts/review.sh`, and `scripts/worktree.sh` exist, while release is described using the recommendation in `reference/release-checklist.md`.
- [ ] AC-05: The four ordering assertions are exactly those frozen in R-4. The first two cite existing doctrine; the latter two cite the committed R-1 evidence and are labelled FR-1007 local conventions rather than Scripture.
- [ ] AC-06: `retire` means producing a keep/merge/retire disposition or a separate proposal after release. The book does not authorize deletion, and “judge before implementation” does not prohibit writing or revising the FR.
- [ ] AC-07: The book states that the sequence is not batch authorization, records the human choice from R-5, never arms auto-merge at `pr`, and preserves review as advisory pending the human merge decision.
- [ ] AC-08: Exactly one outsider run is recorded for the PR carrying this FR. Every unclear phrase is either glossed in the PR body or explicitly dispositioned; no acceptance condition requires a derived YES.
- [ ] AC-09: `reference/README.md` gains exactly one row linking `reference/command-book.md`; `docs/development-process.md`, `reference/onepager-development-process.md`, and `.github/copilot-instructions.md` are unchanged.
- [ ] AC-10: Relative to the implementation base, the changed paths are a subset of D-1 through D-6, and the final diff contains no script, hook, CI, runtime, graph, prompt, changelog, or doctrine change.

## Alternatives Considered

| # | Alternative | Disposition |
|---|---|---|
| 1 | Add the sequence to `.github/copilot-instructions.md` | REJECTED for now — the instruction byte ceiling (FR-942) is 14 bytes from full; and Scripture graduation needs recurrence. Propose after the book has been used from two sessions. |
| 2 | Encode the sequence as a script (`scripts/rite.sh wt fr judge …`) | REJECTED — each word already has its script; the missing thing is the contract between them, which is a document. A meta-script would hide the human verdict between steps that the manual loop exists to keep. |
| 3 | Put it in `docs/development-process.md` §3.1 | REJECTED — that section explains *why* the manual loop wins; the book is *how* to run it. The book links to §3.1; §3.1 is not edited. |

## Related

- `docs/development-process.md`, `reference/onepager-development-process.md`, `reference/release-checklist.md`
- [FR-995](FR-995-outsider-reader.md), [FR-1001](FR-1001-yamlgraph-outsider-demo-repo.md)
- diary `2026-09-05-reflection-fr-1001-the-expectations-were-about-the-other-model.md` ("arm auto-merge after the last push")
