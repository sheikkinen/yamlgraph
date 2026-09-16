# Authoring brief: FR-1049 opencode judge variant — third backend node in the sole-route judge adapter

Governing FR: feature-requests/FR-1049-opencode-judge-variant.md (judged 2026-09-16, APPROVED; this brief is deliverable D-1, judgement C-3).

## Task

Modify **exactly one file**:

1. `.github/skills/judge-fr/adapters/graph.yaml`

No new files. No change to `.github/skills/judge-fr/adapters/prompts/judge.yaml`
(already interpolates `{{ artifact_path }}`), `doctrine.md`,
`judgement.template.md`, `scripts/judge.sh`, or any other file. Do not run
`scripts/judge.sh`, the judge graph, or any copilot/claude/opencode binary
live — the smoke below is mocked.

### `graph.yaml` — target shape

Keep the file header comments (NON-AUTHORITATIVE prototype, lineage,
`version`, `name`, `description`, `prompts_relative`, `prompts_dir`) exactly
as they are. Replace the `state`, `nodes`, and `edges` sections so the graph
reads:

```yaml
state:
  fr_path: str
  backend: str            # "copilot" | "claude" | "opencode"; scripts/judge.sh always sets it (FR-960/FR-1049)
  artifact_path: str      # per-backend-per-FR path computed by scripts/judge.sh (FR-960)
  judge_result: dict

nodes:
  select:
    type: passthrough
    output: {}
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
      model: claude-opus-5     # exact id (the `opus` alias resolved to this on 2.1.255 — FR-960 witness §2.4); never an alias (REQ-YG-632, PR #577 review P3)
      tools: [Read, Glob, Grep, Write]         # availability (--tools); no Bash, no Edit, no MCP
      allowed_tools: [Read, Glob, Grep, Write] # approval (--allowedTools) for the same four
      max_turns: 40
    prompt: judge            # SAME prompt file (NC-412 zero duplication)
    variables:
      fr_path: "{state.fr_path}"
      artifact_path: "{state.artifact_path}"
    state_key: judge_result
    timeout: 600
  judge_opencode:
    type: copilot
    backend: opencode         # FR-1048 backend; bills the operator's provider key
    cli_flags:
      model: deepseek/deepseek-v4-pro   # provider/model; compile-time fail-closed (FR-1048 §5); H-1 human spend decision
    prompt: judge             # SAME prompt file (NC-412 zero duplication)
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
    condition: backend == "copilot"
  - from: select
    to: judge_claude
    condition: backend == "claude"
  - from: select
    to: judge_opencode
    condition: backend == "opencode"
  - from: judge
    to: END
  - from: judge_claude
    to: END
  - from: judge_opencode
    to: END
```

Constraints on the result (FR-1049 judgement C-4, C-5, C-9; FR-931 REQ-YG-632):

- The `judge` node is byte-identical to today's node; its `model: gpt-5.6-sol`,
  `allow_all_paths`, and `allow_all_tools` stay.
- The `judge_claude` node is byte-identical to today's node (four tools in both
  keys, exact `claude-opus-5`).
- The `judge_opencode` node has **only** `model` in `cli_flags` — no
  `tools`, `allowed_tools`, `max_turns`, `allow_all_tools`, `allow_all_paths`,
  `auto`, `agent`, `resume`, or any other key. Its model is exactly
  `deepseek/deepseek-v4-pro` (the H-1 human spend decision; FR-1048 requires
  the `provider/model` grammar).
- Exactly three `type: copilot` nodes, all `prompt: judge`.
- The three routing conditions are the mutually exclusive `backend == "copilot"`,
  `backend == "claude"`, `backend == "opencode"`. The Copilot edge's former
  `backend != "claude"` catch-all is **replaced** by `backend == "copilot"`
  (a catch-all would silently misroute `opencode` to the Copilot seat — the
  expression router returns on first match).

## Precedent

- The existing adapter itself (`.github/skills/judge-fr/adapters/graph.yaml`) —
  the `judge` and `judge_claude` nodes are kept as the precedent nodes; the
  new `judge_opencode` mirrors `judge_claude` minus the tool flags.
- FR-960 (`feature-requests/FR-960-claude-judge-variant.md` and its brief) —
  the second-backend shape this FR extends to a third.
- FR-1048 (`feature-requests/FR-1048-opencode-cli-backend.md`) — the
  `backend: opencode` contract: only `model`/`resume`, `provider/model`
  grammar, no permission/tool flag.
- `.chaplain/graphs/watcher-plan/step-judge-v2.yaml` — lineage of the adapter.

## Validation

Lint and validate the graph; then the mocked routing smoke (no judge is
launched — `subprocess.run` is patched):

```bash
yamlgraph graph lint .github/skills/judge-fr/adapters/graph.yaml
yamlgraph graph validate .github/skills/judge-fr/adapters/graph.yaml
python -m pytest tests/unit/test_fr1049_opencode_judge_variant.py -k TestGraphRouting -q --no-cov -p no:cacheprovider
python -m pytest tests/unit/test_fr960_claude_judge_variant.py -q --no-cov -p no:cacheprovider
python -m pytest tests/unit/test_fr931_sole_route_model_pin.py -q --no-cov -p no:cacheprovider
```

All must pass. Lint must report 0 errors. The `judge_opencode` node must not
trigger `E-COPILOT-OPENCODE-MODEL` or `E-COPILOT-OPENCODE-FLAG-SHAPE` (its
`model` is a valid `provider/model` and it carries no forbidden flag).

## Report

Write `tmp/draft-authoring-report.md` with the required headings
(`Artifacts`, `Precedent`, `Validation`, `Repairs`, `Blocked validation`),
listing the one modified repo-relative path under `Artifacts` and the five
validation commands with their results. Do not use verdict vocabulary.

**Prior art:** FR-1049-opencode-judge-variant.md (governing FR — this brief executes its authorized graph surface); FR-960 (second-backend shape), FR-1048 (backend contract), FR-931 (model pin), NC-412/NC-414 (one prompt, recursion guard) dispositioned there.
