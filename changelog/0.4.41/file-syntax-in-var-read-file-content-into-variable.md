---
type: feat
scope: file
---
- **`@file` syntax in `--var`**: Read file content into variable
  - `yamlgraph graph run graph.yaml --var document=@report.txt`
  - Only treats as file if value starts with `@` (emails like `user@domain.com` stay literal)
