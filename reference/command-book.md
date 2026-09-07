# The Command Book — one-word verdicts and what each one obliges

The manual plan-judge-enforce loop is driven by one-word operator verdicts
(`docs/development-process.md` §3.1). This page fixes what each word obliges,
what witnesses that it was done, and where its authority comes from. It adds no
gate that does not already exist elsewhere, except two local ordering
conventions marked **[FR-1007 convention]**.

## The sequence

```
research, wt, fr, judge, doc pr, outsider, enforce, pr, outsider, dogfood, review, diary, merge, release, retire
```

Grammar (frozen by FR-1007):

- Fifteen ordered **entries**. `doc pr` is one entry. `outsider` appears twice
  on purpose: once on the plan PR, once on the implementation PR. Aliases
  (below) add no entries.
- A shorter utterance is the same sequence with entries already done or not
  applicable. Mandatory subsets: **plan-only** — `fr, judge, doc pr, outsider,
  merge`; **documentation-only** — `wt, fr, judge, doc pr, outsider, diary,
  merge` (no `enforce`, `dogfood`, `review`); **implementation** — all fifteen,
  `release` and `retire` may follow in a later session.
- Saying an entry twice re-runs its gate (`judge` after a material amendment).

**Authorization.** The sequence is an ordering reference, not a batch grant —
with one operator-recorded exception: a `merge` given in the sequence *is*
permission to proceed (operator decision 2026-09-05, FR-1007 R-5). The agent
still aborts and reports instead of merging when any of these holds: `review`
returned a blocking finding not yet fixed; an `outsider` item is neither glossed
nor dispositioned; the `diary` entry is not committed; CI is not green. Review
stays advisory; the human's word was given in advance, not skipped.

## Route classification

- **D** — canonical doctrine with a declared sole route (`.github/skills/*/doctrine.md`, `.github/copilot-instructions.md`).
- **P** — operational procedure or recommended command (a `SKILL.md`, a `reference/*.md`, a script not declared sole).
- **C** — FR-1007 local ordering convention, with committed incident evidence.
- **A** — alias; no independent obligation.

## The entries

