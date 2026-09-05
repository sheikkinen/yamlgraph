# The Command Book — one-word verdicts and what each one obliges

The manual plan-judge-enforce loop is driven by one-word operator commands
(`docs/development-process.md` §3.1: "the operator judges with a one-word
verdict"). This book fixes what each word means: the gate it names, the
artifact that proves the gate was passed, and the sole route where doctrine
prescribes one. A word without its artifact was not done.

## The full sequence

```
research, wt, fr, judge, doc pr, outsider, enforce, pr, outsider, dogfood, review, diary, merge, release, retire
```

Shorter forms are the same sequence with steps already done or not applicable
(a docs-only change has no `enforce`; a plan-only PR stops at `doc pr,
outsider, merge`). A word said twice — `judge` after a material amendment,
`outsider` on every PR — is the gate run again, not a typo.

| Word | Gate | Artifact that proves it | Sole route / rule |
|---|---|---|---|
| **research** | Who solved this before? What don't I understand? Is this the right question? | committed research record (`docs/…research…md`, `FR-NNN.research.md`, or spike under `docs/spikes/`) with expectations written *before* runs; answer to `is_this_a_graph` | Commandment 1. `ask_before_generate`; a description of what exists is inventory, a statement of what it means for us is analysis |
| **wt** | Fresh branch in a worktree before any write | `tmp/worktrees/feat/<name>` exists; main untouched | `scripts/worktree.sh new <name>`; `one_session_one_repo`; main-write is denied (FR-888/889) |
| **fr** | Write the plan | `feature-requests/FR-NNNN-<slug>.md`: Ideal Result before Proposed Solution, first consumer + first event, ACs, Alternatives, `**Prior art:**` with REJECTED FRs dispositioned | `feature-requests/TEMPLATE.md`; `ideal_result_backwards`. On any number collision enumerate main + open PRs and pick ≥ max+3 — never +1 |
| **judge** | Independent verdict on the FR; never in the author's head | `FR-NNNN-<slug>.judgement.md` (`# Judgement`, `**Verdict:**`, `**Prior art:**`); revisions folded into the FR; status line updated | `scripts/judge.sh <fr>` → `tmp/draft-judgement-copilot-<FR>.md`. Prompt-adapter, sister-session and subagent judging are forbidden. Re-judge after any material amendment |
| **doc pr** | Freeze the plan on main before code exists | merged PR whose diff is FR + judgement (+ the doc itself for docs-only FRs) | title `docs(fr): FR-NNNN …`; nothing else in the diff |
| **outsider** | A reader with no project context reads the PR body; the author glosses what it flags | posted comment on the PR; body edited; report under `tmp/` (or `out/` in the standalone) | `scripts/outsider.sh <pr> --comment` (Copilot route) or `yamlgraph-outsider <pr> --comment` (provider-API route, FR-1001). Advisory. One run per PR; never loop to YES; run **before** `review` |
| **enforce** | Build exactly D-1…D-n from the judgement | RED commit (failing test) then GREEN commit; graphs/prompts only via a committed brief + `tmp/draft-authoring-report.md`; human decision recorded before any paid or public side effect | "Obey the Judgement". `scripts/author.sh <brief>` is the only way to author `graph.yaml`/`prompts/*.yaml`. Pre-command guard denies `--no-verify`, `SKIP=`, multiline `-m`, `pytest \| head` |
| **pr** | Open the implementation PR | PR with a plain-language body; FR status updated with an AC table — *met* / *NOT MET with evidence*; changelog fragment under `changelog/unreleased/`; deviations named | title `feat\|fix(scope): FR-NNNN …`; squash merge; auto-merge is **not** armed here |
| **outsider** | (again) on the implementation PR | comment + glosses, as above | same |
| **dogfood** | Use the shipped thing on its own PR | the tool's own output on the PR that ships it (comment, report, run log) | "the tool has to turn on the tool"; a mock dogfood is a unit test with extra steps |
| **review** | Informed adversary reads diff + FR + judgement + doctrine | `tmp/draft-review.md`; each finding fixed in a commit or dispositioned as a PR comment | `scripts/review.sh <pr> <fr>` only; never in the author's session; advisory until the human merge decision |
| **diary** | Metacognitive entry: the trap, the heuristic, the Seed | `docs/diary/YYYY-MM-DD-reflection-fr-NNNN-<slug>.md` containing literal `**Seed:**` | gate on feat/fix PRs requires the filename pattern and the Seed; a session's diary debt survives the session |
| **merge** | Let CI judge | squash commit on main; branch deleted | `gh pr merge N --squash --auto --delete-branch` armed **after the last push**, never at `pr` time (#597 merged ahead of its own amendments) |
| **release** | Ship what merged | version bump, tag, GitHub release; `CHANGELOG.md` regenerated from fragments | `.github/skills/release-version/`; `reference/release-checklist.md`. Unreleased fragments are not shipped |
| **retire** | What does this supersede? | keep / merge / retire disposition for each superseded artifact, filed as an FR or a line in the shipping FR | operator's standing correction: after any composing or wrapping artifact, propose the subtraction unprompted. Deletion via the FR pipeline is the safest operation in the repo |

## Ordering that matters

- **judge before any edit.** The operator's own rule: research → plan → judge → enforce, never skip judge. Amend the plan → judge again.
- **outsider before review.** The ignorant reader first, so the informed one is not asked to catch language it cannot see (`two_ends_of_the_knowledge_axis`).
- **auto-merge at `merge`, not at `pr`.** Armed early, it outruns `outsider`, `review` and `diary`.
- **retire after release.** Subtraction is proposed against what shipped, not what was planned.

## Words that are not commands

`reflect` → write the diary entry now (same as `diary`). `commit push` → commit the current tree with a conventional message, push, no PR — only legal on a worktree branch. `plan` → `fr`. `enforce. tdd` → `enforce` with RED committed before GREEN (which is what `enforce` already means).

## Related

- `docs/development-process.md` §3.1 — why the manual loop dominates and where the one-word verdicts come from
- `.github/copilot-instructions.md` — Sermon of the Chaplain (Research · Plan · Judge · Enforce · Purge · Submit · Distill)
- `.github/skills/{judge-fr,review-pr,outsider-view,graph-authoring,release-version}/` — the sole routes
