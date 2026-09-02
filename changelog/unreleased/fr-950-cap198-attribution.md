---
type: fix
scope: capabilities
req: REQ-YG-541
---
- **FR-950 CAP-198 attribution and py3.14-safe fork-capability test**: CAP-198 `fr:` attribution now includes FR-950, which amended REQ-YG-541 with the Windows-safe fork-registration guarantee — its changelog fragment claimed the req while the capability registry attributed it only to FR-713, failing the cross-wiring gate. The FR-950 fork-capability test now pre-imports dependencies before deleting `os.register_at_fork`: on CPython 3.14 POSIX, stdlib `asyncio` and `random` call it at import behind an `os.fork` guard, so the bare deletion broke the interpreter instead of exercising yamlgraph's own import-time guard. (REQ-YG-541)
