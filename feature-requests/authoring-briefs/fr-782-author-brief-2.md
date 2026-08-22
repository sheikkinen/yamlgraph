# Task brief — FR-782 self-portrait graph: repair Python tool loading

Modify exactly one file: `examples/demos/self-portrait/graph.yaml`.
Do NOT create, modify, or delete anything else.

## Defect

Every tool in the `tools:` section uses the graph-relative form:

```yaml
  prepare_run:
    type: python
    path: tools.py
    function: prepare_run
```

`path:` loads the file with `importlib.util.spec_from_file_location`,
which gives the module no parent package, so `tools.py`'s relative
imports (`from . import portrait_io, wikidata`) fail. The run aborts:

```
❌ Error: Python tool load failed in strict mode (config.tool_load_mode=strict):
prepare_run: attempted relative import with no known parent package; ...
```

## Repair

Switch every one of the seven tools from the `path:` form to the
`module:` form, keeping the same `function:` values:

```yaml
  prepare_run:
    type: python
    module: examples.demos.self-portrait.tools
    function: prepare_run
```

Tools to convert: `prepare_run`, `extract_sources`, `enrich_topics`,
`build_synthesis_payload`, `verify_consent`, `render_portrait`,
`render_extraction_only`.

Committed precedent for the hyphenated-directory module path:
`examples/demos/file-hook/graph.yaml` uses
`module: examples.demos.file-hook.tools`.

Change nothing else in the graph — nodes, edges, state, checkpointer,
defaults, and the interrupt/consent routing stay exactly as they are.

## Validation to run

```bash
yamlgraph graph lint examples/demos/self-portrait/graph.yaml
yamlgraph graph validate examples/demos/self-portrait/graph.yaml
python -m pytest tests/unit/test_fr782_self_portrait.py -q --no-cov -k "graph or prompt"
```

A grounded LLM smoke run against the synthetic fixture is executed by the
requesting session afterwards — do not run it here.

**Prior art:** historical authoring brief migrated from tmp/ by FR-852; dispositions in `feature-requests/FR-852-preserve-authoring-briefs.md`.
