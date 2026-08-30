---
type: removal
scope: cli
---
- **FR-912 Retire the skill/agent export surface**: Deleted `yamlgraph skill export` — the `skill` CLI group, `yamlgraph/export/skill.py`, `yamlgraph/export/skill_writer.py`, `yamlgraph/cli/skill_commands.py`, `reference/skills-export.md`, and the three FR-348/350/351 acceptance test files. Four months in the tree produced zero committed artifacts: every `.github/skills/**` file is hand-authored, including the flagship graph-authoring skill written by hand while the generator existed. CAP-142 and CAP-143 are now `status: retired`. With FR-910's MCP module already gone, the `yamlgraph/export/` package retires with its last member and the `export-seam` and `compile-seam` import-linter contracts retire with it.
