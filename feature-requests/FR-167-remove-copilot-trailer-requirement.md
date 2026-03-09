# Feature Request: Remove Co-authored-by Copilot Trailer Requirement

**FR-167**
**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Implemented
**Effort:** 0.5 days
**Requested:** 2026-03-08

## Summary

Remove the `Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>` trailer requirement from the codebase. Supersede FR-132 (copilot-trailer-enforcement). Delete trailer injection from `finalize_merge.sh`, remove the associated test, and stop Inquisitor from auditing it.

## Value Statement

Maintainers reclaim audit bandwidth currently spent on a non-functional trailer that adds no value to the project, eliminating a recurring source of false-positive violations and CALCIFIED findings.

## Problem

The Copilot `Co-authored-by` trailer has consumed disproportionate audit attention:

1. **No functional value.** The trailer is a GitHub Copilot convention injected into the system prompt of the agent. It does not affect CI, attribution, licensing, or any downstream tooling. It is metadata noise.
2. **Audit ritual, not process.** Inquisitor audits XXII–XXVI flagged the trailer as CALCIFIED-4 through CALCIFIED-6 — five consecutive violations. This spawned FR-132, which proposes a pre-commit hook to enforce it. The cure (mechanical enforcement of a non-requirement) is worse than the disease.
3. **FR-132 is scope creep.** FR-132 proposes modifying `.pre-commit-config.yaml`, `enforce_worktree.sh`, and `finalize_merge.sh` to enforce a trailer that exists only because the Copilot agent's system prompt instructs it to add one. This is not a project requirement — it is an agent configuration artifact.
4. **The Knowledge Graph's own trap applies.** `audit_as_ritual`: "3+ audits without fix → ritual, not process." The correct fix is not to mechanize the ritual — it is to recognize the ritual serves no purpose and eliminate the audit criterion.

## Proposed Solution

### 1. Remove trailer from `finalize_merge.sh`

Delete the `Co-authored-by: Copilot` line from the heredoc commit message (line ~106):

```bash
# Before (line 106)
Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>

# After
# (line deleted)
```

### 2. Remove trailer test from `test_finalize_merge.py`

Delete `test_commit_includes_co_author()` (lines ~435–448):

```python
# Delete entirely
def test_commit_includes_co_author(self, tmp_path):
    """Commit includes Co-authored-by trailer."""
    ...
```

### 3. Supersede FR-132

Update FR-132 status from `Approved` to `Superseded` with a reference to FR-167:

```markdown
**Status:** Superseded by FR-167
```

### 4. Stop Inquisitor from auditing the trailer

The Inquisitor's audit prompt in `.chaplain/inquisitor.sh` does not explicitly check for the trailer — it appears in audit findings via implicit commit metadata review. Once the trailer is removed from `finalize_merge.sh` and FR-132 is superseded, the Inquisitor will stop flagging it because:
- No script injects it → no expectation to check
- FR-132 is superseded → no open requirement to audit against

If the Inquisitor continues to flag it after these changes (due to LLM pattern recognition from historical audits), add an explicit exclusion note to the audit prompt.

### 5. No changes to diary entries

Historical diary entries (audits X through XXVI+) document the audit trail and should remain as-is. They are historical records, not active requirements.

### 6. No changes to `enforce_worktree.sh`

FR-132 proposed adding the trailer to `enforce_worktree.sh`. Since FR-132 is superseded, no changes are needed — the script correctly lacks the trailer.

## Acceptance Criteria

- [x] `scripts/finalize_merge.sh` no longer injects `Co-authored-by: Copilot` trailer
- [x] `tests/unit/test_finalize_merge.py::test_commit_includes_co_author` deleted
- [x] FR-132 status updated to `Superseded by FR-167`
- [x] `pytest tests/unit/test_finalize_merge.py -v` passes without the removed test
- [x] `ruff check scripts/ yamlgraph/ tests/` clean
- [x] No REQ-YG-XXX references need updating (none exist for the trailer)
- [x] CHANGELOG.md updated

## Alternatives Considered

1. **Implement FR-132 as-is.** This would mechanize the trailer requirement with a pre-commit hook. Rejected: the trailer has no functional value; enforcing it wastes developer time and hook execution budget on every commit.

2. **Keep trailer in `finalize_merge.sh` but stop auditing it.** This removes the audit noise but leaves dead convention in the script. Rejected: the Scripture says "Kill all entropy and false idols" — dead conventions are entropy.

3. **Replace with a meaningful attribution mechanism.** If co-authorship attribution is genuinely needed, use GitHub's native co-author detection or a project-level `.mailmap`. Rejected as out of scope — no evidence this attribution serves any downstream consumer.

## Related

- **FR-132** (copilot-trailer-enforcement): Superseded by this FR
- **Inquisitor Audits XXII–XXVI**: Audit trail documenting the trailer as CALCIFIED
- **Knowledge Graph**: `audit_as_ritual` trap — "3+ audits without fix → ritual, not process"
- `scripts/finalize_merge.sh:106`: Trailer injection point
- `tests/unit/test_finalize_merge.py:435-448`: Trailer validation test
