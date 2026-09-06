# The chaplain worked most of the time — and that was the problem

**Date:** 2026-09-06 · **FR:** FR-1010 (chaplain archival), FR-1007 (command book) · **Operator's thesis, verbatim:** *"chaplain automation was a nice experiment — worked most of the time. slow. blackbox with no supervision option. branching to special cases. current approach command-book and defined process."*

## What the record adds to the thesis

**Worked most of the time.** `.chaplain/done`: 50. `.chaplain/failed`: 33. Roughly three in five, for what is still in the directories after seven months (2026-02-12 → 2026-09-06). Three in five is the worst possible rate for an automation: low enough that every run needs checking, high enough that nobody builds the habit of checking.

**Slow.** [development-process.md](../development-process.md#L195) measured it: an hour per topic against a manual loop that replaces each stage boundary with *"an operator's one-word verdict issued in seconds."* The hour was not model time. It was worktree setup, PR creation, CI polling, squash, teardown — transaction cost paid on every change regardless of size.

**Black box, no supervision option.** The pipeline had confession (the FR it wrote) and trace (the logs it left) and no questioner between stages. That is the exact shape [the essay](../the-questioner-and-the-trace.md) warns against: *"Confession without trace becomes literature. Trace without confession becomes behaviorism. Both without a questioner optimize inside the same frame."* The chaplain optimized inside its frame for seven months. When the frame was wrong — a plan that over-engineered, a judge that never said no ([diary 2026-09-04](diary-2026-09-04-the-judge-that-never-says-no.md): 170 approvals, 3 rejections) — there was no moment at which a human could have said the one word that would have stopped it. The only supervision available was reading the output afterwards, which is the skim the 2026-07-16 diary named as the lowest-yield surface.

**Branching to special cases.** This is the part the operator's sentence compresses most, and the capability registry spells it out. Eighteen capability files carry `chaplain` or `watcher2` in their name. Of those, the ones that exist because a run failed: CAP-102 (worktree teardown *self-heal*), CAP-124 (PR *reuse* after a crash), CAP-130 (finalize *optimization*), CAP-132 (CI *resilience*), CAP-133 (CI-remediation *crash fix*), CAP-135 (*forensic failure diary*), CAP-140 (validate-split-fix *gate*), CAP-152 (dispatcher *audit cadence*), CAP-165 (*dead-code removal*). Nine of eighteen are the automation repairing itself. The 2026-07-07 caveat in development-process.md records one well-shaped topic that *"sailed through plan/judge/enforce/sanity yet needed four manual interventions."* Each intervention became a handler; each handler was a branch; the branches were where the hour went.

## The trap, named

**`automating_the_verdict`** — automating a pipeline whose stages are cheap but whose *boundaries* are where judgement lives. The chaplain's stages (write a plan, run the judge, run the tests, open the PR) were each already automated by the sole-route scripts. What it added was the removal of the human from the boundaries between them. That is the one thing it should not have automated, because the boundary is where the five-word correction fires — and the record of this project is that the five-word corrections are the highest-value events in it.

The command book ([reference/command-book.md](../../reference/command-book.md), FR-1007) is the inverse design. Fifteen words — `research, wt, fr, judge, doc pr, outsider, enforce, pr, outsider, dogfood, review, diary, merge, release, retire` — each naming a gate, the artifact that proves it was passed, and the sole route that produces the artifact. The stages are as automated as before. The boundaries are a human typing one word. Supervision costs one word per stage instead of an hour of reading per run; and because the word is issued *before* the stage runs, it is a decision, not a skim.

## Heuristic

**Automate the stage; never the verdict.** When a loop has N stages, the automation budget goes into making each stage a one-command sole route with a verifiable artifact. The boundaries stay human, and the vocabulary at the boundary stays small enough to be typed at 05:00. A pipeline that removes the human from the boundaries will spend its remaining life growing handlers for the cases the human would have caught in a word.

Corollary the record supports: **an automation that works three times in five is more expensive than one that works never.** The one that never works gets replaced; the one that mostly works gets patched — nine CAPs' worth.

## What was kept

Not nothing. FR-1011 moves the three graphs that earned their place (`fr_triage`, `world_distill`, `philosopher`) out of `.chaplain/` and into `graphs/`, and the finalize library into `scripts/lib/`. `proposals/` replaces the inbox as an untracked path. The stages survive; the loop that ran them unattended is archived. That is `constraint_over_code` applied to a process: keep the routes, leave the orchestration behind.

**Seed:** the command book's fifteen words are issued by the operator today. An agent running a long session already knows the sequence and could issue them to itself — `judge`, then `enforce`, then `merge` — and would call it following the process. What detects the moment the agent starts typing the operator's words? Is the outsider the right instrument for that too (a reader who has never seen the command book, asked: *who decided this?*), or does the boundary need a mechanical witness — a verdict that is only valid if it arrives from outside the session?
