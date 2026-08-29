---
type: fix
scope: process
req: REQ-YG-627
---
- **FR-907 FR number uniqueness guard**: `tests/unit/test_fr_numbering.py` fails when two feature requests claim the same number. Concurrent sessions allocate FR numbers by reading the directory and incrementing, so they reliably collide — 36 duplicated numbers had accumulated since FR-082, and FR-900/901/902 each landed on `main` twice. The 36 are grandfathered as a ratchet that may shrink but never grow; every new collision now fails at commit time. (REQ-YG-627)
