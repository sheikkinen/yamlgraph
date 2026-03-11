---
type: feat
scope: skipifexists
---
- **FR-050 skip_if_exists semantics (BREAKING)**: Now checks truthiness, not existence. Empty `[]`, `""`, `None`, `0`, `False` do NOT trigger skip — fixes diary-digest curate_seeds bug
