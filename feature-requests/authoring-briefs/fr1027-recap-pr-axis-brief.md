# Authoring brief: FR-1027 recap pull-request axis (graph wiring only)

**FR:** `feature-requests/FR-1027-recap-pull-request-axis.md`
**Judgement:** `feature-requests/FR-1027-recap-pull-request-axis.judgement.md`
— APPROVED WITH REVISIONS, R-1..R-5 folded, authority active. Gate C-2
requires this graph edit to come through the governed authoring route.

## Task

Wire one already-implemented, already-tested graph-local python node into the
existing `examples/demos/recap/` graph. The node module
`examples/demos/recap/nodes/prs.py` exists and its unit tests are committed;
this task adds only the declarations that make the graph call it.

`examples/demos/recap/prompts/recap.yaml` must NOT be touched. Judgement gate
C-4: the pull-request axis is code-owned and must never reach the synthesis
prompt, the LLM schema, or `synthesize`'s `variables`. The graph must still
have exactly one LLM node, `synthesize`.

## Edits

Path-only list. Make exactly these changes and nothing else.

- `examples/demos/recap/graph.yaml`

### 1. `state:` — add one key

Add, alongside the existing `since` / `repo_path` / `referenced` /
`unreferenced` keys:

```yaml
  pr_axis: dict     # FR-1027: code-owned pull-request axis (never model-visible)
```

### 2. `tools:` — add one python tool

Add after the existing `attach_statuses_fn` entry:

```yaml
  collect_prs_fn:
    type: python
    module: examples.demos.recap.nodes.prs
    function: collect_prs
    description: "PR axis (FR-1027): origin→owner/name, one bounded gh invocation, code-owned merged/closed-unmerged/open buckets; absence, unreachability and cap are reported, never substituted."
```

Do not add any `type: shell` tool. Every existing shell tool in this graph is
asserted to be a portable `git -C {repo_path}` command; the `gh` boundary is
fixed-argv python inside `prs.py`.

### 3. `nodes:` — add one python node

Add after the existing `partition` node:

```yaml
  get_prs:
    type: python
    tool: collect_prs_fn
    requires: [repo_path, since]
```

It takes no `state_key`: `collect_prs` returns its own `pr_axis` update, the
same way `partition` returns `referenced` / `unreferenced`.

### 4. `edges:` — splice the node into the existing chain

The chain today is:

```
START → get_commits → get_churn → get_frs → get_fragments
      → get_fr_statuses → partition → synthesize → finalize_recap → END
```

Insert `get_prs` between `partition` and `synthesize`, so the resulting chain
is:

```
START → get_commits → get_churn → get_frs → get_fragments
      → get_fr_statuses → partition → get_prs → synthesize
      → finalize_recap → END
```

Concretely: change the edge `partition → synthesize` into `partition →
get_prs`, and add `get_prs → synthesize`. Every other edge is unchanged.

## Validation

Both commands run from the repository root.

### Lint

```
yamlgraph graph lint examples/demos/recap/graph.yaml
```

Must pass.

### Smoke (offline, no LLM, no network)

The graph's single LLM node needs a key and its `gh` collection needs a
GitHub remote, so the smoke is the deterministic prefix of the chain,
exercised against a throwaway repository that has no `origin`. This is the
FR-922 latency budget and the AC-14 shape: the axis must report its own
absence without a network call.

```
python -c "import json, subprocess, tempfile, pathlib; \
d=tempfile.mkdtemp(); \
subprocess.run(['git','init','-q',d],check=True); \
p=pathlib.Path(d,'a.txt'); p.write_text('x'); \
subprocess.run(['git','-C',d,'add','-A'],check=True); \
subprocess.run(['git','-C',d,'-c','user.email=t@t','-c','user.name=t','commit','-q','-m','feat: FR-1 seed'],check=True); \
import sys; sys.path.insert(0,'.'); \
from examples.demos.recap.nodes.prs import collect_prs; \
print(json.dumps(collect_prs({'repo_path': d, 'since': '1 week ago'}), indent=2))"
```

Expected: `pr_axis.available` is `false`, `pr_axis.reason` is
`no origin remote`, and all three buckets are empty.

### Structure suite

```
pytest tests/unit/test_recap_pr_axis.py tests/unit/test_recap_demo.py tests/unit/test_fr702_recap_disposition.py tests/unit/test_weekly_recap.py -q --no-cov
```

Must be green, including the pre-existing `test_collection_is_tool_nodes` and
`test_git_commands_are_portable`, which are expected to pass **unmodified**
(AC-03): the new node is `type: python`, so the frozen `type: tool` set and
the all-shell-tools-are-git invariant both still hold.

## Precedent

- `examples/demos/recap/nodes/partition.py` — the graph-local python node
  module this one sits beside; `partition` is the precedent for a `type:
  python` node that returns its own state keys with no `state_key:`.
- `examples/demos/corpus_census/adapters/corpus_adapters.py` — the committed
  `gh` boundary (fixed argv, `shell=False`, finite timeout) that `prs.py`
  follows.
- FR-704 — the reason the axis is attached in `finalize_recap` rather than
  shown to the model.
