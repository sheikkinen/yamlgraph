---
type: feat
scope: testing
---
- **FR-756 Core Test Isolation**: introduced `process` test marker with collection-time boundary lint (unmarked unit tests referencing `.chaplain/`, `examples/`, or `scripts/` fail collection), and added CI `core-test` job running `pytest tests/unit -m "not process" -q --no-cov` to prove the shipped package green in isolation.
