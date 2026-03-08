# Feature Request: Add .chaplain/inbox Instructions to CLAUDE.md

**Priority:** LOW
**Type:** Enhancement
**Status:** Approved
**Effort:** 0.5 days
**Requested:** 2026-03-08

## Summary

Add `.chaplain/inbox` workflow instructions to `CLAUDE.md` so that Claude Code sessions (not only GitHub Copilot) know how to submit topics for the Plan → Judge → Enforce pipeline.

## Value Statement

AI agents using Claude Code can autonomously propose improvements by writing topics to `.chaplain/inbox/`, closing the loop between audit findings and feature request generation.

## Problem

The `.chaplain/inbox` workflow is documented in `.github/copilot-instructions.md` under "Submitting Proposals":

```
- Write a markdown file to `.chaplain/inbox/` with a descriptive kebab-case filename
- Content: plain text description of the problem or task — freeform, but actionable
- The `.chaplain/watch.sh` daemon picks it up and runs Plan → Judge → Enforce automatically
- Proposals are consumed on pickup; rejected FRs are skipped by the enforce pipeline
```

However, `CLAUDE.md` — the instruction file consumed by Claude Code (claude.ai/code) — contains **no mention** of the `.chaplain/inbox` mechanism. This means:

1. Claude Code sessions have no way to discover or use the autonomous proposal pipeline.
2. The Inquisitor audit loop (`inquisitor.sh --propose`) writes to `.chaplain/inbox/`, but agents reading only `CLAUDE.md` wouldn't know this pathway exists.
3. Documentation drift: two AI instruction files with asymmetric coverage of a core workflow.

## Proposed Solution

Add a "Submitting Proposals" section to `CLAUDE.md`, mirroring the content in `copilot-instructions.md`. Place it after the "Development Process" section:

```markdown
### Submitting Proposals
- Write a markdown file to `.chaplain/inbox/` with a descriptive kebab-case filename (e.g., `refactor-state-builder.md`)
- Content: plain text description of the problem or task — freeform, but actionable
- The `.chaplain/watch.sh` daemon picks it up and runs Plan → Judge → Enforce automatically
- For new features, a one-paragraph problem statement suffices — the Chaplain generates the FR and PR
- Proposals are consumed on pickup (moved out of inbox); rejected FRs are skipped by the enforce pipeline
```

No new code. No new scripts. Pure documentation alignment.

## Acceptance Criteria

- [ ] `CLAUDE.md` contains a "Submitting Proposals" section describing the `.chaplain/inbox/` workflow
- [ ] Instructions match the canonical text in `.github/copilot-instructions.md` (single source of truth)
- [ ] Section placement is logical (after "Development Process", before "Development Commands")
- [ ] No duplication or contradiction with existing documentation
- [ ] `grep -c "chaplain/inbox" CLAUDE.md` returns ≥ 1

## Alternatives Considered

1. **Do nothing** — `copilot-instructions.md` already has the instructions. Rejected because `CLAUDE.md` is read by a different tool (Claude Code) that doesn't consume `copilot-instructions.md`.
2. **Single instruction file** — Merge `CLAUDE.md` into `copilot-instructions.md`. Rejected because they serve different tools with different conventions (Claude Code expects `CLAUDE.md` at repo root).
3. **Symlink or include** — Point one file to the other. Rejected as overengineering for a 5-line section.

## Related

- `.github/copilot-instructions.md` — Canonical source of "Submitting Proposals"
- `feature-requests/068-chaplain-watch.md` — watch.sh design
- `feature-requests/FR-055-autonomous-chaplain.md` — Chaplain pipeline
- `feature-requests/FR-099-chaplain-inbox-smoke-test.md` — Inbox validation
- `.chaplain/watch.sh` — The daemon that processes inbox topics
