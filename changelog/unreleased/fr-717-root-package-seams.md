---
type: feat
scope: architecture
req: REQ-YG-546
---
- **FR-717 Root-Package Seams**: Layer 2's flat bag of 27 root modules gains three named seams as packages — `yamlgraph/a2a/` (server, message), `yamlgraph/export/` (skill, skill_writer, mcp), and `yamlgraph/compile/` (graph_loader, node_compiler, edge_compiler, map_compiler, pipeline_template, verify_insert). Move-only (rename similarity 99–100%, witnessed per PR); root module count 27 → 17. Three new import-linter contracts turn the implicit clusters into enforced boundaries: a2a and export are leaves the linter/compilers never import; compile never imports the leaf surfaces (5 contracts kept). Top-level re-exports unchanged. (REQ-YG-546)
