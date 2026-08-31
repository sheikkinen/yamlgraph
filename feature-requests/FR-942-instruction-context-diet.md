# Feature Request: Instruction Context Diet

**Priority:** MEDIUM
**Type:** Enhancement
**Status:** Judged — APPROVED WITH REVISIONS (R-1..R-6 folded below)
**Effort:** 1 day
**Requested:** 2026-08-31
**First consumer / first event:** every agent turn in this repo, at prompt assembly when `.github/copilot-instructions.md` + `CLAUDE.md` (56,610 bytes combined) are injected
**Research:** [FR-942-instruction-context-diet.research.md](FR-942-instruction-context-diet.research.md) — committed record with reproducible byte evidence, six solution classes, precedent dispositions, `is_this_a_graph` answer (R-1)
**Judgement:** [FR-942-instruction-context-diet.judgement.md](FR-942-instruction-context-diet.judgement.md)
**Prior art:** FR-941-home-config-cleanup.md — disjoint home-side sibling (executed 2026-08-31); FR-918 — stale-reference witness for the FR-761 walkthrough; FR-743 — conflicting/current precedent on SessionStart visibility, dispositioned in the research record; FR-889 — size-gate precedent the byte budget extends

## Summary

Deduplicate the two repo instruction files, move reference tables out of per-turn doctrine, and compress inflated Scripture entries — targeting ~6–8k tokens saved per turn with zero heuristics lost.

## Value Statement

Every agent turn in this repo gets cheaper and the doctrine gets sharper: compressed trap entries fire more reliably because the trigger condition is no longer buried in incident narrative.

## Problem

Witnessed 2026-08-31 (measured: `copilot-instructions.md` 261 lines / 34.6 KB; `CLAUDE.md` 515 lines / 22 KB):

1. **Verbatim duplication.** The "Submitting Proposals" section appears in full in both files. Conventions, commit format, FR discipline, and TDD rules appear in both with divergent phrasing — a drift risk, not just token cost.
2. **Reference material riding in doctrine.** `CLAUDE.md` carries a ~25-row environment-variable table, a branch-protection table, a 9-item CI-check list, and the FR-761 constraints walkthrough (which self-describes as stale post-FR-918). None steer per-turn behavior; all belong in `reference/` with pointers.
3. **Scripture entry inflation.** Knowledge Graph trap/cure entries have grown from one-liners to 100–200-word narratives with inline incident citations (`threshold_encodes_forecast`, `junk_drawer_cap`, `read_raw_output_first`, `two_strike_split`, `one_session_one_repo`). The Scripture's own claim "216 lines produce 21k lines of Python" is now 261 lines with falling density.

## Ideal Result

Every agent turn is assembled from exactly two thin, non-overlapping instruction files totalling **at most 33,966 bytes** (frozen baseline 56,610):

- `.github/copilot-instructions.md` — the sole doctrine surface: Scripture, Knowledge Graph (governed entries each ≤40 words, provenance externalized), process contracts, proposal submission.
- `CLAUDE.md` — retained thin surface: development commands, anti-pattern table, and direct pointers to relocated reference material. Never deleted by this FR.
- `reference/development-operations.md` — the committed destination for operational reference (not injected per turn).
- `docs/scripture-provenance.md` — verbatim incident narratives and citations removed from governed entries, keyed `<collection>.<key>`.
- `scripts/size_gate.py` — enforces the 33,966-byte combined ceiling forever, alongside its existing line gate.

### Source-to-destination map (R-2, frozen)

| Source (CLAUDE.md section) | Destination |
|---|---|
| Key Environment Variables table | `reference/development-operations.md#key-environment-variables` |
| Branch Protection (rules table, merge queue note) | `reference/development-operations.md#branch-protection` |
| CI checks list | `reference/development-operations.md#ci-checks` |
| Reproducible Dependency Governance + Direct-Import Scan (FR-761) | `reference/development-operations.md#dependency-governance-fr-761` |
| Submitting Proposals (duplicate) | deleted — canonical copy stays in `.github/copilot-instructions.md` only |

`CLAUDE.md` retains a direct link to each relocated section.

## Proposed Solution

1. **Dedupe:** zero duplicated sections between the two files. `CLAUDE.md` becomes thin — dev commands, anti-pattern table, pointers. Doctrine lives solely in `copilot-instructions.md`.
2. **Relocate:** env-var table, branch-protection table, CI-check list, FR-761 walkthrough → `reference/` (or compress to pointers where reference docs already exist).
3. **Compress Scripture (R-3, frozen):** governed collections are exactly `traps`, `cures`, `questions`, and `process`. Each governed scalar is capped at **40 whitespace-delimited words** (counted by `len(value.split())`). Boundaries, generative methods, seeds, the Ten Commandments, and the Sermon are **not authorized** for compression. Collection/key sets must remain exactly equal before/after. For each changed key, `docs/scripture-provenance.md` carries the removed incident narrative and every removed citation **verbatim**, keyed `<collection>.<key>` (FR-XXX, NC-XXX, dates, commands, named incidents included — token-grep on FR-XXX alone is insufficient). **No heuristic deleted, only compressed.** Semantic preservation is a **human gate** (C-4): the reviewer confirms side-by-side that every compressed trap/cure/process entry retains its trigger and prescribed response, and every question retains its `MOMENT:` firing condition.
4. **Session-start autocompaction — evaluation only:** disposition the option of automatic instruction compaction at session start. Questions to answer: (a) does the Copilot hook surface allow substituting/augmenting instructions at session start, or is compaction only achievable by editing committed files? (b) if committed-file-only, is a CI byte-budget gate on the two instruction files (analogous to the 400-line module rule) the cheaper standing cure against re-bloat? Deliverable: implement/reject recommendation recorded in this FR; implementation, if accepted, is a follow-up FR.

