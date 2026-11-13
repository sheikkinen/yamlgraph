---
type: feat
scope: contrib
req: REQ-YG-726
---
- **FR-1159 Map memo ships as `yamlgraph.contrib.map_memo`**: the FR-1116 memo moved from `examples/shared/map_memo.py` into the package unchanged, so installed users can declare `map_memo_split` / `map_memo_merge` inline with `module: yamlgraph.contrib.map_memo`. The `examples/shared` manifests resolve the module instead of a file path; `import yamlgraph.contrib` does not load it. The new `examples/demos/map_memo` demo summarizes three notes, and a second run over unchanged notes makes zero LLM calls. A wheel witness installs the built package outside the checkout and runs a split/merge round trip from there. (REQ-YG-726)
