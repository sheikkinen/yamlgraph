# Authoring brief: FR-960 Claude judge variant — second backend node in the sole-route judge adapter

Governing FR: feature-requests/FR-960-claude-judge-variant.md (judged 2026-09-02, APPROVED WITH REVISIONS; this brief is deliverable D-2, R-2).

## Task

Modify **exactly two files**, both existing:

1. `.github/skills/judge-fr/adapters/graph.yaml`
2. `.github/skills/judge-fr/adapters/prompts/judge.yaml`

No new files. No change to `.github/skills/judge-fr/doctrine.md`,
`.github/skills/judge-fr/judgement.template.md`, `scripts/judge.sh`, or
any other file. Do not run `scripts/judge.sh`, the judge graph, or any
copilot/claude binary live — the smoke below is mocked.

### 1. `graph.yaml` — target shape

Keep the file header comments (NON-AUTHORITATIVE prototype, lineage,
`version`, `name`, `description`, `prompts_relative`, `prompts_dir`)
exactly as they are. Replace the `state`, `nodes`, and `edges` sections so
the graph reads:

```yaml
state:
  fr_path: str
  backend: str            # "copilot" | "claude"; scripts/judge.sh always sets it (FR-960)
  artifact_path: str      # per-backend-per-FR path computed by scripts/judge.sh (FR-960)
  judge_result: dict

nodes:
  select:
    type: passthrough
  judge:
    type: copilot
    backend: cli
    cli_flags:
      model: gpt-5.6-sol
      allow_all_paths: true
      allow_all_tools: true  # NC-414 (csap): required for non-interactive tool use;
                             # without it the file write of the draft artifact
                             # is denied while the CLI still exits 0
    prompt: judge
    variables:
      fr_path: "{state.fr_path}"
      artifact_path: "{state.artifact_path}"
    state_key: judge_result
    timeout: 600
  judge_claude:
    type: copilot
    backend: claude          # FR-959 backend; bills the operator's Claude subscription
    cli_flags:
      model: opus
      tools: [Read, Glob, Grep, Write]         # availability (--tools); no Bash, no Edit, no MCP
      allowed_tools: [Read, Glob, Grep, Write] # approval (--allowedTools) for the same four
      max_turns: 40
    prompt: judge            # SAME prompt file (NC-412 zero duplication)
    variables:
      fr_path: "{state.fr_path}"
      artifact_path: "{state.artifact_path}"
    state_key: judge_result
    timeout: 600

edges:
  - from: START
    to: select
  - from: select
    to: judge
    condition: backend != "claude"
  - from: select
    to: judge_claude
    condition: backend == "claude"
  - from: judge
    to: END
  - from: judge_claude
    to: END
```

Constraints on the result (FR-960 judgement C-4, C-5; FR-931 REQ-YG-632):

- The `judge` node is byte-identical to today's node except for the added
  `artifact_path` variable; its `model: gpt-5.6-sol`, `allow_all_paths`,
  and `allow_all_tools` stay.
- The `judge_claude` node has **no** `allow_all_tools`, no `allow_all_paths`,
  no `provider`, and exactly the four tools listed, in both keys.
- Exactly two `type: copilot` nodes, both `prompt: judge`.

### 2. `prompts/judge.yaml`

Replace the literal `tmp/draft-judgement.md` in the `user:` text with
`{{ artifact_path }}` — one substitution, nothing else changes (the
`system:` block, the NC-414 recursion-guard wording, and the doctrine
pointer stay byte-identical). The prompt is Jinja2-rendered because it
already contains `{{ fr_path }}`.

## Precedent

- The existing adapter itself (`.github/skills/judge-fr/adapters/graph.yaml`) — the
  `judge` node is kept as the precedent node.
- `examples/demos/ramp_incidents/graph.yaml` and
  `examples/demos/book-summary/graph.yaml` — `condition:` edge expressions
  of the `x != y` form.
- `.chaplain/graphs/watcher-plan/step-judge-v2.yaml` — lineage of the
  adapter.
- FR-959 (`feature-requests/FR-959-claude-cli-backend-primitive.md`) — the
  `backend: claude` contract and the `tools` / `allowed_tools` /
  `max_turns` keys; `reference/graph-yaml.md` § Claude Code backend.

## Validation

Lint and validate the graph; then the mocked routing smoke (no judge is
launched — `subprocess.run` is patched):

```bash
yamlgraph graph lint .github/skills/judge-fr/adapters/graph.yaml
yamlgraph graph validate .github/skills/judge-fr/adapters/graph.yaml
python -m pytest tests/unit/test_fr960_claude_judge_variant.py -k TestGraphRouting -q --no-cov -p no:cacheprovider
python -m pytest tests/unit/test_fr931_sole_route_model_pin.py -q --no-cov -p no:cacheprovider
```

All four must pass. Lint must report 0 errors; `W-COPILOT-*` warnings on the
`judge_claude` node are not expected (it sets both `tools` and
`allowed_tools`, no `allow_all_tools`, a Claude alias model).

## Report

Write `tmp/draft-authoring-report.md` with the required headings
(`Artifacts`, `Precedent`, `Validation`, `Repairs`, `Blocked validation`),
listing both modified repo-relative paths under `Artifacts` and the four
validation commands with their results. Do not use verdict vocabulary.

**Prior art:** FR-960-claude-judge-variant.md (governing FR — this brief executes its authorized graph surface); FR-958 judgement R-2/C-3 (four-tool restriction), FR-959 (backend), FR-931 (model pin), NC-412/NC-414 (one prompt, recursion guard) dispositioned there.
