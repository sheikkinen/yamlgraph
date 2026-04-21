# Feature Request: FR-265 create_worktree drafts ignore fix

**Priority:** HIGH
**Type:** Bug
**Status:** Approved
**Effort:** 0.5 days
**Requested:** 2026-04-21

## Summary

Fix Chaplain copilot pipeline failure where `.chaplain/lib/worktree.py` runs `git add` on a draft under `.chaplain/drafts/`, but repository `.gitignore` excludes that directory. The python node fails with exit code `1`, stopping the pipeline before acceptance tests and judge complete.

## Value Statement

Chaplain pipeline operators get reliable Plan → Research → Worktree → Acceptance Tests → Judge execution without manual recovery when draft FRs are under ignored paths.

## Problem

`create_worktree()` currently does:

- Locate first `*.md` in `{drafts_dir}` via glob
- Run `git add <draft_path>`
- Run `git commit --no-verify ...`

This breaks because root `.gitignore` contains:

- `.chaplain/drafts/`

Observed behavior:

- `git add .chaplain/drafts/<file>.md` returns exit code `1`
- stderr: "The following paths are ignored by one of your .gitignore files: .chaplain/drafts"
- Copilot graph node `create_worktree` fails and aborts workflow

Secondary issue: selecting `fr_files[0]` from a glob is nondeterministic when multiple drafts exist.

## Proposed Solution

Update `.chaplain/lib/worktree.py` to make staging deterministic and robust for ignored draft paths.

1. Add explicit staging for ignored path:

```bash
git add -f <draft_path>
```

2. Keep commit behavior idempotent:

- If `git commit` returns non-zero with "nothing to commit", continue
- Any other git failure should raise

3. Remove nondeterministic draft selection:

- If no draft files: raise `FileNotFoundError` (existing behavior)
- If multiple draft files: raise a clear `ValueError` naming candidates
- If exactly one: proceed

4. Add focused unit tests for the tool behavior using subprocess mocks.

## Acceptance Criteria

- [ ] **AC-01:** `create_worktree()` stages draft FR file with forced add (`git add -f <draft_path>`)
- [ ] **AC-02:** Pipeline no longer fails when draft file is under ignored `.chaplain/drafts/`
- [ ] **AC-03:** `create_worktree()` fails fast with clear `ValueError` when multiple draft files exist
- [ ] **AC-04:** Existing single-draft happy path still succeeds
- [ ] **AC-05:** If `git commit` fails with "nothing to commit", pipeline continues (idempotent)
- [ ] **AC-06:** If `git commit` fails for other reasons (not "nothing to commit"), node raises with clear message
- [ ] **AC-07:** Unit tests added for ignored-path staging, multi-draft guard, and commit idempotency
- [ ] **AC-08:** No changes to `watch.sh` orchestration contract
- [ ] **AC-09:** Draft file remains on disk in `.chaplain/drafts/` after commit (downstream nodes read it)

## Alternatives Considered

### 1) Remove `.chaplain/drafts/` from `.gitignore`

Rejected. Draft and inbox directories are intentionally ignored to avoid committing volatile planning artifacts.

### 2) Copy/move draft into `feature-requests/` before worktree creation

Rejected for this fix. It changes pipeline semantics and interferes with `watch.sh` "new FR detection" timing and judge/amend flow.

### 3) Pass explicit draft path through graph state and stop globbing

Valid follow-up hardening, but not required for the immediate failure. This FR keeps scope to the concrete git-ignore failure plus deterministic selection guard.

## Related

- Issue: `https://github.com/sheikkinen/yamlgraph/issues/148`
- `.chaplain/lib/worktree.py`
- `.chaplain/graphs/copilot/graph.yaml`
- `.chaplain/watch.sh`
- `feature-requests/FR-260-acceptance-tests-before-enforce.md`

## Judge Verdict

**APPROVE** — scope frozen, authority granted.

### Evaluation

1. **Scope clear and minimal?** Yes. Single root cause (`git add` on ignored path), single file to change, with two defensive hardening items (multi-draft guard, commit idempotency) that are tightly coupled.

2. **Contradictions or ambiguities?** None after amendments. Three gaps identified and resolved:
   - **AC gap (commit idempotency):** Proposed solution mentioned handling "nothing to commit" but ACs didn't cover it. Added AC-05 and AC-06.
   - **AC gap (draft file survival):** `write_acceptance_tests` and `judge` nodes both read from `{drafts_dir}` after `create_worktree` commits. The fix must not delete or move the draft. Added AC-09.
   - **AC numbering:** Added explicit AC-XX IDs for traceability.

3. **Acceptance criteria measurable?** Yes — each AC maps to a specific assertion in unit tests.

4. **Implementation approach feasible?** Yes. Three-line change (`git add` → `git add -f`, multi-draft guard, commit stderr inspection). No new modules or dependencies.

5. **Alignment with architecture?** Yes. Follows boundary normalization principle — fixing at the entry point (`git add`) rather than downstream.

6. **Single responsibility?** Yes. All three changes address the same root cause: `create_worktree()` fragility when operating on ignored paths.

7. **Classification:** Bug fix on existing infrastructure. Not a framework primitive, not a pattern — a concrete defect in the Chaplain pipeline.

### Risks verified

| Risk | Status |
|------|--------|
| `git add -f` causes file accumulation on main | Acceptable — judge verdicts move/delete drafts; procedural, not technical |
| Moving draft to `feature-requests/` earlier would be cleaner | Rejected — breaks `write_acceptance_tests` and `judge` prompts that read from `{drafts_dir}` |
| `feature-requests/` path in `enforce_worktree.sh` has same bug | Confirmed NOT affected — `feature-requests/` is not in `.gitignore` |
