# Feature Request: FR-306 Remove `hook test` Artifact from README

**Priority:** LOW
**Type:** Bug
**Status:** Draft
**Effort:** 0.1 days
**Requested:** 2026-05-03

## Summary

Remove the stray trailing line `hook test` from `README.md` so the file ends at the license link.

## Value Statement

Repository readers get a clean, trustworthy top-level README without accidental internal test artifacts.

## Problem

Topic `.chaplain/processing/gh-264-v5.md` requests removing a leftover README artifact. Current state confirms `README.md` ends with an unintended line:

```markdown
hook test
```

Research findings from this worktree:

1. The artifact is present at `README.md:323`.
2. `rg '^hook test$' README.md` matches exactly one line in the target file.
3. Existing README hygiene FRs (`FR-086`, `FR-091`) use minimal, direct documentation edits without adding new tooling.

This creates visible documentation noise at the primary project entry point.

## Proposed Solution

Edit only `README.md` and delete the final `hook test` line. Keep:

1. `## License`
2. A blank line
3. `[MIT w/ SWC](LICENSE)` as the final content line

No other files, sections, or wording changes.

## Acceptance Criteria

- [ ] **AC-01:** `README.md` does not contain a line exactly equal to `hook test`
- [ ] **AC-02:** The last non-empty line of `README.md` is `[MIT w/ SWC](LICENSE)`
- [ ] **AC-03:** Only `README.md` is modified by the fix
- [ ] **AC-04:** No new tooling, scripts, or workflow gates are introduced

## Failing Acceptance Tests (RED)

Current failing checks in `tmp/worktrees/feat/watcher2-gh-264-v5`:

```bash
test "$(tail -n 1 README.md)" = "[MIT w/ SWC](LICENSE)"
# exits 1 (actual last line is: hook test)

! rg -n '^hook test$' README.md
# exits 1 (match found at README.md:323)
```

These checks should pass after implementation.

## Alternatives Considered

1. **Do nothing** — Rejected. Leaves a visible artifact in the project's front-door document.
2. **Add a new lint/check gate for accidental tokens** — Rejected for this request; broader process hardening is outside this single-file bug scope.
3. **Rewrite the README ending section** — Rejected. Unnecessary for a one-line artifact removal.

## Related

- Topic source: `.chaplain/processing/gh-264-v5.md` (main checkout)
- Target file: `README.md`
- Prior doc-hygiene FRs: `feature-requests/FR-086-readme-when-not-to-use.md`, `feature-requests/FR-091-readme-missing-node-types.md`
