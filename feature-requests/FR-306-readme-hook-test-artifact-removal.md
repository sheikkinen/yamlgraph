# Feature Request: FR-306 Remove `hook test` Artifact from README

**Priority:** LOW
**Type:** Bug
**Status:** Implemented
**Effort:** 0.1 days
**Requested:** 2026-05-03

## Summary

Remove the stray trailing line `hook test` from `README.md` so the file ends at the license link.

## Value Statement

Repository readers get a clean, trustworthy top-level README without accidental internal test artifacts.

## Problem

`README.md` currently ends with an unintended line:

```markdown
hook test
```

Research findings:

1. The artifact is present at `README.md:323`.
2. Repository search shows only one real occurrence (`README.md`), indicating this is a leftover edit artifact, not intended documentation content.
3. Existing documentation FRs follow a minimal direct-edit pattern (`FR-086`, `FR-091`) for content hygiene fixes.

This creates visible documentation noise at the primary project entry point.

## Proposed Solution

Edit only `README.md` and delete the final `hook test` line. Keep:

1. `## License`
2. A blank line
3. `[MIT w/ SWC](LICENSE)` as the final content line

No other files, sections, or wording changes.

## Objectives

1. Remove the accidental `hook test` line from `README.md`.
2. Keep the README ending intact except for that single-line deletion.
3. Provide shell-level acceptance checks that fail before implementation.

## Constraints

- Scope is single-file (`README.md`) documentation hygiene only.
- No new lint rules, scripts, CI gates, or watcher pipeline changes.
- No wording rewrite outside the accidental artifact removal.

## Acceptance Criteria

- [x] **AC-01:** `README.md` does not contain a line exactly equal to `hook test`
- [x] **AC-02:** The last non-empty line of `README.md` is `[MIT w/ SWC](LICENSE)`
- [x] **AC-03:** Only `README.md` is modified by the fix
- [x] **AC-04:** No new tooling, scripts, or workflow gates are introduced

## Failing Acceptance Tests (RED)

Current failing checks in this worktree (`tmp/worktrees/feat/watcher2-gh-273`), run from repo root:

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

- Topic source: `.chaplain/processing/gh-273.md`
- Target file: `README.md`
- Prior doc-hygiene FRs: `feature-requests/FR-086-readme-when-not-to-use.md`, `feature-requests/FR-091-readme-missing-node-types.md`
