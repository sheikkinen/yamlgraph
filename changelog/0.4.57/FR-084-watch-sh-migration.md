---
type: feat
scope: watchsh
---
- **FR-084 Watch.sh Migration** Migrate `.chaplain/watch.sh` from inline copilot calls to `yamlgraph graph run`. Added `.chaplain/graph.yaml` (Plan→Judge workflow) and `.chaplain/prompts/{plan,judge}.yaml`. The bash script is now a thin polling wrapper; all workflow logic lives in the YAMLGraph graph.
