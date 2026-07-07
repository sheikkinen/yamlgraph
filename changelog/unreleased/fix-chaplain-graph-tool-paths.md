---
type: fix
scope: chaplain
---
- **Chaplain graph tool paths**: `enforce-session.yaml` and `philosopher/graph.yaml` declared python tool paths repo-root-relative; FR-445 confinement + FR-658 graph_root plumbing resolve `path:` against the graph root, doubling the path (`.../watcher-enforce/.chaplain/graphs/watcher-enforce/tools.py`) and killing every enforce session at launch. Paths are now graph-root-relative; the out-of-root `lib/diary.py` is reached via an in-root proxy in `philosopher/tools.py`.
