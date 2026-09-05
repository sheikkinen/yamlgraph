# Judgement: FR-1007 Command book — what each one-word operator verdict obliges

**Verdict:** APPROVED WITH REVISIONS — the command book is a useful, minimal pattern-documentation artifact, but authority activates only after R-1 through R-7 are folded into the FR and the human decision in R-5 is recorded.

**Prior art:** [FR-1007-command-book.md](FR-1007-command-book.md) — the subject; its `**Prior art:**` line dispositions `docs/development-process.md` §3, the one-pager, the release checklist, FR-995 and FR-1001. R-5 human decision recorded in the FR (operator, 2026-09-05: merge given in a sequence is permission to proceed; agent may abort or fix).

**Reviewed against:** `feature-requests/FR-1007-command-book.md`; `reference/command-book.md`; `.github/copilot-instructions.md`; `.github/skills/judge-fr/doctrine.md`; `.github/skills/judge-fr/judgement.template.md`; `.github/skills/graph-authoring/doctrine.md`; `.github/skills/outsider-view/doctrine.md`; `.github/skills/review-pr/doctrine.md`; `.github/skills/feature-request/SKILL.md`; `.github/skills/release-version/SKILL.md`; `feature-requests/TEMPLATE.md`; `docs/development-process.md`; `reference/onepager-development-process.md`; `reference/release-checklist.md`; `reference/development-operations.md`; `reference/README.md`; `feature-requests/FR-995-outsider-reader.md`; `feature-requests/FR-1001-yamlgraph-outsider-demo-repo.md`; and path-existence checks for `scripts/author.sh`, `scripts/judge.sh`, `scripts/outsider.sh`, `scripts/review.sh`, and `scripts/worktree.sh`. The cited `docs/diary/2026-09-05-reflection-fr-1001-the-expectations-were-about-the-other-model.md` is absent from HEAD and therefore supplied no evidence.

## What is sound

The proposal has one responsibility and a small surface: one vocabulary reference plus one index entry (`feature-requests/FR-1007-command-book.md:14-16,30-33`). A separate reference page is smaller than a new orchestration script and avoids hiding the human decisions between phases (`feature-requests/FR-1007-command-book.md:45-49`). This satisfies **scope** and **single responsibility**.

The problem is real enough to document. The repository already describes an operator-driven manual loop and explicitly records the use of short verdicts such as `reflect`, `diary`, and `commit push` (`docs/development-process.md:177-196`). The FR names a concrete first consumer and event (`feature-requests/FR-1007-command-book.md:8`). Strategically, this is **pattern documentation**, not a framework primitive: the underlying routes and process stages already exist.

The implementation shape is feasible and aligned with the documentation architecture. `reference/README.md` already provides an index (`reference/README.md:7-24`), the five named scripts exist, and existing doctrine supplies concrete judge, author, outsider, review, worktree, and release behavior (`.github/copilot-instructions.md:204-212`; `.github/skills/graph-authoring/doctrine.md:91-107`; `.github/skills/outsider-view/doctrine.md:56-60`; `.github/skills/review-pr/doctrine.md:58-80`; `reference/development-operations.md:49-59`; `reference/release-checklist.md:5-20`). This satisfies **feasibility** and supports **architecture alignment** once the authority distinctions in R-2 are corrected.

The proposal correctly answers `is_this_a_graph: No` (`feature-requests/FR-1007-command-book.md:9`). A static cross-reference table needs no model call. Its structural claims can be checked directly, so **testability** is achievable after the acceptance criteria are made precise.

## Required revisions

### R-1: Supply substantive committed research

Replace the anecdotal `**Research:**` field with a link to a committed `feature-requests/FR-1007-command-book.research.md`, or to an equivalent committed in-body record. The record must contain four to six genuine solution classes, exact precedent lines, preserved disagreement, and the existing `is_this_a_graph: No` answer. It must specifically test whether a new command book is preferable to extending an existing process reference, adding a compact section to an existing reference, generating an artifact inventory, or introducing orchestration.

The current field cites a process description and an unrecorded session claim (`feature-requests/FR-1007-command-book.md:9`), while the alternatives table contains only three author dispositions (`feature-requests/FR-1007-command-book.md:43-49`). That does not satisfy the prospective research gate (`.github/skills/judge-fr/doctrine.md:118-130`; `.github/skills/feature-request/SKILL.md`, “Research Evidence”). Remove the dangling diary citation at line 55 or restore a committed evidence file at that exact path.

### R-2: Distinguish doctrine, required routes, recommended commands, and local conventions

Add a source-of-authority rule to the FR and require the book to classify every row as one of:

1. canonical doctrine and its sole route;
2. an operational procedure or recommended command;
3. an FR-1007 local ordering convention; or
4. an alias with no independent obligation.

Replace “the five skill doctrines” and the blanket “sole route” wording (`feature-requests/FR-1007-command-book.md:24,32,38`) with exact sources. The repository itself distinguishes canonical doctrine files and sole routes from operational `SKILL.md` procedures (`docs/development-process.md:101-114`); the release command is recommended rather than declared sole (`reference/release-checklist.md:5-20`). The book must be subordinate to each cited source: a conflict is a book defect, not a doctrine override.

### R-3: Freeze the vocabulary grammar

Define the sequence as exactly fifteen ordered **entries**, not fifteen words. State that `doc pr` is one atomic entry, that `outsider` intentionally appears twice because it applies once to the plan PR and once to the implementation PR, and that aliases do not add entries. Define when a shorter sequence is permitted and which entries are mandatory for documentation-only, plan-only, and implementation changes.

