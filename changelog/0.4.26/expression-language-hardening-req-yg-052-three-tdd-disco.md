---
type: fix
scope: expression
req: REQ-YG-052
---
- **Expression language hardening (REQ-YG-052)** — Three TDD-discovered defects fixed: (1) quote-aware compound split — `and`/`or` inside quoted string values no longer breaks conditions; (2) right-side state reference — unquoted identifiers resolve as state path before literal fallback, enabling `score < threshold`; (3) chained arithmetic detection — `{state.a + state.b + state.c}` raises `ValueError` instead of silent wrong results. 24 new tests.
