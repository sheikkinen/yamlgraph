# Feature Request: FR-452 Standalone Planner Demo

**Priority:** MEDIUM
**Type:** Feature
**Status:** Proposed
**Effort:** 1 day
**Requested:** 2026-05-24

## Summary

Create a standalone planner demo (`examples/demos/planner/`) that transforms a rough topic file into a structured feature request. Mirrors the Chaplain's `step-plan-unified.yaml` but uses `type: agent` with shell tools instead of `type: copilot`, making it portable — runs in CI, scripts, and cron without the VS Code runtime.

## Value Statement

Teams get a scriptable FR planner that researches the codebase, drafts a structured FR, and outputs a JSON plan — usable standalone or as the first step in a plan→judge→enforce pipeline.

## Problem

The Chaplain's planner (`step-plan-unified.yaml`) is a `type: copilot` node requiring the VS Code Copilot CLI runtime (`gpt-5.3-codex`, `allow_all_tools: true`). This makes it:

1. **Not portable** — can't run in CI, cron, or bare terminals
2. **Opaque** — full tool access means no predictable tool budget
3. **Coupled** — requires the full Chaplain FSM dispatcher to invoke

The judge demo (FR-450) proved the pattern: an `agent` node with 5 task-shaped shell tools produces genuine, evidence-based structured output — portable and scriptable.

## Proposed Solution

### Architecture: Mirror the Judge Demo

```
examples/demos/planner/
├── graph.yaml          # Graph with agent node + shell tools
├── prompts/
│   └── planner.yaml    # Planner prompt with inline PlanResult schema
├── demo.sh             # Run planner and extract structured plan
├── demo-output.log     # Captured output
└── README.md
```

### Tools: 5 Task-Shaped Shell Tools

Reuse the judge's proven toolset, minus `run_tests` (planner doesn't run tests), plus `write_file` (planner produces a FR file):

```yaml
tools:
  read_file:
    type: shell
    command: cat {file}
    description: "Read a project file in full."
    parse: text

  search:
    type: shell
    command: rg -n --glob {glob} {pattern} .
    description: "Search files matching a glob pattern."
    parse: text

  list_dir:
    type: shell
    command: ls {dir}
    description: "List contents of a directory."
    parse: text

  git_log:
    type: shell
    command: git log --oneline --all --grep={pattern}
    description: "Search git history for commits mentioning a pattern."
    parse: text

  write_file:
    type: shell
    command: cat > {file_path} << 'YAMLGRAPH_EOF'
    {content}
    YAMLGRAPH_EOF
    description: "Write content to a file. Use to create the feature request."
    parse: text
```

Design rationale:

| Tool | From Judge? | Why |
|------|-------------|-----|
| `read_file` | Yes | Read topic file, FR template, architecture doc |
| `search` | Yes | Find existing patterns, similar FRs, prior art |
| `list_dir` | Yes | Explore codebase structure |
| `git_log` | Yes | Find prior attempts, related work |
| `write_file` | **New** | Planner must produce a FR file (judge only reads) |

**Note:** `write_file` via heredoc is the simplest portable approach. The agent `execute_shell_tool()` → `sanitize_variables()` → `shlex.quote()` pipeline handles injection. However, heredoc with `shlex.quote()` may need validation — the `content` variable contains multi-line markdown. If heredoc doesn't work cleanly through the shell tool pipeline, fall back to Python's `pathlib.Path.write_text()` via a `type: python` tool instead.

### Node Configuration

```yaml
nodes:
  planner:
    type: agent
    prompt: planner
    model: claude-sonnet-4-6
    temperature: 0.3
    tools: [read_file, search, list_dir, git_log, write_file]
    max_iterations: 15
    state_key: plan_result
```

