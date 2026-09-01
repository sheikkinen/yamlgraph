# 2026-09-01 — FR-949: the judge loop converges, the operator overrides, the index collides again

## The arc

Channel C (GitHub-Issues delegation via self-hosted runner) went from audit of
FR-948, through a spike with two live witnesses, three judge rounds, two
operator vetoes, one branch-deletion recovery, to a fully offline-enforced
bundle — 77 witnesses, five commits of RED/GREEN proof trail — in one day.

## Traps encountered

**one_session_one_repo, twice.** The FR-948 session squash-merged its PR and
deleted the shared branch + worktree while my unpushed rev-4 commit sat on
that branch. The commit went dangling; recovery was `git branch <pin>
699d3a1c` + cherry-pick onto a fresh branch. Second collision of the same arc.
The Scripture's ritual (commit immediately, audit after) saved the work, but
the deeper cure was structural: this enforcement ran in its own worktree from
the first command. The worktree is to sessions what the disposable checkout is
to delegated payloads — same boundary law at a different scale.

**noqa_as_reflex.** I decorated every subprocess call in the new test file
with `# noqa: S603/S607` — and the confession gate rightly demanded sixteen
confessions. The codes were already per-file-ignored for `tests/**` in
pyproject. The noqa comments weren't suppressing anything; they were noise
that CREATED a doctrine debt. Before annotating, check what the config already
forgives: the suppression you don't write is the cheapest confession.

**mock_escape_hatch, resisted deliberately.** `windows_job.ps1` is offline-
tested only by static contract markers (deadline default, Job Object API
names, unconditional cleanup). The temptation was a PowerShell mock harness
proving "timeout works" on macOS. But the feature exists because of a physical
phenomenon — Windows process-tree ownership — so the behavioral truth belongs
to the AC-17 live witness. A mocked Job Object test would be a unit test in an
E2E costume, and worse: green paint over unwitnessed kernel behavior. The FR
records this as a decision, not a gap.

**pycache_dirties_the_boundary.** `submit.sh` runs the worker's own normalizer
before checking tree cleanliness — and the normalizer's `__pycache__` dirtied
the tree it was about to judge. Fix at the entry boundary:
`PYTHONDONTWRITEBYTECODE=1` in the script, not a porcelain filter downstream.
The checker must not mutate the checked.

## Insight: the judge loop converged 8 → 7 → 4, then the operator cut

Three rounds of APPROVED WITH REVISIONS produced monotonically fewer, sharper
revisions — the fold loop worked as designed. But convergence is asymptotic;
the operator's "do not rejudge" (O-3) was the halting oracle the loop lacks.
Two of the final revisions were vetoed with a rationale no judge had: the
system doesn't exist yet, so output filtering and repo allowlists optimize a
hypothetical. The judge judges the spec against doctrine; only the operator
can judge the spec against reality's stage of existence. That division —
mechanical convergence, human halting — looks like the durable shape of
plan-judge under supervision.

## Insight: the spike runner became dev infrastructure by operator fiat

The imac-spike runner was authored as disposable evidence. The operator kept
it for dev. Spike artifacts have a way of becoming load-bearing the moment
they work; the FR explicitly fences it ("evidence, not production") so the
promotion, if it comes, must pass through an FR rather than through inertia.

**Seed:** the delegation issue is a typed request/result surface between
machines — exactly the shape of a chaplain inbox entry. When channels A and C
have coexistence data, could the winning channel become the chaplain's
transport, making `delegate`-labeled issues the mechanical form of "submit to
inbox" — and the coexistence experiment itself a template for how doctrine
chooses between competing infrastructures with witnesses instead of taste?
