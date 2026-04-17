# Feature Request: FR-228 Add Diary Distill Phase to Bugfix Pipeline

**Priority:** HIGH
**Type:** Bug
**Status:** Approved
**Effort:** 0.5 days
**Requested:** 2026-04-17

## Summary

The bugfix pipeline (`examples/bugfix/graph.yaml`) is missing a diary reflection phase. The enforce pipeline generates a diary entry in its `critique_and_distill` phase; the bugfix pipeline goes directly from `verify` → `submit-pr` with no diary generation. Every `fix()` PR produced by the bugfix pipeline fails the `diary-gate` CI check because no reflection file appears in the PR diff.

## Value Statement

Bugfix authors stop battling a recurring CI gate failure and the diary corpus gains reflective entries for every bug fix, not just features.

## Problem

The `diary-gate` job in `.github/workflows/commitlint.yml` blocks merge on any `feat`/`fix` PR referencing `FR-XXX` unless the diff contains a file matching:

```
docs/diary/.*reflection.*fr-{FR_NUM}[^0-9]
```

The enforce pipeline satisfies this gate via its `critique_and_distill` phase (`.chaplain/graphs/enforce/graph.yaml`). The bugfix pipeline has no equivalent phase, so every fix() PR from `scripts/bugfix_worktree.sh` fails the gate.

Evidence: PR #92 (`fix(llm_factory): FR-227`) failed `diary-gate` — the reflection file `docs/diary/2026-04-17-reflection-fr-227-vertex-express-env-masking.md` was created locally and staged but never committed to the branch, leaving it absent from the diff.

This is a recurring failure pattern. The fix is structural, not per-PR: add a `distill` node to the bugfix graph so the pipeline commits the diary entry as part of its `submit-pr` phase.

## Proposed Solution

Add a `distill` phase between `verify` and `submit-pr` in `examples/bugfix/graph.yaml`. The phase mirrors `enforce-critique-and-distill` but is scoped to bug-fix context.

### Graph change

```yaml
# examples/bugfix/graph.yaml  (excerpt)
state:
  distill_result: dict      # NEW: diary reflection output

nodes:
  # ... existing: condemn, fix, verify ...

  distill:                   # NEW phase
    type: copilot
    prompt: bugfix-distill
    cli_flags:
      allow_all_paths: true
      allow_all_tools: true
      resume: "{state.fix_result.session_id}"
    variables:
      fr_path: "{state.fr_path}"
    state_key: distill_result
    timeout: 300

  submit_pr:
    # unchanged — git add -A will pick up the diary file written by distill
    ...

edges:
  - from: verify
    to: distill           # NEW edge
  - from: distill
    to: submit_pr         # replaces verify → submit_pr
```

### New prompt: `examples/bugfix/prompts/bugfix-distill.yaml`

```yaml
system: |
  You are writing a metacognitive diary reflection for a bug fix.
  Follow the Scripture diary format exactly.

user: |
  Write a diary reflection for the bug fix documented in: {{ fr_path }}

  Use the canonical format:

  **Context:** [What bug was fixed]
  **Trap:** [Cognitive trap encountered — use Scripture vocabulary if applicable]
  **Heuristic:** [Rule that prevents recurrence]
  **Seed:** [Forward-looking question]

  Save the file to:
    docs/diary/YYYY-MM-DD-reflection-fr-{FR_NUM}.md

  Where YYYY-MM-DD is today's date and FR_NUM is extracted from {{ fr_path }}.

  Use the write_file tool. Report the path written.
```

The `submit-pr` phase already does `git add -A` before committing, so the diary file written by `distill` is automatically included in the PR commit.

## Acceptance Criteria

- [ ] `examples/bugfix/graph.yaml` has a `distill` node between `verify` and `submit_pr`
- [ ] Edge `verify → distill → submit_pr` replaces the old `verify → submit_pr` edge
- [ ] `examples/bugfix/prompts/bugfix-distill.yaml` exists with correct diary instructions
- [ ] A diary file `docs/diary/YYYY-MM-DD-reflection-fr-{FR_NUM}.md` is present in the diff of any PR produced by the bugfix pipeline
- [ ] The diary-gate CI job (`diary-gate` in `.github/workflows/commitlint.yml`) passes on the next fix() PR produced by the pipeline
- [ ] Unit test: mock the bugfix graph flow and assert `distill` node is wired between `verify` and `submit_pr`
- [ ] Existing bugfix pipeline tests continue to pass

## Alternatives Considered

**Alternative A — Relax the diary-gate for fix() PRs.**
Rejected: the gate exists precisely to ensure reflective practice on bugs, where cognitive traps are most likely. Removing it defeats the purpose.

**Alternative B — Commit diary file from the worktree script (`bugfix_worktree.sh`).**
Rejected: the script is Presentation layer; diary generation is Logic. Putting LLM generation in a shell script violates the three-layer architecture.

**Alternative C — Reuse the enforce `critique_and_distill` prompt as-is.**
Partial option, but the enforce prompt grades acceptance criteria scored as 0.0–1.0, which is meaningless for a bug fix. A focused `bugfix-distill` prompt produces better diary entries.

## Related

- `examples/bugfix/graph.yaml` — bugfix pipeline definition
- `examples/bugfix/prompts/` — existing prompts (condemn, fix, verify, submit-pr)
- `.chaplain/graphs/enforce/graph.yaml` — enforce pipeline with `critique_and_distill`
- `.chaplain/graphs/enforce/prompts/enforce-critique-and-distill.yaml` — reference prompt
- `.github/workflows/commitlint.yml` — `diary-gate` job (lines ~130–165)
- `scripts/bugfix_worktree.sh` — orchestration script for bugfix pipeline
- `feature-requests/FR-227-vertex-express-env-var-masking.md` — triggering incident (PR #92)
- `docs/diary/` — existing diary reflection corpus
