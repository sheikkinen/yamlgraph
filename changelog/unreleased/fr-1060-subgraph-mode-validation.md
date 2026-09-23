---
type: fix
scope: subgraph
req: REQ-YG-685
---
- **FR-1060 Subgraph `mode` is validated instead of silently ignored**: `GraphConfigSchema` and `yamlgraph graph validate` now route every `type: subgraph` node through `SubgraphNodeConfig`, which has always owned the `invoke | direct` contract but was never applied to a real graph — `GraphConfigSchema.nodes` is typed `dict[str, NodeConfig]`, whose `mode` is `str | None`. An unsupported mode (`stream`, a typo) validated, ran, and silently took the invoke path; `mode: direct` combined with `input_mapping`/`output_mapping` was likewise accepted even though the model rejects it. Both now fail validation with a diagnostic naming the supported modes. The linter no longer emits W501/W502 against `mode: direct`, where the mappings it recommended are the ones validation rejects, and the `reference/graph-yaml.md` property table documents `direct` rather than the nonexistent `stream`. (REQ-YG-685)
