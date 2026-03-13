# Feature Request: Philosopher Reflect World Context

**FR-194**
**Priority:** LOW
**Type:** Enhancement
**Status:** Approved
**Effort:** 1 day
**Requested:** 2026-03-13

## Summary

Enrich the philosopher's `reflect` prompt with external world context by adding a `load_context` python node that reads a curated `docs/world-context.md` file, connecting diary reflections to competitor moves and ecosystem developments. Includes bootstrapping the context file itself.

## Value Statement

The philosopher agent produces richer, outward-aware diary reflections by grounding its observations in real-world ecosystem context rather than operating in a purely internal loop.

## Problem

The philosopher graph (`examples/philosopher/graph.yaml`) scans diary entries for recurring patterns and proposes graduations — but its `reflect` node only sees internal state (`scan_result`, `proposals`). It has no awareness of what is happening in the broader ecosystem (LangGraph releases, competitor frameworks, LLM provider changes, protocol updates).

FR-046 (Diary World Digest) solves the *production* of world context via automated fetching, but it does not feed that context into the philosopher's reflection. There is a missing link: a curated `docs/world-context.md` file that the philosopher can read to ground its reflections.

Currently, `docs/world-context.md` does not exist. This FR covers:

1. **Bootstrapping** the `docs/world-context.md` file with a defined structure
2. **Loading** it into graph state via a new `load_context` python node
3. **Enriching** the `reflect` prompt to incorporate world context

## Proposed Solution

### 1. Bootstrap `docs/world-context.md`

Create a curated markdown file with a stable structure:

```markdown
# World Context

Last updated: 2026-03-13

## Ecosystem

- LangGraph 1.0.x: current features, recent changes
- Competing frameworks: LlamaIndex Workflows, CrewAI, DSPy

## LLM Providers

- Recent model releases and capability changes
- Pricing shifts affecting provider strategy

## Protocols

- MCP spec updates
- A2A developments

## Seeds Connection

- Open seeds from diary that connect to external developments
```

This file is manually curated (or eventually auto-updated by FR-046's digest pipeline). It is a plain markdown file — no special tooling required.

### 2. Add `load_context` python node

Add a new tool and node to the philosopher graph:

```yaml
# In tools section
tools:
  load_context_tool:
    type: python
    module: examples.philosopher.tools
    function: load_world_context

# In nodes section, inserted before reflect
nodes:
  load_context:
    type: python
    tool: load_context_tool
    state_key: world_context
```

The python function:

```python
def load_world_context(state: dict) -> dict:
    """Load world context from docs/world-context.md.

    Returns empty string if the file does not exist,
    allowing the graph to run gracefully without it.
    """
    context_path = Path("docs/world-context.md")
    if not context_path.exists():
        return {"world_context": ""}
    return {"world_context": context_path.read_text()}
```

### 3. Update graph edges

Insert `load_context` between `propose` and `reflect`:

```yaml
edges:
  - from: START
    to: scan
  - from: scan
    to: analyze
  - from: analyze
    to: propose
  - from: propose
    to: load_context
  - from: load_context
    to: reflect
  - from: reflect
    to: write_diary
  - from: write_diary
    to: END
```

### 4. Enrich `reflect` prompt

Add `world_context` variable to the reflect node and update the prompt template:

```yaml
# In graph.yaml reflect node
reflect:
  type: copilot
  prompt: reflect
  variables:
    scan_result: "{state.scan_result}"
    proposals: "{state.proposals}"
    world_context: "{state.world_context}"
  state_key: diary_entry
  timeout: 300
```

Add a conditional section to `prompts/reflect.yaml`:

```yaml
user: |
  ## Scan Results
  {{ scan_result | tojson(indent=2) }}

  ## Proposals Generated
  {% if proposals and proposals.output %}
  {{ proposals.output }}
  {% else %}
  No graduation candidates found.
  {% endif %}

  {% if world_context %}
  ## World Context
  {{ world_context }}
  {% endif %}

  ## Instructions
  Write a brief diary entry...
  (existing instructions, updated to mention world context if present)
```

### 5. Add `world_context` to state declaration

```yaml
state:
  world_context: str   # External ecosystem context (from docs/world-context.md)
```

## Acceptance Criteria

- [ ] `docs/world-context.md` exists with a documented structure and initial content
- [ ] `load_world_context()` function returns file contents when file exists
- [ ] `load_world_context()` returns empty string when file is missing (graceful degradation)
- [ ] Philosopher graph includes `load_context` node between `propose` and `reflect`
- [ ] `reflect` prompt conditionally renders world context (omitted when empty)
- [ ] `world_context` declared in graph state section
- [ ] Existing philosopher behavior unchanged when `docs/world-context.md` is absent
- [ ] Unit test: `load_world_context` with existing file returns content
- [ ] Unit test: `load_world_context` with missing file returns empty string
- [ ] Unit test: reflect prompt renders with and without world context
- [ ] Tests added with `@pytest.mark.req` traceability
- [ ] Documentation updated (README or philosopher example docs)

## Alternatives Considered

1. **Use `data_files` instead of a python node** — `data_files` loads at compile time and fails if the file is missing. A python node allows graceful degradation (empty string when file absent), which is essential since `docs/world-context.md` may not always be present.

2. **Have FR-046 write directly to graph state** — This would couple the world-digest pipeline to the philosopher graph. Keeping a file as the interface allows manual curation and decouples the two pipelines.

3. **Inline the context in the graph YAML via `data_files`** — Would require the file to exist at compile time. The python node approach is more resilient.

4. **Read world context inside the `reflect` prompt via Jinja2** — Jinja2 templates should not perform I/O; side effects belong in python nodes per the three-layer pattern.

## Judgement Notes

**Verdict: APPROVE** — 2026-03-13

Scope is clear, minimal, and internally consistent. Single responsibility: all three pieces (bootstrap file, python node, prompt enrichment) serve the same goal and are tightly coupled. Alternatives analysis is sound — correctly rejects `data_files` (compile-time), Jinja2 I/O (violates three-layer), and direct coupling to FR-046.

**Implementation notes (non-blocking):**

1. **Path from state, not hardcoded.** `scan_diary_markers` takes `diary_dir` from `state["diary_dir"]`. For consistency, `load_world_context` should take the path from state (e.g., `world_context_path: str` with default `"docs/world-context.md"`) rather than hardcoding `Path("docs/world-context.md")`.

2. **REQ-YG-194.** Add requirement to `ARCHITECTURE.md` and extend `scripts/req_coverage.py` per convention. Tag tests with `@pytest.mark.req("REQ-YG-194")`.

## Related

- **FR-046** (`feature-requests/046-diary-world-digest.md`): Diary World Digest — produces the world context that this FR consumes
- **FR-184/FR-185**: Philosopher pipeline and CopilotResult envelope
- `examples/philosopher/graph.yaml`: The philosopher graph being modified
- `examples/philosopher/prompts/reflect.yaml`: The reflect prompt being enriched
- `docs/diary/2026-03-13-chaplain.md`: Diary entry identifying the bootstrap gap
