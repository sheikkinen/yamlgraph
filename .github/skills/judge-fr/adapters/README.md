# judge-fr adapters — execution instructions (operational, not doctrine)

## YAMLGraph prototype (NC-412 A-1: manual only, output advisory)

Sole documented operator command (NC-415 — serializes via OS lock and
lineage sentinel; the graph remains the judge execution route):

```bash
scripts/judge.sh feature-requests/NC-XXX-slug.md                      # default backend: copilot
JUDGE_BACKEND=claude scripts/judge.sh feature-requests/NC-XXX-slug.md # FR-960: Claude Code backend
```

**Round sentinel (FR-1022, REQ-YG-668).** If the adjacent
`feature-requests/NC-XXX-slug.judgement.md` already holds two `**Verdict:**`
lines, the wrapper does not run the graph: it writes
`**Verdict:** REJECTED — Operator: Rethink and rewrite the FR. It's getting too
complicated as a planning document.` to the draft path and exits 77. Advisory
like every draft; the human exits are marking the FR Rejected or re-filing a
shorter plan as a new FR file. There is no override.

Direct invocation (what the wrapper runs; use the wrapper instead):

```bash
uv run yamlgraph graph run .github/skills/judge-fr/adapters/graph.yaml \
  --var fr_path=feature-requests/NC-XXX-slug.md \
  --var backend=copilot \
  --var artifact_path=tmp/draft-judgement-copilot-NC-XXX-slug.md --full
```

**Backend selection (FR-960, REQ-YG-642).** One graph, one prompt, one
wrapper — still one route. The graph holds two `type: copilot` nodes that
share `prompts/judge.yaml`: `judge` (Copilot CLI, `gpt-5.6-sol`, the
default) and `judge_claude` (`backend: claude`, FR-959). `scripts/judge.sh`
reads `JUDGE_BACKEND` (`copilot` | `claude`; anything else exits 64 before
the lock is taken) and routes with a state-conditioned edge. The Claude node
has exactly four tools available **and** approved — `Read, Glob, Grep,
Write` via `--tools` and `--allowedTools` — with no `allow_all_tools`, no
Bash, no Edit, no MCP: a judge that can run the judge is not a judge. It
bills the operator's Claude subscription through FR-959's per-invocation
preflight; the residual payer boundary is FR-959's (see
`reference/graph-yaml.md` § Claude Code backend), not restated here.

**Artifact path (FR-960).** The draft is written to
`tmp/draft-judgement-<backend>-<fr-slug>.md` — **per backend, per FR**, not
per run. On 2026-09-02 two sessions' judge runs shared the fixed name
`tmp/draft-judgement.md`; the second run's startup `rm -f` deleted the
first run's verified verdict three seconds after the wrapper had accepted
it (the lock protects the run, never the previous output). With the new
name, two backends on one FR and two FRs back to back coexist; a rerun of
the **same** backend on the **same** FR deliberately replaces its own
earlier draft. The wrapper prints the path and the backend on success.
Humans fold accepted content into the real `.judgement.md`. The graph must
never auto-fold, auto-commit, open/update PRs, poll inboxes, manage
worktrees, run CI, or merge.

**Load-bearing flags (NC-414):** BOTH `allow_all_paths: true` AND
`allow_all_tools: true` are required for the file-write contract.
Copilot CLI needs `--allow-all-tools` for non-interactive tool use;
without it the judge runs, renders a verdict, is denied the write,
and still exits 0. This applies to the Copilot node only; the Claude node
uses FR-959's separate availability/approval controls instead of a bypass.
**Verify by artifact existence, never by exit code**: after a run, check
that `tmp/draft-judgement-<backend>-<fr-slug>.md` exists and is non-empty
with a verdict line.

## VS Code prompt adapter

FORBIDDEN as a judge execution route (one judge to rule them all — the
graph above is the sole route). The sole review route is likewise a
review graph via `scripts/review.sh` (NC-413) — the reviewer prompt
adapter was deleted; the reviewer reviews PRs, it does not judge FRs.

Both adapters point at `../doctrine.md` — the canonical, non-invocable
judge contract. No doctrine lives in any adapter file.
