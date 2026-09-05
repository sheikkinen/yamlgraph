# Feature Request: Outsider reader — an adversarial third reader for PR (and FR) descriptions

**Priority:** HIGH
**Type:** Enhancement (process instrument, advisory)
**Status:** Proposed
**Effort:** 1 day (spike exists; skill layout + wrapper + canary fixtures)
**Requested:** 2026-09-05
**First consumer / first event:** the author of any `feat`/`fix` PR, at the moment the PR is opened and before `scripts/review.sh` runs — the outsider's report tells them what a reader with no project context cannot understand from the title and body. Second consumer: the reviewer, who receives the "what a merge decision would still need" list and partitions it into *exists-but-unlinked* and *absent*. Third: this FR itself (dogfood — see Acceptance Criteria).
**Research:** [docs/2026-09-05-research-plan-cap-journey-census.md §12](../docs/2026-09-05-research-plan-cap-journey-census.md) — the spike record (setup, two prompt versions, three canaries with expectations written before each run, results, conclusions), and the committed spike copy at [docs/spikes/outsider-reader-2026-09-05/](../docs/spikes/outsider-reader-2026-09-05/) (graph, prompt v1 and v2, tools, wrapper, inputs, six reports, `EXPECTATIONS.md`). Alternatives dispositioned in-body.
**Prior art:** [.github/skills/judge-fr/doctrine.md](../.github/skills/judge-fr/doctrine.md) — reads an FR *with* doctrine; this reader reads *without* anything (inverted input closure). [.github/skills/review-pr/doctrine.md](../.github/skills/review-pr/doctrine.md) — reads a PR against its FR and judgement with file access; this reader has no file access and no FR; it runs *before* review and hands review its checklist. [scripts/review.sh](../scripts/review.sh) — wrapper shape copied (lock, artifact check, exit code not trusted). [FR-742](FR-742-undelivered-diary-detection.md) — successor briefing; same "addressed to whoever is addressed to no one" problem, different artifact. Diary [2026-07-16-the-human-skims](../docs/diary/diary-2026-07-16-the-human-skims.md) — documents optimise for the next agent, not the human; this FR makes that measurable per PR. No REJECTED FR found in this territory (grep of `feature-requests/` for "outsider", "plain language", "readability", "comprehension": none).

## Summary

A reader that knows nothing about this project reads a pull request's title and body — and nothing else — and reports, in four fixed sections, what it understood, what it could not understand, and what a merge decision would still need. It runs on `gpt-5.6-sol` from a directory outside the repository (so the Copilot CLI cannot load the project's instructions), has no file access and no tools, and its output is advisory. It sits before `review-pr` in the Submit step. Later the same reader can be pointed at an FR body; that is not in scope here.

## Value Statement

Authors learn, before a reviewer's time is spent, which parts of their description only make sense to someone who already knows the project; reviewers receive a checklist of what the description did not tell them.

## Problem

On 2026-09-05 the operator judged four consecutive recaps and PR #591's description unreadable to an outsider ("even I have hard time understanding what's being said"). The description was a pasted commit message in project shorthand. The rulebook already says *who reads this when* and *substance over presence*; neither fired, because the only reader in the loop was the author, whose vocabulary is the problem. An author-side "write plainly" rule was considered and rejected: it asks the writer to judge their own clarity — same session, same priors, same blind spot (the recap failures happened while the author held the rule in mind).

The spike (plan §12) ran a context-free reader on three inputs. Against the original #591 body it produced 33 things it could not understand and could not say who the change was for. Against the operator-approved plain rewrite it restated the change correctly but still found six phrases that assumed team context ("the business plan", "the fast, cheap one we had agreed to try"). Against the final body it said YES and listed five project-specific terms, which were then glossed. It also found a real defect the humans missed: the plain rewrite's title claimed a census of 242 while the text reported 30. Its "what is missing" section listed sixteen items of which ten existed in the PR but were not pointed to, and six were genuinely absent — including automated tests on a `feat` PR, a rule violation found by a reader who has never seen the rule.

