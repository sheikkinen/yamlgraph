# The chaplain worked most of the time — it automated a process that was not yet stable

**Date:** 2026-09-06 · **FR:** FR-1010 (chaplain archival), FR-1007 (command book) · **Operator's thesis, verbatim:** *"chaplain automation was a nice experiment — worked most of the time. slow. blackbox with no supervision option. branching to special cases. current approach command-book and defined process."*

## What the record adds to the thesis

**Worked most of the time.** `.chaplain/done`: 50. `.chaplain/failed`: 33. Roughly three in five, for what is still in the directories after seven months (2026-02-12 → 2026-09-06). Three in five is the worst possible rate for an automation: low enough that every run needs checking, high enough that nobody builds the habit of checking.

**Slow.** [development-process.md](../development-process.md#L195) measured it: an hour per topic against a manual loop that replaces each stage boundary with *"an operator's one-word verdict issued in seconds."* The hour was not model time. It was worktree setup, PR creation, CI polling, squash, teardown — transaction cost paid on every change regardless of size.

**Black box, no supervision option.** The pipeline had confession (the FR it wrote) and trace (the logs it left) and no questioner between stages. That is the exact shape [the essay](../the-questioner-and-the-trace.md) warns against: *"Confession without trace becomes literature. Trace without confession becomes behaviorism. Both without a questioner optimize inside the same frame."* The chaplain optimized inside its frame for seven months. When the frame was wrong — a plan that over-engineered, a judge that never said no ([diary 2026-09-04](diary-2026-09-04-the-judge-that-never-says-no.md): 170 approvals, 3 rejections) — there was no moment at which a human could have said the one word that would have stopped it. The only supervision available was reading the output afterwards, which is the skim the 2026-07-16 diary named as the lowest-yield surface.

**Branching to special cases.** This is the part the operator's sentence compresses most, and the capability registry spells it out. Eighteen capability files carry `chaplain` or `watcher2` in their name. Of those, the ones that exist because a run failed: CAP-102 (worktree teardown *self-heal*), CAP-124 (PR *reuse* after a crash), CAP-130 (finalize *optimization*), CAP-132 (CI *resilience*), CAP-133 (CI-remediation *crash fix*), CAP-135 (*forensic failure diary*), CAP-140 (validate-split-fix *gate*), CAP-152 (dispatcher *audit cadence*), CAP-165 (*dead-code removal*). Nine of eighteen are the automation repairing itself. The 2026-07-07 caveat in development-process.md records one well-shaped topic that *"sailed through plan/judge/enforce/sanity yet needed four manual interventions."* Each intervention became a handler; each handler was a branch; the branches were where the hour went.

## The trap, named

**`automating_before_stable`** — the operator's correction to my first draft, verbatim: *"processwise — chaplain went one step too far. automating a process that was not stable yet. if command-book commands get monotonous at some point — follow clear logic — program or llm, then that part can be automated. e.g. pr-outsider-review go hand-in-hand."*

My first draft named the trap `automating_the_verdict` — never remove the human from the boundaries. That is too strong, and the record contradicts it: for the mechanical words the human was never really at the boundary anyway. The actual error was **order**. The chaplain automated the whole fifteen-word sequence in one move, in February, before any sub-sequence of it had been observed to run the same way twice. Every one of the nine self-repair CAPs is a place where the process was still changing under the automation — the loop encoded a shape the process had not yet settled into, and then had to be patched each time the process moved. Slow, black-box and special-cased are all downstream of that one mistake.

The command book ([reference/command-book.md](../../reference/command-book.md), FR-1007) is the inverse *order*, not just the inverse design. Fifteen words — `research, wt, fr, judge, doc pr, outsider, enforce, pr, outsider, dogfood, review, diary, merge, release, retire` — each a gate with a verifiable artifact and a sole route. Because a human types each word, the sequence is *observable*: which words always follow which, where a correction lands between two words, which stretches run identically ten times. That observation is the stability measurement the chaplain never had. And the record of two days already shows a stable stretch: `pr → outsider → review` ran hand-in-hand every time, and for docs PRs `doc pr → outsider → gloss → merge` ran seven times with no correction inside it.

## Heuristic

**Automate a sub-sequence only after it has become monotonous under human issue.** The command book is not the alternative to automation; it is the instrument that tells you *which stretch* is ready for it. A run of words that is issued identically N times with no correction landing between them follows clear logic and can become one command — program or LLM, whichever the logic needs. A stretch where corrections still land between the words is not stable, and automating it buys the chaplain's nine CAPs again. The boundaries that stay human are the ones where corrections still arrive.

First candidate from the record: `pr → outsider` (always together, no correction between them in ~10 runs). Second: `doc pr → outsider → merge` for docs-only PRs. Not yet: anything containing `judge` or `review` — both still produce revisions the operator reads.

Corollary the record supports: **an automation that works three times in five is more expensive than one that works never.** The one that never works gets replaced; the one that mostly works gets patched.

## What was kept

Not nothing. FR-1011 moves the three graphs that earned their place (`fr_triage`, `world_distill`, `philosopher`) out of `.chaplain/` and into `graphs/`, and the finalize library into `scripts/lib/`. `proposals/` replaces the inbox as an untracked path. The stages survive; the loop that ran them unattended is archived. That is `constraint_over_code` applied to a process: keep the routes, leave the orchestration behind.

**Seed:** the command-book sequence is now a log — every session records which word followed which and where a correction landed. That log is the stability measurement. What is the threshold? N identical runs with zero corrections inside the stretch — five? ten? — and does the count reset when the sole route under one of the words changes? If the threshold is written down, the next automation is a census over the command log rather than a February-style guess, and the operator's silence between two words becomes data instead of absence.
