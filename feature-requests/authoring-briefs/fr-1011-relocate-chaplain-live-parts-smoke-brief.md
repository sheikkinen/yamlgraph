# Authoring brief: FR-1011 validation-only — philosopher smoke from its relocated path

**Governing FR:** feature-requests/FR-1011-relocate-chaplain-live-parts.md (judged APPROVED WITH REVISIONS 2026-09-06; AC-14 three real smokes). Sibling of `fr-1011-relocate-chaplain-live-parts-brief.md`, which relocated the graphs and ran the first two smokes; split because three full-pipeline smokes in one run risk the backend's 900 s ceiling (`scripts/author_preflight.py` budget finding).
**Prior art:** the relocated graph itself — `graphs/philosopher/graph.yaml` (moved from `.chaplain/graphs/philosopher/` by the sibling brief's run).
**Target directory:** repository root of the current working tree. This run authors NOTHING: no file under `graphs/`, `prompts/`, or anywhere else may be created, moved, or edited. Its only outputs are under `tmp/` and the report.
**Artifacts to author:** none. If lint or the smoke fails, record the exact command and error under "Blocked validation" and stop — do not repair the graph, its prompts, or its tools (FR-1011 C-5 forbids semantic change; path repairs belong to the requesting session).

## Task

Validate the relocated philosopher graph from its new path with a side-effect-contained real run.

## Validation the authoring run must perform

```bash
yamlgraph graph lint graphs/philosopher/graph.yaml
```

```bash
mkdir -p tmp/fr1011-diary tmp/fr1011-inbox
cp docs/diary/diary-2026-09-0*.md tmp/fr1011-diary/
yamlgraph graph run graphs/philosopher/graph.yaml --var diary_dir=tmp/fr1011-diary --var inbox_dir=tmp/fr1011-inbox --var date=$(date +%F) --full
```

Record each command verbatim with its outcome, and list every file the run
created under `tmp/fr1011-inbox/` and `tmp/fr1011-diary/` under "Artifacts"
(they are the smoke's evidence, not authored artifacts). Confirm with
`git status --short` that nothing tracked changed and that no file appeared
under `docs/diary/` or `proposals/`.
