# Feature Request: Home Config Cleanup — Dead Agents and Global CLAUDE.md

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Proposed
**Effort:** 0.5 days
**Requested:** 2026-08-31
**First consumer / first event:** every Copilot/Claude agent session in every workspace, at session start when the agent roster and global instructions are injected
**Research:** In-body dispositioned alternatives table (below) — session context analysis 2026-08-31

## Summary

Remove or relocate dead user-home agent definitions and gut the contradicting global `~/.claude/CLAUDE.md`, cutting ~2k tokens of dead weight and one live doctrine contradiction from every session in every workspace.

## Value Statement

The operator's agents stop paying ~2k tokens/turn for kalevala songwriting in a Python framework repo, and stop receiving planning doctrine that contradicts the Scripture.

## Problem

Witnessed 2026-08-31 (session context analysis):

1. **Dead agents.** `~/.claude/agents/` contains 7 global agent definitions; 6 are creative-workflow agents irrelevant to yamlgraph and most other workspaces (`forge-image-generator`, `image-art-analyzer`, `image-prompt-architect`, `kalevala-songwriter`, `long-video-generator`, `topical-image-downloader`). Each carries a multi-paragraph description with embedded examples; combined they inject ~2k tokens into the agent roster of every turn in every workspace. Only `project-planner` has plausible cross-repo use.
2. **Contradicting global instructions.** `~/.claude/CLAUDE.md` (15 lines) mandates a `docs/plan-<topic>-initial.md` → `plan-mvp` → `plan-barebones` planning process and "implement statemachine transitions as self-contained scripts" — both contradict this repo's FR-pipeline-only doctrine (the statemachine line is a leftover from statemachine-engine). It also says "Estimate effort realistically" while platform instructions forbid time estimates. It loads into every session as a live contradiction source (`instruction` boundary: agent system prompts are where vendor/global instructions enter — treat drift there as a defect).

## Proposed Solution

1. Disposition each of the 7 files in `~/.claude/agents/`: **keep-global / move-to-owning-workspace / delete**. Default expectation: the 6 creative agents move to their home projects (e.g. an image-gen workspace) or die; `project-planner` is evaluated on its own merits against the repo's FR pipeline (likely delete — the Sermon supersedes it).
2. Gut `~/.claude/CLAUDE.md` to lines true everywhere. Candidate surviving content: the no-Co-authored-by rule only (already enforced by repo hooks — evaluate deleting the file entirely).
3. Witness: record `ls ~/.claude/agents` and `cat ~/.claude/CLAUDE.md` before/after in this FR at enforcement time.

**Scope note:** targets live in `$HOME`, outside the repo write barrier. Enforcement is shell ops against `~/.claude/`; the repo diff is this FR itself plus the recorded witness. No repo code changes.

## Acceptance Criteria

- [ ] Each of the 7 agent files has a written disposition (keep/move/delete) with one-line rationale, recorded in this FR
- [ ] Dispositions executed; `ls ~/.claude/agents` after-state recorded in this FR
- [ ] `~/.claude/CLAUDE.md` contains no planning-process doctrine, no statemachine-engine leftovers, no effort-estimation directive (or the file is deleted); after-state recorded
- [ ] A fresh agent session in yamlgraph shows no creative agents in the roster (operator spot-check)

## Alternatives Considered

| Alternative | Disposition |
|---|---|
| Leave as-is; tokens are cheap | Rejected — cost is per-turn × per-session × all workspaces; the contradiction risk (conflicting planning doctrine) is worse than the token cost |
| Rewrite CLAUDE.md into a good global doctrine | Rejected — no content has been identified that is true in every workspace and not already enforced elsewhere; growth_as_default |
| Move agents into VS Code user prompts folder instead | Rejected — same global injection problem, different loader |
| Repo-side ignore/filter of global agents | Rejected — no such filter surface exists in the loader; fix at the source boundary, not downstream |

## Related

- Sibling FR: FR-942 (repo instruction context diet) — same analysis session, repo-side counterpart
- Scripture: `instruction` boundary; `vendor_default_as_help`; normalize at the boundary where external data enters
