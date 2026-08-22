# Task brief: FR-777 — convert planner/enforcer/judge to toolbelt manifest references

## Authority

FR-777 (feature-requests/FR-777-shared-shell-toolbelt-manifests.md),
judged APPROVED WITH REVISIONS 2026-08-06
(feature-requests/FR-777-shared-shell-toolbelt-manifests.judgement.md).
Judgement deliverable D-2; conditions C-2 (this route), C-4 (effective
behavior unchanged).

## Artifacts to modify (governed)

1. examples/demos/planner/graph.yaml
2. examples/demos/enforcer/graph.yaml
3. examples/demos/judge/graph.yaml

No prompt files change. No other graphs change.

## The change (identical pattern, all three graphs)

In each graph's `tools:` block, replace ONLY the four inline shell tool
declarations `read_file`, `search`, `list_dir`, `git_log` (each currently
`type: shell` + `command` + `description` + `parse`) with pure manifest
references:

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
```

The manifests already exist at examples/shared/toolbelt/*.tool.yaml
(committed working tree). Manifest paths resolve relative to the
referencing graph (REQ-YG-574) — `../../shared/toolbelt/` is correct
from all three demo dirs.

## Must NOT change

- Any other tool declaration (planner: write_file; enforcer: git_diff,
  lint, run_tests, write_file, edit_file; judge: run_tests) — they stay
  inline exactly as-is.
- nodes:, edges:, state:, prompts, temperatures, max_iterations, tool
  lists on agent nodes — byte-identical.
- Nothing under yamlgraph/ (FR-777 C-1).

## Validation

- `yamlgraph graph lint` on all three graphs must pass.
- Smoke: `yamlgraph graph validate` / config load for all three.
- Test suite: `pytest tests/unit/test_fr777_shell_toolbelt.py -q --no-cov`
  must go from 14 failed to 0 failed (RED committed as
  "test(examples): FR-777 RED shell toolbelt manifest suite").
  Do NOT run the demos' agent runs (they call live LLMs); config-load
  tests suffice for the authoring report.

**Prior art:** historical authoring brief migrated from tmp/ by FR-852; dispositions in `feature-requests/FR-852-preserve-authoring-briefs.md`.
