# Feature Request: Diary Index Graph — Framework Indexes Its Own Reflections

**Priority:** MEDIUM
**Type:** Feature
**Status:** Approved
**Effort:** 2 days
**Requested:** 2026-04-19

## Summary

Build a YAMLGraph demo graph at `examples/demos/diary-index/` that reads all diary entries from `docs/diary/*.md`, extracts structured data (traps, heuristics, seeds, FR references) from each using a `type: map` + `type: llm` pattern, and produces a cross-reference index at `docs/diary-index.yaml`. The framework builds an index of its own reflective process.

## Value Statement

Project maintainers get automatic discovery of recurring traps, graduating heuristics, and dormant seeds across 450+ diary entries, replacing linear grep-based search with a structured, queryable index.

## Problem

The diary corpus (`docs/diary/`) contains 450+ entries with no structured index. Knowledge exists but discovery is linear — grep only. Recurring patterns that should surface for Scripture graduation require manual effort to identify. The philosopher's reflection (`2026-04-19-philosopher-diary-corpus-reflection.md`) was produced manually; the same analysis should be reproducible and automated via a YAMLGraph graph.

Specific gaps:
1. **No cross-reference** — traps like `downstream_fix` appear in many entries but there is no index of which entries reference which traps.
2. **No seed recurrence tracking** — seeds planted in early entries may recur across multiple later entries, signaling readiness for graduation. This is invisible today.
3. **No FR linkage** — diary entries reference FR numbers but there is no reverse index from FR to diary reflections about it.

## Proposed Solution

A 4-node graph using the existing `type: map` pattern to iterate over diary files, deterministic Python aggregation, and a dedicated write node:

```
START → list_files → extract_all (map) → aggregate → write_index → END
```

### Graph structure

```yaml
version: "1.0"
name: diary-index
description: >
  Read diary entries, extract traps/heuristics/seeds/FR references,
  produce a structured cross-reference index.

prompts_relative: true
prompts_dir: prompts

defaults:
  provider: anthropic
  model: claude-haiku
  temperature: 0.2

state:
  diary_files: list
  extractions:
    type: list
    reducer: sorted_add
  index: dict
  output_path: str

tools:
  list_diary_files:
    type: python
    path: ./tools.py
    function: list_diary_files
    description: "List all diary .md files with their content"
  aggregate_index:
    type: python
    path: ./tools.py
    function: aggregate_index
    description: "Deterministically aggregate extractions into a cross-reference index"
  write_index:
    type: python
    path: ./tools.py
    function: write_index
    description: "Write the final index to docs/diary-index.yaml"

nodes:
  list_files:
    type: python
    tool: list_diary_files
    state_key: diary_files

  extract_all:
    type: map
    over: "{state.diary_files}"
    as: entry
    max_items: 500
    node:
      type: llm
      prompt: extract_entry
      state_key: extraction
      variables:
        filename: "{state.entry.filename}"
        content: "{state.entry.content}"
    collect: extractions
    on_error: skip

  aggregate:
    type: python
    tool: aggregate_index
    state_key: index

  write_index:
    type: python
    tool: write_index
    state_key: output_path

edges:
  - from: START
    to: list_files
  - from: list_files
    to: extract_all
  - from: extract_all
    to: aggregate
  - from: aggregate
    to: write_index
  - from: write_index
    to: END
```

### Design decisions addressing Judgement issues

**Issue 1 — Aggregation is `type: python`, not `type: llm`.**
The `aggregate` node performs deterministic data processing: counting trap occurrences, sorting by frequency, building reverse indexes. These are pure data operations. An LLM would add non-determinism, cost, and unreliable counting. The `aggregate_index` Python function receives the `extractions` list from state and computes statistics deterministically, making acceptance criteria 4–6 testable and repeatable.

**Issue 2 — `write_index` tool is now invoked.**
A dedicated 4th node (`write_index`) persists the index to `docs/diary-index.yaml`, following the horoscope demo's `save` node pattern: `type: python, tool: write_index, state_key: output_path`.

**Issue 3 — Ground-truth fixture for testable criteria.**
A unit test uses a fixture of 5 known diary entries with predetermined traps/seeds/FRs. The test runs `aggregate_index()` against pre-built extraction data and asserts expected output. The full corpus run remains a demo, not a test.

