# Plan: Worldgen Context Strategy

**Problem**: Deepen prompt passes canon as ID-only index (`- hilde (character)`). The LLM generates backstories without seeing other entities' content, causing name collisions, calendar errors, and orphaned references.

**Discovered**: FR-656 session. LangSmith trace `019f22d4` confirms ~4K tokens/deepen call, ~103K total for 3 loops. Canon is 43 files, ~13K tokens as full YAML.

**Decision**: Option B (agent with tools) + Option D (validation gate). Option A rejected — context dump is omnipotent-LLM thinking; tools create enforcement boundaries at every lookup.

## Current Architecture

```
select_thin → deepen (map×5) → reflect → collect → create_skeletons (map×N) → gate → persist
                 │                                        │
                 ▼                                        ▼
        sees: synopsis + target entity           sees: canon index + synopsis
              + canon INDEX (id + type only)            + red_link description
              + event_context for character
```

## Target Architecture

```
select_thin → deepen (map×5) → reflect → collect → create_skeletons (map×N) → gate → persist
                 │                                        │
                 ▼                                        ▼
        AGENT with tools:                         AGENT with tools:
        - lookup_canon_page(id)                   - lookup_canon_page(id)
        - list_canon_ids()                        - list_canon_ids()
        - validate_draft(yaml)                    - validate_draft(yaml)
        Each lookup injects constraints.          Gate validates mechanical rules.
        Lookup log = audit trail.
```

## Options

### A. Full Canon in Context — REJECTED

**Change**: Dump all canon YAML into every deepen/skeleton prompt.

**Why rejected**: Omnipotent-LLM thinking. Throwing 13K tokens of context at the LLM and hoping it reads the right parts. No enforcement boundaries. No audit trail of what was actually consulted. The LLM can still invent "Ottokar" with Ulf's full page sitting in context — there's no mechanism to catch it mid-generation. More tokens ≠ more reliability.

Also: doesn't scale, and prevents the in-progress validation that tools enable.

---

### B. Agent Node with Canon Lookup Tools — SELECTED

**Change**: Convert deepen map sub-node from `type: llm` to `type: agent`. Provide a `lookup_canon_page(id)` tool. LLM decides which pages to read.

```yaml
deepen:
  type: map
  over: "{state.thin_entities}"
  node:
    type: agent
    prompt: deepen_entity
    tools:
      - lookup_canon_page  # returns full YAML + injected constraints
      - list_canon_ids     # returns all IDs with types
      - validate_draft     # mechanical validation of in-progress page
    max_tool_calls: 10
```

**Three tools, three enforcement boundaries:**

1. **`lookup_canon_page(id)`** — Returns full YAML for an entity. Each response injects contextual constraints:
   - For characters: "Year 0 = flood. birth_years are negative. This character's father is {name} (from relationships)."
   - For events: "Year 0 = flood. Negative = before flood."
   - The tool response is the boundary where external data enters — normalize here per Scripture.

2. **`list_canon_ids()`** — Returns all IDs with types. The agent calls this first to understand what exists. Prevents duplicate entity creation.

3. **`validate_draft(page_yaml)`** — Mechanical validation of an in-progress page before final submission. Checks: birth_year sign, relationship targets exist, no duplicate IDs (the_X vs X), required fields present. The agent can self-correct before returning.

**Why tools > context dump:**
- Every lookup is an **audit checkpoint** — the trace shows exactly which pages the agent consulted.
- If Gunnar's backstory mentions "Ottokar," the trace shows the agent never called `lookup_canon_page("ulf")` — the error is **traceable to a missing lookup**, not a missed detail in a 13K token wall.
- `validate_draft` enables **in-progress correction** — mechanical validation mid-generation, not post-generation.
- Each tool response can inject domain-specific constraints that wouldn't survive in a context dump (the LLM would skim past them).

| Metric | Current | After |
|--------|---------|-------|
| Input tokens per deepen call | ~1,200 | ~3-8K (depends on lookups) |
| LLM round-trips per entity | 1 | 2-5 |
| Wall time per entity | ~25s | ~60-120s |
| 3 loops total | ~24K tokens | ~50-100K tokens |
| Cost | ~$0.006 | ~$0.03-0.05 |

**Effort**: 3 Python tools + prompt rewrite + worldgen.yaml changes. ~0.5 day.

**Risk**: Agent loop adds latency and non-determinism. Mitigated by `validate_draft` catching errors before persist. DeepSeek tool calling is functional — the tools are simple (lookup by ID, validate schema), not complex multi-step reasoning.

---

### C. Selective Context (Graph Neighborhood) — REJECTED

