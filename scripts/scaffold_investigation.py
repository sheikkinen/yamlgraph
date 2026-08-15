#!/usr/bin/env python3
"""FR-792 multi-step investigation scaffold (REQ-YG-596, CAP-235).

Generates a working N-step investigation pipeline skeleton from the
architectural contract proven by the enforced API discovery instance
(FR-783..FR-791): a routing orchestrator composing per-step graph-runtime
tool manifests via ``type: tool_call`` nodes, per-step agent graph stubs
with typed output schemas, prompt stubs, and a tools/README.md.

Usage (the sole authorized surface — no CLI subcommand):

    python scripts/scaffold_investigation.py \
        --name company-research \
        --steps "registry,financials,news" \
        --home examples/company-research [--stub]

``--stub`` replaces agent/llm placeholders with deterministic passthrough
nodes so the generated orchestrator runs end-to-end without provider keys.

Operator tool: committing generated graph/prompt artifacts under governed
paths still requires the graph-authoring route (scripts/author.sh) with
its validation record (FR-792 AC-10).
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from string import Template

ORCHESTRATOR_HEADER = Template(
    """\
version: "1.0"
name: $name
description: "TODO: describe the $name investigation pipeline"

prompts_relative: true
prompts_dir: prompts

state:
  objective:
    type: str
    description: "What this investigation should find out"
$state_blocks
  result:
    type: dict
    description: "Terminal investigation result"

tools:
$tool_blocks

nodes:
$node_blocks

edges:
$edge_blocks
"""
)

ORCH_STATE_BLOCK = Template(
    """\
  ${step}_result:
    type: dict
    default: {}
    description: "${step} step tool-call wrapper"
"""
)

ORCH_TOOL_BLOCK = Template(
    """\
  $step:
    manifest: steps/$step.tool.yaml
"""
)

ORCH_NODE_BLOCK = Template(
    """\
  $step:
    type: tool_call
    tool: $step
    args:
      objective: "{state.objective}"
    state_key: ${step}_result
    on_error: fail

"""
)

SYNTH_LLM_NODE = """\
  synthesize:
    type: llm
    prompt: synthesize
    state_key: result
    on_error: fail
"""

SYNTH_STUB_NODE = """\
  synthesize:
    type: passthrough
    output:
      result:
        verdict: stub
        summary: "deterministic stub synthesis"
"""

ORCH_EDGE_BLOCK = Template(
    """\
  # TODO: add skip condition for $to_node
  - from: $from_node
    to: $to_node
"""
)

STEP_MANIFEST = Template(
    """\
# Graph-runtime tool manifest for the $step step ($name pipeline).
# Consumed by the orchestrator via type: tool_call node.

name: $step
description: "TODO: describe what the $step step investigates"
runtime:
  type: graph
  path: $step/graph.yaml
  input_mapping:
    objective: objective
  output_key: investigation_result
"""
)

STEP_GRAPH_AGENT = Template(
    """\
version: "1.0"
name: $step
description: "TODO: describe the $step investigation step"

prompts_relative: true
prompts_dir: prompts

state:
  objective:
    type: str
    description: "What this step should investigate"
  max_iterations:
    type: int
    default: 5
    description: "Maximum tool-call iterations for the agent"
  investigation_result:
    type: dict
    description: "Structured ${step}Result output"

# TODO: add shared leaf tool manifests (see ../../tools/README.md), e.g.
# tools:
#   my_tool:
#     manifest: ../../tools/my_tool.tool.yaml

nodes:
  investigate:
    type: agent
    prompt: investigate
    # TODO: add tool manifests to the tools list
    tools: []
    max_iterations: 5
    state_key: investigation_result

edges:
  - from: START
    to: investigate
  - from: investigate
    to: END
"""
)

STEP_GRAPH_STUB = Template(
    """\
version: "1.0"
name: $step
description: "Deterministic stub for the $step investigation step"

state:
  objective:
    type: str
    description: "What this step should investigate"
  investigation_result:
    type: dict
    description: "Structured ${step}Result output"

nodes:
  investigate:
    type: passthrough
    output:
      investigation_result:
        findings:
          - "stub finding from $step"
        confidence: stub

edges:
  - from: START
    to: investigate
  - from: investigate
    to: END
"""
)

STEP_PROMPT = Template(
    """\
system: |
  TODO: describe the $step investigation doctrine.

  You are the $step step of the $name investigation pipeline. Investigate
  the objective using the available tools and report only evidence-backed
  findings. Empty findings are a valid outcome; never invent results.

user: |
  Investigate this objective: {{ objective }}

  Use at most {{ max_iterations }} tool-call iterations.

output_schema:
  type: object
  properties:
    findings:
      type: array
      description: "Evidence-backed findings from the $step step"
      items:
        type: string
    confidence:
      type: string
      description: "Confidence level such as high, medium, or low"
  required:
    - findings
    - confidence
  additionalProperties: false
"""
)

SYNTH_PROMPT = Template(
    """\
system: |
  TODO: describe the synthesis doctrine for the $name pipeline.

  You are the terminal synthesis step. Combine the step results into one
  structured verdict. Report only steps whose result wrappers are
  non-empty; never invent findings.

