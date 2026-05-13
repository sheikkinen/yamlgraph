# TypeScript Node.js Subprocess Demo

Minimal direct integration pattern for Node.js/TypeScript backends: run YAMLGraph as a subprocess and parse JSON from stdout.

## What this demonstrates

1. `yamlgraph graph run ... --json` returns machine-readable final state on stdout.
2. `child_process.execFile` consumes that JSON without MCP/A2A infrastructure.

Use this pattern for simple request/response backend calls. Prefer MCP/A2A when you need long-lived tool discovery, multi-agent orchestration, or protocol-level interoperability.

## Quick start

```bash
./demo.sh
```

## Files

```
typescript-node/
├── graph.yaml         # deterministic Python-node graph (no LLM key required)
├── tools.py           # Python function used by graph.yaml
├── package.json
├── tsconfig.json
├── src/
│   └── index.ts       # execFile("yamlgraph", ["graph", "run", ..., "--json"])
├── demo.sh
└── demo-output.log
```
