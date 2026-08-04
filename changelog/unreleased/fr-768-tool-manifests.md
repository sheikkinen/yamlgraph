---
type: feat
scope: tools
req: REQ-YG-574
---
- **FR-768 Tool Manifests**: `manifest:` key in `tools:` entries loads a typed
  manifest YAML and translates it into the equivalent inline shell/python/graph
  tool declaration at graph load. Manifest paths resolve relative to the graph;
  runtime paths resolve relative to the manifest. Invalid manifests fail at
  load, never at invocation. Translation only — no new execution engine.
  (REQ-YG-574)
