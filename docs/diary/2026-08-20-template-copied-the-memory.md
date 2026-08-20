# 2026-08-20 — The Template Copied the Memory

The fresh cookbook fork looked correct: new repository, two secrets, green auth
probe, owner issue #1. Intake completed green in 34 seconds — suspiciously
fast. The step record showed slug and pipeline skipped. The template had copied
the source repository's append-only issue ledger, where issue #1 was already
terminal. Idempotency keyed only on the integer, so memory from one repository
became identity in another.

**Trap: treating copied state as harmless example data.** A template copies
tracked operational state as faithfully as code. State without provenance is
not portable; once copied, its local identifiers impersonate the new system's
identifiers. The false-green workflow made this worse: idempotent skip is
success in the source repo but silent starvation in a new repo.

**Heuristic:** every durable key that can cross a repository boundary must carry
repository identity before comparison. Template initialization should be
tested with the lowest local identifier, especially issue #1, not with an
unused high number that evades inherited state.

**Outcome:** RED `e3a2242`, GREEN `fc5a844`; ledger identity is now
`(repository, issue)`, 17 canonical records retained exact order and values,
55 tests and remote CI passed, and the failed witness remains public rather
than being rewritten into success.

**Seed:** should gitclaw report `skip-terminal` back to the issue even when it is
legitimate, so idempotency can never masquerade as an unexplained green no-op?
