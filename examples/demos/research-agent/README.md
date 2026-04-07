# Research Agent Demo

5-step agentic research pipeline: **Extract Intent → Plan → Execute → Validate → Respond**.

## Usage

```bash
yamlgraph graph run examples/demos/research-agent/graph.yaml \
  --var query="How does the agent node type work?" \
  --var scope="yamlgraph/"
```

Custom scope:

```bash
yamlgraph graph run examples/demos/research-agent/graph.yaml \
  --var query="What shell tools are available?" \
  --var scope="yamlgraph/tools/"
```

## What It Does

| Step | Node | Type | Purpose |
|------|------|------|---------|
| 1 | `extract_intent` | llm | Parse query into structured fields (topic, key questions, expected artifacts) |
| 2 | `plan_research` | agent | Explore directory structure, identify relevant files, output ordered plan |
| 3 | `execute_research` | agent | Follow the plan: read files, search patterns, gather evidence |
| 4 | `validate_findings` | llm | Check findings against original intent; flag gaps and confidence |
| 5 | `synthesize_report` | llm | Combine findings + validation into final structured report |

## Key Concepts

- **Structured intent extraction** — LLM parses raw question into typed fields via Pydantic schema
- **Least-privilege tool assignment** — `plan_research` gets discovery tools only; `execute_research` gets full access
- **Explicit validation node** — Critique is a separate, auditable phase (not embedded in prompts)
- **Linear flow** — No loops; validation reports gaps but does not trigger re-execution
- **`tool_results_key`** — Raw tool call history captured for debugging

## Tools

| Tool | Description | Nodes |
|------|-------------|-------|
| `search_code` | Grep Python files for a pattern | plan, execute |
| `list_files` | List Python files in a directory | plan, execute |
| `read_file` | Read first 80 lines of a file | execute |
| `count_lines` | Count lines in a file | execute |

## Output

The final `report` state key contains a structured research report with:
- Direct answer to the original question
- File references and code evidence
- Acknowledged gaps from validation

## Related

- [code-analysis](../code-analysis/) — Agent with 8 shell tools, 2 nodes
- [feature-brainstorm](../feature-brainstorm/) — 4-node agent pipeline
- [verified-search](../verified-search/) — Verification via prompt, not separate node
- [verification-gate](../verification-gate/) — `verification` field on generation nodes
- [reflexion](../reflexion/) — Loop-back pattern with quality gates
