# Feature Request: FR-657 — Agentic Event Deepening with Canon Tools

**Priority:** HIGH
**Type:** Enhancement
**Status:** Enforced
**Effort:** 0.5 days
**Requested:** 2026-07-02
**Judged:** 2026-07-02
**Enforced:** 2026-07-02

## Summary

Convert the worldgen event-deepening step from blind LLM generation to an
agent with canon lookup and validation tools. The deepen prompt currently
passes only an ID index of the canon (`- hilde (character)`), so the LLM
generates backstories without seeing other entities' content. This caused
name collisions (3 different names for Hilde's father), impossible birth
years (positive instead of negative), and conflated events in the FR-656
worldgen run.

## Problem

The `deepen` map node calls the LLM once per thin entity with:
- Synopsis text (~300 tokens)
- Target entity YAML
- Canon as ID+type list only (no content)
- Event context for characters

The LLM cannot cross-reference existing pages. Evidence from worldgen run
(LangSmith trace `019f22d4`):

1. **Name collisions**: Gunnar's backstory invents "Ottokar" for Hilde's
   father. Ulf's page was in the canon but the LLM only saw `- ulf (character)`.
2. **Calendar errors**: 4 characters got positive birth_years (148, 125, 125, 125).
   The deepen prompt said "Year 0 = the Ashfall" but the LLM had no reference
   birth_years to compare against.
3. **Conflated events**: `the_slaughter_at_ash_ridge` merged two fathers' deaths
   because the LLM couldn't read either character's page.
4. **Duplicate locations**: `salt_road` and `the_salt_road` created because
   `collect_red_links` saw two prose mentions without normalization.

Root cause: the deepen prompt is cheap (~1,200 input tokens) but blind.

## Approach

Replace context dump with tool boundaries. Each tool call is an enforcement
checkpoint where constraints are injected and compliance can be validated.

### Phase 1: Event-only agent (this FR)

Events are the ideal test scope:
- Smallest entity count (12 events)
- Most constrained schema (`year`, `participants`, `affected_locations`, `scope`)
- Where the worst errors were (ashfall year, slaughter conflation)
- Pydantic model `Event` already exists in `schema/canon.py`

**Graph change — split deepen by entity type:**

```yaml
nodes:
  split:
    type: python
    tool: split_thin_by_type

  deepen_events:
    type: agent
    prompt: deepen_event_agent
    tools:
      - lookup_canon_page
      - list_canon_ids
      - validate_draft
    max_tool_calls: 8

  deepen_other:
    type: map
    over: "{state.thin_other}"
    node:
      type: llm
      prompt: deepen_entity
```

**Three tools:**

1. `lookup_canon_page(id)` — Returns full YAML for an entity. Injects
   contextual constraints in the response: "Year 0 = flood. Negative = before
   flood. Existing birth_years: hilde=-24, gunnar=-26, ..." The tool response
   is the boundary where external data enters — normalize here.

2. `list_canon_ids()` — Returns all IDs with types. Agent calls this first
   to understand what exists. Prevents duplicate entity creation.

3. `validate_draft(page_yaml)` — Mechanical validation of in-progress page.
   Checks: year sign, participant IDs exist, affected_location IDs exist,
   scope is valid enum, no the_X/X duplicate IDs. Returns pass/fail with
   specific error messages. Agent can self-correct before returning.

### Future phases (separate FRs)

- Phase 2: All entity types through agent
- Phase 3: CRUD tools replace structured output
- Phase 4: Graph collapse (9 nodes → 4)

See `docs/plan-worldgen-context.md` for full analysis.

## Acceptance Criteria

1. **AC-1**: `nodes/canon_tools.py` implements `lookup_canon_page(id, canon_dir)`,
   `list_canon_ids(canon_dir)`, `validate_draft(page_yaml, canon_dir)` as
   YAMLGraph Python tools.
2. **AC-2**: `nodes/split_thin_by_type.py` partitions `state.thin_entities`
   into `state.thin_events` and `state.thin_other`, returned as dict update.
3. **AC-3**: `prompts/deepen_event_agent.yaml` instructs the agent to call
   `list_canon_ids` first, then `lookup_canon_page` for each participant,
   then generate, then `validate_draft` before returning.
4. **AC-4**: `worldgen.yaml` registers new tools, adds `split` node, adds
   `deepen_events` (agent, `timeout: 120`) and `deepen_other` (existing llm
   map) nodes with correct routing edges.
5. **AC-5**: `lookup_canon_page` response includes the entity's full YAML
   plus a 2-line calendar convention header. No aggregated data from other
   entities.
6. **AC-6**: `validate_draft` returns `{"valid": bool, "errors": list[str]}`
   and rejects: positive years for events, participant IDs not in canon,
   `the_X`/`X` duplicate IDs.

## Judgement

**Verdict: GRANTED WITH AMENDMENTS (2026-07-02)**

The FR correctly diagnoses the root cause (blind LLM, no cross-reference)
and prescribes the right cure (tool boundaries over context dumps). Evidence
from LangSmith trace is concrete. Phased approach (events first) is minimal.

**Amendments applied:**
1. AC-2 clarified: `split_thin_by_type` is a Python tool that returns two
   state keys, not a routing node. Graph edges handle routing.
2. AC-4: agent sub-node must include `timeout: 120` (linter W203 requirement).
3. AC-5 narrowed: no aggregated data from other entities in lookup response.
   Injecting all birth_years is context-dump thinking sneaking through the
   tool boundary. The agent calls `lookup_canon_page` per participant instead.
4. AC-6 amended: `validate_draft` must return `{"valid": bool, "errors": list[str]}`
   contract so the agent can mechanically decide self-correction.
5. Prerequisite: `anchor_events.py` dict-reference fix must be committed
   before enforcement begins.

**Scope freeze:**
- Events only. Characters, locations, factions unchanged (existing llm path).
- Three tools. No CRUD tools (Phase 3 in separate FR).
- DeepSeek provider. Anthropic fallback acceptable but not required for AC.
- No changes to `schema/canon.py`.
- Existing 4477+ tests must pass.

## Verification (enforcement)

- Clean canon (Phase 0 defects fixed manually first).
- Run worldgen. Events deepened by agent, characters by existing llm path.
- No event has a positive `year` value.
- All event `participants` reference existing character IDs.
- No duplicate locations created.
- LangSmith trace shows agent called `lookup_canon_page` before generating
  event content (audit trail).
- Existing tests pass (4477+).

## Constraints

- Events only. Characters, locations, factions unchanged (existing llm path).
- DeepSeek as provider (must work with DeepSeek function calling).
- No changes to `schema/canon.py` — the Pydantic models are stable.
- The `anchor_events.py` fix for unhashable dict references (committed in
  this session) is a prerequisite.

## Risks

- DeepSeek tool calling may be unreliable for multi-step lookups. Mitigation:
  tools are simple (lookup by ID, validate schema), not complex reasoning.
  If DeepSeek fails, fall back to Anthropic for the agent node only.
- Wall time increase: ~25s → ~60s per event. Acceptable for 12 events.
- Agent may not call lookup tools unprompted. Mitigation: prompt explicitly
  instructs "Before generating, call lookup_canon_page for each participant."

## Related

- [FR-655](FR-655-genesis-graph.md) — Genesis pipeline
- [FR-656](FR-656-tighten-genesis-prompt.md) — Prompt tightening (same session)
- [plan-worldgen-context.md](../docs/plan-worldgen-context.md) — Full analysis
- LangSmith trace `019f22d4` — Failed worldgen run evidence