## Raw Output Read (measurement / metric-tooling FRs only)

- **Samples read:** six reports, all read end-to-end, committed under [docs/spikes/outsider-reader-2026-09-05/out/](../docs/spikes/outsider-reader-2026-09-05/out/): `pr-591-*` (original body, prompt v1 and v2), `plain-591-*` (approved plain account, v1 and v2), `pr-591-v2-*` (rewritten body, v2).
- **What I saw:**
  - v1 on the plain account: 41 items, 16 typed "undefined term" — for *plain English* ("what counts as use", "what does valid mean", "someone running a pipeline"). Told to "be exhaustive", the model interrogated ordinary words as if they were jargon. The item count did not separate a bad description (33) from a good one (41); it scaled with text length and diligence.
  - v1 restatement of the original body: "instruments and pilots *something called* the FR-990 CAP journey census … the intended users are not stated." The hedge is the signal. The restatement of the plain account was correct in one read. Restatement separates; count does not.
  - v2 (comprehension-only, cap 8): counts became informative — 8 (original body, all real shorthand) / 6 (plain account) / 5 (rewritten body). The six on the plain account were all self-referential team context; the operator-approved text was plain but not self-contained.
  - v2's YES/NO produced a **false YES** on the original body: "30/30" and a wildcard path satisfied "what was found" and "where to look". The verdict cannot be asked of the model.
  - Report B's chapter 4 (v1), checked line by line against the PR: 10 of 16 "missing" items existed but were unlinked; 6 were absent (tests, runs 1–2, indirect-use evidence, cost, locality, model comparison). The reader cannot partition these — only someone with the files can. That is the reviewer handoff.
  - `cli_flags.model: "{state.model}"` is not templated; the CLI failed with *Model "{state.model}" is not available* and exit 0 / empty output. The artifact check caught it; the exit code would not have.

## Ideal Result

