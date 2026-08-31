# Feature Request: Instruction Context Diet

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Proposed
**Effort:** 1 day
**Requested:** 2026-08-31
**First consumer / first event:** every agent turn in this repo, at prompt assembly when `.github/copilot-instructions.md` + `CLAUDE.md` (~15k tokens, 57.5 KB) are injected
**Research:** In-body dispositioned alternatives table (below) — session context analysis 2026-08-31
**Prior art:** FR-941-home-config-cleanup.md — deliberate sibling from the same analysis, not overlap: FR-941 cures the `$HOME`-side injection (global agents, `~/.claude/CLAUDE.md`), this FR cures the repo-side files; disjoint targets, no shared enforcement surface

## Summary

Deduplicate the two repo instruction files, move reference tables out of per-turn doctrine, and compress inflated Scripture entries — targeting ~6–8k tokens saved per turn with zero heuristics lost.

## Value Statement

Every agent turn in this repo gets cheaper and the doctrine gets sharper: compressed trap entries fire more reliably because the trigger condition is no longer buried in incident narrative.

## Problem

Witnessed 2026-08-31 (measured: `copilot-instructions.md` 261 lines / 34.6 KB; `CLAUDE.md` 515 lines / 22 KB):

1. **Verbatim duplication.** The "Submitting Proposals" section appears in full in both files. Conventions, commit format, FR discipline, and TDD rules appear in both with divergent phrasing — a drift risk, not just token cost.
2. **Reference material riding in doctrine.** `CLAUDE.md` carries a ~25-row environment-variable table, a branch-protection table, a 9-item CI-check list, and the FR-761 constraints walkthrough (which self-describes as stale post-FR-918). None steer per-turn behavior; all belong in `reference/` with pointers.
3. **Scripture entry inflation.** Knowledge Graph trap/cure entries have grown from one-liners to 100–200-word narratives with inline incident citations (`threshold_encodes_forecast`, `junk_drawer_cap`, `read_raw_output_first`, `two_strike_split`, `one_session_one_repo`). The Scripture's own claim "216 lines produce 21k lines of Python" is now 261 lines with falling density.

## Proposed Solution

1. **Dedupe:** zero duplicated sections between the two files. `CLAUDE.md` becomes thin — dev commands, anti-pattern table, pointers. Doctrine lives solely in `copilot-instructions.md`.
2. **Relocate:** env-var table, branch-protection table, CI-check list, FR-761 walkthrough → `reference/` (or compress to pointers where reference docs already exist).
3. **Compress Scripture:** cap trap/cure/question entries at ~40 words — trigger condition + heuristic inline; incident citations move to `docs/scripture-provenance.md` keyed by entry name. **No heuristic deleted, only compressed**; the Judge verifies each compressed entry still names its firing moment.
4. **Session-start autocompaction — evaluation only:** disposition the option of automatic instruction compaction at session start. Questions to answer: (a) does the Copilot hook surface allow substituting/augmenting instructions at session start, or is compaction only achievable by editing committed files? (b) if committed-file-only, is a CI byte-budget gate on the two instruction files (analogous to the 400-line module rule) the cheaper standing cure against re-bloat? Deliverable: implement/reject recommendation recorded in this FR; implementation, if accepted, is a follow-up FR.

### §4 Disposition (2026-08-31): session-start autocompaction REJECTED

Evaluated empirically in session `909b2af4` (the evaluating agent's own session):

- **(a) Hook surface cannot substitute — and cannot even augment.** `SessionStart` fires (probe witness: `audit.jsonl` 2026-08-31T17:32:21Z, this session; 332 firings on record) and the FR-743 briefing hook ran, producing 5 lines when executed directly (`now.py --brief`, rc=0) — yet **none of it reached the agent context**. SessionStart stdout is agent-invisible on the current platform build (the negative AC-00 verdict FR-743 anticipated). Independent of visibility, hooks are additive-only: the platform assembles `copilot-instructions.md` + `CLAUDE.md` into the prompt from committed files with no hook interposition point. Runtime autocompaction cannot subtract a single token; at best it would add.
- **(b) Committed-file compaction is the sole subtraction mechanism** (§1–3 of this FR), and the standing re-bloat guard is a **byte-budget gate**: extend the existing pre-commit file-size gate (currently >400 warn / >450 error, Python-scoped) with a byte budget for the two instruction files. Cheap, mechanical, at the merge boundary — accepted into this FR's enforcement scope as the §4 deliverable replacing autocompaction.
- **Side finding (FR-743's business, recorded here as witness):** the SessionStart briefing hook is currently dead weight — it runs, emits, and is seen by no one. FR-743's own judged fallback (first-PreToolUse delivery) is the recorded cure; its AC-00 verdict can now be marked negative with this witness.

**Acceptance criterion update:** "Autocompaction option dispositioned" → satisfied (rejected, this section); replaced by: instruction-file byte-budget gate added to pre-commit within this FR's enforcement.

## Acceptance Criteria

- [ ] No section appears in both `copilot-instructions.md` and `CLAUDE.md` (verify: no shared heading with >2 identical consecutive sentences)
- [ ] Env-var table, branch-protection table, CI-check list, FR-761 walkthrough absent from `CLAUDE.md`; content reachable via `reference/` pointer
- [ ] Every Scripture trap/cure/question entry ≤ ~40 words; provenance preserved in `docs/scripture-provenance.md` with all FR/incident citations intact (verify: every FR-XXX cited before compression appears in the provenance file)
- [ ] Combined byte count of the two instruction files reduced ≥ 40% (baseline 57.5 KB)
- [x] Autocompaction option dispositioned in this FR (rejected — see §4 Disposition; hook surface is additive-only and SessionStart stdout is agent-invisible)
- [ ] Instruction-file byte-budget gate added to pre-commit (replaces autocompaction as the standing re-bloat guard)
- [ ] Existing hooks/gates that grep these files (pre-commit forbidden-phrase checks, fr-checks) still pass

## Alternatives Considered

| Alternative | Disposition |
|---|---|
| Leave as-is; correctness over cost | Rejected — duplication is a drift/contradiction risk independent of token cost; two phrasings of one rule eventually disagree |
| Delete CLAUDE.md entirely (single instruction file) | Deferred to Judge — viable if Claude Code sessions are no longer used in this repo; the FR author lacks that fact |
| Compress via LLM summarization pass | Rejected for Scripture — heuristics are load-bearing constraint text (`constraint_over_code`); compression must be reviewed line-by-line, not generated |
| Session-start autocompaction as primary cure | Demoted to evaluation task — normalize at the boundary (the committed files) first; runtime compaction treats the symptom |
| CI byte-budget gate only, no cleanup | Rejected as sole action — gates shape, not substance (`gate_checks_shape_not_substance`); but evaluated as the standing re-bloat guard in §4 |

## Related

- Sibling FR: FR-941 (user-home cleanup) — same analysis session, $HOME-side counterpart
- Scripture: `constraint_over_code`; `growth_as_default` (subtraction is the mature default); FR-918 (FR-761 staleness witness)
