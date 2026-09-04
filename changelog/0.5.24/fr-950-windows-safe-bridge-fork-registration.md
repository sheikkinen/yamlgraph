---
type: fix
scope: bridge
req: REQ-YG-541
---
- **FR-950 Windows-safe bridge fork registration**: `yamlgraph/utils/bridge.py` called `os.register_at_fork` unconditionally at module import, raising `AttributeError` on Windows and disabling every entry point — `import yamlgraph`, `yamlgraph graph lint`, `yamlgraph graph run`, and pytest collection — before argument parsing began. The registration is now guarded by runtime capability detection: fork-capable runtimes keep FR-713's child reset unchanged, and runtimes without `os.register_at_fork` perform no fork setup. Neither path starts the bridge loop thread at import. (REQ-YG-541)