**Issue 4 — Cost mitigated via `model: claude-haiku`.**
The `defaults` section specifies `model: claude-haiku`, the cheapest Anthropic model. At ~$0.25/MTok input, 450 diary entries (~2KB avg = ~900K tokens) costs ~$0.25–0.50 per run. README documents expected cost. Incremental indexing (processing only new entries) is deferred to a future FR.

### Extraction schema (per-entry)

```yaml
# prompts/extract_entry.yaml
system: >
  You are a structured data extractor. Given a diary entry, extract
  the requested fields precisely. For traps and heuristics, use the
  canonical names from the Scripture when possible (e.g. downstream_fix,
  quick_confidence, symptom_patch). For seeds, quote the forward-looking
  question or idea verbatim.

user: |
  Extract structured data from this diary entry.

  Filename: {{ filename }}

  Content:
  {{ content }}

schema:
  name: DiaryExtraction
  fields:
    filename:
      type: str
      description: "Diary entry filename"
    date:
      type: str
      description: "ISO date from entry header or filename"
    title:
      type: str
      description: "Entry title"
    traps:
      type: list[str]
      description: "Cognitive trap names encountered (e.g. downstream_fix, quick_confidence)"
    heuristics:
      type: list[str]
      description: "General principles or rules stated"
    seeds:
      type: list[str]
      description: "Forward-looking questions or ideas for future exploration"
    fr_references:
      type: list[str]
      description: "Feature request identifiers mentioned (FR-XXX format)"
    category:
      type: str
      description: "Entry category: reflection | audit | git-report | world-digest | chaplain | philosopher | other"
```

### Aggregation output

The `aggregate_index` Python function produces a dict with:
- **entries**: Per-entry metadata (filename, date, title, category, traps, heuristics, seeds, FRs)
- **traps_index**: Trap name → list of filenames, sorted by occurrence count descending
- **seeds_index**: Seed text → list of filenames, sorted by occurrence count descending
- **fr_index**: FR-XXX → list of diary entry filenames (reverse index)
- **heuristics_candidates**: Heuristics appearing 2+ times (candidates for Scripture graduation)
- **statistics**: Total entries, entries by category, total unique traps/seeds/FRs

### Python tools

`tools.py` provides three functions:
1. `list_diary_files()` — globs `docs/diary/*.md`, reads each file, returns list of `{filename, content}` dicts.
2. `aggregate_index(state)` — receives `state["extractions"]`, deterministically computes the cross-reference index. Returns the index dict.
3. `write_index(state)` — writes `state["index"]` to `docs/diary-index.yaml` via PyYAML. Returns the output path.

### Demo directory layout

```
examples/demos/diary-index/
├── graph.yaml
├── README.md
├── tools.py
├── demo-output.log
└── prompts/
    └── extract_entry.yaml
```

## Cost and Performance

- **Per-run cost**: ~452 LLM calls using `claude-haiku` at ~$0.25/MTok input. Average diary entry ~2KB → ~900K input tokens total. Estimated cost: **$0.25–0.50 per full run**.
- **Latency**: With map node parallelism, expected wall-clock time 2–5 minutes.
- **Mitigation**: `claude-haiku` is specified as default model. The README documents expected cost so users make an informed choice.
- **Future optimization**: Incremental indexing (skip entries already in index) deferred to a separate FR to keep scope minimal.

## Acceptance Criteria

- [ ] Graph runs via `yamlgraph graph run examples/demos/diary-index/graph.yaml --full`
- [ ] Graph lints clean via `yamlgraph graph lint examples/demos/diary-index/graph.yaml`
- [ ] Produces a valid YAML file at `docs/diary-index.yaml` (parseable by PyYAML)
- [ ] `aggregate` node is `type: python` — deterministic counting, no LLM
- [ ] `write_index` node persists the index to disk (follows horoscope `save` pattern)
- [ ] Index includes top-N most recurring traps with entry count and filenames
- [ ] Index includes top-N most recurring seeds with entry count and filenames
- [ ] Index includes FR → diary entry reverse mapping
- [ ] Index includes heuristics appearing 2+ times (Scripture graduation candidates)
- [ ] Unit test: `aggregate_index()` tested against a 5-entry ground-truth fixture with known traps/seeds/FRs, asserting expected output deterministically
- [ ] Unit test: graph YAML loads and lints clean
- [ ] Extraction prompt uses inline `schema:` for structured output (no Python Pydantic models)
- [ ] `tools.py` contains no hardcoded prompts (Commandment 1)
- [ ] `defaults.model` set to `claude-haiku` to control cost
- [ ] `demo-output.log` included proving the demo was executed (FR-206 demo-gate)
- [ ] README.md documents usage, expected output format, cost estimate, and FR reference
- [ ] `examples/README.md` entry added for diary-index demo

