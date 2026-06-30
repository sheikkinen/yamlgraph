---
type: feat
scope: tools
req: REQ-YG-474
---
- **FR-625 Built-in write_data_file Tool**: Adds `type: write_data_file` tool type that writes structured data (dict/list) to YAML files within the graph workspace. Symmetric counterpart to `data_files` read directive. Features: graph-relative path resolution, atomic writes (tempfile + os.replace), path traversal guard, self-modification guard via compile-time closure (graph file and prompts_dir protected). YAML-only in v1. (REQ-YG-474, REQ-YG-475, REQ-YG-476, REQ-YG-477)
