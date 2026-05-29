# Feature Request: Standalone Enforcer Demo

**Priority:** MEDIUM
**Type:** Feature
**Status:** Enforced
**Effort:** 1–2 days
**Requested:** 2026-05-23

## Summary

Build a standalone enforcer demo (`examples/demos/enforcer/`) that takes a planned and judged feature request and implements it. Same architectural pattern as the planner (FR-452) and judge (FR-450) demos: single agent node with shell+python tools, structured output schema, portable demo.sh runner.

## Value Statement

Teams get a scriptable, portable implementation agent that transforms a feature request into working code, tests, and commits — completing the plan→judge→enforce pipeline as three composable, reusable demos.

## Problem

The Chaplain pipeline (plan → judge → enforce) currently has:
- **Planner demo** (`examples/demos/planner/`) — transforms topic into FR ✅
- **Judge demo** (`examples/demos/judge/`) — evaluates FR and renders verdict ✅
- **Enforcer demo** — MISSING ❌

Without a standalone enforcer demo:
1. Users cannot see the full plan→judge→enforce pipeline in action
2. The enforcer is tightly coupled to the Chaplain's copilot CLI runtime
3. No portable, scriptable implementation agent exists for CI gates or ad-hoc use
4. The three-demo pattern is incomplete

## Proposed Solution

Create `examples/demos/enforcer/` following the proven pattern from planner and judge demos:

### Graph: `examples/demos/enforcer/graph.yaml`

Single agent node with task-shaped tools:

```yaml
version: "1.0"
name: fr-enforcer
description: "FR-462 — Standalone FR enforcer with task-shaped tools and structured implementation result"
prompts_relative: true
prompts_dir: prompts

state:
  fr_path: str
  implementation_result: dict

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

  run_tests:
    type: shell
    command: pytest {test_file} -v --no-cov --tb=short 2>&1
    description: "Run a specific test file to verify implementation."
    parse: text

  git_commit:
    type: shell
    command: git add -A && git commit -m {message}
    description: "Stage all changes and commit with given message."
    parse: text

  write_file:
    type: python
    path: tools/write_file.py
    function: write_file
    description: "Write content to a file. Creates parent directories if needed."

nodes:
  enforcer:
    type: agent
    prompt: enforcer
    temperature: 0.3
    tools: [read_file, search, list_dir, run_tests, git_commit, write_file]
    max_iterations: 25
    state_key: implementation_result

edges:
  - from: START
    to: enforcer
  - from: enforcer
    to: END
```

### Prompt: `examples/demos/enforcer/prompts/enforcer.yaml`

```yaml
system: |
  You are a feature request enforcer. Your task is to implement a feature request
  by reading the FR file, understanding the requirements, and writing code that
  satisfies the acceptance criteria.

  You have access to tools to:
  - Read files and directories
  - Write and edit code
  - Run tests
  - Commit changes to git

  Work methodically:
  1. Read the FR file to understand requirements and acceptance criteria
  2. Explore the codebase to understand existing patterns
  3. Implement the feature incrementally
  4. Run tests to verify implementation
  5. Commit changes with clear messages

  Return a structured result with:
  - success: bool (true if all acceptance criteria met)
  - files_changed: list[str] (paths of modified/created files)
  - tests_passed: bool (true if all tests pass)
  - commit_hash: str (final commit SHA, or empty if no commits)
  - summary: str (brief implementation summary)

user: |
  **Enforce.** Implement the feature request at {{ fr_path }}.

  ## Steps

  1. **Read the FR** — use read_file on the FR path
  2. **Read architecture** — use read_file on ARCHITECTURE.md and CLAUDE.md
  3. **Explore** — use list_dir and search to understand existing patterns
  4. **Implement** — use write_file to create/edit files
  5. **Test** — use run_tests to verify implementation
  6. **Fix** — iterate until tests pass (max 5 cycles)
  7. **Commit** — use git_commit with Conventional Commits format

schema:
  name: ImplementationResult
  fields:
    success:
      type: bool
      description: "True if implementation satisfies all acceptance criteria"
    files_changed:
      type: list[str]
      description: "Paths of files created or modified"
    tests_passed:
      type: bool
      description: "True if all tests pass"
    commit_hash:
      type: str
      description: "Final commit SHA, or empty string if no commits"
    summary:
      type: str
      description: "Brief implementation summary"
```

### Tools: `examples/demos/enforcer/tools/write_file.py`

```python
"""Enforcer demo tools."""

def write_file(path: str, content: str) -> str:
    """Write content to a file. Creates parent directories if needed."""
    import pathlib

    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    return f"Wrote {len(content)} chars to {path}"
```

### Demo Runner: `examples/demos/enforcer/demo.sh`

```bash
#!/bin/bash
set -euo pipefail

# Usage: ./demo.sh <path-to-fr-file>
if [[ $# -eq 0 ]]; then
  echo "Usage: $0 <path-to-feature-request.md>"
  echo ""
  echo "Run the FR enforcer agent and save structured result to result.json."
  exit 1
fi

FR_PATH="$1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}") && pwd")"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
LOG="$SCRIPT_DIR/demo-output.log"
RESULT="$SCRIPT_DIR/result.json"

cd "$PROJECT_ROOT"
source .env 2>/dev/null || true

export PROVIDER="${PROVIDER:-anthropic}"
export ANTHROPIC_MODEL="${ANTHROPIC_MODEL:-claude-sonnet-4-6}"

yamlgraph graph run examples/demos/enforcer/graph.yaml \
  --var fr_path="$FR_PATH" --json 2>>"$LOG" | \
python3 -c "
import json, sys
data = json.load(sys.stdin)
result = data.get('implementation_result')
if not isinstance(result, dict):
    print('No structured result in output', file=sys.stderr)
    sys.exit(1)
json.dump(result, sys.stdout, indent=2)
print()
with open('$RESULT', 'w') as f:
    json.dump(result, f, indent=2)
    f.write('\\n')
print(f'Result saved to $RESULT', file=sys.stderr)
" 2>&1 | tee -a "$LOG"

echo -e "\\n✓ Graph execution completed successfully" | tee -a "$LOG"
```

