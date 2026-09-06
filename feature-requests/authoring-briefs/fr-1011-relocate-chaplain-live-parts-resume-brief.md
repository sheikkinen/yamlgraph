# Authoring brief: FR-1011 resumed validation — fr_triage and world_distill smokes from their relocated paths, one comment line

**Governing FR:** feature-requests/FR-1011-relocate-chaplain-live-parts.md (judged APPROVED WITH REVISIONS 2026-09-06; AC-14 three real smokes). Resumes `fr-1011-relocate-chaplain-live-parts-brief.md`, whose run relocated the graphs (all `R100`) and passed the three lints but recorded both smokes under "Blocked validation": the triage graph appends to **Proposed** FRs only and the committed FR-1011 copy is Judged; `world_distill` needed the `feedparser` package, which the requesting session has since installed into the environment (`pip install feedparser`; it is a declared `digest` extra in `pyproject.toml`).
**Prior art:** the relocated graphs themselves — `graphs/fr_triage/graph.yaml`, `graphs/world_distill/graph.yaml`.
**Target directory:** repository root of the current working tree.
**Artifacts to author:** exactly ONE comment-line edit in `graphs/philosopher/graph.yaml` (below). Nothing else may be created, moved, or edited; no prompt, node, edge, schema, tool, provider or model change (FR-1011 C-5). If lint or a smoke fails, record the exact command and error under "Blocked validation" and stop — do not repair semantics or install anything.

## Task

1. In `graphs/philosopher/graph.yaml`, replace line 5 — currently
   `# FR-196: relocated from examples/philosopher/ to .chaplain/graphs/philosopher/; FR-1011: relocated to graphs/philosopher/`
   — with exactly
   `# FR-196 moved this graph out of examples/philosopher/ into the chaplain runtime; FR-1011 relocated it to graphs/philosopher/`
   so the relocated package no longer spells the retired directory path (FR-1011 invariant R-2). No other byte in the file changes.
2. Run the validation below.

## Validation the authoring run must perform

```bash
yamlgraph graph lint graphs/philosopher/graph.yaml
yamlgraph graph lint graphs/fr_triage/graph.yaml
yamlgraph graph lint graphs/world_distill/graph.yaml
```

The triage smoke uses a **Proposed** FR copied to `tmp/` (FR-214 is `**Status:** Proposed` and carries no `## Triage` section); the graph appends a Triage section to the copy only:

```bash
mkdir -p tmp
cp feature-requests/FR-214-fix-extract-variables-nested-set.md tmp/fr1011-smoke-fr.md
yamlgraph graph run graphs/fr_triage/graph.yaml --var fr_path=tmp/fr1011-smoke-fr.md --full
yamlgraph graph run graphs/world_distill/graph.yaml --var date=$(date +%F) --var output_path=tmp/fr1011-world-context.md --full
```

Record each command verbatim with its outcome. After the runs confirm:
the smoke FR copy under `tmp/` now contains exactly one `## Triage` heading; the world-context output file named by `--var output_path` was written and is non-empty; `git status --short` shows no change under `docs/`, `feature-requests/`, or `proposals/`, and the only modified tracked file from this run is `graphs/philosopher/graph.yaml`. Report those three facts under "Validation".
