---
type: fix
scope: loader
req: REQ-YG-565
---
- **FR-747 Loader Error UX**: the two FR-744 boundary errors now name their fix. `load_prompt` raises the prompt contract when a YAML uses a `messages:` role list (parsed-structure detection, F3); `module:` import failures hint `path: <mod>.py` only when the file exists next to the graph (F2); `graph lint` gains a prompt-resolution pass (E006) and a module-vs-graph-local check (E008) closing the witnessed lint gap (AC-03). (REQ-YG-565)