**Why rejected**: The errors we found were all **cross-entity** (Gunnar→Hilde's father, Ælfgard→Erik's death date) — exactly the 2-hop references a 1-hop neighborhood misses. Two-hop approaches full canon size anyway, making this a worse version of Option A.

---

### D. Post-Generation Validation Gate (Complementary)

**Change**: Enhance `validate_pages` to catch mechanical errors regardless of context strategy.

```python
# In validate_pages.py — add after Pydantic validation
def validate_cross_refs(page, canon):
    errors = []
    if page["type"] == "character":
        if page.get("birth_year", 0) > 0:
            errors.append(f"{page['id']}: birth_year {page['birth_year']} is positive (should be negative)")
        for rel in page.get("relationships", []):
            to = rel.get("to", rel.get("id", ""))
            if to == "?" or to not in canon:
                errors.append(f"{page['id']}: relationship to '{to}' not in canon")
    # Duplicate ID detection (the_X vs X)
    normalized = page["id"].removeprefix("the_")
    if normalized != page["id"] and normalized in canon:
        errors.append(f"{page['id']}: duplicate of existing '{normalized}'")
    return errors
```

**Fixes**: birth_year sign, placeholder relationships, duplicate IDs, dangling references.

**Doesn't fix**: Name collisions in prose (semantic, not mechanical). Calendar arithmetic errors.

**Effort**: ~20 lines in validate_pages.py + tests. 0.25 day.

**Risk**: None. Pure addition. Rejects bad pages before persist.

---

## Comparison Matrix

| Criterion | A. Full Context | B. Agent + Tools | C. Neighborhood | D. Gate |
|-----------|:-:|:-:|:-:|:-:|
| Fixes name collisions | hope | ✓ (audit trail) | △ (1-hop miss) | ✗ |
| Fixes calendar errors | hope | ✓ (constraint injection) | △ | ✓ (sign only) |
| Fixes duplicates | hope | ✓ (list_canon_ids) | ✓ | ✓ |
| Fixes placeholder refs | hope | ✓ (validate_draft) | ✓ | ✓ |
| In-progress validation | ✗ | ✓ | ✗ | ✗ (post only) |
| Audit trail | ✗ | ✓ (lookup log) | ✗ | ✓ (reject log) |
| Scales to 1000+ pages | ✗ (~200 max) | ✓ | ✓ | ✓ |
| Implementation effort | 15 min | 0.5 day | 0.5 day | 0.25 day |
| New failure modes | none | agent loop | missing neighbors | none |
| Cost increase | 25× (~$0.15) | 5-8× (~$0.04) | 3-5× (~$0.02) | 0× |

## Recommendation

**B + D, evolving to E.** Agent with lookup tools (0.5 day) + validation gate (0.25 day), then evolve to full CRUD tools.

- Option A rejected: context dump is omnipotent-LLM thinking. No enforcement boundaries, no audit trail. "Hope it reads the right part" is not a strategy.
- Option C rejected: 1-hop neighborhood misses the exact cross-entity errors we observed.
- Tools create boundaries at every lookup. Each tool response is a checkpoint where constraints are injected and compliance can be validated. The lookup log makes errors traceable to missing lookups, not missed context.
- The validation gate (D) is belt-and-suspenders — catches mechanical errors that even a well-behaved agent might produce.
- Agent approach is not premature — it's about the interaction pattern, not the canon size. Even with 5 pages, tools give boundaries that a context dump doesn't.

---

### E. Full CRUD Tools — Logical Endpoint of B

**Insight**: If the agent has `lookup_canon_page` and `validate_draft`, the next step is obvious — move creation and persistence into tools too. The Pydantic schema leaves the prompt and becomes the tool parameter schema. Validation moves from post-generation gate to tool boundary.

**Current seam (B):**
```
Agent → structured output (big JSON) → Python parses → Python validates → Python persists
```

**Target seam (E):**
```
Agent → create_character(id, name, birth_year, ...) → tool validates + persists → feedback
Agent → update_character(id, backstory=...) → tool validates + persists → feedback
Agent → create_event(id, year, scope, ...) → tool validates + persists → feedback
```

**Tools (one per entity type + lookup/list):**

| Tool | Parameters | Boundary enforcement |
|------|-----------|---------------------|
| `list_canon_ids()` | — | Returns all IDs with types |
| `lookup_canon_page(id)` | entity ID | Returns YAML + injected constraints |
| `create_character(id, name, birth_year, ...)` | Pydantic Character fields | Validates: birth_year < 0, faction exists, relationship targets exist. Persists atomically. Returns success/error. |
| `update_character(id, ...)` | Partial fields | Same validation. Merges with existing page. |
| `create_event(id, year, scope, ...)` | Pydantic Event fields | Validates: year convention, participants exist, affected_locations exist. |
| `create_location(id, name, ...)` | Pydantic Location fields | Validates: no the_X/X duplicates. |

