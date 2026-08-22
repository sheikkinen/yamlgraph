# Task: FR-780 GREEN — convert research-agent to shared toolbelt manifests

Governing FR: feature-requests/FR-780-research-agent-toolbelt-conversion.md
(judged APPROVED WITH REVISIONS 2026-08-07; conditions C-1..C-5). RED suite
committed: tests/unit/test_fr780_research_agent_toolbelt.py — 8 failing
tests define the target shape exactly. Precedent: the planner demo
(examples/demos/planner/graph.yaml lines 12-22) already declares the same
four tools by manifest reference.

## Files to modify (nothing else)

1. examples/demos/research-agent/graph.yaml
2. examples/demos/research-agent/prompts/plan_research.yaml
3. examples/demos/research-agent/prompts/execute_research.yaml

Hard boundaries (GATE conditions): no yamlgraph/ changes; no edits to
examples/shared/toolbelt/*.tool.yaml; do not change max_iterations; do
NOT touch the FR-779 surface — state declarations, {state.query}/
{state.scope} bindings, and the conditional validate_findings edges must
survive byte-identical.

## Change 1: graph.yaml tools block

Replace the current inline `search_code`, `list_files`, `read_file`
declarations and add `git_log`, so the tools block becomes:

```yaml
tools:
  read_file:
    manifest: ../../shared/toolbelt/read_file.tool.yaml
  search:
    manifest: ../../shared/toolbelt/search.tool.yaml
  list_dir:
    manifest: ../../shared/toolbelt/list_dir.tool.yaml
  git_log:
    manifest: ../../shared/toolbelt/git_log.tool.yaml
  count_lines:
    type: shell
    command: wc -l {file}
    description: Count lines in a file
```

(count_lines stays inline — demo-local, no toolbelt equivalent.)

## Change 2: graph.yaml agent tool lists

- `plan_research.tools`: `[search, list_dir]`
- `execute_research.tools`: `[search, list_dir, read_file, count_lines, git_log]`
  (exact order — the RED test asserts these lists verbatim)

## Change 3: prompts — canonical names, args, scope translation

Rewrite the tool sections of both prompts. Required content (RED test
asserts the strings "glob" and "list_dir" appear, and that "first 80
lines" and "Python files" do NOT appear in either prompt):

prompts/plan_research.yaml system section — describe:
- search(pattern, glob): search files matching a glob pattern from the
  repository root
- list_dir(dir): list contents of a directory
- Instruct: honor the given scope by passing it as the list_dir dir
  argument and as a glob prefix for search (e.g. scope "yamlgraph/" →
  --glob 'yamlgraph/**/*'); never silently search the whole repository
  when a scope is given.

prompts/execute_research.yaml system section — describe:
- search(pattern, glob), list_dir(dir), read_file(file) (reads the file
  in full), count_lines(file), git_log(pattern) for prior-art history
- Same scope-translation instruction as above.

Keep the user sections and everything else in both prompts unchanged.

## Validation

- `yamlgraph graph lint examples/demos/research-agent/graph.yaml`
- `yamlgraph graph validate examples/demos/research-agent/graph.yaml`
- `pytest tests/unit/test_fr780_research_agent_toolbelt.py -q --no-cov` — all 11 must pass
- `pytest tests/unit/test_fr779_research_agent_demo.py -q --no-cov` — all 8 must still pass (regression boundary)

**Prior art:** historical authoring brief migrated from tmp/ by FR-852; dispositions in `feature-requests/FR-852-preserve-authoring-briefs.md`.
