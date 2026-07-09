# Recap — Timeframe Change Inventory (FR-700)

Answers *"what changed in this repo in the last day/week?"* for **any** git
repository. Deterministic git collection via `type: tool` nodes; exactly one
LLM node groups the inventory into workstreams and flags **orphans** —
commits with no FR/issue reference, and graph/prompt YAML changes with no
changelog fragment.

Mechanizes the Scripture's `changelog_first_diagnostic` cure: enumerate what
changed before reproducing anything.

## Run

```bash
# On this repository
yamlgraph graph run examples/demos/recap/graph.yaml \
  --var since="1 week ago" --var repo_path=. --full

# On any other repository
yamlgraph graph run examples/demos/recap/graph.yaml \
  --var since="yesterday" --var repo_path=/path/to/repo --full
```

## Output (structured state, via `--full`)

| Field | Meaning |
|-------|---------|
| `workstreams` | Commits grouped by FR reference or theme, each tagged with the **verbatim** FR `[Status: …]` at HEAD (or `[no FR status]`) |
| `orphans` | Unreferenced commits (partitioned deterministically by code); graph/prompt edits without changelog fragments |
| `hotspots` | Files touched by multiple workstreams |

Convention absence (no `feature-requests/` / `changelog/unreleased/`) is
detected by the Jinja2 template and reported to the model as "not detected" —
the raw `fr_changes`/`fragments` state keys stay available for downstream code.

## Portability

- All git commands use `git -C {repo_path}` — no cwd assumptions, no reflog syntax.
- Missing convention paths yield empty output natively (`git log -- <missing>` exits 0).
- A `repo_path` that is **not** a git repo fails loudly (tool node raises).
- Commit collection capped at 300; truncation is reported, not hidden.

## Difference from git-report

| Aspect | [git-report](../git-report/) | recap |
|--------|------------------------------|-------|
| Pattern | `agent` node — LLM decides which tools to call | Fixed pipeline — `type: tool` chain, LLM never picks tools |
| Question | Open-ended ("who touched X?") | Fixed ("what changed since T?") |
| Judgements | Multi-step exploration | Exactly one (group + flag orphans) |
| Partitioning | Model reads raw output | Jinja2 partitions paths in the template |
| Repo assumptions | Current directory | Any repo via `--var repo_path` |

## Teaching points

1. `type: tool` nodes for deterministic collection — no LLM in the loop until judgement is actually needed.
2. Mechanizable work is split by kind: file-*path* partitioning and truncation/convention notices live in Jinja2 in the prompt template; commit-*reference* detection (FR-702) and the id→status join (FR-703) are `type: python` passes around the LLM node ([nodes/partition.py](nodes/partition.py)) — the model can neither mis-flag a referenced commit as an orphan nor drop a status join.
3. Disposition is collected and joined by code, never by the model: a `git grep` tool reads verbatim FR `Status:` lines at HEAD; a post-pass appends `[Status: …]` per id (per-id tags when a merged workstream's statuses differ). Its exit-1 ("no matches") is normalized at the boundary while real errors still fail loudly.
4. Inline schema keeps serialization out of the model's job: lists only, Pydantic-validated. The prompt's only formatting demand: name FR ids in full, never shorthand — so downstream arithmetic is never starved.
