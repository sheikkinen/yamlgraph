# Multi-Step Investigation Scaffold (FR-792)

Generate a working N-step investigation pipeline skeleton from the
architectural contract proven by the API discovery family (FR-783..FR-791):
orchestrator → graph-runtime step manifests → step graphs → shared leaf
tool manifests.

## Invocation (the sole surface)

```bash
python scripts/scaffold_investigation.py \
  --name company-research \
  --steps "registry,financials,news,sanctions" \
  --home examples/company-research
```

There is no `yamlgraph graph scaffold` CLI subcommand (FR-792 R-2).

## Generated skeleton contract

```
<home>/
├── graph.yaml                       # orchestrator: tool_call node per step,
│                                    # TODO skip-condition edges, synthesize terminal
├── prompts/synthesize.yaml          # terminal verdict schema (found/not_found/needs_manual)
├── steps/
│   ├── <step>.tool.yaml             # runtime.type: graph manifest per step
│   └── <step>/
│       ├── graph.yaml               # single agent node, tools: [] TODO, max_iterations 5
│       └── prompts/investigate.yaml # TODO prompt with findings/confidence output_schema
└── tools/README.md                  # how to add FR-768 leaf manifests, edges, prompts
```

Every generated graph passes `yamlgraph graph lint` out of the box.

## `--stub` mode

`--stub` replaces agent/llm placeholders with deterministic passthrough
nodes: each step emits a canned `findings`/`confidence` result and the
synthesize terminal emits `verdict: stub`. The stub orchestrator runs
end-to-end via `yamlgraph graph run` (or `load_and_compile(...).compile().invoke(...)`)
with no provider keys — used by the FR-792 pytest smoke.

## Governance

The scaffold is an operator tool, not a bypass of the graph-authoring
sole route: committing generated `graph.yaml`/`prompts/*.yaml` artifacts
under governed paths still requires `scripts/author.sh` with its
validation record (FR-792 AC-10, FR-767).