## Judgement Notes (2026-04-19)

**Verdict: APPROVED** — Scope frozen. Authority granted to implement.

**Findings:**

1. **Single responsibility** — ✅ The FR addresses one concern: building a structured cross-reference index of diary entries. It does not conflate indexing with reflection (philosopher) or diary writing (chaplain).

2. **Follows existing patterns** — ✅ Graph structure mirrors the horoscope demo (map → aggregate → save). Python tool loading via `path:` is supported. The `sorted_add` reducer and `max_items` override are existing features.

3. **Nested variable access** — ✅ Verified. `{state.entry.filename}` resolves correctly via `resolve_state_expression` in `yamlgraph/utils/expressions.py` (line 86–91), which supports nested dict/attribute access.

4. **`on_error: skip` placement** — ⚠️ Minor. Currently placed at the map node level, but `on_error` is an LLM node property. The map compiler's `_wrap_for_reduce` already catches all sub-node exceptions and records them as error entries in the collection. The `on_error: skip` at the map level is silently ignored but harmless. During implementation, the implementor should either (a) move it into the `node:` block, or (b) remove it since map branches already survive individual failures.

5. **`max_items: 500`** — ✅ The default `DEFAULT_MAX_MAP_ITEMS = 100` would truncate 452 entries. The per-node `max_items: 500` override is the correct mitigation.

6. **`model: claude-haiku`** — ⚠️ Minor. The implementor should verify this resolves to a valid model name in the LLM factory. May need to be `claude-haiku-4-5` or similar depending on provider alias support.

7. **Acceptance criteria** — ✅ All 17 criteria are specific, measurable, and testable. The ground-truth fixture approach (AC #10) correctly separates deterministic unit testing from the full-corpus demo.

8. **Cost analysis** — ✅ Reasonable. ~$0.25–0.50 per run with Haiku. Incremental indexing correctly deferred to a future FR.

9. **Output location** — ✅ Writing to `docs/diary-index.yaml` is intentional — the index is a maintained repo artifact, not a transient output.

**No contradictions or ambiguities found. No scope expansion needed.**

## Alternatives Considered

1. **Pure Python script** — A `scripts/diary_index.py` could parse diary entries with regex. Rejected: misses the meta-narrative of the framework indexing itself, and regex is fragile against varying diary formats (Commandment: YAMLGraph and LLM should be used instead of complex regex logic).

2. **Extend philosopher daemon** — The philosopher already reads diary entries. However, the philosopher's purpose is reflection and distillation, not indexing. Adding indexing would violate single responsibility.

3. **Static analysis only (no LLM)** — Extract traps/seeds via regex patterns. Rejected: diary entries use varied phrasing ("trap encountered", "the trap was", "cognitive hazard", etc.) that LLM extraction handles naturally.

4. **LLM-based aggregation** — Use `type: llm` for the aggregate node. Rejected per Judgement Issue 1: aggregation is deterministic counting and sorting — an LLM adds non-determinism, unreliable counting, potential hallucinated statistics, and makes acceptance criteria untestable.

## Related

- `docs/diary/2026-04-19-philosopher-diary-corpus-reflection.md` — Manual version of this analysis
- `examples/demos/horoscope/` — Map node + Python save reference pattern
- `examples/demos/python-map/` — Python sub-node in map reference
- FR-093 (`FR-093-chaplain-diary-append.md`) — Chaplain diary writing
- FR-184 (`FR-184-philosopher-daemon.md`) — Philosopher daemon (related but distinct purpose)
- FR-206 — Demo-gate CI enforcement (requires `demo-output.log`)
- Scripture: `seeds.inquisitor_auto_escalation` — Auto-create FR when audit pattern hits threshold (related goal)