**What this eliminates:**
- The `schema:` block in prompt YAML (the FR-656 Jinja2 collision headache)
- The JSON extraction fallback (FR-464) — no giant structured output to parse
- The `validate_pages` + `persist_pages` separation — each tool call validates and persists atomically
- The `new_entities` list pattern — agent calls `create_character()` when it needs a new entity
- The `collect_red_links` → `create_skeletons` → `gate` → `persist` chain collapses entirely

**Graph simplification:**
```
# Before (9 nodes, complex routing)
reload → anchor → select → deepen (map, llm) → reflect → collect → create_skeletons (map, llm) → gate → persist → reload

# After (4 nodes)
reload → anchor → select → deepen (agent with CRUD tools) → reload
```

The `reflect` node may survive as a post-batch review, or fold into the agent's own assessment after each entity.

**Sequential vs Parallel:**

| Mode | Consistency | Speed | Tokens |
|------|:-:|:-:|:-:|
| Sequential (single agent, all entities) | ✓✓✓ Entity 3 sees entity 2's creations | Slow (1 at a time) | Lower (shared context) |
| Parallel map (one agent per entity) | ✓ Each agent isolated | Fast (5× parallel) | Higher (5× base context) |

Sequential is the stronger guarantee. When deepening Gunnar, the agent can call `lookup_canon_page("ulf")` and see the character it created 2 minutes ago while deepening Hilde. Parallel agents can't — each is isolated, which is exactly the current problem.

**Risk**: More LLM round-trips per entity (1 → 3-8). Wall time per entity doubles (~25s → ~60s). At DeepSeek pricing: cents. The sequential penalty is real but bounded — 5 entities × 60s = 5 minutes vs 1 minute parallel.

**Implementation path**: B first (lookup tools only, keep structured output for creation), then evolve to E once B proves stable. The tools are additive — `create_character` doesn't require removing the schema block; it replaces it.

---

## Implementation Phases

### Phase 0: Fix current canon (manual, 15 min)
Fix the 15 defects from the canon review. No code changes.

### Phase 1: Event-only agent (test scope, 0.25 day)

Events are the ideal test case:
- **Smallest count**: 12 events vs 15 characters. Fast iteration.
- **Most constrained schema**: `year` (must be negative), `participants` (must exist), `affected_locations` (must exist), `scope` (enum). Every field has a mechanical validation rule.
- **Where the worst errors were**: ashfall `year: 0`, slaughter conflated two fathers.
- **Pydantic model exists**: `Event` in `schema/canon.py` maps directly to tool parameters.

**Graph change — split deepen by entity type:**
```yaml
# worldgen.yaml
nodes:
  split:
    type: python
    tool: split_thin_by_type  # routes events vs others

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
      prompt: deepen_entity  # existing prompt, unchanged
```

**What this tests:**
- DeepSeek tool calling reliability (simple lookups, not complex reasoning)
- Wall time impact (1 round-trip → 3-8 per event)
- Quality comparison: agent-deepened events vs llm-deepened characters from same run
- Tool constraint injection: does "year must be negative" in the tool response actually prevent `year: 0`?

**Deliverables:**
- `nodes/split_thin_by_type.py` — routes events to agent, others to llm map
- `nodes/canon_tools.py` — `lookup_canon_page`, `list_canon_ids`, `validate_draft`
- `prompts/deepen_event_agent.yaml` — agent prompt for event deepening
- Worldgen.yaml edge additions for the split routing

**Exit criteria:** Re-run worldgen. Events have correct years, valid participant IDs, no conflated references. Characters still go through existing path.

### Phase 2: All entities through agent (B, 0.25 day)

If Phase 1 succeeds, remove the split and route all entity types through the agent node. The `deepen_other` map node is removed. The agent prompt branches by entity type (already does via Jinja2).

### Phase 3: CRUD tools (E, 0.5 day)

Replace structured output with `create_character()`, `update_character()`, `create_event()`, etc. Graph collapses from 9 nodes to 4. Sequential agent processes all thin entities in one session.

### Phase 4: Retire scaffolding

Remove `collect_red_links`, `create_skeletons`, `gate`, `persist` chain. The agent creates and persists via tools. `validate_pages` gate logic lives inside the CRUD tools.
