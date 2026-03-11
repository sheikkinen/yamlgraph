---
type: fix
scope: e103
---
- **E103 Linter False Positive**: Guard-condition edges (`condition: "expr"`) targeting a router node no longer trigger E103. E103 now only fires for `type: conditional` fan-out edges with a single string target. Previously, valid expression edges to routers were incorrectly flagged, and the suggested fix (`to: [node]`) caused a runtime crash ("unhashable type: 'list'").
