# Feature Request: Elevate Scripture Reference in README

**Priority:** LOW
**Type:** Enhancement
**Status:** Implemented
**Effort:** 0.5 days
**Requested:** 2026-02-24

## Summary

Replace the buried "Remember" section at the bottom of README.md with a visible "Development Process" section positioned between "Testing" and "Security", making the Plan→Judge→Enforce workflow discoverable to new contributors.

## Value Statement

New contributors discover the development discipline before their first PR, reducing review friction and improving contribution quality.

## Problem

The README mentions the Scripture only at the very bottom in a "Remember" section (line 312–321):

```markdown
## Remember

Read the Scripture in .github/copilot-instructions.md.

Base process with Opus 4.5:
 - new feature specific chat
 - "Let us pray"
 - "Plan new project/xxxx"
 - "Judge" & "Amend" loop
 - "Enforce"
```

This has two issues:
1. **Invisible** — Most readers never scroll past Security. The development process that makes YAMLGraph maintainable is hidden.
2. **Informal** — The current text reads as personal notes ("Let us pray"), not contributor guidance.

## Proposed Solution

Replace the `## Remember` section (lines 312–321) with a `## Development Process` section placed between `## Testing` and `## Security`. Remove the old `## Remember` section entirely.

```markdown
## Development Process

YAMLGraph follows a structured development workflow documented in [the Scripture](.github/copilot-instructions.md):

1. **Research** — Explore alternatives before coding
2. **Plan** — Write a feature request with acceptance criteria
3. **Judge** — Critically review until scope is minimal and clear
4. **Enforce** — TDD, smallest sufficient change
5. **Distill** — Capture lessons in `docs/diary.md`

New contributors: read the Scripture before your first PR.
```

## Acceptance Criteria

- [x] `## Development Process` section exists in README.md between `## Testing` and `## Security`
- [x] Section links to `.github/copilot-instructions.md`
- [x] All five process steps (Research, Plan, Judge, Enforce, Distill) are listed
- [x] `## Remember` section is removed
- [x] No other README sections are modified
- [x] `yamlgraph graph lint examples/demos/hello/graph.yaml` still passes (smoke test)

## Alternatives Considered

1. **Add a separate CONTRIBUTING.md** — Rejected. The process is short enough for inline documentation, and a separate file adds discovery friction. Can be revisited if contributing guidance grows.
2. **Keep "Remember" and add a duplicate section higher up** — Rejected. Duplication invites drift. One authoritative location is better.
3. **Link from README to CLAUDE.md's "Development Process" section** — Rejected. CLAUDE.md is agent-facing; README is human-facing. The README should be self-contained for the five-line summary.

## Related

- `.github/copilot-instructions.md` — The Scripture (source of truth)
- `CLAUDE.md` § "Development Process" — Agent-facing version of the same workflow
- `feature-requests/FR-086-readme-when-not-to-use.md` — Recent README enhancement
