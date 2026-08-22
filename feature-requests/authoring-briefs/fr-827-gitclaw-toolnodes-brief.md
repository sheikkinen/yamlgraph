# Task Brief: fold ledger/contain/push tool nodes into gitclaw.yaml

Governing FR: feature-requests/FR-827-gitclaw-forkable-runner.md.
Amendment to the previously authored orchestrator at
`/Users/sheikki/Documents/src/gitclaw/gitclaw.yaml` (external sibling
repo — write files there directly, do not git-commit). The prior
authoring deviated from the FR's pipeline spec: `contain` and `push`
are `tool_call` stages IN the graph, and ledger transitions are
orchestrated by the graph (FR-826 precedent). Fix that.

## Context (read first)

- `/Users/sheikki/Documents/src/gitclaw/gitclaw.yaml` — current graph
  (plan → judge → judge_gate → enforce → review → review_gate).
- `/Users/sheikki/Documents/src/gitclaw/tools/ledger.py` — CLI:
  `python -m tools.ledger record <issue> <state>` (validates
  transition legality, appends state/issues.jsonl),
  `should-run <issue>` (exit 0/78).
- `/Users/sheikki/Documents/src/gitclaw/tools/contain.py` — CLI:
  `python -m tools.contain <feature_name>` exits 1 on any changed
  path outside the feature allowlist.
- reference/graph-yaml.md — shell/tool node syntax.

## Change

Extend `gitclaw.yaml` with deterministic shell tool nodes so the
graph orchestrates the full pipeline. The workflow will only do:
trust gate + should-run + `yamlgraph graph run gitclaw.yaml`.

Node sequence (LLM nodes unchanged; insert shell nodes between):

1. `ledger_seen` — after START: `python -m tools.ledger record {issue_number} seen`
   then commit ledger: `git add state/issues.jsonl && git commit -m "gitclaw: #{issue_number} seen"`.
   (One shell node may run both commands; keep it simple.)
2. plan (existing) → `ledger_planned` (record + commit) → judge
3. judge → judge_gate (existing):
   - APPROVED → `ledger_judged_approved` (record + commit) → enforce
   - else → `reject_close` — shell: record `judged_rejected`, commit,
     `gh issue comment {issue_number} --body-file features/{feature_name}/judgement.md`
     and `gh issue close {issue_number}` → END
4. enforce → `ledger_enforced` (record + commit) → review
5. review → review_gate (existing):
   - APPROVED → `ledger_reviewed_approved` → contain
   - REJECTED first lap → record `reviewed_rejected`, commit → enforce
   - REJECTED final → `reject_final` — record `reviewed_rejected_final`,
     commit, comment review.md on issue, close → END
6. `contain` — shell: `python -m tools.contain {feature_name}`;
   on_error: fail (fail closed).
7. `push` — shell: explicit-path add ONLY —
   `git add features/{feature_name} state/issues.jsonl && git commit -m "feat(gitclaw): #{issue_number} {feature_name}" && git push`,
   then record `pushed`, then
   `gh issue comment {issue_number} --body "Implemented in $(git rev-parse HEAD)"`,
   `gh issue close {issue_number}`, record `closed`, commit ledger, push again.
   (Splitting push into 2-3 shell nodes is fine if cleaner; each
   ledger record must precede its dependent side effect per FR-826.)

All shell nodes: `on_error: fail`. Use `{state.issue_number}` /
`{state.feature_name}` variable interpolation as the shell node
syntax requires. Runtime variables must be shell-quoted per yamlgraph
shell tool conventions (it sanitizes with shlex.quote automatically —
verify in reference).

## Validation

Lint + `graph info` structure check only — do NOT run the copilot
stages or the gh/git side effects. Record honestly.

```bash
yamlgraph graph lint /Users/sheikki/Documents/src/gitclaw/gitclaw.yaml
yamlgraph graph info /Users/sheikki/Documents/src/gitclaw/gitclaw.yaml
```

**Prior art:** historical authoring brief migrated from tmp/ by FR-852; dispositions in `feature-requests/FR-852-preserve-authoring-briefs.md`.
