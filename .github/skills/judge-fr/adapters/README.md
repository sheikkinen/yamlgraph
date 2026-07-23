# judge-fr adapters — execution instructions (operational, not doctrine)

## YAMLGraph prototype (NC-412 A-1: manual only, output advisory)
Sole documented operator command (csap NC-415 — serializes via OS lock
and lineage sentinel; the graph remains the judge execution route):

```bash
scripts/judge.sh feature-requests/FR-XXX-slug.md
```

Direct invocation (what the wrapper runs; use the wrapper instead):
```bash
uv run yamlgraph graph run .github/skills/judge-fr/adapters/graph.yaml \
  --var fr_path=feature-requests/NC-XXX-slug.md --full
```

The graph writes `tmp/draft-judgement.md`; humans fold accepted content
into the real `.judgement.md`. The graph must never auto-fold,
auto-commit, open/update PRs, poll inboxes, manage worktrees, run CI,
or merge.

**Load-bearing flags (csap NC-414):** BOTH `allow_all_paths: true` AND
`allow_all_tools: true` are required for the file-write contract.
Copilot CLI needs `--allow-all-tools` for non-interactive tool use;
without it the judge runs, renders a verdict, is denied the write,
and still exits 0. **Verify by artifact existence, never by exit
code**: after a run, check that `tmp/draft-judgement.md` exists and
is non-empty with a verdict line.

## VS Code prompt adapter

FORBIDDEN as a judge execution route (one judge to rule them all — the
graph above is the sole route). The reviewer adapter
`.github/prompts/review-pr.prompt.md` is unaffected: it reviews PRs,
it does not judge FRs.

Both adapters point at `../doctrine.md` — the canonical, non-invocable
judge contract. No doctrine lives in any adapter file.