| # | Entry | Obligation | Witness (durable / transient) | Verify | Authority · class |
|---|---|---|---|---|---|
| 1 | **research** | Who solved this before; what don't I understand; is this the right question; `is_this_a_graph` answered; expectations written before any run | durable: `feature-requests/FR-NNNN.research.md`, a `docs/*research*.md`, or a spike under `docs/spikes/` | file exists and the FR's `**Research:**` field links it | Commandment 1; `.github/skills/judge-fr/doctrine.md` research gate · **D** |
| 2 | **wt** | A fresh branch in its own worktree before any write | transient: `tmp/worktrees/feat/<name>/`; durable: the branch ref | `git worktree list`; `git branch --list feat/<name>` | `scripts/worktree.sh new <name>`; `one_session_one_repo`; main-write denied by FR-888/889 · **P** |
| 3 | **fr** | Write the plan: Ideal Result before Proposed Solution, first consumer + first event, ACs, Alternatives, `**Prior art:**` with REJECTED FRs dispositioned; number chosen ≥ max+3 across main and open PRs | durable: `feature-requests/FR-NNNN-<slug>.md` | file exists; template sections present (pre-commit `fr-checks`) | `feature-requests/TEMPLATE.md`; Sermon "Plan"; `ideal_result_backwards` · **D** |
| 4 | **judge** | Independent verdict, never in the author's session; revisions folded into the FR; status line updated. Re-run after any material amendment | durable: `feature-requests/FR-NNNN-<slug>.judgement.md` with `# Judgement`, `**Verdict:**`, `**Prior art:**` | file exists; FR status cites it | `scripts/judge.sh <fr>` → `tmp/draft-judgement-copilot-<FR>.md` — declared sole route; prompt-adapter, sister-session and subagent judging forbidden · **D** |
| 5 | **doc pr** | Freeze the plan on main before implementation: a PR whose diff is FR + judgement (+ research, + the document itself for docs-only FRs) | durable: merged PR titled `docs(fr): FR-NNNN …` | `gh pr view N --json state,title`; `git log --grep 'FR-NNNN'` on main | Sermon "Judge … freeze scope"; conventional-commit gate · **P** |
| 6 | **outsider** | A reader given only the PR title + body reports what it could not follow; author glosses or dispositions each item. Exactly one run; never loop to YES; **before** `review` | durable: the posted PR comment; transient: `tmp/outsider-pr-N-<stamp>.md` | `gh pr view N --json comments`; body edited | `scripts/outsider.sh <pr> --comment` (Copilot route, FR-995) or `yamlgraph-outsider <pr> --comment` (provider-API route, FR-1001). Advisory · **D** (outsider-before-review is doctrine: `.github/copilot-instructions.md` Submit step) |
| 7 | **enforce** | Build exactly D-1…D-n of the judgement. RED commit (failing test) before GREEN. Graphs/prompts only through a committed brief. Human decision recorded in the FR before any paid or public side effect | durable: RED and GREEN commits in `git log`; `feature-requests/authoring-briefs/<fr>-brief.md`; transient: `tmp/draft-authoring-report.md` | `git log --oneline` shows RED then GREEN; brief committed; report cited in the FR | Sermon "Enforce"; Commandment 7; `scripts/author.sh <brief>` — declared sole route for `graph.yaml`/`prompts/*.yaml`; pre-command guard denies `--no-verify`, `SKIP=`, multiline `-m`, `pytest \| head` · **D** |
| 8 | **pr** | Open the implementation PR: plain-language body; FR status updated with an AC table (*met* / *NOT MET with evidence*); changelog fragment; deviations named. Auto-merge is **not** armed here | durable: open PR titled `feat\|fix(scope): FR-NNNN …`; `changelog/unreleased/<fr>.md`; FR "Implementation status" section | `gh pr view N`; fragment exists; `gh pr view N --json autoMergeRequest` is null | `CLAUDE.md` PR conventions; changelog gate (FR-179) · **P**; no-auto-merge-here · **C** (evidence: PR #597, 2026-09-05, merged ahead of its own amendments — `FR-1007-command-book.research.md`) |
| 9 | **outsider** | Same as entry 6, on the implementation PR | as entry 6 | as entry 6 | as entry 6 · **D** |
| 10 | **dogfood** | Run the shipped thing on the PR that ships it | durable: the tool's output attached to the PR (comment, committed evidence file) | the artifact is present and names the PR | `docs/development-process.md` §7; `mock_escape_hatch` · **P** |
| 11 | **review** | Informed adversary: diff + FR + judgement + doctrine → merge verdict. Never in the author's session. Each finding fixed in a commit or dispositioned as a PR comment | transient: `tmp/draft-review.md`; durable: fix commits / disposition comments on the PR | `gh pr view N --json comments,commits` | `scripts/review.sh <pr> <fr>` — declared sole route; advisory until the human merge decision · **D** |
| 12 | **diary** | Metacognitive entry: the trap, the heuristic, a `**Seed:**` | durable: `docs/diary/YYYY-MM-DD-reflection-fr-NNNN-<slug>.md` | file matches the pattern and contains `**Seed:**` (PR gate on feat/fix) | Sermon "Distill"; Conventions ("Final task on any list …") · **D** |
| 13 | **merge** | Arm auto-merge **after the last push**, then let CI judge | durable: squash commit on main; branch deleted | `gh pr view N --json state,mergeCommit` | `gh pr merge N --squash --auto --delete-branch`; "What survives the fire may merge" · **P**; timing (at `merge`, never at `pr`) · **C** (same evidence as entry 8) |
| 14 | **release** | Bump, tag, GitHub release; `CHANGELOG.md` regenerated from fragments | durable: tag `vX.Y.Z`; GitHub release; version in `pyproject.toml` | `git tag --contains`; `gh release view vX.Y.Z` | `reference/release-checklist.md`; `.github/skills/release-version/SKILL.md` — recommended procedure, not a declared sole route · **P** |
| 15 | **retire** | For each artifact the shipped work supersedes, a keep / merge / retire **disposition** — a proposal or a line in the shipping FR, never the deletion itself. After `release`, against what shipped | durable: the disposition text in an FR (`## Alternatives Considered` or a new FR) | `grep -n 'retire\|supersede' feature-requests/FR-NNNN*.md` | operator standing correction (additive default; FR-765 arc); Commandment 8; after-release timing · **C** (evidence: FR-1004 retired the FR-995 ledger the day after it shipped; FR-1001 shipped without a disposition of spike 2 — `FR-1007-command-book.research.md`) |

## Ordering that matters

1. **judge before implementation** — and again after a material amendment. Writing and revising the FR precedes judgement; code does not. (doctrine)
2. **outsider before review** — the ignorant reader first, so the informed one is not asked to catch language it cannot see. (doctrine: `.github/copilot-instructions.md` Submit step; FR-995)
3. **auto-merge at `merge`, not at `pr`** — armed early it outruns `outsider`, `review` and `diary`. (**[FR-1007 convention]**, evidence PR #597)
4. **retire after release** — subtraction is proposed against what shipped, not what was planned. (**[FR-1007 convention]**, evidence FR-1004 / FR-1001)

## Aliases (class A)

`reflect` → `diary`. `plan` → `fr`. `enforce. tdd` → `enforce` (RED before GREEN is already its meaning). `commit push` → commit the current tree with a conventional message and push the branch; not a PR; legal only on a worktree branch.

## Related

- `docs/development-process.md` §3.1 (why the manual loop dominates), §2.1 (doctrine vs procedure)
- `.github/copilot-instructions.md` — Sermon
- `feature-requests/FR-1007-command-book.md` and `FR-1007-command-book.research.md`
