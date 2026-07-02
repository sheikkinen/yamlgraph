# FR-651: Deepen prompt enforces temporal fields

**Priority:** MEDIUM
**Type:** Bug
**Status:** Enforced
**Effort:** 0.25 days
**Requested:** 2026-07-02

## Summary

The deepen prompt does not instruct the LLM to populate `birth_year` (characters) or `year` (events). After 3 worldgen loops, only the 3 seed characters have birth_year and only 1 of 3 events has year.

## Value Statement

anchor_events computes age arithmetic and event timelines from these fields — without them, deepened characters get no temporal context in subsequent loops, and the world has no coherent timeline.

## Problem

Evidence from the last pipeline run:
- 5/8 characters missing `birth_year` (all LLM-generated)
- 2/3 events missing `year` (the_ashfall, the_reforging)
- Premise establishes "Year 0 = the Ashfall, current ~200" but LLM ignores it

The deepen prompt (`prompts/deepen_entity.yaml`) has type-specific sections for character, event, faction, location — but none mention temporal fields.

## Proposed Solution

Add explicit instructions to the deepen prompt:

**Character section** — add after "Add relationships to other entities":
```
- Set birth_year (integer). Year 0 = the Ashfall. Use the calendar_note and existing birth_years for consistency.
```

**Event section** — add after "Chain of cause and effect to other events":
```
- Set year (integer). Year 0 = the Ashfall. Negative = before Ashfall.
- Set scope: world | regional | local
```

Also inject `calendar_note` from premise into the user template so the LLM has the temporal reference.

## Acceptance Criteria

- [ ] Deepen prompt instructs LLM to populate `birth_year` for characters
- [ ] Deepen prompt instructs LLM to populate `year` and `scope` for events
- [ ] `calendar_note` from premise available in deepen prompt context
- [ ] Pipeline run produces characters with `birth_year` populated
- [ ] Pipeline run produces events with `year` populated

## Related

- FR-647: Event propagation (added birth_year/year/scope to schema)
- [prompts/deepen_entity.yaml](../examples/novel_fandom/prompts/deepen_entity.yaml)

## Judgement

**Verdict: Granted with amendments.**

### What's sound
- Clear problem with evidence. Prompt gap, not code gap. Minimal change.
- `calendar_note` is already extracted by `reload_canon` from premise but not threaded to state — needs a state key addition.

### Amendments

1. **`calendar_note` is not in worldgen state.** `reload_canon` extracts `synopsis_text` but not `calendar_note`. Either: (a) add `calendar_note` extraction to `reload_canon` and a state_key in worldgen.yaml, or (b) embed the calendar reference directly in the premise `synopsis_text` that already flows to the prompt. Option (b) is simpler — just add a line to the deepen prompt: "Calendar: Year 0 = the Ashfall. Current story ~year 200." hardcoded until calendar_note flows through state.
2. **Drop acceptance criterion "Pipeline run produces..."** — prompt changes are probabilistic. The test should verify the prompt text contains the instruction, not that the LLM obeys it.
3. **Add `affected_locations` instruction to event section** — this field is also empty on all events.

### Scope freeze
One file: `prompts/deepen_entity.yaml`. No code changes.
