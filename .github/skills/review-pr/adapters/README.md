# review-pr adapters — execution instructions (operational, not doctrine)

## YAMLGraph prototype (manual only, output advisory)

Sole documented operator command (NC-413 parity — serializes via OS
lock and lineage sentinel; the graph remains the review execution
route):

```bash
scripts/review.sh <pr-number-or-branch> feature-requests/NC-XXX-slug.md
```

Direct invocation (what the wrapper runs; use the wrapper instead):

```bash
uv run yamlgraph graph run .github/skills/review-pr/adapters/graph.yaml \
  --var pr=<pr> --var fr_path=feature-requests/NC-XXX-slug.md --full
```

The graph writes `tmp/draft-review.md`; the human makes the merge
decision. The graph must never approve, merge, comment, auto-fold,
auto-commit, open/update PRs, poll inboxes, or run CI.

**Load-bearing flags (csap NC-414):** BOTH `allow_all_paths: true` AND
`allow_all_tools: true` are required for the file-write contract;
without the latter the CLI exits 0 while the write is denied.
**Verify by artifact existence, never by exit code**: after a run,
check that `tmp/draft-review.md` exists, is non-empty, and has the
merge-verdict line.

## VS Code prompt adapter

FORBIDDEN as a review execution route (parity with judge-fr: one
reviewer to rule them all — the graph above is the sole route;
`review-pr.prompt.md` deleted under NC-413).