user: |
  Objective: {{ objective }}

$result_lines

output_schema:
  type: object
  properties:
    verdict:
      type: string
      enum:
        - found
        - not_found
        - needs_manual
    summary:
      type: string
      description: "Evidence-backed synthesis of all step findings"
  required:
    - verdict
    - summary
  additionalProperties: false
"""
)

TOOLS_README = Template(
    """\
# Shared leaf tools for the $name pipeline

Shared deterministic side effects (HTTP probes, CLI queries, parsers)
live here as FR-768 `*.tool.yaml` manifests, consumed by whichever step
graph needs them via a relative `manifest:` reference:

```yaml
tools:
  my_tool:
    manifest: ../../tools/my_tool.tool.yaml
```

Each manifest declares `name` (must match the graph-local tool key),
`description`, and a `runtime` of type `shell`, `python`, or `graph`.
Paths inside a manifest resolve relative to the manifest file.

## Customizing the skeleton

- **Prompts:** replace every TODO prompt under `steps/<step>/prompts/`
  with real investigation doctrine; keep the typed `output_schema:`.
- **Conditional edges:** the orchestrator's edges carry TODO markers —
  add a `condition:` expression to skip steps based on earlier results
  (see the API discovery orchestrator for precedent).
- **Committing:** generated graph and prompt artifacts under governed
  paths must go through the graph-authoring route (`scripts/author.sh`)
  with its validation record before being committed.
"""
)


def _validate_slug(value: str, kind: str) -> str:
    if not re.fullmatch(r"[a-z][a-z0-9_-]*", value):
        raise ValueError(f"invalid {kind} {value!r}: use lowercase slugs")
    return value


def scaffold_investigation(
    name: str, steps: list[str], home: Path, *, stub: bool = False
) -> Path:
    """Generate the investigation skeleton under ``home``. Returns ``home``."""
    _validate_slug(name, "name")
    if not steps:
        raise ValueError("at least one step is required")
    for step in steps:
        _validate_slug(step, "step")
    if len(set(steps)) != len(steps):
        raise ValueError("step names must be unique")

    home = Path(home)
    (home / "steps").mkdir(parents=True, exist_ok=True)
    (home / "tools").mkdir(parents=True, exist_ok=True)

    state_blocks = "".join(ORCH_STATE_BLOCK.substitute(step=s) for s in steps)
    tool_blocks = "".join(ORCH_TOOL_BLOCK.substitute(step=s) for s in steps)
    node_blocks = "".join(ORCH_NODE_BLOCK.substitute(step=s) for s in steps)
    node_blocks += SYNTH_STUB_NODE if stub else SYNTH_LLM_NODE

    route = ["START", *steps, "synthesize", "END"]
    edge_blocks = "".join(
        ORCH_EDGE_BLOCK.substitute(from_node=a, to_node=b)
        for a, b in zip(route, route[1:], strict=False)
    )

    (home / "graph.yaml").write_text(
        ORCHESTRATOR_HEADER.substitute(
            name=name,
            state_blocks=state_blocks.rstrip("\n"),
            tool_blocks=tool_blocks.rstrip("\n"),
            node_blocks=node_blocks.rstrip("\n"),
            edge_blocks=edge_blocks.rstrip("\n"),
        )
    )

    if not stub:
        result_lines = "\n".join(
            f"  {s} result: {{{{ {s}_result | default({{}}) | tojson }}}}"
            for s in steps
        )
        (home / "prompts").mkdir(exist_ok=True)
        (home / "prompts" / "synthesize.yaml").write_text(
            SYNTH_PROMPT.substitute(name=name, result_lines=result_lines)
        )

    for step in steps:
        step_dir = home / "steps" / step
        step_dir.mkdir(parents=True, exist_ok=True)
        (home / "steps" / f"{step}.tool.yaml").write_text(
            STEP_MANIFEST.substitute(step=step, name=name)
        )
        if stub:
            (step_dir / "graph.yaml").write_text(STEP_GRAPH_STUB.substitute(step=step))
        else:
            (step_dir / "graph.yaml").write_text(STEP_GRAPH_AGENT.substitute(step=step))
        (step_dir / "prompts").mkdir(exist_ok=True)
        (step_dir / "prompts" / "investigate.yaml").write_text(
            STEP_PROMPT.substitute(step=step, name=name)
        )

    (home / "tools" / "README.md").write_text(TOOLS_README.substitute(name=name))
    return home


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument(
        "--name", required=True, help="pipeline slug, e.g. company-research"
    )
    parser.add_argument("--steps", required=True, help="comma-separated step slugs")
    parser.add_argument("--home", required=True, type=Path, help="target directory")
    parser.add_argument(
        "--stub",
        action="store_true",
        help="deterministic passthrough steps runnable without provider keys",
    )
    args = parser.parse_args()
    steps = [s.strip() for s in args.steps.split(",") if s.strip()]
    home = scaffold_investigation(args.name, steps, args.home, stub=args.stub)
    print(f"scaffolded {len(steps)}-step investigation at {home}")


if __name__ == "__main__":
    main()
