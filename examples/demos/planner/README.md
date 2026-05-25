# Standalone Planner Demo

**FR-452** — Transforms a rough topic file into a structured feature request.

Mirrors the Chaplain's `step-plan-unified.yaml` but uses `type: agent` with
shell tools instead of `type: copilot`, making it portable — runs in CI,
scripts, and cron without the VS Code runtime.

## Usage

```bash
./demo.sh <path-to-topic-file>
```

### Example

```bash
# Create a topic file
cat > /tmp/my-idea.md << 'EOF'
Add rate limiting to the CLI to prevent accidental API cost spikes.
EOF

# Run the planner
./demo.sh /tmp/my-idea.md
```

### Output

- `tmp/plan-output.md` — Generated feature request (rename with FR number)
- `plan.json` — Structured plan result with metadata

### Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `PROVIDER` | `anthropic` | LLM provider |
| `ANTHROPIC_MODEL` | `claude-sonnet-4-6` | Model for Anthropic |

## Architecture

```
planner/
├── graph.yaml          # Agent node + 5 tools
├── prompts/
│   └── planner.yaml    # PlanResult schema + instructions
├── tools/
│   └── write_file.py   # Python tool (pathlib.Path.write_text)
├── demo.sh             # CLI runner
├── demo-output.log     # Captured output
└── README.md
```

### Tools

| Tool | Type | Purpose |
|------|------|---------|
| `read_file` | shell | Read project files (topic, template, architecture) |
| `search` | shell | Search codebase with ripgrep |
| `list_dir` | shell | Explore directory structure |
| `git_log` | shell | Find prior art in git history |
| `write_file` | python | Write the FR file (`pathlib.Path.write_text`) |

### PlanResult Schema

```json
{
  "fr_path": "tmp/plan-output.md",
  "title": "Feature Title",
  "summary": "One-paragraph summary",
  "research_findings": ["finding 1", "finding 2"],
  "scope_assessment": "single_responsibility",
  "estimated_effort": "2 days with rationale"
}
```

## Pipeline Composition

The planner outputs `fr_path` in `PlanResult`, which the judge demo can
consume as input:

```bash
# Plan → Judge pipeline
./examples/demos/planner/demo.sh topic.md
./examples/demos/judge/demo.sh tmp/plan-output.md
```