## Acceptance Criteria

- [x] `examples/demos/enforcer/` directory exists with graph, prompts, tools, README
- [x] `examples/demos/enforcer/graph.yaml` defines single agent node with 5 shell tools + 1 python tool (dict-style definitions)
- [x] `examples/demos/enforcer/prompts/enforcer.yaml` includes structured output schema with 5 fields
- [x] `examples/demos/enforcer/tools/write_file.py` implements file writing via python tool
- [x] `examples/demos/enforcer/demo.sh` accepts FR path argument, no hardcoded model
- [x] Graph lints clean: `yamlgraph graph lint examples/demos/enforcer/graph.yaml`
- [x] Demo runs end-to-end: `./demo.sh <fr-path> <repo-root>` completes without error
- [x] Output includes structured `implementation_result` dict with success/files_changed/tests_passed/commit_hash/summary
- [x] `demo-output.log` captured proving successful execution (demo-gate requirement)
- [x] README documents the enforcer pattern, tool constraints, and usage
- [x] Tests added: `tests/unit/test_fr462_standalone_enforcer_demo.py` tagged `@pytest.mark.req("REQ-YG-426")`
- [x] Capability registered: `capabilities/CAP-161-enforcer-demo.yaml` with REQ-YG-426
- [x] ARCHITECTURE.md includes manual row for CAP-161 and REQ-YG-426

## Alternatives Considered

1. **Use `type: copilot` instead of `type: agent`** — Copilot nodes require VS Code runtime. The whole point of this demo series is portability and scriptability. Agent nodes with shell tools are portable.

2. **Reuse enforcer from Chaplain pipeline** — The Chaplain enforcer is tightly coupled to the watcher FSM and session continuations. A standalone demo needs to be self-contained and runnable without the full pipeline infrastructure.

3. **Multi-node pipeline (plan → implement → test → commit)** — Over-engineered for a demo. A single agent node with good tools and prompt structure achieves the same result. The Chaplain unified enforce (FR-183) consolidated from 3 steps to 1 for the same reason.

4. **Include acceptance test writing** — Out of scope. Acceptance tests are authored during the plan-judge phase (FR-260). The enforcer's job is to implement against an existing contract, not write the contract.

## Related

- **FR-452** — Standalone planner demo (transforms topic → FR)
- **FR-450** — Standalone judge demo (evaluates FR → verdict)
- **FR-447** — Original judge demo (established the agent+tools pattern)
- **FR-183** — Simplified enforce pipeline (unified 3 nodes into 1)
- **FR-260** — Acceptance tests before enforce (enforcer receives pre-written tests)
- **examples/demos/planner/** — Planner demo reference implementation
- **examples/demos/judge/** — Judge demo reference implementation
- **examples/enforce/** — Chaplain enforcer graph (production reference)
- **Scripture** — Commandments 2 (demonstrate with example), 4 (honor existing patterns), 8 (document removals)

## Research Findings

1. **Planner and judge demos exist and are proven** — Both FR-452 and FR-450 are implemented and working. The enforcer completes the trilogy.

2. **Agent+tools pattern is established** — Judge demo uses `type: agent` with 4 shell tools + 1 python tool. Same pattern applies to enforcer.

3. **Portable demos are valued** — Both planner and judge demos are portable (no VS Code runtime required), making them usable in CI, scripts, and cron jobs.

4. **Chaplain enforcer is complex** — The production enforcer in `.chaplain/graphs/watcher-enforce/` uses copilot nodes, session continuations, and FSM integration. A standalone demo should be simpler and self-contained.

5. **Tool constraints are important** — Judge demo demonstrates least-privilege tool assignment (read-only tools only). Enforcer demo should follow the same pattern: read tools for exploration, write tools for implementation, test/commit tools for validation.

## Scope Assessment

**Scope is clear and minimal:**
- Single demo directory with 5 files (graph, prompts, tools, demo.sh, README)
- No framework changes required
- No modifications to existing demos or examples
- Follows proven pattern from planner and judge demos
- Completes the plan→judge→enforce trilogy

**Single responsibility:** Demonstrate the enforcer pattern in isolation, before integration into the Chaplain pipeline.

**Architecture alignment:** Follows three-layer pattern (Presentation: demo.sh, Logic: graph.yaml, Side Effects: tools.py).

## Estimated Effort

**1–2 days:**
- Day 1: Write graph, prompts, tools, demo.sh (4 hours)
- Day 1: Write README and tests (2 hours)
- Day 2: Run demo end-to-end, capture demo-output.log, register capability (4 hours)
- Day 2: Code review and refinement (2 hours)

**Blockers:** None. All dependencies (agent node type, shell tools, python tools) are already implemented.

**Risk:** Low. Pattern is proven by planner and judge demos. No framework changes required.
