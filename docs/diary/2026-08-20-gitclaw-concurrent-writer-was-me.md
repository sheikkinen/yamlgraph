# 2026-08-20 — gitclaw: the concurrent writer was me

**Context:** FR-827 enforcement — forkable issue-to-feature cron
runner, plan→judge→enforce→review pipeline run by Copilot CLI inside
GitHub Actions. Six defects found, all by witnesses rather than
inspection, all cured RED→GREEN. Issue #3 went from filed to closed
with a working committed feature in 5m7s of runner time.

## The trap: one_session_one_repo, remote edition

The first on-runner witness failed at the terminal push. Root cause:
while the runner executed the pipeline, I pushed a test commit to the
same main branch from my desk. Every ledger transition on the runner
committed locally and evaporated with the ephemeral workspace; the
one tool that pushed was rejected non-fast-forward.

The Scripture already names this trap — but its wording assumes two
agent sessions sharing a *local* working tree. The generalization: a
CI runner executing your pipeline **is a parallel session**, and the
shared resource is not the index but the *remote ref*. I kept hands
off the gitclaw working tree, felt compliant, and collided anyway.
The boundary is the ref, not the directory.

The cure was double: `git pull --rebase && git push` at all 10
transition sites (durability + concurrency tolerance in one move),
and a behavioral rule for the enforcing session — no pushes to a repo
whose pipeline is in flight. Note the asymmetry: the mechanical fix
makes the *pipeline* tolerant, but nothing yet makes *me* tolerant.
The second half is still discipline, which the Scripture says is
where defects live.

## The insight: durability failures masquerade as the last step's bug

The failed run's log blamed `push_feature_and_close`. The actual
defect was distributed across every *earlier* tool that committed
without pushing — seven silent non-durabilities and one loud one. Only
the tool with `on_error: fail` spoke. This is `composition_bug` with a
twist: every component was individually correct even at runtime; the
failure was that correctness on an ephemeral machine is worthless
unless exported. **On ephemeral infrastructure, a state transition is
not complete until it is durable at origin.** Commit-without-push on a
runner is a no-op wearing a receipt.

## The second insight: my convention was an unstated LLM contract

The cron extractor required `state_key == feature directory name`. I
invented that convention writing `cron_run.py`; the enforce-phase LLM,
authoring a fresh graph from its own judgement, picked `aphorism` for
a feature living in `daily-aphorism-about-software-craft/`. Perfectly
reasonable — the contract existed only in my head and my test
fixtures. `two_strike_split` applied preemptively: rather than
patching the enforce prompt ("always name your state_key after the
directory"), the extractor now reconciles at the boundary — accepts a
lone self-named `{k: {k: text}}` candidate, fails closed on zero or
many. Prompts are the wrong place for schemas; the reading side must
tolerate the writing side's freedom or reject it loudly.

## What the witnesses bought

Every defect this session was found by *executing the adopter's
path*, not by reviewing code: the push race by filing a real issue,
the extractor mismatch by running the generated feature through the
real cron loop, the trailing-slash contain bug by a real untracked
dir. The generated aphorism is a fitting closing verdict on the
system that produced it:

> The craft of software is knowing which cracks are load-bearing.

The verdict-token inflation, the evaporating ledger, and the
state_key mismatch were all load-bearing cracks — invisible in lint,
fatal in production, found only under real load.

**Seed:** The runner-as-parallel-session generalization suggests the
ledger itself should carry a *lease*: intake records `running` with a
run ID, and any other writer (human or CI) checks the lease before
pushing. Could `one_session_one_repo` graduate from discipline to a
mechanical gate — a pre-push hook that queries in-flight Actions runs
on the target repo and refuses to race them?
