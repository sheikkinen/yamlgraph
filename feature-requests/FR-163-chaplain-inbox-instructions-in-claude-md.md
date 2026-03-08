# Feature Request: FR-163 Add .chaplain/inbox Instructions to CLAUDE.md

**Priority:** LOW
**Type:** Enhancement
**Status:** Approved
**Effort:** 0.5 days
**Requested:** 2026-03-08

## Summary

Add a "Submitting Proposals" section to `CLAUDE.md` documenting the `.chaplain/inbox/` workflow, mirroring the existing instructions in `.github/copilot-instructions.md`.

## Value Statement

Claude Code sessions gain the ability to discover and use the autonomous proposal pipeline (`.chaplain/inbox/` → Plan → Judge → Enforce), closing the loop between audit findings and feature request generation.

## Problem

The `.chaplain/inbox/` workflow — where AI agents write topic files that are automatically picked up and processed through the Chaplain pipeline — is documented only in `.github/copilot-instructions.md`. The `CLAUDE.md` file, consumed by Claude Code (claude.ai/code), contains no mention of this mechanism.

This creates three issues:

1. **Discovery gap**: Claude Code sessions cannot discover or use the autonomous proposal pipeline.
2. **Broken audit loop**: The Inquisitor (`inquisitor.sh --propose`) writes to `.chaplain/inbox/`, but agents reading only `CLAUDE.md` don't know this pathway exists.
3. **Documentation drift**: Two AI instruction files with asymmetric coverage of a core workflow.

## Proposed Solution

Add a "Submitting Proposals" subsection to `CLAUDE.md`, placed after the "Development Process" section (after "### 4. Reflect: Is This Really Needed?" and its example block, before "## Development Commands"). The text must match the canonical source in `.github/copilot-instructions.md`:

```markdown
### Submitting Proposals
- Write a markdown file to `.chaplain/inbox/` with a descriptive kebab-case filename (e.g., `refactor-state-builder.md`)
- Content: plain text description of the problem or task — freeform, but actionable
- The `.chaplain/watch.sh` daemon picks it up and runs Plan → Judge → Enforce automatically
- For new features, a one-paragraph problem statement suffices — the Chaplain generates the FR and PR
- Proposals are consumed on pickup (moved out of inbox); rejected FRs are skipped by the enforce pipeline
```

**Scope**: Documentation-only. No new code, scripts, or configuration changes.

## Acceptance Criteria

- [ ] `CLAUDE.md` contains a "### Submitting Proposals" section describing the `.chaplain/inbox/` workflow
- [ ] Section text matches the canonical source in `.github/copilot-instructions.md` (verbatim)
- [ ] Section is placed between "Development Process" and "Development Commands"
- [ ] `grep -c "chaplain/inbox" CLAUDE.md` returns ≥ 1
- [ ] No duplication or contradiction with existing documentation
- [ ] PR follows Conventional Commits: `docs(claude-md): FR-163 add chaplain inbox instructions`

## Alternatives Considered

1. **Do nothing** — `.github/copilot-instructions.md` already has the instructions. Rejected because Claude Code reads `CLAUDE.md`, not `copilot-instructions.md`.
2. **Single instruction file** — Merge into one file. Rejected because the tools expect different filenames by convention (`CLAUDE.md` for Claude Code, `.github/copilot-instructions.md` for Copilot).
3. **Symlink or include mechanism** — Overengineering for a 5-line section.

## Related

- `.github/copilot-instructions.md` — Canonical source of "Submitting Proposals" section
- `feature-requests/068-chaplain-watch.md` — `watch.sh` design
- `feature-requests/FR-055-autonomous-chaplain.md` — Chaplain pipeline design
- `feature-requests/FR-099-chaplain-inbox-smoke-test.md` — Inbox validation
- `.chaplain/watch.sh` — Daemon that processes inbox topics
