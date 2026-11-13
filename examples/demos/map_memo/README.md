# Map memo demo

Summarize three small notes with a Python read -> LLM subgraph worker.
The pipeline prepares paths, splits reused results from pending work, maps only
pending notes, and merges the results into a persistent SQLite memo.
The map uses `min_success: 0` so completed work reaches the merge; the merge
requires success over the entire population with `min_success: 1.0`.

The memo tools ship in `yamlgraph.contrib.map_memo`. Declare them inline,
as an installed user would, without repo-relative shared manifests:

```yaml
tools:
  map_memo_split:
    type: python
    module: yamlgraph.contrib.map_memo
    function: map_memo_split
    description: Split items into reused and todo by content signature.
  map_memo_merge:
    type: python
    module: yamlgraph.contrib.map_memo
    function: map_memo_merge
    description: Merge executed map results with reused ones and persist them.
```

The demo's own `prepare` and `read_note` tools live in this source checkout.
Run from the repository root with Inception credentials configured
(`INCEPTION_API_KEY`); the worker defaults to `inception` / `mercury-2.5`.

```powershell
yamlgraph graph run examples\demos\map_memo\graph.yaml --full
yamlgraph graph run examples\demos\map_memo\graph.yaml --full
```

Starting with no store, the first run makes three LLM calls. The unchanged
second run makes zero LLM calls and reports `reused_ok: 3` in
`merged.result.counts`. Edit just one note in `examples\demos\map_memo\notes`
and run again: one call, with two reused results.

To force a full run, delete the store:

```powershell
Remove-Item outputs\map_memo_demo\memo.sqlite
```

On a POSIX shell, the equivalent is `rm outputs/map_memo_demo/memo.sqlite`.
The next run summarizes all three notes again.

Inputs can be isolated with
`--var notes_dir=<directory> --var store=<sqlite-path>`.
Notes are processed in filename order, with at most 20 pending items.
The signature covers note content plus the main graph, worker graph, and
prompt files. CLI provider/model overrides are not part of the signature:
changing those alone does not invalidate saved summaries. Use a separate
store or delete the existing one when switching provider/model intentionally.
