# FR Enforcer Demo

**Standalone feature request implementation agent** that transforms a planned and judged feature request into working code, tests, and commits.

Part of the **plan → judge → enforce** trilogy:
- [Planner Demo](../planner/) — transforms topic → FR
- [Judge Demo](../judge/) — evaluates FR → verdict
- **Enforcer Demo** — implements FR → code + tests + commits

## Quick Start

```bash
# Run the enforcer on a feature request
./demo.sh feature-requests/FR-462-standalone-enforcer-demo.md

# View the structured result
cat result.json
```

## Architecture

### Graph: `graph.yaml`

Single agent node with 6 task-shaped tools:

| Tool | Type | Purpose |
|------|------|---------|
| `read_file` | shell | Read project files |
| `search` | shell | Search codebase with ripgrep |
| `list_dir` | shell | List directory contents |
| `run_tests` | shell | Run pytest on test files |
| `git_commit` | shell | Stage and commit changes |
| `write_file` | python | Write files with parent dir creation |

**Agent configuration:**
- `max_iterations: 25` — bounded exploration
- `temperature: 0.3` — deterministic implementation
- Structured output schema: `ImplementationResult`

### Prompt: `prompts/enforcer.yaml`

Guides the agent through:
1. Read the FR to understand requirements
2. Explore codebase for patterns
3. Implement incrementally
4. Run tests to verify
5. Commit with Conventional Commits format

Returns structured `ImplementationResult`:
```json
{
  "success": true,
  "files_changed": ["yamlgraph/new_module.py", "tests/unit/test_new_module.py"],
  "tests_passed": true,
  "commit_hash": "a1b2c3d4...",
  "summary": "Implemented FR-462 with 3 new modules and 45 tests"
}
```

### Tools: `tools/write_file.py`

Python tool for file writing with automatic parent directory creation.

### Runner: `demo.sh`

Portable shell script that:
1. Accepts FR path as argument
2. Sets up environment (provider, model)
3. Runs the graph with `--json` output
4. Parses structured result
5. Saves to `result.json`
6. Logs execution to `demo-output.log`

## Tool Constraints

Following the **least-privilege principle**:

| Tool | Capability | Constraint |
|------|-----------|-----------|
| `read_file` | Read-only | No write access |
| `search` | Read-only | Pattern matching only |
| `list_dir` | Read-only | Directory listing only |
| `run_tests` | Execute | Pytest only, no arbitrary commands |
| `write_file` | Write | File creation only, no deletion |
| `git_commit` | Execute | Commit only, no force push |

## Usage Patterns

### Standalone Implementation

```bash
# Implement a single FR
./demo.sh feature-requests/FR-462-standalone-enforcer-demo.md

# Check result
jq .success result.json
```

### CI/CD Integration

```bash
# In a GitHub Actions workflow
- name: Enforce FR
  run: |
    cd examples/demos/enforcer
    ./demo.sh "${{ github.event.inputs.fr_path }}"

- name: Upload result
  uses: actions/upload-artifact@v4
  with:
    name: implementation-result
    path: examples/demos/enforcer/result.json
```

### Chaining with Planner and Judge

```bash
# Full pipeline: topic → FR → verdict → implementation
cd examples/demos/planner
./demo.sh my-topic.md
FR_PATH=$(jq -r .fr_path planner/result.json)

cd ../judge
./demo.sh "$FR_PATH"
VERDICT=$(jq -r .verdict judge/result.json)

if [[ "$VERDICT" == "APPROVE" ]]; then
  cd ../enforcer
  ./demo.sh "$FR_PATH"
fi
```

## Implementation Notes

### Acceptance Criteria Validation

The enforcer validates all acceptance criteria from the FR:
- ✅ Files created/modified match expected paths
- ✅ Tests pass (run via `run_tests` tool)
- ✅ Commits follow Conventional Commits format
- ✅ Code follows existing patterns (verified via search)

### Error Recovery

If tests fail:
1. Agent reads error output
2. Analyzes root cause
3. Fixes code
4. Re-runs tests
5. Repeats up to 5 cycles

### State Preservation

The agent maintains state across iterations:
- `files_changed` accumulates all modifications
- `commit_hash` captures final commit
- `tests_passed` reflects final test status

## Related

- **FR-452** — Standalone planner demo
- **FR-450** — Standalone judge demo
- **FR-462** — This enforcer demo (completes the trilogy)
- **ARCHITECTURE.md** — Design philosophy and patterns
- **reference/patterns.md** — Implementation patterns

## Troubleshooting

### No output from graph

Check that the FR path is correct:
```bash
ls -la feature-requests/FR-462-standalone-enforcer-demo.md
```

### Tests fail to run

Verify pytest is installed:
```bash
pytest --version
```

### Git commit fails

Check that you're in a git repository:
```bash
git status
```

### Model not found

Set the model explicitly:
```bash
export ANTHROPIC_MODEL=claude-opus-4-1
./demo.sh feature-requests/FR-462-standalone-enforcer-demo.md
```

## Design Philosophy

The enforcer follows the **three-layer architecture** (ARCHITECTURE.md):

```
Presentation: demo.sh (shell script, no Python)
Logic:        graph.yaml (agent node with tools)
Side Effects: tools/ (file I/O, git, pytest)
```

**Why this pattern?**
- **Portable**: No VS Code runtime required
- **Scriptable**: Works in CI, cron, containers
- **Composable**: Chains with planner and judge
- **Observable**: Structured JSON output
- **Testable**: Each tool is independently verifiable

## Contributing

To extend the enforcer:

1. **Add a new tool** in `graph.yaml` under `tools:`
2. **Update the prompt** in `prompts/enforcer.yaml` to use the tool
3. **Test locally** with `./demo.sh <fr-path>`
4. **Document** in this README

Example: Adding a `format_code` tool

```yaml
# graph.yaml
tools:
  format_code:
    type: shell
    command: ruff format {path}
    description: "Format Python code with ruff."
    parse: text

# prompts/enforcer.yaml
# Add to tool list in system prompt
```

## License

Same as YAMLGraph (MIT).
