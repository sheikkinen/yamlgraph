# Feature Request: Graduate `impossibly_large_sequential_task` trap + `map_reduce_the_corpus` cure into Scripture

**Priority:** MEDIUM
**Type:** Feature
**Status:** JUDGED
**Effort:** 0.25 days
**Requested:** 2026-09-02
**First consumer / first event:** any future agent (or the operator) working a session where an evaluation task looks "too big for serial review" — the Scripture entry fires per generation and the census cost estimate becomes the required first move instead of an optional detour.
**Research:** in-body dispositioned research record (§ Recurrence and precedent) — three-recurrence tally required by the `graduation` process rule.
**Prior art:**
- [FR-892-corpus-census-pipeline-injected-adapters.md](FR-892-corpus-census-pipeline-injected-adapters.md) — base map-reduce pipeline (the machinery this cure names).
- [FR-899-org-repo-census-azure.md](FR-899-org-repo-census-azure.md) — org repo census (map-reduce precedent #2).
- [FR-962-person-profile-census-authored-prs.md](FR-962-person-profile-census-authored-prs.md) — authored-PR census (map-reduce precedent #3, filed in the same session as this graduation).
- [reference/patterns/corpus-map-reduce.md](../reference/patterns/corpus-map-reduce.md) — the pattern reference the cure points at.
- `first_person_tool_horizon` in operator memory — the agent-side trap that fires when the tool doesn't turn on itself.

## Summary

Add one trap (`impossibly_large_sequential_task`) and one cure (`map_reduce_the_corpus`) to the Knowledge Graph in `.github/copilot-instructions.md`. The pair names a specific class of framing — *"should we review N items? / would take weeks / audit / boil-the-ocean"* about a finite enumerable corpus — and the mechanical response — *cost the census first*.

## Value Statement

Prevents a specific recurring class of cheaper-move: agent frames a bounded corpus as too big to review, offers a smaller alternative, never reaches for the census pipeline that already sits in the reference doctrine. Value is per-generation, not per-session — the rule fires whenever the alarm words appear.

## Problem

The `first_person_tool_horizon` trap (in `operator-calibration.md`) records that agents don't spontaneously turn yamlgraph on their own work. It fired again on 2026-09-02 inside the FR-962 session — the same session that shipped a corpus census demo. Operator prompt sequence:

1. Agent proposes small diff-time gate for test-watering detection.
2. Operator: *"map-reduce would review (with mercury) the 6000+ tests in no time…"*
3. Agent: *"You're right, I forgot I built the tool."*
4. Operator: *"'would take weeks' = you haven't checked map-reduce pattern - sounds like scripture."*

Three explicit corrections in one session on a single trap-shape. The generalisation transcends the specific agent instance — it is repo-wide operational doctrine that any agent working the yamlgraph codebase should observe.

## Ideal Result

`.github/copilot-instructions.md` contains, in the `traps:` block:

```yaml
impossibly_large_sequential_task: "'Should we review N items?' / 'would take weeks' / 'audit' / 'boil-the-ocean' about a finite enumerable corpus → the framing IS the corpus-map-reduce signal; the census is affordable when serial isn't (FR-402, FR-748, FR-851, FR-884, FR-892, FR-899, FR-962)"
```

and in the `cures:` block:

```yaml
map_reduce_the_corpus: "For any finite enumerable corpus where sequential review is prohibitive, cost the yamlgraph census FIRST — N × per-item tokens × cheap-map pricing — BEFORE offering smaller alternatives. Discover, extract, map, reduce, synth. reference/patterns/corpus-map-reduce.md is the contract; smaller gates may complement but not replace the estimate"
```

## Proposed Solution

Two-line edit to `.github/copilot-instructions.md`:

- Trap insertion inside the `traps:` block, adjacent to `growth_as_default` (shared "assumption that closes the door" mechanism).
- Cure insertion inside the `cures:` block, adjacent to `read_raw_output_first` (shared "operational law about a corpus of records" mechanism).

No new code, no new tests, no framework changes. This is a documentation-doctrine change with per-generation runtime effect through Scripture context loading.

## Acceptance Criteria

- [ ] AC-01: `impossibly_large_sequential_task` appears in `traps:` block of `.github/copilot-instructions.md`, cites the six census precedents (FR-402, FR-748, FR-851, FR-884, FR-892, FR-899, FR-962) verbatim.
- [ ] AC-02: `map_reduce_the_corpus` appears in `cures:` block, cites `reference/patterns/corpus-map-reduce.md` as the contract, names the four alarm words (would-take-weeks / audit / boil-the-ocean / should-we-review-N).
- [ ] AC-03: Insertion positions chosen so `git blame` for the two lines returns FR-965 as the sole author, no adjacent line touched beyond context lines.
- [ ] AC-04: Diary entry `docs/diary/diary-2026-09-02-the-cheaper-move.md` (already committed via FR-962) is cited in the FR body as the third-recurrence witness.
- [ ] AC-05: Judged via `scripts/judge.sh` before enforcement.

## Alternatives Considered

- **Do nothing** — rely on `first_person_tool_horizon` in operator memory. Rejected: operator memory is per-session-load per-agent; Scripture is repo-wide and applies to every agent working this codebase.
- **Add only the trap** without a cure — rejected: traps without cures leave the fix ambiguous. The pair is what fires.
- **File a separate FR for the FR-915 test-watering hole** — orthogonal; that FR (candidate FR-963) is about a specific enforcement infrastructure fix. This FR is about the general operational law.
- **Add a mechanical detection gate in code** (grep alarm-words in the agent's response before send) — rejected: Scripture is the mechanism yamlgraph already uses for this class of per-generation rule. Adding code detection would double-encode.

## Recurrence and precedent (three-recurrence tally for graduation eligibility)

1. `first_person_tool_horizon` recorded in `operator-calibration.md` (2026-08-22): *"agent treats yamlgraph as codebase-under-maintenance, never as its own instrument… parallel haiku analysis is table stakes."*
2. FR-962 session (2026-09-02, morning): operator asked *"should we review all 6000+ tests?"*, agent answered *"boil-the-ocean"* + proposed a small diff-time gate. Operator: *"map-reduce would review (with mercury) the 6000+ tests in no time…"*
3. FR-962 session (2026-09-02, later same session): after agent recorded the correction in memory as an agent-specific detection rule, operator: *"'would take weeks' = you haven't checked map-reduce pattern - sounds like scripture."*

Three occurrences of the same trap-shape with escalating operator specificity — the last one explicitly asking for Scripture graduation. Meets the `graduation` process rule: heuristic appears twice → FR; confirmed recurrence → Scripture.

## Related

- Diary: [diary-2026-09-02-the-cheaper-move.md](../docs/diary/diary-2026-09-02-the-cheaper-move.md) — the addendum names the exact correction sequence.
- Precedents (all corpus-map-reduce runs the trap-cure references): FR-402, FR-748, FR-851, FR-884, FR-892, FR-899, FR-962.

## Implementation Status

- 2026-09-02: Filed. To route through `scripts/judge.sh` after PR ready.

## Judgement

Just change the copilot_instructions.md Knowledge Graph to include the `impossibly_large_sequential_task` trap and the `map_reduce_the_corpus` cure as specified.

**Judgement:** ACCEPTED — the FR meets the graduation criteria with three recurrences and explicit operator instruction for Scripture update.
