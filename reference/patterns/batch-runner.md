# Batch-Runner Pattern

Use this pattern when you need to run one graph over a **varying set of input
files chosen at runtime** — an evaluation corpus, a folder of documents, a
sweep of fixtures — and collect one result per input.

The instinct is to reach for `data_files:` or a `map` node. Neither fits, and
understanding *why* is the pattern.

## Why not `data_files:`

The [`data_files:`](../graph-yaml.md) directive loads YAML into state, but it is
the wrong tool for a runtime corpus:

| Constraint (`data_loader.py`) | Consequence |
|-------------------------------|-------------|
| **Static** — resolved at compile time | Cannot vary the file per run |
| **Escape-bounded** — `file_path.relative_to(graph_dir)` | Rejects any path outside the graph's own directory |
| **No transform** — raw `safe_load` | Cannot strip/reshape rows before they enter state |

`data_files` is for *config that ships with the graph* (a schema, a soul,
a rubric). It is not for *the data this particular run happens to process*.

## Why not a `map` node

A [`map` node](../patterns.md) fans a graph out over a list **already in
state**, one sub-invocation per item. That is the right tool when items are
independent and the list is part of the run's logic. It is the wrong tool when:

- the items live in **separate files on disk** (the map's `input` reads state, not the filesystem), or
- the graph needs to see the **whole list at once** for cross-item context.

Isolating each item discards that context. If your accuracy depends on an item
seeing its neighbours (sequence labeling, dependency-aware classification), a
naive map makes results *worse*.

## The pattern: a thin Python runner

Runtime file selection and I/O are **presentation / side-effect concerns**, not
graph logic (the three-layer architecture). So the loop belongs in a small
Python runner, not in the graph:

```python
# run.py — selects the corpus, the graph stays pure
EXAMPLE_DIR = Path(__file__).resolve().parent
DATA_DIR = EXAMPLE_DIR / "fixtures"
RESULTS_DIR = EXAMPLE_DIR / "results"

def _compile():
    config = load_graph_config(str(GRAPH_PATH))
    return compile_graph(config).compile()

def run_one(app, path: Path):
    rows = load_rows(path)            # ← transform at the boundary
    result = app.invoke({"rows": rows})
    return result.get("output")

def main(argv=None):
    app = _compile()                  # compile ONCE, invoke many
    paths = sorted(DATA_DIR.glob("*.yaml"))
    if args.only:                     # optional single-input selection
        paths = [p for p in paths if p.stem == args.only]
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    for path in paths:
        try:
            out = run_one(app, path)
        except Exception:             # one bad input must not abort the batch
            out = None
        write_result(RESULTS_DIR / f"{path.stem}.yaml", out)
```

### The five rules that make it a pattern, not a script

1. **Compile once, invoke many.** `_compile()` outside the loop — graph
   compilation is the expensive step; each input is just an `invoke`.
2. **Transform at the boundary.** The runner loads *and reshapes* rows
   (stripping labels, normalising) before they enter state — the thing
   `data_files` cannot do.
3. **Isolate failures.** Wrap each `invoke` so one malformed input yields a
   recorded null result, not an aborted batch.
4. **Stable output naming.** One result file per input, keyed by input stem, so
   a separate evaluator can join predictions to ground truth.
5. **The graph stays pure.** No file paths, no `glob`, no corpus knowledge in
   the YAML — it processes whatever state it is handed. The runner owns *which*
   files; the graph owns *what to do* with their contents.

## Reference implementation

[`examples/plot_modeller/run.py`](../../examples/plot_modeller/run.py) runs the
`classify_kinds` graph over four ground-truth fixtures, strips the authored
labels at load time, writes `results/<genre>.yaml` per input, then hands off to
[`evaluate.py`](../../examples/plot_modeller/evaluate.py) (FR-570).

## When to use which

| Need | Use |
|------|-----|
| Config that ships with the graph (schema, rubric, persona) | `data_files:` |
| Fan out over an in-state list, items independent | `map` node |
| Run a graph over runtime-selected files, transform on load, collect per-input results | **Batch runner (this pattern)** |
