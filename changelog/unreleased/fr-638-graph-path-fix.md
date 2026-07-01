---
type: fix
scope: examples
req: REQ-YG-487
---
- **FR-638 Graph Path Fix**: Move novel_fandom subgraphs to example root
  so `data_files` glob resolves within the graph directory. Fix roster
  JSON string parsing in `retrieve_window`. (REQ-YG-487)
