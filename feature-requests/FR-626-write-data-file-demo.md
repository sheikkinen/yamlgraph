# FR-626: Write Data File Demo — Accumulating World Bible

**Status:** Judged ✅
**Priority:** Low
**Type:** Feature (demo)
**Effort:** 0.5 day
**Requested:** 2026-06-30
**Judged:** 2026-06-30

## Problem

FR-625 added the `write_data_file` tool type but there is no demo proving the
read→augment→write-back cycle works end-to-end via CLI. The `data-files` demo
shows the read half; this demo shows the full round-trip — a YAML-only graph
that accumulates structured knowledge across runs without custom Python.

Without a demo, the feature is documented but not proven (Commandment 2:
"Code that has not been run must not be demoed").

## Proposal

Create `examples/demos/write_data_file/` demonstrating a "world bible" that
grows across invocations.

### Demo structure

```
examples/demos/write_data_file/
├── graph.yaml          # Read wiki → LLM compresses → Write wiki back
├── prompts/
│   └── compress.yaml   # Merge existing + new into updated wiki
├── wiki/
│   └── world.yaml      # Seed file (starts near-empty, grows across runs)
├── README.md
└── demo-output.log
```

### Graph design

```yaml
version: "1.0"
name: write-data-file-demo
description: Accumulating world bible via read-compress-write cycle
prompts_relative: true
prompts_dir: prompts

data_files:
  wiki: wiki/world.yaml           # READ existing wiki at compile time

state:
  new_fact: str                    # Input: new information to integrate
  updated_wiki: dict               # LLM output: compressed wiki
  _written: str                    # File path confirmation

tools:
  save_wiki:
    type: write_data_file
    state_key: _written

nodes:
  compress:
    type: llm
    prompt: compress
    state_key: updated_wiki
    provider: google
    temperature: 0.2

  persist:
    type: python
    tool: save_wiki
    variables:
      path: "wiki/world.yaml"
      data: "{state.updated_wiki}"

edges:
  - from: START
    to: compress
  - from: compress
    to: persist
  - from: persist
    to: END
```

### Usage pattern

```bash
# Run 1 — seed a character
yamlgraph graph run examples/demos/write_data_file/graph.yaml \
  --var new_fact="Kael is a wandering blacksmith who lost his forge in the Ashfall." \
  --full

# Run 2 — add a location
yamlgraph graph run examples/demos/write_data_file/graph.yaml \
  --var new_fact="The Crimson Bazaar is a floating market above the salt flats." \
  --full

# Run 3 — connect them
yamlgraph graph run examples/demos/write_data_file/graph.yaml \
  --var new_fact="Kael arrived at the Crimson Bazaar seeking dragonsteel." \
  --full
```

After three runs, `wiki/world.yaml` contains accumulated knowledge — proving
the read→augment→write-back cycle without custom Python.

### Prompt design

The compress prompt receives `state.wiki` (existing bible) and `state.new_fact`
(new info). It returns a structured dict with keys: `setting`, `characters`,
`locations`, `events`. Jinja2 template with `tojson` filter for wiki rendering.

Inline schema enforces structure via Pydantic.

## Constraints

1. No custom Python — entire demo is YAML-only (graph + prompt + seed file).
2. Provider: `google` (cheapest for demo; fast enough for structured output).
3. Seed file must be git-tracked; demo-output.log must show multi-run accumulation.
4. Prompt must handle empty lists gracefully (first run starts from seed).
5. Demo must `graph lint` clean.

## Acceptance Criteria

- [ ] `yamlgraph graph lint examples/demos/write_data_file/graph.yaml` passes.
- [ ] Three consecutive `graph run` invocations accumulate data in `wiki/world.yaml`.
- [ ] `wiki/world.yaml` after 3 runs contains characters, locations, and events.
- [ ] `demo-output.log` captures all 3 runs showing progression.
- [ ] README.md documents the read→augment→write-back pattern.
- [ ] No custom Python files in the demo directory.

## Related

- FR-625: Built-in `write_data_file` tool (implementation)
- FR-021: `data_files` directive (read half)
- `examples/demos/data-files/`: Existing read-only demo

---

## Judgement

**Authority: GRANTED.**

### Assessment

Clean demo FR. Minimal scope, clear deliverable, no code risk. The demo proves
FR-625 works end-to-end via CLI — which is the Commandment 2 obligation that
FR-625 enforcement deliberately deferred.

### Corrections

None. The FR is already minimal and well-scoped.

### Scope Freeze

- Create demo directory with graph.yaml, prompt, seed wiki, README.
- Run 3 times, capture demo-output.log.
- Lint clean. No custom Python. Git-track seed state (reset after demo capture).
- Commit the demo with seed state restored to empty (so next user starts fresh).

### Enforcement Order

1. Create directory structure and files.
2. `yamlgraph graph lint` — must pass.
3. Run 3 invocations with distinct facts.
4. Capture output to `demo-output.log`.
5. Reset `wiki/world.yaml` to seed state for git commit.
6. Commit.
