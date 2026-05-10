---
type: fix
scope: chaplain
---
- **fix(chaplain): tighten bash\_context placeholder regex** — `\{[^}]+\}` matched shell group syntax and JSON literals, producing spurious warnings on every pipeline run. Tightened to `\{[a-zA-Z_]\w*\}`.