### §4 Disposition (2026-08-31): session-start autocompaction REJECTED

Evaluated empirically in session `909b2af4` (the evaluating agent's own session):

- **(a) Hook surface cannot substitute — and cannot even augment.** `SessionStart` fires (probe witness: `audit.jsonl` 2026-08-31T17:32:21Z, this session; 332 firings on record) and the FR-743 briefing hook ran, producing 5 lines when executed directly (`now.py --brief`, rc=0) — yet **none of it reached the agent context**. SessionStart stdout is agent-invisible on the current platform build (the negative AC-00 verdict FR-743 anticipated). Independent of visibility, hooks are additive-only: the platform assembles `copilot-instructions.md` + `CLAUDE.md` into the prompt from committed files with no hook interposition point. Runtime autocompaction cannot subtract a single token; at best it would add.
- **(b) Committed-file compaction is the sole subtraction mechanism** (§1–3 of this FR), and the standing re-bloat guard is a **byte-budget gate**: extend the existing pre-commit file-size gate (currently >400 warn / >450 error, Python-scoped) with a byte budget for the two instruction files. Cheap, mechanical, at the merge boundary — accepted into this FR's enforcement scope as the §4 deliverable replacing autocompaction.
- **Side finding (FR-743's business, recorded here as witness):** the SessionStart briefing hook is currently dead weight — it runs, emits, and is seen by no one. FR-743's own judged fallback (first-PreToolUse delivery) is the recorded cure; its AC-00 verdict can now be marked negative with this witness.

**Acceptance criterion update:** "Autocompaction option dispositioned" → satisfied (rejected, this section); replaced by: instruction-file byte-budget gate added to pre-commit within this FR's enforcement.

## Acceptance Criteria (revised per judgement — AC-01..AC-14 adopted verbatim)

- [ ] AC-01: `**Research:**` links to a committed substantive record (R-1): reproducible injection + byte evidence, solution classes, precedent dispositions, disagreement, `is_this_a_graph`
- [ ] AC-02: `## Ideal Result` precedes `## Proposed Solution`; CLAUDE.md frozen as retained/thin; exact R-2 source-to-destination map present
- [ ] AC-03: `Submitting Proposals` exists only in `.github/copilot-instructions.md`; committed normalization test finds no identical normalized three-sentence run across the two files
- [ ] AC-04: the four relocated blocks are absent from `CLAUDE.md`; every replacement pointer resolves to the exact committed destination
- [ ] AC-05: `traps`/`cures`/`questions`/`process` collection/key sets unchanged; no other collection or Scripture section compressed
- [ ] AC-06: every governed scalar ≤40 whitespace-delimited words; every question retains `MOMENT:`; human review record confirms trigger + prescribed response retained per entry
- [ ] AC-07: `docs/scripture-provenance.md` has exactly one keyed record per changed governed entry, preserving removed narrative and citations verbatim; preservation test passes
- [ ] AC-08: `wc -c .github/copilot-instructions.md CLAUDE.md` combined ≤ 33,966 bytes (baseline 56,610)
- [ ] AC-09: `scripts/size_gate.py` rejects combined instruction size >33,966 bytes and missing/empty governed files, preserving the line gate; `.pre-commit-config.yaml` triggers on either instruction Markdown path
- [ ] AC-10: RED and GREEN commits recorded for byte-budget tests; tests cover exact boundary, overage diagnostic naming both files + total, missing/empty files, existing line behavior
- [ ] AC-11: CAP-255 + `ARCHITECTURE.md` REQ-YG-631 describe the instruction-byte ceiling; `python scripts/req_coverage.py --strict` passes
- [ ] AC-12: `pytest .github/hooks/tests/test_size_gate.py -q --no-cov`, `python scripts/size_gate.py`, and `pre-commit run file-size-gate --files CLAUDE.md .github/copilot-instructions.md scripts/size_gate.py .github/hooks/tests/test_size_gate.py` pass; outputs recorded in this FR
- [ ] AC-13: a human explicitly reviews and approves the Scripture, pre-commit, size-gate, capability/requirement, and test diffs before landing (C-4 GATE)
- [ ] AC-14: implementation status records decisions and deviations; one changelog fragment and one diary reflection with `Seed:` included
- [x] Autocompaction dispositioned (rejected — §4 Disposition; witness committed in the research record)

## Alternatives Considered

| Alternative | Disposition |
|---|---|
| Leave as-is; correctness over cost | Rejected — duplication is a drift/contradiction risk independent of token cost; two phrasings of one rule eventually disagree |
| Delete CLAUDE.md entirely (single instruction file) | Rejected by judgement R-2 — still-recognized platform instruction entry point; deletion requires a separate, human-evidenced amendment |
| Compress via LLM summarization pass | Rejected for Scripture — heuristics are load-bearing constraint text (`constraint_over_code`); compression must be reviewed line-by-line, not generated |
| Session-start autocompaction as primary cure | Demoted to evaluation task — normalize at the boundary (the committed files) first; runtime compaction treats the symptom |
| CI byte-budget gate only, no cleanup | Rejected as sole action — gates shape, not substance (`gate_checks_shape_not_substance`); but evaluated as the standing re-bloat guard in §4 |

## Related

- Sibling FR: FR-941 (user-home cleanup) — same analysis session, $HOME-side counterpart
- Scripture: `constraint_over_code`; `growth_as_default` (subtraction is the mature default); FR-918 (FR-761 staleness witness)