Every `feat`/`fix` PR gets, within a minute of opening, a comment from a reader with zero project context: one paragraph restating the change, at most eight phrases it could not understand, and a short list of what a merge decision would still need. The author fixes the text; the reviewer partitions the list. A derived verdict (not the model's) says whether the description stands alone. Over twenty PRs the count of "could not understand" items per PR is recorded; if it falls, the instrument worked, and only then is a blocking gate considered.

## Proposed Solution

Copy the spike; do not reinvent it.

1. **Skill layout** — `.github/skills/outsider-view/`: `doctrine.md` (what it is; inverted input closure — title + body only, no files, no tools, no doctrine, run from a clean directory; what it is not — not a reviewer, not a rewriter, not a gate; output advisory), `adapters/graph.yaml` and `adapters/prompts/outsider.yaml` copied from `docs/spikes/outsider-reader-2026-09-05/` via the authoring route (`scripts/author.sh`, brief cites the spike files as the source), `adapters/README.md` in the judge/review style.
2. **Wrapper** — `scripts/outsider.sh <pr-number> [--fr <path>]`, copied from the spike's `outsider.sh` (itself copied from `review.sh`): fetches title + body with `gh pr view`, writes the PR text to a **clean temporary directory outside the repo**, runs the graph from there, verifies the report by artifact (heading `## 1. In my own words` present), never trusts the exit code. Lock and lineage sentinel as in `review.sh`.
3. **Derived verdict in code** (small python tool node after the model): YES iff section 3 has ≤ 2 items **and** section 1 contains none of the hedge markers `does not say`, `something called`, `not stated`, `cannot tell`. The model's own section-2 answer is kept in the report as its opinion, labelled as such.
4. **Model** — `gpt-5.6-sol`, pinned literally in `cli_flags` (operator decision: PR-level text is read by the judge-class model). No `allow_all_paths`, no `allow_all_tools`.
5. **Canary fixtures** — the three spike inputs and `EXPECTATIONS.md` move to `.github/skills/outsider-view/fixtures/`; a `--selftest` flag runs all three and fails if they do not separate (original body: derived NO, ≥ 5 items; rewritten body: derived YES, ≤ 5 items; plain account: correct restatement, NO for pointer reasons).
6. **Posting** — the wrapper prints the report path; posting it as a PR comment is a separate explicit `--comment` flag, off by default. Nothing auto-merges, auto-approves, or blocks.
7. **Measurement** — a one-line append to `docs/census/outsider-ledger.jsonl` per run: PR, derived verdict, section-3 count, section-4 count, git SHA. Twenty rows before any gate is proposed.

## Acceptance Criteria

- [ ] AC-1: `scripts/outsider.sh --selftest` runs the three fixtures and passes the separation rule in Proposed Solution 5; the run fails closed if the report lacks the section-1 heading.
- [ ] AC-2: The graph has no `allow_all_paths`/`allow_all_tools`; the wrapper runs it from a directory that contains no `.github/`; a test asserts both (grep on the adapter yaml; wrapper dry-run prints the working directory).
- [ ] AC-3: The derived verdict is computed in code, unit-tested on the six committed reports: original-body reports → NO; rewritten-body report → YES; plain-account reports → NO.
- [ ] AC-4: `scripts/outsider.sh 591` reproduces a report on the current #591 body with ≤ 5 section-3 items (regression against the v2 result).
- [ ] AC-5: Dogfood: this FR's own PR receives an outsider report generated from the spike before merge; the report is posted as a PR comment; every section-3 item is either glossed in the FR text or explicitly kept with a reason in the PR thread.
- [ ] AC-6: `doctrine.md` states the inverted input closure and the three-reader division (author ← section 3; reviewer ← section 4; verdict derived) in ≤ 60 lines; the adapter README follows the judge/review README shape.
- [ ] AC-7: Ledger line written per run (Proposed Solution 7); no gate, no blocking, no auto-comment by default.
- [ ] AC-8: Tests tagged `@pytest.mark.req` under a new CAP; changelog fragment; the spike directory stays as the reference copy and is cited from the skill README.

## Alternatives Considered

| # | Alternative | Disposition |
|---|---|---|
| 1 | Author-side skill: "write PR descriptions plainly" | REJECTED — the writer judges its own clarity; the failures this FR closes happened while the author held that rule. |
| 2 | Extend `review-pr` with a readability section | REJECTED — the reviewer has file access and the FR; once it has read them it is no longer an outsider. Separate reader, handoff list to review instead. |
| 3 | GitHub Copilot PR summary (vendor feature) | REJECTED for this purpose — it *writes* a description from the diff (author side); it does not read the author's text as a stranger. |
| 4 | Cheap model (haiku / mercury-2) | DEFERRED — operator decision is `gpt-5.6-sol` for PR-level text; the restatement paragraph is judgement, not a label. Revisit if the ledger shows cost matters. |
| 5 | Ask the model for the YES/NO | REJECTED by evidence — false YES on the original #591 body (spike v2). Derived in code. |
| 6 | Blocking gate on the derived verdict | DEFERRED — twenty ledger rows first (Proposed Solution 7). A gate calibrated on three inputs is a guess with a hook. |
| 7 | Point the reader at FR bodies as a second target | NOT IN SCOPE (operator, 2026-09-05) — dogfood on this FR's PR instead (AC-5). |

## Related

- [docs/2026-09-05-research-plan-cap-journey-census.md](../docs/2026-09-05-research-plan-cap-journey-census.md) §11 (the approved plain account), §12.1–12.7 (the spike)
- [docs/spikes/outsider-reader-2026-09-05/](../docs/spikes/outsider-reader-2026-09-05/) — committed spike copy
- [FR-990](FR-990-cap-journey-census.md) — the PR whose description was the first input
- Diaries: [the-recap-nobody-outside-could-read](../docs/diary/diary-2026-09-05-the-recap-nobody-outside-could-read.md), [the-junk-drawer-moved-when-i-reworded-it](../docs/diary/2026-09-05-reflection-fr-990-the-junk-drawer-moved-when-i-reworded-it.md)
- Separate FR candidate, not bundled: guard-by-content for graph files under `examples/` (the `gh-profiler.yaml` filename bypass, plan §12.5)
