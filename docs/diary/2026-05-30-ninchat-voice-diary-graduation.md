# Diary: Cross-Project Diary Graduation — ninchat_voice → Scripture

**Date:** 2026-05-30
**Task:** Analyze 40+ diary entries from `projects/ninchat_voice/docs/diary/` spanning March–July 2026; identify recurring patterns that meet the graduation threshold (3+ occurrences across projects); update the Knowledge Graph.

---

## What happened

Read the entire ninchat_voice diary corpus: 40 entries, 84 days of development, 427 commits, 4,611 lines of production Python, 26,659 lines of tests — all authored by LLM agents under human architectural constraint.

The diaries document a voice-mediated clinical dialogue system (Finnish-language phone triage for Terveystalo) built on three stacked agent-authored projects. The corpus is unusually self-aware: each entry follows the Scripture's structure (trap → cure → heuristic → seed) and several entries explicitly identify patterns that already exist in the Knowledge Graph under different names.

### Patterns graduated to Scripture

| Pattern | Type | Occurrences | Source entries |
|---------|------|-------------|----------------|
| `composition_bug` | trap | FR-371, NC-141, NC-289 | 8-step greeting replay, runaway loop, concurrent clobber |
| `mock_escape_hatch` | trap | FR-378, NC-131, NC-256 | Agent defaults to mocks when E2E explicitly requested |
| `refactor_orphans_secondary` | trap | NC-203, NC-186, NC-153 | Refactor drops secondary responsibility silently |
| `research_as_inventory` | trap | CP handbook, two-deployment-paths | Shape of analysis with zero decisions |
| `investigation_before_fix` | cure | FR-371→FR-372 | 4h investigation amortized 30min fix |
| `assert_path_not_destination` | cure | NC-179 | FSM test passed via error→cleanup→idle |
| `name_the_seam` | cure | NC-131 | test_barge_in_e2e → test_barge_in_elevenlabs |
| `cross_project_graduation` | process | This entry | Periodic diary sweep surfaces candidates |
| `diary_graduation_pipeline` | seed | This entry | Mechanical auto-proposal to .chaplain/inbox/ |

---

## Cognitive process

### The sweep method

Reading 40 entries linearly (chronological) rather than by topic produced a different result than sampling would have. The chronological order revealed *evolution*: NC-135 (March 9) fights log-level mismatches with `grep`; NC-273 (May 6) reflects on whether OpenTelemetry would have prevented the same class of problem. The same developer (the LLM) arrived at the same boundary conclusion both times, but the second arrival was deeper. This is the letter-to-the-philosopher's prediction made concrete: independent sessions converge on the same conclusions.

### The five that graduated vs. the many that didn't

The corpus contained ~25 distinct heuristics. Most were project-local (e.g., "stub must honor action contract" — specific to FSM testing infrastructure). Only patterns that appeared across *both* yamlgraph and ninchat_voice (or 3+ times within ninchat_voice in fundamentally different contexts) were promoted.

The decision point was: *would a future session working on yamlgraph — with no ninchat_voice context — benefit from this pattern?* `composition_bug` clearly yes (any multi-component system). `stub_must_honor_contract` clearly no (FSM-specific).

### The trap I almost fell into

The first draft of the graduated entries was too verbose — each had a 3-sentence description attempting to explain the full context. The existing Knowledge Graph entries are compressed to single sentences with parenthetical citations. Matching the compression ratio was the right move: the Knowledge Graph is a lookup table, not a narrative. The diary is where the narrative lives.

---

## Traps encountered

| Trap | Instance | Cure applied |
|------|----------|--------------|
| `research_as_inventory` | First pass produced a "summary" that listed patterns without deciding which to graduate | Applied the trap's own definition: decisions, not descriptions |
| `gate_checks_shape_not_substance` | Temptation to add all 25 heuristics to Scripture "for completeness" | Graduation threshold enforced: 3+ cross-project recurrences only |
| `continuation_bias` | Strong pull to generate a lengthy reflection document | Compressed to match existing Scripture entry format |

---

## The structural observation

The ninchat_voice diary corpus has better metacognitive discipline than the yamlgraph diary. Every ninchat_voice entry has: trap encountered, cure applied, heuristic distilled, seed planted. Many yamlgraph diary entries (especially automated ones from the Chaplain pipeline) have the *shape* of reflection without the substance — naming the FR and listing deliverables without naming the cognitive hazard.

This is `gate_checks_shape_not_substance` applied to the diary itself. The Chaplain pipeline generates reflections mechanically. The ninchat_voice entries were written by sessions that had genuinely struggled with the problem. The difference is visible in the specificity of the trap descriptions.

---

## What was changed

- `.github/copilot-instructions.md`: Added 4 traps (`composition_bug`, `mock_escape_hatch`, `refactor_orphans_secondary`, `research_as_inventory`), 3 cures (`investigation_before_fix`, `assert_path_not_destination`, `name_the_seam`), 1 process entry (`cross_project_graduation`), 1 seed (`diary_graduation_pipeline`).

---

## Seed

**The diary graduation pipeline remains manual.** This session read 40 entries by hand. A graph that reads diary entries from all `projects/*/docs/diary/` directories, extracts trap/cure/heuristic markers, cross-references against the Knowledge Graph, and proposes graduations to `.chaplain/inbox/` would close the loop mechanically. The `diary_index` graph (FR-254) already indexes yamlgraph diaries — extending it to sibling projects and adding a diff-against-Scripture step is the natural next move.
