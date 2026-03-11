---
type: fix
scope: reqcoveragepy
---
- **req_coverage.py key collisions** — switched from `{stem}::{func}` to class-qualified `{stem}::{Class}::{func}` keys. Fixes 7 tests lost when duplicate method names appeared in different classes within the same file.
