# judge-fr adapters — execution instructions (operational, not doctrine)

## YAMLGraph prototype (NC-412 A-1: manual only, output advisory)

```bash
uv run yamlgraph graph run .github/skills/judge-fr/adapters/graph.yaml \
  --var fr_path=feature-requests/NC-XXX-slug.md --full
```

The graph writes `tmp/draft-judgement.md`; humans fold accepted content
into the real `.judgement.md`. The graph must never auto-fold,
auto-commit, open/update PRs, poll inboxes, manage worktrees, run CI,
or merge.

## VS Code prompt adapter

`/judge-fr` (see `.github/prompts/judge-fr.prompt.md`).

Both adapters point at `../doctrine.md` — the canonical, non-invocable
judge contract. No doctrine lives in any adapter file.
