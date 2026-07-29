# graph-authoring adapters — execution instructions (operational, not doctrine)

## YAMLGraph adapter (FR-765: manual only, output advisory)

Sole documented operator command (serializes via OS lock and lineage
sentinel; the graph is the authoring execution route):

```bash
scripts/author.sh <task-brief.md>
```

The task brief is a committed or explicitly provided markdown file that
closes the input: the task description, target directory, and desired
artifact names live inside the brief — never in hidden chat narrative.

Direct invocation (what the wrapper runs; use the wrapper instead):

```bash
uv run yamlgraph graph run .github/skills/graph-authoring/adapters/graph.yaml \
  --var task_path=path/to/task-brief.md --full
```

The graph authors files in the working tree and writes
`tmp/draft-authoring-report.md`; humans review and commit. The graph
must never auto-commit, open/update PRs, poll inboxes, manage
worktrees, run CI, or merge.

**Load-bearing flags (NC-414):** BOTH `allow_all_paths: true` AND
`allow_all_tools: true` are required for the file-write contract.
Copilot CLI needs `--allow-all-tools` for non-interactive tool use;
without it the agent authors nothing, is denied every write, and still
exits 0. **Verify by artifact existence, never by exit code**: after a
run, check that `tmp/draft-authoring-report.md` exists, is non-empty,
contains the `Artifacts`, `Precedent`, `Validation`, `Repairs`, and
`Blocked validation` headings, and lists at least one repo-relative
authored path that exists. The wrapper enforces exactly this.

## Not a judge or review route

This adapter authors graph artifacts. It must not invoke `judge-fr`,
`review-pr`, their adapters, or any judgement/review graph, and its
report must not use verdict vocabulary.

The adapter points at `../doctrine.md` — the canonical, non-invocable
authoring workflow contract. No doctrine lives in any adapter file.