- `temperature: 0.3` — slightly creative for research/drafting (unlike judge's `0`)
- `max_iterations: 15` — planner does more work than judge (research + draft + write)
- `model: claude-sonnet-4-6` — same model as judge for consistency

### Structured Output Schema

```yaml
schema:
  name: PlanResult
  fields:
    fr_path:
      type: str
      description: "Path to the generated feature request file"
    title:
      type: str
      description: "FR title (used as filename)"
    summary:
      type: str
      description: "One-paragraph summary of the planned feature"
    research_findings:
      type: list[str]
      description: "Key findings from codebase research"
    scope_assessment:
      type: str
      description: "Assessment: single_responsibility | needs_split | too_broad"
    estimated_effort:
      type: str
      description: "Effort estimate with rationale"
```

### Prompt Design

The planner prompt follows the Chaplain's plan-unified pattern but adapted for agent tools:

1. **Read the topic** — `read_file` on the topic file
2. **Read the FR template** — `read_file` on `feature-requests/TEMPLATE.md`
3. **Research the codebase** — `search` for related patterns, existing FRs, architecture alignment
4. **Check prior art** — `git_log` for related commits, rejected work
5. **Draft the FR** — `write_file` to create the FR in `feature-requests/`
6. **Return structured plan** — JSON with path, title, findings

### State

```yaml
state:
  topic_file: str
  plan_result: dict
```

Input: `topic_file` — path to a freeform topic/idea file (like `.chaplain/inbox/` entries).

### demo.sh

```bash
#!/usr/bin/env bash
set -euo pipefail
# Usage: ./demo.sh <path-to-topic-file>
# Example: ./demo.sh .chaplain/inbox/refactor-state-builder.md
```

## Acceptance Criteria

- [ ] Graph has 5 tools: `read_file`, `search`, `list_dir`, `git_log`, `write_file`
- [ ] No `| head -N` truncation in any tool
- [ ] `max_iterations` set to 15
- [ ] Prompt instructs agent to read FR template and architecture doc
- [ ] `PlanResult` schema includes `fr_path`, `title`, `summary`, `research_findings`
- [ ] Demo runs successfully and produces a FR file in `feature-requests/`
- [ ] Agent evidence includes: architecture search, existing FR landscape, git history
- [ ] `demo.sh` outputs structured `plan.json`
- [ ] `write_file` tool validated through shell tool pipeline (or fallback to Python tool)

## Alternatives Considered

- **Use `type: copilot`** — The Chaplain does this. But copilot nodes require VS Code runtime. The whole point of this demo series is portable, scriptable pipeline steps.
- **Reuse judge demo tools exactly** — Judge has `run_tests` but no `write_file`. Planner needs the opposite. 4 of 5 tools are shared; the 5th differs by role.
- **Multi-node pipeline (research → draft → write)** — Over-engineered for a demo. Single agent node with good tools and prompt structure achieves the same. The Chaplain unified plan (FR-305) consolidated from 3 steps to 1 for the same reason.
- **Include acceptance test writing** — The Chaplain's unified plan includes test writing. Out of scope for this demo — that's an enforce concern. Keep planner focused on planning.

## Related

- FR-450 — Judge demo hardening (established the pattern)
- FR-447 — Original judge demo
- `.chaplain/graphs/watcher-plan/step-plan-unified.yaml` — Chaplain copilot planner
- `.chaplain/graphs/watcher-plan/prompts/plan-unified.yaml` — Chaplain plan prompt
- `feature-requests/TEMPLATE.md` — FR template the planner should use
- Scripture: `spec_kill`, `ask_before_generate`, `demo_vs_test`

## Open Questions

1. **`write_file` via heredoc** — Does `shlex.quote()` handle multi-line content in heredoc correctly? If not, use a `type: python` tool with `pathlib.Path.write_text()`. Needs validation during enforcement.
2. **FR numbering** — Should the planner auto-assign the next FR number? The Chaplain's `capture_fr` step handles this. For the demo, manual numbering or sequential scan of `feature-requests/` may suffice.
3. **Pipeline composition** — Can `demo.sh` chain planner → judge? e.g., `./planner/demo.sh topic.md | ./judge/demo.sh -`. Future scope, but worth considering in the state contract design.
