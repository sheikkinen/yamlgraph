# Task: gitclaw.yaml — durable ledger pushes with rebase (push-race fix)

## Context

Target repo: `/Users/sheikki/Documents/src/gitclaw` (separate git repo).
Target artifact: `/Users/sheikki/Documents/src/gitclaw/gitclaw.yaml` (existing, lint-clean).
Do NOT touch prompts/, tools/, features/, workflows.

On-runner witness run 32321156335 (issue #3) failed at the final
`push_feature_and_close` with a non-fast-forward rejection: another
writer pushed to main while the pipeline ran. Worse: every other
ledger tool only `git commit`s locally — on an ephemeral GitHub
Actions runner those transitions evaporate when the job ends, so a
mid-pipeline failure leaves NO durable ledger state at origin.

## Required changes (minimal, surgical — no other edits)

1. Every shell tool in `gitclaw.yaml` that performs `git commit`
   (`ledger_seen_commit`, `ledger_planned_commit`,
   `ledger_judged_approved_commit`, `ledger_enforced_commit`,
   `ledger_reviewed_approved_commit`, `ledger_reviewed_rejected_commit`,
   `reject_judgement_close`, `reject_review_final_close`) must, after
   its commit, append:
   `&& git pull --rebase && git push`
   so each transition is durable at origin and tolerates concurrent
   writers.
2. `push_feature_and_close`: insert `git pull --rebase && ` before
   BOTH existing `git push` commands.
3. No other change. Keep `>-` folded scalars, quoting style, tool
   names, node wiring, verdicts, timeouts identical.

## Validation

```bash
cd /Users/sheikki/Documents/src/gitclaw
yamlgraph graph lint gitclaw.yaml
grep -c "git pull --rebase && git push" gitclaw.yaml   # expect 8
grep -c "git pull --rebase" gitclaw.yaml               # expect 10 (8 ledger + 2 in push tool)
```

Smoke: lint only — do not execute the graph (it operates on live
GitHub issues). Record honest lint output in the authoring report at
`/Users/sheikki/Documents/src/gitclaw/features/../docs` — write report to
`/Users/sheikki/Documents/src/gitclaw/docs/authoring-report-2026-08-20-push-race.md`.

**Prior art:** historical authoring brief migrated from tmp/ by FR-852; dispositions in `feature-requests/FR-852-preserve-authoring-briefs.md`.
