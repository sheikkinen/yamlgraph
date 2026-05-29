---
type: fix
scope: demo
req: REQ-YG-427
---
- **FR-463 Enforcer Demo Safety Hardening**: Path-restricted `write_file`/`edit_file`, removed `git_commit` (separation of concerns), added `run_command` honeypot, `git_log`, `lint`, `git_diff` tools. 10 tools total. (REQ-YG-427)