This removes the ambiguity between “fifteen-word sequence,” a two-word `doc pr` token, and a repeated `outsider` (`feature-requests/FR-1007-command-book.md:14-16,37`). It also makes the table count mechanically testable.

### R-4: Reconcile and source the four ordering claims

Name all four orderings in the FR and classify them accurately:

1. judge before implementation, with re-judgement after a material FR amendment — existing doctrine;
2. outsider before review — existing doctrine (`.github/copilot-instructions.md:211`; `feature-requests/FR-995-outsider-reader.md:8`);
3. arm auto-merge only at the `merge` step, after the last push — new FR-1007 local convention requiring committed incident evidence;
4. propose retirement only after release — new FR-1007 local convention requiring a precise definition and committed evidence.

Change “three [new orderings]” at `feature-requests/FR-1007-command-book.md:32` to two. Define `retire` as a proposal or disposition only; actual removal requires its own judged scope. Replace “judge before any edit” with “judge before implementation,” because writing and revising the FR necessarily precedes judgement.

### R-5: Preserve the human merge decision

State that the displayed sequence is an ordering reference, not batch authorization: no token authorizes a later token, and no earlier `pr` instruction may arm auto-merge. Review is advisory and the merge decision belongs to a human (`.github/skills/review-pr/doctrine.md:7-9,74-80`).

**Human decision required:** Must `merge` be uttered after the review result is available, or may an earlier sequence containing `merge` remain valid if review has no blocking findings and CI later passes?

- **A — recommended:** require a fresh post-review `merge` instruction.
- **B:** permit advance authorization, but require the book to state the exact no-blocker and green-CI predicates that preserve it.

Record the selected option in the FR before authority activates.

### R-6: Make the evidence promise truthful

Replace the claim that every word leaves a file whose absence proves omission (`feature-requests/FR-1007-command-book.md:8,20,28,37`) with a per-entry evidence contract. Each row must name:

- the obligation;
- whether its witness is durable or transient;
- the exact path, Git ref, GitHub object, command result, or status transition that witnesses it;
- the command or assertion used to verify that witness; and
- the authority source and route classification from R-2.

A worktree directory can disappear during cleanup, while merge and release are represented by Git/GitHub objects, so “missing file means skipped step” is not generally true. If successor reconstruction remains an objective, every row must name a durable witness; otherwise narrow the Ideal Result to live-session gate checking.

### R-7: Replace aspirational criteria with exact assertions and close the diff

Rewrite AC-01 through AC-05 using the revised criteria below. In particular:

- replace “passes the outsider step” with exactly one advisory run whose findings are glossed or explicitly dispositioned; do not require a YES result (`feature-requests/FR-1007-command-book.md:40`; `.github/skills/outsider-view/doctrine.md:33-39,56-60`);
- choose `reference/README.md` as the one index surface and remove “if” (`feature-requests/FR-1007-command-book.md:33`);
- correct Alternative 3 so it does not imply a second link from `docs/development-process.md` (`feature-requests/FR-1007-command-book.md:49`);
- include the research record and required diary in the allowed diff, because the current AC-05 excludes both (`feature-requests/FR-1007-command-book.md:41`; `.github/copilot-instructions.md:212`; `docs/development-process.md:89-100`).

## Scope is frozen

| Deliverable | Surface |
|---|---|
| D-1 | `feature-requests/FR-1007-command-book.research.md` — substantive research record required by R-1 |
| D-2 | `feature-requests/FR-1007-command-book.md` — folded revisions, selected R-5 human decision, and final implementation status |
| D-3 | `feature-requests/FR-1007-command-book.judgement.md` — human-reviewed final judgement |
| D-4 | `reference/command-book.md` — fifteen-entry vocabulary, evidence, authority, routes, aliases, and four orderings |
| D-5 | `reference/README.md` — exactly one index row linking D-4 |
| D-6 | `docs/diary/YYYY-MM-DD-reflection-fr-1007-*.md` — reflection containing `**Seed:**` |

Not authorized: changes to `.github/copilot-instructions.md`; any skill doctrine or adapter; scripts, hooks, CI, runtime code, graph or prompt artifacts; a `rite.sh` or other orchestrator; automatic execution of the sequence; enabling auto-merge before the human merge decision; performing retirement or deletion under FR-1007; a changelog fragment; or documentation changes outside D-1 through D-6.

## Revised acceptance criteria

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

## Conditions for enforcement

| # | Condition | Severity |
|---|---|---|
| C-1 | No implementation authority exists until R-1 through R-7 are folded, the R-5 human decision is recorded, the FR status records that revisions are folded, and the final judgement is committed. | GATE |
| C-2 | The command book remains subordinate to cited doctrine and procedures; any conflict is corrected in the book rather than treated as a new doctrine rule. | GATE |
| C-3 | Only the two local conventions identified in R-4 may be introduced; every other obligation must quote or link an existing committed authority. | GATE |
| C-4 | No command sequence may bypass a human merge decision, and no auto-merge may be armed before the selected R-5 authorization point. | GATE |
| C-5 | Outsider output remains advisory, runs once per PR, and does not become a blocking gate or a loop-to-YES requirement. | GATE |
| C-6 | Retirement under this FR stops at a disposition or separate proposal; no artifact is deleted. | GATE |
| C-7 | The implementation diff is confined to D-1 through D-6. | GATE |

Authority granted: after all revisions and gates are satisfied, implement only the documentation surfaces D-1 through D-6 as a subordinate operator-vocabulary reference; no process automation or enforcement change is authorized.
