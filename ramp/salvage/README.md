# Salvage — scripture-dev

Assets lifted under FR-868 before `scripture-dev` was archived.
Source: `https://github.com/sheikkinen/scripture-dev` at
`9d4677a9d501b686d1408d69145debc5c116dd99` (the classified SHA).

Lift decision (2026-08-24, operator-delegated): **pattern pair only**
out of the graph's 25-lift proposal — the raw read (FR-868 AC-10)
found the rest inflated (`plausible_wrong_answer`).

| file | why lifted |
|---|---|
| `render.sh` | The parameterised-rendering idea: `__PLACEHOLDER__` templates rendered from a tiny YAML config, POSIX-only, no PyYAML. Candidate mechanism for parameterising `ramp/assets/` per target. |
| `scripture.yaml` | The config half of the pair — six keys (prefixes, size/complexity/coverage gates) that name exactly what varies per target repo. |

These are preserved as a **pattern reference**, not wired into
`ramp/manifest.yaml`. If the ramp installer grows per-target
parameterisation, this is the precedent to consult (or consciously
reject) first.
